from datetime import datetime
import os
import re
import subprocess
import json

from pydantic import BaseModel


class StreamInfo(BaseModel):

    index: int
    codec_type: str
    codec_name: str
    coded_height: int = 0
    coded_width: int = 0


class VideoInfo(BaseModel):

    name: str
    format_name: str
    duration_seconds: int = 0
    size: int = 0
    bit_rate: int = 0
    streams: list[StreamInfo]

    @property
    def duration(self):
        duration = self.duration_seconds
        hours, remainder = divmod(duration, 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{hours}:{minutes:02}:{seconds:02}"


def get_media_info(file_path: str) -> VideoInfo | None:
    entries_required = (
        "format=format_name,duration,size,bit_rate : "
        "stream=index,codec_type,codec_name,coded_height,coded_width"
    )
    ffprobe_cmd = [
        "ffprobe",
        "-v",
        "error",
        "-show_entries",
        entries_required,
        "-of",
        "json",
        file_path,
    ]
    try:
        # Run ffprobe command to get media info
        result = subprocess.run(
            ffprobe_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        # If command ran successfully, parse the output
        if result.returncode == 0:
            info = json.loads(result.stdout)
            format: dict[str, str] = info.get("format", {})
            # Create VideoInfo object
            video_info = VideoInfo(
                name=os.path.basename(file_path),
                format_name=str(format.get("format_name", "N/A")),
                duration_seconds=int(float(format.get("duration", "0"))),
                size=int(format.get("size", "0")),
                bit_rate=int(format.get("bit_rate", "0")),
                streams=[],
            )
            # Loop through streams and create StreamInfo objects
            for stream in info["streams"]:
                stream_info = StreamInfo(
                    index=int(stream.get("index", 0)),
                    codec_type=str(stream.get("codec_type", "N/A")),
                    codec_name=str(stream.get("codec_name", "N/A")),
                    coded_height=int(stream.get("coded_height", 0)),
                    coded_width=int(stream.get("coded_width", 0)),
                )
                video_info.streams.append(stream_info)
            return video_info
        else:
            print(f"Error: {result.stderr}")
    except Exception as e:
        print(f"Exception: {str(e)}")
    return None


def get_silence_timestamps(file_path):
    time = datetime.now()
    try:
        result = subprocess.run(
            [
                "ffmpeg",
                "-i",
                file_path,
                "-af",
                "silencedetect=noise=-30dB:d=3",
                "-f",
                "null",
                "-",
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        silence_start = None
        silence_end = None
        for line in result.stderr.split("\n"):
            if "silence_start" in line:
                silence_start = float(
                    re.search(r"silence_start: (\d+\.\d+)", line).group(1)  # type: ignore
                )
            if "silence_end" in line:
                silence_end = float(
                    re.search(r"silence_end: (\d+\.\d+)", line).group(1)  # type: ignore
                )
            if silence_start is not None and silence_end is not None:
                print(f"Silence start: {silence_start}, Silence end: {silence_end}")
                break
        timeTook = datetime.now() - time
        print(f"Time took: {timeTook}")
        return silence_start, silence_end
    except Exception as e:
        print(f"Exception: {str(e)}")
    timeTook = datetime.now() - time
    print(f"Time took: {timeTook}")
    return None, None


def detect_silence(file_path, output_file, end_timestamp):
    time = datetime.now()
    try:
        # Remove silence
        remove_cmd = [
            "ffmpeg",
            "-i",
            file_path,
            "-to",
            str(end_timestamp),
            "-c:v",
            "copy",
            "-c:a",
            "copy",
            "-c:s",
            "copy",
            output_file,
        ]
        remove_result = subprocess.run(
            remove_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
        )
        if remove_result.returncode == 0:
            # print("STDERR:")
            # print(remove_result.stderr)
            print(f"Silent parts removed and saved to {output_file}")
        else:
            print(f"Error: {remove_result.stderr}")
    except Exception as e:
        print(f"Exception: {str(e)}")
    timeTook = datetime.now() - time
    print(f"Time took: {timeTook}")
    return None


# folder = "/media/movies/all/Pechi (2024) {imdb-tt33034505}"
# input_file = f"{folder}/Pechi - Trailer-trailer.webm"
# output_file = f"{folder}/Pechi - Trailer 1-trailer.mkv"
# res = get_media_info(input_file)
# print(res)
# if not res:
#     print("No media info")
#     exit(0)
# streams = res.streams
# if not any(stream.codec_type == "audio" for stream in streams):
#     # No audio stream, delete the trailer file
#     print("No audio stream")
# silence_start, silence_end = get_silence_timestamps(input_file)
# We will use the start time of the silence to remove the silent part from the video
# if silence_start is not None and silence_end is not None:
#     detect_silence(
#         input_file,
#         output_file,
#         silence_start,
#     )
# else:
#     print("No silence detected")
