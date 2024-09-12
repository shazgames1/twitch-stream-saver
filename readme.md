Here’s the updated documentation with the new optional argument `--download-folder`, including a note that it must be an absolute path:

```markdown
# Twitch Stream Saver

A Python program that allows users to record Twitch streams programmatically without the need for screen recording. This tool uses the Twitch GraphQL API and FFmpeg to capture and download streams.

## Requirements

- Python 3.6 or higher
- FFmpeg

## Installation

1. Clone the repository:

   ```bash
   git clone https://github.com/shazgames1/twitch-stream-saver
   cd twitch-stream-saver
   ```

2. (Optional) Create a virtual environment:

   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```

3. Install the required Python packages:

   ```bash
   pip install -r requirements.txt
   ```

4. Ensure FFmpeg is installed and accessible from your command line. You can download it from [FFmpeg's official website](https://ffmpeg.org/download.html).

## Usage

To record a Twitch stream, use the following command:

```bash
python3 src/main.py <username or url> --download --quality <quality> --fps <fps> --download-folder <path>
```

## Command-Line Options

- `<username or url>`: The Twitch username or URL of the streamer you want to record.
- `--download`: (Optional) Flag to indicate that the stream should be downloaded without asking the user.
- `--quality <quality>`: (Optional) Specify the desired quality of the stream (Acceptable values are 160, 360, 480, 720, or 1080). If the desired quality is not available, the highest quality of the stream will be used. If not provided, the highest quality of the stream will be used.
- `--fps <fps>`: (Optional) Specify the desired frame rate for the output video. Acceptable values are 24, 30, or 60. If not provided, the original frame rate of the stream will be used.
- `--download-folder <path>`: (Optional) Specify the path to the folder where the downloaded video will be saved. This must be an absolute path (for example `/home/user/Downloads` or `C:\Users\User\Downloads`).

### Examples

To record the stream of the user `di_rubens` at `720`p quality with a target frame rate of `30`, run:

```bash
python3 src/main.py di_rubens --download --quality 720 --fps 30 --download-folder "/home/user/Downloads"
```

To record the stream using the URL of the streamer:

```bash
python3 src/main.py https://www.twitch.tv/di_rubens --download
```
