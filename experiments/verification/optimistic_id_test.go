package wpACSS

import (
	"bytes"
	"testing"

	"github.com/opDPSSTeam/DPSS/internal/party"
	"github.com/opDPSSTeam/DPSS/pkg/utils"
)

func TestSessionIDOwnership(t *testing.T) {
	sessionID := utils.IntToBytes(1)
	queuedID := append(sessionID, utils.Uint32ToBytes(0)...)
	expected := append([]byte(nil), queuedID...)
	participant := party.NewHonestParty(0, 4, 1, 1, nil, nil, nil, nil, nil, nil, nil, nil, nil)
	genRecPoly(participant, sessionID, 1, 4)
	t.Logf("session len=%d cap=%d; queued ID before=%x after=%x", len(sessionID), cap(sessionID), expected, queuedID)
	if !bytes.Equal(queuedID, expected) {
		t.Fatal("recovery polynomial generation overwrote a queued sibling instance ID")
	}
}
