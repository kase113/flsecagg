package party

import (
	"crypto/ed25519"
	cryptorand "crypto/rand"
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"sync"
	"testing"
	"time"

	"github.com/DyCAPSTeam/DyCAPS/internal/bls"
	"github.com/DyCAPSTeam/DyCAPS/pkg/core"
	"github.com/DyCAPSTeam/DyCAPS/pkg/protobuf"
	"golang.org/x/crypto/nacl/box"
	"google.golang.org/protobuf/proto"
)

type flCiphertext struct {
	First  []byte
	Second []byte
}

type flEnvelope struct {
	Recipient  uint32
	Sender     uint32
	Type       string
	Ciphertext []byte
	Signature  []byte
}

type flHandoff struct {
	Instance             string
	Generation           int
	PublicKey            []byte
	SignerPublic         []byte
	RecipientPublicKeys  [][]byte
	RecipientPrivateKeys [][]byte
	OldSharePoints       [][]byte
	Packets              [][]flEnvelope
	Prefix               []flCiphertext
}

type flStoredHandoff struct {
	Instance            string
	Generation          int
	PublicKey           []byte
	SignerPublic        []byte
	RecipientPublicKeys [][]byte
	OldSharePoints      [][]byte
	Packets             [][]flEnvelope
	Prefix              []flCiphertext
}

type flRecipientKeys struct {
	RecipientPrivateKeys [][]byte `json:"recipient_private_keys"`
}

func flWrite(t *testing.T, path string, value any) {
	t.Helper()
	data, err := json.MarshalIndent(value, "", "  ")
	if err != nil {
		t.Fatal(err)
	}
	if err := os.WriteFile(path, data, 0600); err != nil {
		t.Fatal(err)
	}
}

