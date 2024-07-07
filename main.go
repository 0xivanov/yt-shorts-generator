package main

import (
	"context"
	"fmt"
	"io"
	"log"
	"net/http"
	"os"
	"os/exec"
	"time"

	"google.golang.org/api/option"
	"google.golang.org/api/youtube/v3"
)

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

func getLatestVideo(service *youtube.Service, channelID string) ([]string, error) {
	videos := make([]string, 0)
	call := service.Search.List([]string{"id"}).ChannelId(channelID).Order("date").Type("video").MaxResults(50)
	response, err := call.Do()
	if err != nil {
		return videos, err
	}

	if len(response.Items) > 0 {
		for index, item := range response.Items {
			if index == 50 {
				break
			}

			isShort, _ := CheckIfShorts(item.Id.VideoId)
			if !isShort {
				videos = append(videos, item.Id.VideoId)
			}
			if len(videos) == 1 {
				break
			}
		}
	}
	if len(videos) == 0 {
		return videos, fmt.Errorf("no videos found")
	}
	return videos, nil
}

func downloadVideo(videoID string) error {
	currentDir, err := os.Getwd()
	if err != nil {
		fmt.Println("Error getting current directory:", err)
		return err
	}

	cmd := exec.Command("yt-dlp", "-P", currentDir+"/downloads", "--remux-video", "mp4", "--ffmpeg-location", currentDir, videoID)
	return cmd.Run()
}

func handler(w http.ResponseWriter, r *http.Request) {
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

	videoIDs, err := getLatestVideo(service, channelID)
	if err != nil {
		http.Error(w, fmt.Sprintf("Error fetching latest video: %s", err.Error()), http.StatusInternalServerError)
		return
	}

	if err := downloadVideo(videoIDs[0]); err != nil {
		http.Error(w, fmt.Sprintf("Error downloading video: %s", err.Error()), http.StatusInternalServerError)
		return
	}

	fmt.Fprintf(w, "Video downloaded successfully")
}

func CheckIfShorts(videoID string) (bool, error) {
	url := fmt.Sprintf("https://www.youtube.com/shorts/%s", videoID)
	client := &http.Client{
		Timeout: 10 * time.Second,
		CheckRedirect: func(req *http.Request, via []*http.Request) error {
			// Do not follow redirects
			return http.ErrUseLastResponse
		},
	}

	resp, err := client.Get(url)
	if err != nil {
		return false, err
	}
	defer resp.Body.Close()

	// Read the response body (though we don't use it)
	_, err = io.ReadAll(resp.Body)
	if err != nil {
		return false, err
	}

	// Check if the status code is 200
	if resp.StatusCode == 200 {
		return true, nil
	}

	return false, nil
}

func main() {
	http.HandleFunc("/", handler)
	fmt.Println("Starting server at port 8080")
	if err := http.ListenAndServe(":8080", nil); err != nil {
		log.Fatalf("Could not start server: %s\n", err.Error())
	}
}
