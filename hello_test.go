package main

import "testing"

func TestGreet(t *testing.T) {
	tests := []struct {
		name string
		input string
		want string
	}{
		{name: "default", input: "", want: "Hello, World!"},
		{name: "with name", input: "Go", want: "Hello, Go!"},
		{name: "whitespace only", input: "   ", want: "Hello, World!"},
		{name: "with spaces", input: "  Alice  ", want: "Hello, Alice!"},
		{name: "unicode", input: "世界", want: "Hello, 世界!"},
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