func flGroup(epoch uint32) []*HonestParty {
	privateKeys, publicKey := SigKeyGen(4, 3)
	members := make([]*HonestParty, 4)
	inboxes := make([]chan *protobuf.Message, 4)
	for index := range members {
		members[index] = NewHonestParty(epoch, 4, 1, uint32(index), nil, nil, nil, nil, publicKey, privateKeys[index])
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

func flParallel(members []*HonestParty, operation func(*HonestParty)) {
	var pending sync.WaitGroup
	for _, member := range members {
		pending.Add(1)
		go func(member *HonestParty) {
			defer pending.Done()
			operation(member)
		}(member)
	}
	pending.Wait()
}

func flPoint(t *testing.T, data []byte) *bls.G1Point {
	t.Helper()
	point, err := bls.FromCompressedG1(data)
	if err != nil {
		t.Fatal(err)
	}
	return point
}

func flScalar(value int) bls.Fr {
	var scalar bls.Fr
	if value < 0 {
		bls.AsFr(&scalar, uint64(-value))
		bls.SubModFr(&scalar, &bls.ZERO, &scalar)
	} else {
		bls.AsFr(&scalar, uint64(value))
	}
	return scalar
}

func flEncrypt(publicKey *bls.G1Point, value int) flCiphertext {
	scalar := flScalar(value)
	randomizer := bls.RandomFr()
	var first, second, message bls.G1Point
	bls.MulG1(&first, &bls.GenG1, randomizer)
	bls.MulG1(&second, publicKey, randomizer)
	bls.MulG1(&message, &bls.GenG1, &scalar)
	bls.AddG1(&second, &second, &message)
	return flCiphertext{bls.ToCompressedG1(&first), bls.ToCompressedG1(&second)}
}

func flDecode(t *testing.T, point *bls.G1Point) int {
	t.Helper()
	for value := -48; value <= 48; value++ {
		scalar := flScalar(value)
		var candidate bls.G1Point
		bls.MulG1(&candidate, &bls.GenG1, &scalar)
		if bls.EqualG1(&candidate, point) {
			return value
		}
	}
	t.Fatal("aggregate coefficient outside [-48,48]")
	return 0
}

func flAdd(t *testing.T, left, right flCiphertext) flCiphertext {
	var first, second bls.G1Point
	bls.AddG1(&first, flPoint(t, left.First), flPoint(t, right.First))
	bls.AddG1(&second, flPoint(t, left.Second), flPoint(t, right.Second))
	return flCiphertext{bls.ToCompressedG1(&first), bls.ToCompressedG1(&second)}
}

func flEnvelopeHeader(envelope flEnvelope) []byte {
	return []byte(fmt.Sprintf("dycaps-fl-v1/%d/%d/%s/", envelope.Recipient, envelope.Sender, envelope.Type))
}

func flSeal(t *testing.T, recipient, sender uint32, message *protobuf.Message, recipientKey *[32]byte, signer ed25519.PrivateKey) flEnvelope {
	t.Helper()
	plaintext, err := proto.Marshal(message)
	if err != nil {
		t.Fatal(err)
	}
	envelope := flEnvelope{Recipient: recipient, Sender: sender, Type: message.Type}
	envelope.Ciphertext, err = box.SealAnonymous(nil, plaintext, recipientKey, cryptorand.Reader)
	if err != nil {
		t.Fatal(err)
	}
	envelope.Signature = ed25519.Sign(signer, append(flEnvelopeHeader(envelope), envelope.Ciphertext...))
	return envelope
}

func flOpen(t *testing.T, envelope flEnvelope, recipientPublic, recipientPrivate, signerPublic []byte) *protobuf.Message {
	t.Helper()
	if len(recipientPublic) != 32 || len(recipientPrivate) != 32 || len(signerPublic) != ed25519.PublicKeySize {
		t.Fatal("invalid handoff key length")
	}
	if !ed25519.Verify(ed25519.PublicKey(signerPublic), append(flEnvelopeHeader(envelope), envelope.Ciphertext...), envelope.Signature) {
		t.Fatal("handoff envelope signature verification failed")
	}
	var publicKey, privateKey [32]byte
	copy(publicKey[:], recipientPublic)
	copy(privateKey[:], recipientPrivate)
	plaintext, ok := box.OpenAnonymous(nil, envelope.Ciphertext, &publicKey, &privateKey)
	if !ok {
		t.Fatal("handoff envelope decryption failed")
	}
	message := new(protobuf.Message)
	if err := proto.Unmarshal(plaintext, message); err != nil {
		t.Fatal(err)
	}
	if message.Sender != envelope.Sender || message.Type != envelope.Type {
		t.Fatal("handoff envelope metadata mismatch")
	}
	return message
}

func flVerifyReduce(t *testing.T, member *HonestParty, message *protobuf.Message) bool {
	t.Helper()
	if message.Type != "ShareReduce" {
		return false
	}
	var reduction protobuf.ShareReduce
	if err := proto.Unmarshal(message.Data, &reduction); err != nil {
		t.Fatal(err)
	}
	var valueBytes [32]byte
	copy(valueBytes[:], reduction.V)
	var value, position bls.Fr
	if !bls.FrFrom32(&value, valueBytes) {
		t.Fatal("invalid scalar encoding")
	}
	bls.AsFr(&position, uint64(message.Sender+1))
	commitment, witness := flPoint(t, reduction.C), flPoint(t, reduction.W)
	if !member.KZG.CheckProofSingle(commitment, witness, &position, &value) {
		t.Fatal("saved Reduce proof is invalid")
	}
	bls.AddModFr(&value, &value, &bls.ONE)
	if member.KZG.CheckProofSingle(commitment, witness, &position, &value) {
		t.Fatal("altered Reduce value accepted")
	}
	return true
}

func flSender(t *testing.T) {
	members := flGroup(0)
	secret := bls.RandomFr()
	dealer := &Client{HonestParty: NewHonestParty(0, 4, 1, 0x7fffffff, nil, nil, nil, nil, nil, nil)}
	dealer.SetSecret(*secret)
	for recipient, member := range members {
		dealer.sendChannels[recipient] = member.GetMessage("VSSSend", []byte("sid_a/share"))
	}
	dealer.Share([]byte("sid_a/share"))
	flParallel(members, func(member *HonestParty) { member.VSSShareReceive([]byte("sid_a/share")) })
	var publicKey bls.G1Point
	bls.MulG1(&publicKey, &bls.GenG1, secret)
	signerPublic, signerPrivate, err := ed25519.GenerateKey(cryptorand.Reader)
	if err != nil {
		t.Fatal(err)
	}
	recipientPublicKeys := make([][]byte, len(members))
	recipientPrivateKeys := make([][]byte, len(members))
	recipientKeys := make([]*[32]byte, len(members))
	for recipient := range members {
		publicKey, privateKey, err := box.GenerateKey(cryptorand.Reader)
		if err != nil {
			t.Fatal(err)
		}
		recipientKeys[recipient] = publicKey
		recipientPublicKeys[recipient] = append([]byte(nil), publicKey[:]...)
		recipientPrivateKeys[recipient] = append([]byte(nil), privateKey[:]...)
	}
	fixture := flHandoff{
		Instance:             "sid_a",
		Generation:           0,
		PublicKey:            bls.ToCompressedG1(&publicKey),
		SignerPublic:         append([]byte(nil), signerPublic...),
		RecipientPublicKeys:  recipientPublicKeys,
		RecipientPrivateKeys: recipientPrivateKeys,
		Packets:              make([][]flEnvelope, len(members)),
	}
	for coordinate, value := range []int{1, 2, -3} {
		fixture.Prefix = append(fixture.Prefix, flAdd(t, flEncrypt(&publicKey, value), flEncrypt(&publicKey, []int{4, -1, 1}[coordinate])))
	}
	started := time.Now()
	for _, member := range members {
		var sharePoint bls.G1Point
		bls.MulG1(&sharePoint, &bls.GenG1, &member.fullShare[0])
		fixture.OldSharePoints = append(fixture.OldSharePoints, bls.ToCompressedG1(&sharePoint))
		for recipient := range members {
			member.sendToNextChannels[recipient] = make(chan *protobuf.Message, 2)
		}
		member.PrepareSend([]byte("sid_a/prepare"))
		member.ShareReduceSend([]byte("sid_a/reduce"))
		for recipient := range members {
			for packetIndex := 0; packetIndex < 2; packetIndex++ {
				message := <-member.sendToNextChannels[recipient]
				fixture.Packets[recipient] = append(fixture.Packets[recipient], flSeal(t, uint32(recipient), member.PID, message, recipientKeys[recipient], signerPrivate))
			}
		}
	}
	flWrite(t, os.Getenv("FL_HANDOFF_FIXTURE"), fixture)
	flWrite(t, filepath.Join(os.Getenv("FL_HANDOFF_OUTPUT"), "sender.json"), map[string]any{
		"stage": "sender", "members": 4, "fault_bound": 1, "packets": 32,
		"encrypted_packets": 32, "recipient_scoped": true,
		"prepare_reduce_and_save_ms": float64(time.Since(started).Microseconds()) / 1000,
	})
}

func flPersist(t *testing.T) {
	data, err := os.ReadFile(os.Getenv("FL_HANDOFF_FIXTURE"))
	if err != nil {
		t.Fatal(err)
	}
	var fixture flHandoff
	if err := json.Unmarshal(data, &fixture); err != nil {
		t.Fatal(err)
	}
	if len(fixture.Packets) != 4 || len(fixture.RecipientPrivateKeys) != 4 {
		t.Fatal("unexpected sender fixture")
	}
	stored := flStoredHandoff{
		Instance:            fixture.Instance,
		Generation:          fixture.Generation,
		PublicKey:           fixture.PublicKey,
		SignerPublic:        fixture.SignerPublic,
		RecipientPublicKeys: fixture.RecipientPublicKeys,
		OldSharePoints:      fixture.OldSharePoints,
		Packets:             fixture.Packets,
		Prefix:              fixture.Prefix,
	}
	flWrite(t, os.Getenv("FL_HANDOFF_STORE_A"), stored)
	flWrite(t, os.Getenv("FL_HANDOFF_KEYS"), flRecipientKeys{RecipientPrivateKeys: fixture.RecipientPrivateKeys})
	if err := os.Remove(os.Getenv("FL_HANDOFF_FIXTURE")); err != nil {
		t.Fatal(err)
	}
	flWrite(t, filepath.Join(os.Getenv("FL_HANDOFF_OUTPUT"), "persist.json"), map[string]any{
		"stage": "persist", "saver": "A", "stored_envelopes": 32, "private_keys_in_store": false,
		"source_fixture_removed": true,
	})
}

func flReplicate(t *testing.T) {
	data, err := os.ReadFile(os.Getenv("FL_HANDOFF_STORE_A"))
	if err != nil {
		t.Fatal(err)
	}
	var stored flStoredHandoff
	if err := json.Unmarshal(data, &stored); err != nil {
		t.Fatal(err)
	}
	if len(stored.Packets) != 4 || len(stored.RecipientPublicKeys) != 4 {
		t.Fatal("unexpected saver A store")
	}
	flWrite(t, os.Getenv("FL_HANDOFF_STORE_B"), stored)
	flWrite(t, filepath.Join(os.Getenv("FL_HANDOFF_OUTPUT"), "replicate.json"), map[string]any{
		"stage": "replicate", "source_saver": "A", "destination_saver": "B",
		"replicated_envelopes": 32, "private_keys_replicated": false,
	})
}

func flRetireSaver(t *testing.T) {
	if err := os.Remove(os.Getenv("FL_HANDOFF_STORE_A")); err != nil {
		t.Fatal(err)
	}
	if _, err := os.Stat(os.Getenv("FL_HANDOFF_STORE_B")); err != nil {
		t.Fatal(err)
	}
	flWrite(t, filepath.Join(os.Getenv("FL_HANDOFF_OUTPUT"), "retire.json"), map[string]any{
		"stage": "retire", "retired_saver": "A", "surviving_saver": "B",
		"saver_a_store_removed": true, "saver_b_store_available": true,
	})
}

func flSuccessor(t *testing.T, delayed bool) {
	data, err := os.ReadFile(os.Getenv("FL_HANDOFF_STORE"))
	if err != nil {
		t.Fatal(err)
	}
	var stored flStoredHandoff
	if err := json.Unmarshal(data, &stored); err != nil {
		t.Fatal(err)
	}
	keyData, err := os.ReadFile(os.Getenv("FL_HANDOFF_KEYS"))
	if err != nil {
		t.Fatal(err)
	}
	var keys flRecipientKeys
	if err := json.Unmarshal(keyData, &keys); err != nil {
		t.Fatal(err)
	}
	fixture := flHandoff{
		Instance:             stored.Instance,
		Generation:           stored.Generation,
		PublicKey:            stored.PublicKey,
		SignerPublic:         stored.SignerPublic,
		RecipientPublicKeys:  stored.RecipientPublicKeys,
		RecipientPrivateKeys: keys.RecipientPrivateKeys,
		OldSharePoints:       stored.OldSharePoints,
		Packets:              stored.Packets,
		Prefix:               stored.Prefix,
	}
	if fixture.Instance != "sid_a" || fixture.Generation != 0 || len(fixture.Packets) != 4 || len(fixture.RecipientPrivateKeys) != 4 {
		t.Fatal("unexpected handoff context")
	}
	members := flGroup(1)
	started := time.Now()
	var held []flEnvelope
	openedPackets := 0
	verifiedInputs := 0
	for recipient, packets := range fixture.Packets {
		for _, envelope := range packets {
			if envelope.Recipient != uint32(recipient) {
				t.Fatal("handoff envelope recipient mismatch")
			}
			if os.Getenv("FL_HANDOFF_STAGE") == "quorum" && envelope.Sender >= 2 {
				continue
			}
			if delayed && recipient == 0 && envelope.Type == "ShareReduce" && envelope.Sender > 0 {
				held = append(held, envelope)
				continue
			}
			message := flOpen(t, envelope, fixture.RecipientPublicKeys[recipient], fixture.RecipientPrivateKeys[recipient], fixture.SignerPublic)
			openedPackets++
			if flVerifyReduce(t, members[recipient], message) {
				verifiedInputs++
			}
			members[recipient].GetMessage(message.Type, message.Id) <- message
		}
	}
	flParallel(members, func(member *HonestParty) { member.PrepareReceive([]byte("sid_a/prepare")) })
	reduced := make(chan struct{})
	go func() {
		flParallel(members, func(member *HonestParty) { member.ShareReduceReceive([]byte("sid_a/reduce")) })
		close(reduced)
	}()
	if delayed {
		select {
		case <-reduced:
			t.Fatal("one contribution completed threshold-two reduction")
		case <-time.After(100 * time.Millisecond):
		}
		for _, envelope := range held {
			message := flOpen(t, envelope, fixture.RecipientPublicKeys[0], fixture.RecipientPrivateKeys[0], fixture.SignerPublic)
			openedPackets++
			if flVerifyReduce(t, members[0], message) {
				verifiedInputs++
			}
			members[0].GetMessage(message.Type, message.Id) <- message
		}
	}
	<-reduced
	reduceElapsed := time.Since(started)
	flParallel(members, func(member *HonestParty) { member.ProactivizeAndShareDist([]byte("sid_a/refresh")) })
	refreshElapsed := time.Since(started) - reduceElapsed
	publicKey := flPoint(t, fixture.PublicKey)
	aggregate := make([]flCiphertext, len(fixture.Prefix))
	for coordinate, value := range []int{-2, -1, -2} {
		aggregate[coordinate] = flAdd(t, fixture.Prefix[coordinate], flEncrypt(publicKey, value))
	}
	decoded := make([]int, len(aggregate))
	for _, member := range members {
		var refreshed bls.G1Point
		bls.MulG1(&refreshed, &bls.GenG1, &member.fullShare[0])
		if bls.EqualG1(&refreshed, flPoint(t, fixture.OldSharePoints[member.PID])) {
			t.Fatal("share did not refresh")
		}
	}
	for first := 0; first < len(members); first++ {
		for second := first + 1; second < len(members); second++ {
			indices := make([]bls.Fr, 2)
			bls.AsFr(&indices[0], uint64(first+1))
			bls.AsFr(&indices[1], uint64(second+1))
			weights := make([]bls.Fr, 2)
			GetLagrangeCoefficients(1, indices, bls.ZERO, weights)
			points := make([]bls.G1Point, 2)
			bls.MulG1(&points[0], &bls.GenG1, &members[first].fullShare[0])
			bls.MulG1(&points[1], &bls.GenG1, &members[second].fullShare[0])
			if !bls.EqualG1(bls.LinCombG1(points, weights), publicKey) {
				t.Fatal("handoff changed the instance public key")
			}
			for coordinate, ciphertext := range aggregate {
				bls.MulG1(&points[0], flPoint(t, ciphertext.First), &members[first].fullShare[0])
				bls.MulG1(&points[1], flPoint(t, ciphertext.First), &members[second].fullShare[0])
				var recovered bls.G1Point
				bls.SubG1(&recovered, flPoint(t, ciphertext.Second), bls.LinCombG1(points, weights))
				decoded[coordinate] = flDecode(t, &recovered)
				if decoded[coordinate] != []int{3, 0, -4}[coordinate] {
					t.Fatal("aggregate changed across handoff")
				}
			}
		}
	}
	flWrite(t, filepath.Join(os.Getenv("FL_HANDOFF_OUTPUT"), os.Getenv("FL_HANDOFF_STAGE")+".json"), map[string]any{
		"stage": os.Getenv("FL_HANDOFF_STAGE"), "public_key_preserved": true,
		"generation":       1,
		"shares_refreshed": 4, "threshold": 2, "subsets_checked": 6,
		"aggregate": decoded, "delayed_recipient": delayed,
		"opened_envelopes": openedPackets, "recipient_scoped": true,
		"valid_reduce_proofs": verifiedInputs, "altered_reduce_values_rejected": verifiedInputs,
		"prepare_reduce_ms":       float64(reduceElapsed.Microseconds()) / 1000,
		"refresh_distribution_ms": float64(refreshElapsed.Microseconds()) / 1000,
	})
}

func TestFLHandoff(t *testing.T) {
	switch os.Getenv("FL_HANDOFF_STAGE") {
	case "sender":
		flSender(t)
	case "persist":
		flPersist(t)
	case "replicate":
		flReplicate(t)
	case "retire":
		flRetireSaver(t)
	case "successor", "quorum":
		flSuccessor(t, false)
	case "recover":
		flSuccessor(t, true)
	default:
		t.Fatal("set FL_HANDOFF_STAGE to sender, persist, replicate, retire, successor, quorum, or recover")
	}
}
