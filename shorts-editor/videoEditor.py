import subprocess
from faster_whisper import WhisperModel
import moviepy.editor as mp
from moviepy.editor import TextClip, VideoFileClip, CompositeVideoClip, ColorClip
import os
import random

PODCAST_VIDEO_PATH = "videos/podcast.mp4"
VIDEO_WITH_SUBTITLES = "temp/videos/short.mp4"
CUTED_PART_OF_VIDEO_NORMAL_SCALE = "temp/videos/cuted_normal_video.mp4"
CUTED_PART_OF_VIDEO = "temp/videos/cuted_video.mp4"
CUTED_PART_OF_AUDIO = "temp/audios/cuted_video_audio.mp3"
DONE_SHORTS_FOLDER = "shorts/"
SONGS_FOLDER = "songs/"

HIGHLIGHT_COLOR = "#21fa11"
TEXT_FONT = "Tw-Cen-MT-Condensed-Extra-Bold"
genre_folders = {
    'fun': SONGS_FOLDER+"fun",
    'sad': SONGS_FOLDER+"sad",
    'chill': SONGS_FOLDER+"chill"
}


# ffmpeg -i test.mp4 -ss 00:00:15 -t 00:00:10 -async -1 clip.mp4
def cut_video(start_time):
    command = [
        'ffmpeg',
        '-y',
        '-ss', start_time,
        '-i', PODCAST_VIDEO_PATH,
        '-t', "00:00:30",
        '-map', '0',
        '-c', 'copy',
        CUTED_PART_OF_VIDEO_NORMAL_SCALE
    ]
    subprocess.run(command)
    # ffmpeg -i input.mp4
    # -vf "scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2"
    # -c:a copy output.mp4
    ffmpeg_command = [
        'ffmpeg',
        '-y',
        '-i', CUTED_PART_OF_VIDEO_NORMAL_SCALE,
        '-vf', 'crop=1080:2080',
        CUTED_PART_OF_VIDEO
    ]
    subprocess.run(ffmpeg_command)


def split_text_into_lines(data):
    MaxChars = 10
    # maxduration in seconds
    MaxDuration = 1
    # Split if nothing is spoken (gap) for these many seconds
    MaxGap = 1.5

    subtitles = []
    line = []
    line_duration = 0

    for idx, word_data in enumerate(data):
        word = word_data["word"]
        start = word_data["start"]
        end = word_data["end"]

        line.append(word_data)
        line_duration += end - start

        temp = " ".join(item["word"] for item in line)

        # Check if adding a new word exceeds the maximum character count or duration
        new_line_chars = len(temp)

        duration_exceeded = line_duration > MaxDuration
        chars_exceeded = new_line_chars > MaxChars
        if idx > 0:
            gap = word_data['start'] - data[idx-1]['end']
            # print (word,start,end,gap)
            maxgap_exceeded = gap > MaxGap
        else:
            maxgap_exceeded = False

        if duration_exceeded or chars_exceeded or maxgap_exceeded:
            if line:
                subtitle_line = {
                    "word": " ".join(item["word"] for item in line),
                    "start": line[0]["start"],
                    "end": line[-1]["end"],
                    "textcontents": line
                }
                subtitles.append(subtitle_line)
                line = []
                line_duration = 0

    if line:
        subtitle_line = {
            "word": " ".join(item["word"] for item in line),
            "start": line[0]["start"],
            "end": line[-1]["end"],
            "textcontents": line
        }
        subtitles.append(subtitle_line)

    return subtitles


def read_transcript_and_cut(start_time, title, genre):
    cut_video(start_time)
    create_short(title, genre)


