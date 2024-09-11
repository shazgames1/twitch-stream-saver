import requests
import m3u8
import re
import argparse
import subprocess
from urllib.request import HTTPError
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Tuple
from pathlib import Path


@dataclass
class StreamInfo:
    resolution: Tuple[int, int]  # (width, height)
    frame_rate: int
    url: str


gql_endpoint = "https://gql.twitch.tv/gql"
user_agent = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:130.0) Gecko/20100101 Firefox/130.0"
client_id = "kimne78kx3ncx6brgo4mv6wki5h1ko"
device_id = "9rgCoOahmN2k2SV5dyd4ADo5XRN9xD6A"
playback_access_token_hash = "ed230aa1e33e07eebb8928504583da78a5173989fadfb1ac94be06a04f3cdbe9"


def ask_to_download():
    response = input(
        "Do you want to download the video with ffmpeg? (y/n): ").strip().lower()
    return response == 'y'


def get_output_file_path(username: str, resolution: Tuple[int, int]) -> Path:
    # Define the downloads folder path relative to the script's directory
    root_directory = Path(__file__).parent.parent
    downloads_folder = root_directory / "Downloads"

    # Create the downloads folder if it doesn't exist
    downloads_folder.mkdir(parents=True, exist_ok=True)

    filename = "{username} {timestamp} ({quality}p).mp4".format(
        username=username,
        timestamp=datetime.now().strftime("%Y-%m-%d %H_%M"),
        quality=str(resolution[1])
    )
    full_path = downloads_folder / filename

    return full_path


def download_stream(stream_url: str, output_file_path: Path):
    ffmpeg_command = [
        "ffmpeg",
        "-i", stream_url,
        "-c", "copy",
        "-loglevel", "warning",
        output_file_path
    ]

    # Start the ffmpeg process
    process = subprocess.Popen(
        ffmpeg_command,
        stdin=subprocess.PIPE
    )

    print("Downloading video with ffmpeg")

    try:
        process.wait()
    except KeyboardInterrupt:
        print("\nStopping ffmpeg...")

        process.wait()  # Wait for the process to terminate

        print("ffmpeg has been stopped")
    except Exception as e:
        print(f"An error occurred: {e}")


def extract_username(input_string: str):
    # Check if the input is a URL and extract the username
    url_pattern = r'https?://(www\.)?twitch\.tv/([a-zA-Z0-9_]+)'
    match = re.match(url_pattern, input_string)
    if match:
        return match.group(2)  # Return the username from the URL
    else:
        return input_string  # Return the input string as is if it's not a URL


def get_streams_by_username(username: str) -> Optional[list[StreamInfo]]:
    response = requests.post(
        gql_endpoint,
        json={
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
        },
        headers={
            "User-Agent": user_agent,
            "Client-Id": client_id,
            "Device-Id": device_id
        }
    )

    data = response.json()
    access_token = data.get("data").get("streamPlaybackAccessToken")

    if access_token is None:
        print("Cannot find streamer")
        return None

    value, signature = (
        [access_token.get("value"),
         access_token.get("signature")]
    )

    m3u8_url = f"https://usher.ttvnw.net/api/channel/hls/{username}.m3u8?allow_source=true&cdm=wv&fast_bread=true&platform=web&playlist_include_framerate=true&reassignments_supported=true&sig={
        signature}&supported_codecs=av1,h264&token={value}&transcode_mode=cbr_v1"

    # Work with m3u data
    try:
        playlist = m3u8.load(m3u8_url)
        streams: list[StreamInfo] = []

        for media_playlist in playlist.playlists:
            media_playlist_url = media_playlist.uri
            stream_info = media_playlist.stream_info

            stream = StreamInfo(
                resolution=stream_info.resolution,
                frame_rate=stream_info.frame_rate,
                url=media_playlist_url
            )

            streams.append(stream)

        return streams

    except HTTPError as e:
        if e.code == 404:
            print("Streamer is offline")


def main():
    parser = argparse.ArgumentParser(
        description="Extract Twitch username and preferred quality")
    parser.add_argument('--quality', type=str, required=True,
                        help="Preferred quality (1080, 720, 480, or 360)")
    parser.add_argument('--download', action='store_true',
                        help="Force download without asking for confirmation")
    parser.add_argument('username', type=str, help="Twitch username or URL")

    args = parser.parse_args()

    username = args.username
    desired_quality = int(args.quality)

    streams = get_streams_by_username(username)
    # Find stream with desired quality else return first
    stream = next(filter(
        lambda x: x.resolution[1] == desired_quality, streams), streams[0])

    # If user want to download stream, run ffmpeg else print stream url
    if args.download or ask_to_download():
        output_file_path = get_output_file_path(username, stream.resolution)
        download_stream(stream.url, output_file_path)
    else:
        print(str(stream.resolution[1]) + "p: " + stream.url)


if __name__ == "__main__":
    main()
