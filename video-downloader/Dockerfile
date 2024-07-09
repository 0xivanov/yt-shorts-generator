# Use an official Go runtime as a parent image
FROM golang:1.20-buster AS build

# Set the Current Working Directory inside the container
WORKDIR /app

# Copy the Go Modules manifests
COPY go.mod go.sum ./

# Download all dependencies. Dependencies will be cached if the go.mod and go.sum files are not changed
RUN go mod download

# Copy the source code into the container
COPY . .

# Build the Go app
RUN go build -o main .

# Use a minimal base image to package the application
FROM debian:latest

# Set the Current Working Directory inside the container
WORKDIR /root/

# Copy the Pre-built binary file from the previous stage
COPY --from=build /app/main .

# Copy the ffmpeg binary to the working directory
COPY ffmpeg .

# Make the ffmpeg binaries executable
RUN chmod +x ffmpeg

# Install dependencies: add-apt-repository, update, yt-dlp 
RUN apt-get update && \
    apt-get install -y yt-dlp

# Expose port 8080 to the outside world
EXPOSE 8080

# Command to run the executable
CMD ["./main"]
