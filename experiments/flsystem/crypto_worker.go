package party

import (
	"crypto/ed25519"
	"crypto/rand"
	"encoding/json"
	"fmt"
	"io"
	"sync"

	"github.com/DyCAPSTeam/DyCAPS/internal/bls"
	"github.com/DyCAPSTeam/DyCAPS/pkg/core"
	"github.com/DyCAPSTeam/DyCAPS/pkg/protobuf"
	"golang.org/x/crypto/nacl/box"
	"google.golang.org/protobuf/proto"
)

type runtimeCipher [2][]byte

type runtimePacket struct {
	Recipient  int
	Sender     uint32
	Kind       string
	Ciphertext []byte
	Signature  []byte
}

type runtimeTransfer struct {
	SID        string
	Generation uint32
	Public     []byte
	Signer     []byte
	Packets    []runtimePacket
	Aggregate  []runtimeCipher
	Updates    []string
	Limit      int
	Bound      int
}

type runtimeRequest struct {
	Operation  string
	SID        string
	Update     string
	Dimension  int
	Limit      int
	Bound      int
	Public     []byte
	Values     []int
	Ciphertext []runtimeCipher
	Recipients [][32]byte
	Transfer   runtimeTransfer
}

type runtimeState struct {
	members    []*HonestParty
	public     *bls.G1Point
	aggregate  []runtimeCipher
	updates    []string
	generation uint32
	limit      int
	bound      int
	frozen     bool
	result     []int
}

func runtimeGroup(generation uint32) []*HonestParty {
	private, public := SigKeyGen(4, 3)
	members := make([]*HonestParty, 4)
	inboxes := make([]chan *protobuf.Message, 4)
	for index := range members {
		members[index] = NewHonestParty(generation, 4, 1, uint32(index), nil, nil, nil, nil, public, private[index])
		inboxes[index] = make(chan *protobuf.Message, 1024)
		members[index].dispatchChannels = core.MakeDispatcheChannels(inboxes[index], 4)
	}
	for _, member := range members {
		for recipient := range members {
			member.sendChannels[recipient] = inboxes[recipient]
		}
	}
	return members
}

func runtimeParallel(members []*HonestParty, operation func(*HonestParty)) {
	var pending sync.WaitGroup
	for _, member := range members {
		pending.Add(1)
		go func(member *HonestParty) { defer pending.Done(); operation(member) }(member)
	}
	pending.Wait()
}

func runtimeScalar(value int) bls.Fr {
	var scalar bls.Fr
	if value < 0 {
		bls.AsFr(&scalar, uint64(-value))
		bls.SubModFr(&scalar, &bls.ZERO, &scalar)
	} else {
		bls.AsFr(&scalar, uint64(value))
	}
	return scalar
}

func runtimeEncrypt(public []byte, values []int) ([]runtimeCipher, error) {
	key, err := bls.FromCompressedG1(public)
	if err != nil {
		return nil, err
	}
	output := make([]runtimeCipher, len(values))
	for coordinate, value := range values {
		randomizer, scalar := bls.RandomFr(), runtimeScalar(value)
		var first, second, message bls.G1Point
		bls.MulG1(&first, &bls.GenG1, randomizer)
		bls.MulG1(&second, key, randomizer)
		bls.MulG1(&message, &bls.GenG1, &scalar)
		bls.AddG1(&second, &second, &message)
		output[coordinate] = runtimeCipher{bls.ToCompressedG1(&first), bls.ToCompressedG1(&second)}
	}
	return output, nil
}

func runtimeAdd(left, right []runtimeCipher) ([]runtimeCipher, error) {
	if len(left) != len(right) {
		return nil, fmt.Errorf("ciphertext dimension mismatch")
	}
	output := make([]runtimeCipher, len(left))
	for coordinate := range left {
		for part := 0; part < 2; part++ {
			first, err := bls.FromCompressedG1(left[coordinate][part])
			if err != nil {
				return nil, err
			}
			second, err := bls.FromCompressedG1(right[coordinate][part])
			if err != nil {
				return nil, err
			}
			bls.AddG1(first, first, second)
			output[coordinate][part] = bls.ToCompressedG1(first)
		}
	}
	return output, nil
}

func runtimeHeader(sid string, generation uint32, packet runtimePacket) []byte {
	data, _ := json.Marshal([]any{sid, generation, packet.Recipient, packet.Sender, packet.Kind})
	return data
}