def split_text_into_lines(data):
    MaxChars = 30
    # maxduration in seconds
    MaxDuration = 2.5
    # Split if nothing is spoken (gap) for these many seconds
    MaxGap = 0.5

    subtitles = []
    line = []
    line_duration = 0

    for idx, word_data in enumerate(data):
        start = word_data["start"]
        end = word_data["end"]

        line.append(word_data)
        line_duration += end - start

        temp = " ".join(item["word"] for item in line)

        # Check if adding a new word exceeds the maximum character count or duration
        new_line_chars = len(temp)

        duration_exceeded = line_duration > MaxDuration
        chars_exceeded = new_line_chars > MaxChars
        if idx > 0:
            gap = word_data['start'] - data[idx-1]['end']
            # print (word,start,end,gap)
            maxgap_exceeded = gap > MaxGap
        else:
            maxgap_exceeded = False

        if duration_exceeded or chars_exceeded or maxgap_exceeded:
            if line:
                subtitle_line = {
                    "word": " ".join(item["word"] for item in line),
                    "start": line[0]["start"],
                    "end": line[-1]["end"],
                    "textcontents": line
                }
                subtitles.append(subtitle_line)
                line = []
                line_duration = 0

    if line:
        subtitle_line = {
            "word": " ".join(item["word"] for item in line),
            "start": line[0]["start"],
            "end": line[-1]["end"],
            "textcontents": line
        }
        subtitles.append(subtitle_line)

    return subtitles


def create_caption(textJSON, framesize, font=TEXT_FONT, color='white', highlight_color=HIGHLIGHT_COLOR, stroke_color='black', stroke_width=3.5):
    full_duration = textJSON['end']-textJSON['start']

    word_clips = []
    xy_textclips_positions = []

    x_pos = 0
    y_pos = 0
    line_width = 0  # Total width of words in the current line
    frame_width = framesize[0]
    frame_height = framesize[1]

    x_buffer = frame_width*1/10

    max_line_width = frame_width - 2 * (x_buffer)

    fontsize = int(frame_height * 0.08)  # 7.5 percent of video height

    space_width = ""

    for _, wordJSON in enumerate(textJSON['textcontents']):
        duration = wordJSON['end']-wordJSON['start']
        word_clip = TextClip(wordJSON['word'], font=font, fontsize=fontsize, color=color, stroke_color=stroke_color,
                             stroke_width=stroke_width).set_start(textJSON['start']).set_duration(full_duration)
        word_clip_space = TextClip(" ", font=font, fontsize=fontsize, color=color).set_start(
            textJSON['start']).set_duration(full_duration)
        word_width, word_height = word_clip.size
        space_width, _ = word_clip_space.size
        if line_width + word_width + space_width <= max_line_width:
            # Store info of each word_clip created
            xy_textclips_positions.append({
                "x_pos": x_pos,
                "y_pos": y_pos,
                "width": word_width,
                "height": word_height,
                "word": wordJSON['word'],
                "start": wordJSON['start'],
                "end": wordJSON['end'],
                "duration": duration
            })

            word_clip = word_clip.set_position((x_pos, y_pos))
            word_clip_space = word_clip_space.set_position(
                (x_pos + word_width, y_pos))

            x_pos = x_pos + word_width + space_width
            line_width = line_width + word_width + space_width
        else:
            # Move to the next line
            x_pos = 0
            y_pos = y_pos + word_height+10
            line_width = word_width + space_width

            # Store info of each word_clip created
            xy_textclips_positions.append({
                "x_pos": x_pos,
                "y_pos": y_pos,
                "width": word_width,
                "height": word_height,
                "word": wordJSON['word'],
                "start": wordJSON['start'],
                "end": wordJSON['end'],
                "duration": duration
            })

            word_clip = word_clip.set_position((x_pos, y_pos))
            word_clip_space = word_clip_space.set_position(
                (x_pos + word_width, y_pos))
            x_pos = word_width + space_width

        word_clips.append(word_clip)
        word_clips.append(word_clip_space)

    for highlight_word in xy_textclips_positions:

        word_clip_highlight = TextClip(highlight_word['word'], font=font, fontsize=fontsize, color=highlight_color, stroke_color=stroke_color,
                                       stroke_width=stroke_width).set_start(highlight_word['start']).set_duration(highlight_word['duration'])
        word_clip_highlight = word_clip_highlight.set_position(
            (highlight_word['x_pos'], highlight_word['y_pos']))
        word_clips.append(word_clip_highlight)

    return word_clips, xy_textclips_positions


def generate_subtitles():
    clip = mp.VideoFileClip(CUTED_PART_OF_VIDEO)
    clip.audio.write_audiofile(CUTED_PART_OF_AUDIO)
    model = WhisperModel("base", device="cpu", compute_type="int8")

    segments, _ = model.transcribe(CUTED_PART_OF_AUDIO, word_timestamps=True)
    wordlevel_info = []
    for segment in segments:
        for word in segment.words:
            wordlevel_info.append(
                {'word': word.word.upper(), 'start': word.start, 'end': word.end})
    return wordlevel_info


