import requests
import m3u8
import re
import argparse
import subprocess
import logging
import os
from urllib.request import HTTPError
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Tuple
from pathlib import Path


gql_endpoint = "https://gql.twitch.tv/gql"
user_agent = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:130.0) Gecko/20100101 Firefox/130.0"
client_id = "kimne78kx3ncx6brgo4mv6wki5h1ko"
device_id = "9rgCoOahmN2k2SV5dyd4ADo5XRN9xD6A"
playback_access_token_hash = "ed230aa1e33e07eebb8928504583da78a5173989fadfb1ac94be06a04f3cdbe9"


@dataclass
class StreamInfo:
    resolution: Tuple[int, int]  # (width, height)
    frame_rate: int
    url: str


def validate_download_folder(folder_path: Path) -> Path:
    if not folder_path.exists():
        folder_path.mkdir(parents=True, exist_ok=True)

    if not folder_path.is_dir():
        raise ValueError(f"The path {folder_path} is not a directory.")

    if not os.access(folder_path, os.W_OK):
        raise PermissionError(f"The directory {folder_path} is not writable.")

    if not folder_path.is_absolute():
        raise ValueError(f"The path {
                         folder_path} must be an absolute path. Example: /home/user/Downloads")

    return folder_path


def ask_to_download():
    response = input(
        "Do you want to download the video with ffmpeg? (y/n): ").strip().lower()
    return response == "y"


def get_output_file_path(username: str, resolution: Tuple[int, int], fps: int, download_folder: Path) -> Path:
    # Create the downloads folder if it doesn't exist
    download_folder.mkdir(parents=True, exist_ok=True)

    filename = "{username} {timestamp} ({quality}p{fps}).mp4".format(
        username=username,
        timestamp=datetime.now().strftime("%Y-%m-%d %H_%M"),
        quality=str(resolution[1]),
        fps=fps
    )
    full_path = download_folder / filename

    return full_path


def download_stream(stream: StreamInfo, username: str, download_folder: Path, fps: Optional[int] = None):
    # Base ffmpeg command
    ffmpeg_command = [
        "ffmpeg",
        "-y",  # Override file if exists
        "-i", stream.url,
        "-loglevel", "warning"
    ]

    # Determine if transcoding is required
    transcoding_required = fps is not None and stream.frame_rate != fps

    # If user desired fps is defined and not equal to stream fps, set the frame rate
    # else copy the streams without reencoding
    ffmpeg_command += ["-r",
                       str(fps)] if transcoding_required else ["-c", "copy"]

    # Determine output file path
    output_file_fps = int(stream.frame_rate if fps is None else fps)
    output_file_path = get_output_file_path(
        username, stream.resolution, fps=output_file_fps, download_folder=download_folder)
    ffmpeg_command.append(output_file_path)

    # Start the ffmpeg process
    process = subprocess.Popen(
        ffmpeg_command,
        stdin=subprocess.PIPE
    )

    logging.info("Downloading {quality}p{fps} video with ffmpeg {transcode} to {dest_path}".format(
        quality=stream.resolution[1],
        fps=output_file_fps,
        transcode="with transcoding" if transcoding_required else "without transcoding",
        dest_path=output_file_path
    ))

    try:
        process.wait()
    except KeyboardInterrupt:
        logging.info("Stopping ffmpeg...")

        process.wait()  # Wait for the process to terminate

        logging.info("ffmpeg has been stopped")
    except Exception as e:
        logging.exception(f"An error occurred: {e}")


def extract_username(input_string: str):
    # Check if the input is a URL and extract the username
    url_pattern = r"https?://(www\.)?twitch\.tv/([a-zA-Z0-9_]+)"
    match = re.match(url_pattern, input_string)
    if match:
        return match.group(2)  # Return the username from the URL
    else:
        return input_string  # Return the input string as is if it's not a URL


def get_streams_by_username(username: str) -> Optional[list[StreamInfo]]:
    payload = {
        "operationName": "PlaybackAccessToken",
        "variables": {
            "isLive": True,
            "login": username,
            "isVod": False,
            "vodID": "",
            "playerType": "site",
            "platform": "web"
        },
        "extensions": {
            "persistedQuery": {
                "version": 1,
                "sha256Hash": playback_access_token_hash
            }
        }
    }

    headers = {
        "User-Agent": user_agent,
        "Client-Id": client_id,
        "Device-Id": device_id
    }

    response = requests.post(gql_endpoint, json=payload, headers=headers)
    data = response.json()
    access_token = data.get("data", {}).get("streamPlaybackAccessToken")

    if access_token is None:
        logging.error("Streamer not found")
        return None

    value = access_token.get("value")
    signature = access_token.get("signature")

    m3u8_url = (
        f"https://usher.ttvnw.net/api/channel/hls/{username}.m3u8"
        f"?&sig={signature}&supported_codecs=av1,h264&token={value}"
        "&allow_source=true&cdm=wv&fast_bread=true&platform=web"
        "&playlist_include_framerate=true&reassignments_supported=true"
        "&transcode_mode=cbr_v1"
    )

    # Work with m3u data
    try:
        playlist = m3u8.load(m3u8_url)
        streams = [
            StreamInfo(
                resolution=media_playlist.stream_info.resolution,
                frame_rate=media_playlist.stream_info.frame_rate,
                url=media_playlist.uri
            )
            for media_playlist in playlist.playlists
        ]

        return streams

    except HTTPError as e:
        if e.code == 404:
            logging.error("Streamer is offline")
        else:
            logging.exception(e)

        return None


def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    parser = argparse.ArgumentParser(
        description="Extract Twitch username and preferred quality")
    # Quality
    parser.add_argument("--quality", type=int, choices=[160, 360, 480, 720, 1080],
                        help="Preferred quality (1080, 720, 480, 360 or 160)")
    # Force download
    parser.add_argument("--download", action="store_true",
                        help="Force download without asking for confirmation")
    # FPS
    parser.add_argument("--fps", type=int, choices=[24, 30, 60],
                        help="Optional frame rate (24, 30, or 60)")
    parser.add_argument("username", type=str, help="Twitch username or URL")

    # Download folder path
    parser.add_argument("--download-folder", type=str, default=str(Path(__file__).parent.parent / "Downloads"),
                        help="Path to the download folder (default: [repository_root_folder]/Downloads)")

    args = parser.parse_args()

    username = args.username
    desired_quality = args.quality
    fps = args.fps
    force_download = args.download
    download_folder = Path(args.download_folder)

    try:
        download_folder = validate_download_folder(download_folder)
    except (ValueError, PermissionError) as e:
        logging.error(e)
        return

    streams = get_streams_by_username(username)

    if streams is None:
        return

    # Find stream with desired quality else return first
    stream = next(filter(
        lambda x: x.resolution[1] == desired_quality, streams), streams[0])

    # If user want to download stream, run ffmpeg else print stream url
    if force_download or ask_to_download():
        download_stream(stream, username=username, fps=fps,
                        download_folder=download_folder)
    else:
        print(str(stream.resolution[1]) + "p: " + stream.url)


if __name__ == "__main__":
    main()
