package main

import (
	"context"
	"encoding/json"
	"fmt"
	"io"
	"io/ioutil"
	"log"
	"net/http"
	"os"
	"os/exec"
	"path/filepath"
	"strings"
	"time"

	"github.com/sashabaranov/go-openai"
	"google.golang.org/api/youtube/v3"
)

type AiResponse struct {
	StartTimestamp string `json:"start_timestamp"`
	EndTimestamp   string `json:"end_timestamp"`
	Title          string `json:"title"`
	Genre          string `json:"genre"`
}

func uploadListener(ytService *youtube.Service, openAIClient *openai.Client, channelID string, stopChan chan struct{}) {

	ticker := time.NewTicker(1 * time.Minute)
	defer ticker.Stop()

	latestVideoId := ""

	for {
		select {
		case <-ticker.C:
			videoID, err := getLatestVideoId(ytService, channelID)
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
				fmt.Printf("Downloaded video %s from channel %s\n", videoID, channelID)

				err = callGenerateTranscript(videoID)
				if err != nil {
					fmt.Printf("Error generating transcript: %v\n", err)
					continue
				}
				fmt.Printf("Generated transcript for video %s\n", videoID)

				aiResponses, err := processTranscripts(openAIClient)
				if err != nil {
					fmt.Printf("Error processing transcript: %v\n", err)
					continue
				}
				fmt.Println("Processed transcript")

				err = callGenerateShort(aiResponses, videoID)
				if err != nil {
					fmt.Printf("Error editing: %v\n", err)
					continue
				}
				fmt.Println("Generated short")
				latestVideoId = videoID

			}
		case <-stopChan:
			fmt.Printf("Stopped listening to channel %s\n", channelID)
			return
		}
	}
}

func getLatestVideoId(ytService *youtube.Service, channelID string) (string, error) {
	fmt.Println("Channel ID:", channelID)
	videos := make([]string, 0)
	call := ytService.Search.List([]string{"id"}).ChannelId(channelID).Order("date").Type("video").MaxResults(50)
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

	cmd := exec.Command("yt-dlp", "-o", fmt.Sprintf("%s.mp4", videoID), "-P", currentDir+"/downloads", "--remux-video", "mp4", "--ffmpeg-location", currentDir, videoID)
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

func callGenerateTranscript(videoName string) error {

	cmd := exec.Command("python", "scripts/transcript.py", "--path", fmt.Sprintf("downloads/%s.mp4", videoName))

	cmd.Stderr = os.Stderr

	err := cmd.Run()
	if err != nil {
		return err
	}
	return nil
}

func processTranscripts(openAIClient *openai.Client) ([]string, error) {
	// Specify the folder containing JSON files
	folder := "temp/jsons"

	// Read the folder contents
	files, err := ioutil.ReadDir(folder)
	if err != nil {
		log.Fatal(err)
	}

	aiResponses := make([]string, 0)
	for _, file := range files {
		// Check if the file is a JSON file
		if filepath.Ext(file.Name()) == ".json" {
			// Construct the full file path
			filePath := filepath.Join(folder, file.Name())

			// Read the file
			jsonFile, err := os.Open(filePath)
			if err != nil {
				fmt.Printf("Failed to open file: %s\n", err)
				return nil, err
			}
			defer jsonFile.Close()

			byteValue, err := ioutil.ReadAll(jsonFile)
			if err != nil {
				fmt.Printf("Failed to read file: %s\n", err)
				return nil, err
			}

			content := `
			I have a transcript of a video in json format, where i have start_time in seconds, end_time in seconds and the script as a text for this given time range.
			Find me the most interesting chunk which is around 30 seconds, containing multiple of these chunks.
			Also give me a title and genre for this video. The genres can be: sad ,fun and chill. Return the response in this format:
			json
			{
  			"start_timestamp": "*according time stamp*",
  			"end_timestamp": "*according time stamp*",
  			"title": "according title*",
  			"genre": "according genre*"
			}

			Here is the input for you to work with:			
			json
			%s

			NOTE: Please return only the json in your response and nothing else.
			`

			resp, err := openAIClient.CreateChatCompletion(
				context.Background(),
				openai.ChatCompletionRequest{
					Model: openai.GPT3Dot5Turbo,
					Messages: []openai.ChatCompletionMessage{
						{
							Role:    openai.ChatMessageRoleUser,
							Content: fmt.Sprintf(content, string(byteValue)),
						},
					},
				},
			)

			if err != nil {
				fmt.Printf("OpenAI error: %v\n", err)
				return nil, err
			}

			fmt.Println(resp.Choices[0].Message.Content)
			aiResponses = append(aiResponses, resp.Choices[0].Message.Content)
			// TODO
			break
		}
	}
	return aiResponses, nil
}

func callGenerateShort(aiResponses []string, videoName string) error {
	for _, resp := range aiResponses {
		cleanedString := trim(resp)
		var response AiResponse
		err := json.Unmarshal([]byte(cleanedString), &response)
		if err != nil {
			fmt.Println("Error unmarshaling ai response:", err)
			return err
		}

		cleanedStartTimestamp := strings.ReplaceAll(response.StartTimestamp, "s", "")
		cleanedStartTimestamp = strings.ReplaceAll(cleanedStartTimestamp, "\"", "")

		cmd := exec.Command("python", "scripts/editor.py", "--start", cleanedStartTimestamp, "--genre", response.Genre, "--title", response.Title, "--videoName", videoName+".mp4")
		cmd.Stderr = os.Stderr

		err = cmd.Run()
		if err != nil {
			fmt.Println("Error generating short:", err)
			return err
		}
	}
	return nil
}

func trim(input string) string {
	start := strings.Index(input, "{")
	end := strings.LastIndex(input, "}")

	if start != -1 && end != -1 && start < end {
		// Extract the substring from '{' to '}'
		output := input[start : end+1]
		fmt.Println(output)
		return output
	} else {
		fmt.Println("Invalid input format")
		return ""
	}
}
