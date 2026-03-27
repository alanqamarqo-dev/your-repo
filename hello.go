package main

import (
	"fmt"
	"os"
	"strings"
)

// Greet returns a greeting message for the given name.
// If name is empty, it defaults to "World".
func Greet(name string) string {
	name = strings.TrimSpace(name)
	if name == "" {
		name = "World"
	}
	return fmt.Sprintf("Hello, %s!", name)
}

func main() {
	name := "World"
	if len(os.Args) > 1 {
		name = strings.Join(os.Args[1:], " ")
	}
	fmt.Println(Greet(name))
}