func runtimeOpen(state *runtimeState) ([]int, error) {
	indices, weights := make([]bls.Fr, 2), make([]bls.Fr, 2)
	bls.AsFr(&indices[0], 1)
	bls.AsFr(&indices[1], 2)
	GetLagrangeCoefficients(1, indices, bls.ZERO, weights)
	points := make([]bls.G1Point, 2)
	for index := range points {
		bls.MulG1(&points[index], &bls.GenG1, &state.members[index].fullShare[0])
	}
	if !bls.EqualG1(bls.LinCombG1(points, weights), state.public) {
		return nil, fmt.Errorf("instance public key changed")
	}
	lookup := make(map[string]int, 2*state.bound+1)
	scalar := runtimeScalar(-state.bound)
	var candidate bls.G1Point
	bls.MulG1(&candidate, &bls.GenG1, &scalar)
	for value := -state.bound; value <= state.bound; value++ {
		lookup[string(bls.ToCompressedG1(&candidate))] = value
		bls.AddG1(&candidate, &candidate, &bls.GenG1)
	}
	result := make([]int, len(state.aggregate))
	for coordinate, ciphertext := range state.aggregate {
		first, err := bls.FromCompressedG1(ciphertext[0])
		if err != nil {
			return nil, err
		}
		second, err := bls.FromCompressedG1(ciphertext[1])
		if err != nil {
			return nil, err
		}
		for index := range points {
			bls.MulG1(&points[index], first, &state.members[index].fullShare[0])
		}
		var recovered bls.G1Point
		bls.SubG1(&recovered, second, bls.LinCombG1(points, weights))
		value, ok := lookup[string(bls.ToCompressedG1(&recovered))]
		if !ok {
			return nil, fmt.Errorf("aggregate outside configured integer bound")
		}
		result[coordinate] = value
	}
	return result, nil
}

func RunFLWorker(input io.Reader, output io.Writer) error {
	states := make(map[string]*runtimeState)
	receiverPublic, receiverPrivate := make([][32]byte, 4), make([][32]byte, 4)
	for index := range receiverPublic {
		public, private, err := box.GenerateKey(rand.Reader)
		if err != nil {
			return err
		}
		receiverPublic[index], receiverPrivate[index] = *public, *private
	}
	decoder, encoder := json.NewDecoder(input), json.NewEncoder(output)
	for {
		var request runtimeRequest
		if err := decoder.Decode(&request); err == io.EOF {
			return nil
		} else if err != nil {
			return err
		}
		response, err := runtimeExecute(request, states, receiverPublic, receiverPrivate)
		if err != nil {
			return fmt.Errorf("%s/%s: %w", request.Operation, request.SID, err)
		}
		if err := encoder.Encode(response); err != nil {
			return err
		}
	}
}

