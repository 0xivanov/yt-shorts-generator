from datetime import timedelta
import os
os.environ["IMAGEIO_FFMPEG_EXE"] = "./ffmpeg"
import moviepy.editor as mp
from faster_whisper import WhisperModel
import argparse
import json
import logging

logging.basicConfig()
logging.getLogger("faster_whisper").setLevel(logging.DEBUG)

MAX_DURATION = 60
DONE_SHORTS_FOLDER = "shorts/"
TEMP_AUDIO_FOLDER = "temp/audios/"

TEMP_AUDIO_PATH = TEMP_AUDIO_FOLDER+"podcast_audio.mp3"
VIDEO_WITH_SUBTITLES = "temp/videos/"
JSON_CHUNKS_FOLDER = "temp/jsons/"

SONGS_FOLDER = "songs/"
FUN_SONGS_FOLDER = SONGS_FOLDER+"fun"
SAD_SONGS_FOLDER = SONGS_FOLDER+"sad"
CHILL_SONGS_FOLDER = SONGS_FOLDER+"chill"


def get_transcript(podcast_video_path):
    clip = mp.VideoFileClip(podcast_video_path)
    clip.audio.write_audiofile(TEMP_AUDIO_PATH)
    print("Audio file created")
    model = WhisperModel("base", device="cpu", compute_type="int8")
    segments, _ = model.transcribe(TEMP_AUDIO_PATH, beam_size=5)

    return segments


def generate_transcript(podcast_video_path):
    chunks = []
    chunk = []

    json_chunks = []
    json_chunk = []

    transcript_duration = MAX_DURATION
    transcript = get_transcript(podcast_video_path)

    for transcript_info in transcript:
        print(f"Transcript: {transcript_info.start} - {transcript_info.end} {transcript_info.text}")
        if float(transcript_info.start) >= transcript_duration:
            chunks.append(chunk.copy())
            json_chunks.append(json_chunk.copy())
            transcript_duration = float(transcript_info.start)+MAX_DURATION
            chunk.clear()
            json_chunk.clear()

        json_info = {
            "start_time": transcript_info.start,
            "end_time": transcript_info.end,
            "text": transcript_info.text,
        }
        json_chunk.append(json_info)

        formatted_time = str(timedelta(seconds=transcript_info.start))
        text = transcript_info.text
        chunk.append(f"{formatted_time} {text}\n")

    for i, json_chunk in enumerate(json_chunks, start=0):
        print(f"Creating json_chunk{i}.json")
        with open(JSON_CHUNKS_FOLDER+f"json_chunk{i}.json", "w") as out_file:
            json.dump(json_chunk, out_file, indent=6)


def get_files(folder_path):
    try:
        file_names = [f for f in os.listdir(
            folder_path) if os.path.isfile(os.path.join(folder_path, f))]
        return file_names
    except OSError as e:
        print(f"Error reading files in {folder_path}: {e}")
        return []


def if_folder_exist(folder_path):
    if not os.path.exists(folder_path):
        # If it doesn't exist, create the folder
        os.makedirs(folder_path)
        print(f"Folder '{folder_path}' created.")


def create_folders():
    if_folder_exist(TEMP_AUDIO_FOLDER)
    if_folder_exist(JSON_CHUNKS_FOLDER)
    if_folder_exist(SONGS_FOLDER)
    if_folder_exist(FUN_SONGS_FOLDER)
    if_folder_exist(SAD_SONGS_FOLDER)
    if_folder_exist(CHILL_SONGS_FOLDER)
    if_folder_exist(VIDEO_WITH_SUBTITLES)
    if_folder_exist(DONE_SHORTS_FOLDER)


def main():
    parser = argparse.ArgumentParser(
        description='Script for generating shorts with subtitles')
    parser.add_argument('--path', required=True,
                        help='The podcast video path')
    args = parser.parse_args()

    create_folders()
    generate_transcript(args.path)

if __name__ == "__main__":
    main()
