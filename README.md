# your-repo

A simple Go application that demonstrates clean project structure with tests.

## Quick Start

```bash
# Run directly
go run hello.go

# Run with a custom name
go run hello.go Alice

# Build and run
go build -o your-repo .
./your-repo
```

## Testing

```bash
go test -v ./...
```

## Project Structure

```
.
├── hello.go        # Main application with Greet function
├── hello_test.go   # Unit tests
├── go.mod          # Go module definition
├── .gitignore      # Git ignore rules
└── README.md       # This file
```