func runtimeExecute(request runtimeRequest, states map[string]*runtimeState, receiverPublic, receiverPrivate [][32]byte) (any, error) {
	state := states[request.SID]
	switch request.Operation {
	case "encrypt":
		return runtimeEncrypt(request.Public, request.Values)
	case "receivers":
		return receiverPublic, nil
	case "init":
		if state != nil || request.SID == "" || request.Dimension < 1 || request.Limit < 1 || request.Bound < 1 {
			return nil, fmt.Errorf("invalid instance initialization")
		}
		members, secret := runtimeGroup(0), bls.RandomFr()
		dealer := &Client{HonestParty: NewHonestParty(0, 4, 1, 0x7fffffff, nil, nil, nil, nil, nil, nil)}
		dealer.SetSecret(*secret)
		identifier := []byte(request.SID + "/share")
		for recipient, member := range members {
			dealer.sendChannels[recipient] = member.GetMessage("VSSSend", identifier)
		}
		dealer.Share(identifier)
		runtimeParallel(members, func(member *HonestParty) { member.VSSShareReceive(identifier) })
		var public bls.G1Point
		bls.MulG1(&public, &bls.GenG1, secret)
		aggregate, err := runtimeEncrypt(bls.ToCompressedG1(&public), make([]int, request.Dimension))
		if err != nil {
			return nil, err
		}
		states[request.SID] = &runtimeState{members: members, public: &public, aggregate: aggregate, limit: request.Limit, bound: request.Bound}
		return map[string]any{"public": bls.ToCompressedG1(&public)}, nil
	case "receive":
		transfer := request.Transfer
		if state != nil || transfer.SID != request.SID || len(transfer.Packets) != 32 || len(transfer.Signer) != ed25519.PublicKeySize {
			return nil, fmt.Errorf("invalid transfer")
		}
		members := runtimeGroup(transfer.Generation)
		seen := make(map[string]bool)
		for _, packet := range transfer.Packets {
			if packet.Recipient < 0 || packet.Recipient >= 4 || packet.Sender >= 4 || (packet.Kind != "Prepare" && packet.Kind != "ShareReduce") {
				return nil, fmt.Errorf("invalid packet role")
			}
			header := runtimeHeader(transfer.SID, transfer.Generation, packet)
			if seen[string(header)] || !ed25519.Verify(transfer.Signer, append(header, packet.Ciphertext...), packet.Signature) {
				return nil, fmt.Errorf("invalid or duplicate packet")
			}
			seen[string(header)] = true
			plaintext, ok := box.OpenAnonymous(nil, packet.Ciphertext, &receiverPublic[packet.Recipient], &receiverPrivate[packet.Recipient])
			if !ok {
				return nil, fmt.Errorf("packet decryption failed")
			}
			message := new(protobuf.Message)
			if err := proto.Unmarshal(plaintext, message); err != nil {
				return nil, err
			}
			identifier := fmt.Sprintf("%s/%d/%s", transfer.SID, transfer.Generation, packet.Kind)
			if message.Sender != packet.Sender || message.Type != packet.Kind || string(message.Id) != identifier {
				return nil, fmt.Errorf("packet context mismatch")
			}
			members[packet.Recipient].GetMessage(message.Type, message.Id) <- message
		}
		runtimeParallel(members, func(member *HonestParty) {
			member.PrepareReceive([]byte(fmt.Sprintf("%s/%d/Prepare", transfer.SID, transfer.Generation)))
		})
		runtimeParallel(members, func(member *HonestParty) {
			member.ShareReduceReceive([]byte(fmt.Sprintf("%s/%d/ShareReduce", transfer.SID, transfer.Generation)))
		})
		runtimeParallel(members, func(member *HonestParty) {
			member.ProactivizeAndShareDist([]byte(fmt.Sprintf("%s/%d/refresh", transfer.SID, transfer.Generation)))
		})
		public, err := bls.FromCompressedG1(transfer.Public)
		if err != nil {
			return nil, err
		}
		states[request.SID] = &runtimeState{members: members, public: public, aggregate: transfer.Aggregate, updates: transfer.Updates, generation: transfer.Generation, limit: transfer.Limit, bound: transfer.Bound}
		return map[string]any{"generation": transfer.Generation, "retained_updates": len(transfer.Updates)}, nil
	}
	if state == nil {
		return nil, fmt.Errorf("unknown instance")
	}
	switch request.Operation {
	case "add":
		if state.frozen || len(state.updates) >= state.limit || request.Update == "" {
			return nil, fmt.Errorf("instance admission closed")
		}
		for _, update := range state.updates {
			if update == request.Update {
				return nil, fmt.Errorf("duplicate update")
			}
		}
		aggregate, err := runtimeAdd(state.aggregate, request.Ciphertext)
		if err != nil {
			return nil, err
		}
		state.aggregate = aggregate
		state.updates = append(state.updates, request.Update)
		return map[string]any{"accepted": len(state.updates)}, nil
	case "export":
		if state.frozen || len(state.updates) >= state.limit || len(request.Recipients) != 4 {
			return nil, fmt.Errorf("export requires an active instance and four recipients")
		}
		public, private, err := ed25519.GenerateKey(rand.Reader)
		if err != nil {
			return nil, err
		}
		transfer := runtimeTransfer{SID: request.SID, Generation: state.generation + 1, Public: bls.ToCompressedG1(state.public), Signer: public, Aggregate: state.aggregate, Updates: state.updates, Limit: state.limit, Bound: state.bound}
		for _, member := range state.members {
			for recipient := range state.members {
				member.sendToNextChannels[recipient] = make(chan *protobuf.Message, 2)
			}
			member.PrepareSend([]byte(fmt.Sprintf("%s/%d/Prepare", request.SID, transfer.Generation)))
			member.ShareReduceSend([]byte(fmt.Sprintf("%s/%d/ShareReduce", request.SID, transfer.Generation)))
			for recipient := range state.members {
				for count := 0; count < 2; count++ {
					message := <-member.sendToNextChannels[recipient]
					plaintext, err := proto.Marshal(message)
					if err != nil {
						return nil, err
					}
					ciphertext, err := box.SealAnonymous(nil, plaintext, &request.Recipients[recipient], rand.Reader)
					if err != nil {
						return nil, err
					}
					packet := runtimePacket{Recipient: recipient, Sender: member.PID, Kind: message.Type, Ciphertext: ciphertext}
					packet.Signature = ed25519.Sign(private, append(runtimeHeader(request.SID, transfer.Generation, packet), ciphertext...))
					transfer.Packets = append(transfer.Packets, packet)
				}
			}
		}
		state.frozen = true
		return transfer, nil
	case "open":
		if state.frozen || len(state.updates) != state.limit {
			return nil, fmt.Errorf("opening requires a full authorized instance")
		}
		if state.result == nil {
			result, err := runtimeOpen(state)
			if err != nil {
				return nil, err
			}
			state.result = result
		}
		return state.result, nil
	case "retire":
		if !state.frozen && state.result == nil {
			return nil, fmt.Errorf("retirement requires transfer or completed opening")
		}
		delete(states, request.SID)
		return map[string]any{"retired": request.SID}, nil
	default:
		return nil, fmt.Errorf("unknown operation")
	}
}
