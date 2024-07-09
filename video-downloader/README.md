# YouTube Video Downloader

This application is a Dockerized Go HTTP server that interacts with the YouTube Data API to download videos using yt-dlp. It allows you to specify a YouTube channel username and automatically downloads the latest video from that channel (excluding shorts).

## Features

- Downloads the latest video from a specified YouTube channel (excluding shorts).
- Uses the YouTube Data API to fetch channel information and video metadata.
- Utilizes yt-dlp for downloading videos with specific options.

## Requirements

- Docker installed on your system.
- YouTube API key. Obtain one from the Google Cloud Console.

## Setup

1. **Clone the repository:**

   ```bash
   git clone
   cd repository-directory
   ```

2. **Build the Docker image:**

   ```bash
   docker build -t youtube-downloader .
   ```

3. **Run the Docker container:**

   ```bash
   docker run -d -p 8080:8080 -e YOUTUBE_API_KEY=YOUR_YOUTUBE_API_KEY youtube-downloader
   ```

   Replace `YOUR_YOUTUBE_API_KEY` with your actual YouTube API key.

## Usage

Once the Docker container is running, you can access the HTTP server:

- **Endpoint:** `http://localhost:8080/?username=channel_username`
- Replace `channel_username` with the YouTube channel username you want to download videos from.

Example:
```bash
curl http://localhost:8080/?username=examplechannel
```

## Notes

- The downloaded videos will be stored inside the Docker container unless configured otherwise (consider using Docker volumes for persistent storage).
- Adjust yt-dlp options or add more features as needed by modifying the source code (`main.go`).
