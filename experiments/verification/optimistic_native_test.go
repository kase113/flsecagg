package main

import (
	"fmt"
	"os"
	"path/filepath"
	"regexp"
	"strconv"
	"strings"
	"testing"

	"github.com/opDPSSTeam/DPSS/internal/bls"
	"github.com/opDPSSTeam/DPSS/internal/polyring"
)

func TestNativeOutput(t *testing.T) {
	directory := os.Getenv("OPTIMISTIC_LOG_DIR")
	if directory == "" {
		t.Fatal("set OPTIMISTIC_LOG_DIR to the native main output directory")
	}
	count, err := strconv.Atoi(os.Getenv("OPTIMISTIC_N"))
	if err != nil || count < 4 {
		t.Fatal("set OPTIMISTIC_N >= 4")
	}
	faults, err := strconv.Atoi(os.Getenv("OPTIMISTIC_F"))
	if err != nil || faults < 1 || count != 3*faults+1 {
		t.Fatal("set OPTIMISTIC_F with N=3F+1")
	}
	shares := make([]bls.Fr, count)
	sharePattern := regexp.MustCompile(`newShare: ([0-9]+)`)
	for node := 0; node < count; node++ {
		data, err := os.ReadFile(filepath.Join(directory, fmt.Sprintf("exeLogNew%d.log", node)))
		if err != nil {
			t.Fatal(err)
		}
		matches := sharePattern.FindAllStringSubmatch(string(data), -1)
		if len(matches) != 1 || !strings.Contains(string(data), "DpssNew finished") || !strings.Contains(string(data), "enter the optimistic path") {
			t.Fatalf("node %d: expected one completed optimistic output", node)
		}
		bls.SetFr(&shares[node], matches[0][1])
		t.Logf("node=%d new_share=%s", node, shares[node].String())
	}
	var secret bls.Fr
	bls.AsFr(&secret, 12345)
	positions := make([]bls.Fr, faults+1)
	values := make([]bls.Fr, faults+1)
	checked := 0
	var visit func(int, int)
	visit = func(start, depth int) {
		if depth == faults+1 {
			polynomial := polyring.LagrangeInterpolate(uint32(faults), positions, values)
			if !bls.EqualFr(&polynomial[0], &secret) {
				t.Fatalf("subset %d reconstructed %s, expected 12345", checked, polynomial[0].String())
			}
			for node := 0; node < count; node++ {
				var position, evaluated bls.Fr
				bls.AsFr(&position, uint64(node+1))
				bls.EvalPolyAt(&evaluated, polynomial, &position)
				if !bls.EqualFr(&evaluated, &shares[node]) {
					t.Fatalf("subset %d disagrees with new share %d", checked, node)
				}
			}
			checked++
			return
		}
		for node := start; node < count; node++ {
			bls.AsFr(&positions[depth], uint64(node+1))
			values[depth] = shares[node]
			visit(node+1, depth+1)
		}
	}
	visit(0, 0)
	t.Logf("VERIFIED: %d threshold subsets reconstruct 12345; all %d shares agree with every degree-%d polynomial", checked, count, faults)
}
