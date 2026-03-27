package main

import (
	"fmt"
	"testing"
)

func TestGreet(t *testing.T) {
	tests := []struct {
		name  string
		input string
		want  string
	}{
		{name: "default", input: "", want: "Hello, World!"},
		{name: "with name", input: "Go", want: "Hello, Go!"},
		{name: "whitespace only", input: "   ", want: "Hello, World!"},
		{name: "with spaces", input: "  Alice  ", want: "Hello, Alice!"},
		{name: "unicode", input: "世界", want: "Hello, 世界!"},
		{name: "arabic", input: "أحمد", want: "Hello, أحمد!"},
		{name: "long name", input: "John Doe", want: "Hello, John Doe!"},
	}
	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			got := Greet(tt.input)
			if got != tt.want {
				t.Errorf("Greet(%q) = %q, want %q", tt.input, got, tt.want)
			}
		})
	}
}

func BenchmarkGreet(b *testing.B) {
	for i := 0; i < b.N; i++ {
		Greet("World")
	}
}

func ExampleGreet() {
	fmt.Println(Greet(""))
	fmt.Println(Greet("Go"))
	// Output:
	// Hello, World!
	// Hello, Go!
}
