package listener

import (
	"fmt"
	"io"
	"net/http"
	"os"
	"os/exec"
	"time"

	"google.golang.org/api/youtube/v3"
)

func UploadListener(service *youtube.Service, channelID string, stopChan chan struct{}) {

	ticker := time.NewTicker(1 * time.Minute)
	defer ticker.Stop()

	latestVideoId := ""

	for {
		select {
		case <-ticker.C:
			videoID, err := getLatestVideoId(service, channelID)
			if err != nil {
				fmt.Printf("Error getting latest video ID: %v\n", err)
				continue
			}
			if videoID == latestVideoId {
				fmt.Println("No new video uploaded")
				continue
			}

			err = downloadVideo(videoID)
			if err != nil {
				fmt.Printf("Error downloading video: %v\n", err)
			} else {
				latestVideoId = videoID
				fmt.Printf("Downloaded video %s from channel %s\n", videoID, channelID)
			}
		case <-stopChan:
			fmt.Printf("Stopped listening to channel %s\n", channelID)
			return
		}
	}
}

func getLatestVideoId(service *youtube.Service, channelID string) (string, error) {
	fmt.Println("Channel ID:", channelID)
	videos := make([]string, 0)
	call := service.Search.List([]string{"id"}).ChannelId(channelID).Order("date").Type("video").MaxResults(50)
	response, err := call.Do()
	if err != nil {
		return "", err
	}

	if len(response.Items) > 0 {
		for index, item := range response.Items {
			if index == 50 {
				break
			}

			isShort, _ := checkIfShorts(item.Id.VideoId)
			if !isShort {
				videos = append(videos, item.Id.VideoId)
			}
			if len(videos) == 1 {
				break
			}
		}
	}
	if len(videos) == 0 {
		return "", fmt.Errorf("no videos found")
	}
	return videos[0], nil
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

func checkIfShorts(videoID string) (bool, error) {
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