def get_random_song(folder_path):
    files = [f for f in os.listdir(folder_path) if os.path.isfile(
        os.path.join(folder_path, f))]
    if not files:
        print("No files in the specified folder.")
        return None

    random_file = random.choice(files)
    return os.path.join(folder_path, random_file)


def fade_out_audio(input_file, output_file, fade_duration):
    # Get the duration of the input video
    ffprobe_cmd = ['ffprobe', '-i', input_file, '-show_entries',
                   'format=duration', '-v', 'quiet', '-of', 'csv=p=0']
    duration = float(subprocess.check_output(ffprobe_cmd).decode())

    # Calculate the start time for the fade-out
    start_time = max(0, duration - fade_duration)

    # Build the ffmpeg command
    ffmpeg_cmd = [
        'ffmpeg',
        '-i', input_file,
        '-af', f'afade=t=out:st={start_time}:d={fade_duration}',
        '-c:v', 'copy',
        output_file
    ]

    # Execute the ffmpeg command
    subprocess.run(ffmpeg_cmd)


def is_folder_empty(folder_path):
    contents = os.listdir(folder_path)
    return len(contents) == 0


def create_short(title, genre):
    input_video = VideoFileClip(CUTED_PART_OF_VIDEO)
    frame_size = input_video.size

    all_linelevel_splits = []
    linelevel_subtitles = split_text_into_lines(generate_subtitles())

    for line in linelevel_subtitles:
        out_clips, positions = create_caption(line, frame_size)

        max_width = 0
        max_height = 0

        for position in positions:
            # print (out_clip.pos)
            # break
            x_pos, y_pos = position['x_pos'], position['y_pos']
            width, height = position['width'], position['height']

            max_width = max(max_width, x_pos + width)
            max_height = max(max_height, y_pos + height)

        color_clip = ColorClip(size=(int(max_width*1.1), int(max_height*1.1)),
                               color=(64, 64, 64))
        color_clip = color_clip.set_opacity(0)
        color_clip = color_clip.set_start(
            line['start']).set_duration(line['end']-line['start'])

        # centered_clips = [each.set_position('center') for each in out_clips]

        clip_to_overlay = CompositeVideoClip([color_clip] + out_clips)
        clip_to_overlay = clip_to_overlay.set_position("bottom")

        all_linelevel_splits.append(clip_to_overlay)

    final_video = CompositeVideoClip([input_video] + all_linelevel_splits)

    # Set the audio of the final video to be the same as the input video
    final_video = final_video.set_audio(input_video.audio)

    # Save the final clip as a video file with the audio included
    final_video.write_videofile(
        VIDEO_WITH_SUBTITLES, fps=24, codec="libx264", audio_codec="aac")
    # merge audio
    title = title.replace(" ", "_")+".mp4"
    song_folder = genre_folders[genre]

    if is_folder_empty(song_folder):
        song = get_random_song(song_folder)

        song = song.replace("/", "\\")
        video_path = VIDEO_WITH_SUBTITLES.replace("/", "\\")
        temp_name = DONE_SHORTS_FOLDER+"trash"+title
        command = [
            'ffmpeg',
            '-y',
            '-i', video_path,
            '-i', song,
            '-filter_complex', '[0:a][1:a]amix=inputs=2:duration=first',
            '-c:v', 'copy',
            '-c:a', 'aac',
            '-strict', 'experimental',
            temp_name
        ]
        subprocess.run(command)

        fade_out_audio(temp_name, DONE_SHORTS_FOLDER+title, 3)
        os.remove(temp_name)
        return

    fade_out_audio(VIDEO_WITH_SUBTITLES, DONE_SHORTS_FOLDER+title, 3)

    # ffmpeg -i short.mp4 -i song.mp3 -filter_complex "[0:a][1:a]amix=inputs=2:duration=first" -c:v copy -c:a aac -strict experimental output_video.mp4


if __name__ == "__main__":
    create_short("testing", "fun", "no")
    # cut_video("0:20:14")
