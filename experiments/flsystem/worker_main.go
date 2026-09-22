package main

import (
	"log"
	"os"

	"github.com/DyCAPSTeam/DyCAPS/internal/party"
)

func main() {
	if err := party.RunFLWorker(os.Stdin, os.Stdout); err != nil {
		log.Fatal(err)
	}
}
