.PHONY: all build test bench cover clean run

# Default target
all: build test

# Build the binary
build:
	go build -o your-repo .

# Run the application
run:
	go run hello.go

# Run all tests
test:
	go test -v -race ./...

# Run benchmarks
bench:
	go test -bench=. -benchmem ./...

# Show test coverage
cover:
	go test -coverprofile=coverage.out ./...
	go tool cover -func=coverage.out
	@rm -f coverage.out

# Clean build artifacts
clean:
	rm -f your-repo coverage.out
