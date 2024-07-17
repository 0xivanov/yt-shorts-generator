# Shorts Generator

This project is a Go-based server that automates the creation and editing of YouTube Shorts using Python scripts. It provides a seamless workflow for generating short video clips from longer videos, applying predefined edits, and preparing them for upload to YouTube.

## Setup

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

go mod tidy
```

Create .env file. See .env.example

## Usage

- **Endpoint:** `http://localhost:8080/addChannel?username=channel_username`
- Replace `channel_username` with the YouTube channel username you want to download videos from.

Example:
```bash
curl http://localhost:8080/addChannel?username=examplechannel
```
