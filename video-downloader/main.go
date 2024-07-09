package main

import (
	"context"
	"fmt"
	"log"
	"net/http"
	"os"
	"sync"

	"github.com/0xivanov/shorts-generator/listener"
	"google.golang.org/api/option"
	"google.golang.org/api/youtube/v3"
)

// Global map to store the active channel listeners
var channelListeners = make(map[string]chan struct{})
var mu sync.Mutex

func getChannelID(service *youtube.Service, username string) (string, error) {
	call := service.Channels.List([]string{"id"}).ForHandle(username)
	response, err := call.Do()
	if err != nil {
		return "", err
	}

	if len(response.Items) > 0 {
		return response.Items[0].Id, nil
	}

	return "", fmt.Errorf("no channel found")
}

func removeChannel(w http.ResponseWriter, r *http.Request) {

	username := r.URL.Query().Get("username")
	if username == "" {
		http.Error(w, "Username is required", http.StatusBadRequest)
		return
	}

	ctx := context.Background()
	apiKey := os.Getenv("YOUTUBE_API_KEY")

	service, err := youtube.NewService(ctx, option.WithAPIKey(apiKey))
	if err != nil {
		http.Error(w, fmt.Sprintf("Error creating YouTube service: %s", err.Error()), http.StatusInternalServerError)
		return
	}

	channelID, err := getChannelID(service, username)
	if err != nil {
		http.Error(w, fmt.Sprintf("Error fetching channel ID: %s", err.Error()), http.StatusInternalServerError)
		return
	}

	stopChan := channelListeners[channelID]

	stopChan <- struct{}{}
}

func addChannel(w http.ResponseWriter, r *http.Request) {
	username := r.URL.Query().Get("username")
	if username == "" {
		http.Error(w, "Username is required", http.StatusBadRequest)
		return
	}

	ctx := context.Background()
	apiKey := os.Getenv("YOUTUBE_API_KEY")

	service, err := youtube.NewService(ctx, option.WithAPIKey(apiKey))
	if err != nil {
		http.Error(w, fmt.Sprintf("Error creating YouTube service: %s", err.Error()), http.StatusInternalServerError)
		return
	}

	channelID, err := getChannelID(service, username)
	if err != nil {
		http.Error(w, fmt.Sprintf("Error fetching channel ID: %s", err.Error()), http.StatusInternalServerError)
		return
	}

	mu.Lock()
	defer mu.Unlock()
	if _, exists := channelListeners[channelID]; exists {
		http.Error(w, "Channel is already being listened to", http.StatusConflict)
		return
	}

	stopChan := make(chan struct{})
	channelListeners[channelID] = stopChan

	go listener.UploadListener(service, channelID, stopChan)

	fmt.Fprintf(w, "Started listening to channel %s", channelID)
}

func main() {
	http.HandleFunc("/addChannel", addChannel)
	http.HandleFunc("/removeChannel", removeChannel)
	fmt.Println("Starting server at port 8080")
	if err := http.ListenAndServe(":8080", nil); err != nil {
		log.Fatalf("Could not start server: %s\n", err.Error())
	}
}
