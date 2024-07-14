import callOpenAi
from datetime import timedelta
import moviepy.editor as mp
from faster_whisper import WhisperModel
import argparse
import videoEditor
import os
import json

MAX_DURATION = 60
VIDEOS_FOLDER = "videos/"
DONE_SHORTS_FOLDER = "shorts/"
TEMP_AUDIO_FOLDER = "temp/audios/"

TEMP_AUDIO_PATH = TEMP_AUDIO_FOLDER+"podcast_audio.mp3"
VIDEO_WITH_SUBTITLES = "temp/videos/"
JSON_CHUNKS_FOLDER = "temp/jsons/"

SONGS_FOLDER = "songs/"
FUN_SONGS_FOLDER = SONGS_FOLDER+"fun"
SAD_SONGS_FOLDER = SONGS_FOLDER+"sad"
CHILL_SONGS_FOLDER = SONGS_FOLDER+"chill"

json_template_time_stamps = """
{
  "start_timestamp": "according time stamp*",
  "end_timestamp": "according time stamp*"
}
"""

json_template_info = """
{
  "title": "according title*",
  "genre": "according genre*"
}
"""


def get_transcript(podcast_video_path):
    clip = mp.VideoFileClip(podcast_video_path)
    clip.audio.write_audiofile(TEMP_AUDIO_PATH)
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

    for i, json_chunk in enumerate(json_chunks, start=1):
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
    if_folder_exist(VIDEOS_FOLDER)
    if_folder_exist(TEMP_AUDIO_FOLDER)
    if_folder_exist(JSON_CHUNKS_FOLDER)
    if_folder_exist(SONGS_FOLDER)
    if_folder_exist(FUN_SONGS_FOLDER)
    if_folder_exist(SAD_SONGS_FOLDER)
    if_folder_exist(CHILL_SONGS_FOLDER)
    if_folder_exist(VIDEO_WITH_SUBTITLES)
    if_folder_exist(DONE_SHORTS_FOLDER)


def get_time_stamps(content):
    while True:
        json_data = callOpenAi.call_chat_GPT(
            f"Find the most interesting 30 seconds part of this text respond in this json use this as a refrence {json_template_time_stamps}. Name the field for range btween start and end timestamp don't round or change time stamp value and don't include text field {content}")
        try:
            data = json.loads(json_data)
            return data["start_timestamp"]
        except:
            continue


def get_video_info(content):
    while True:
        json_data = callOpenAi.call_chat_GPT(
            f"Give me example title and genre of transcript respond in json format use this as a reference {json_template_info}.The avaible genres you can choose are : sad ,fun and chill.This is the  transcript {content}")
        print(json_data)
        try:
            data = json.loads(json_data)
            return data["title"], data["genre"]
        except:
            continue


def main():
    parser = argparse.ArgumentParser(
        description='Script for generating shorts with subtitles')
    parser.add_argument('--path', required=True,
                        help='The podcast video path')
    args = parser.parse_args()

    create_folders()
    generate_transcript(args.path)
    for file_name in get_files(JSON_CHUNKS_FOLDER):
        with open(JSON_CHUNKS_FOLDER+file_name, 'r') as file:
            content = file.read()

            start_time = get_time_stamps(content)
            title, genre = get_video_info(content)

            videoEditor.read_transcript_and_cut(
                start_time=start_time, title=title, genre=genre)


if __name__ == "__main__":
    main()
