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
python3 src/main.py <streamer_name> --quality <quality> --download
```

## Command-Line Options

- `<streamer_name>`: The Twitch username of the streamer you want to record.
- `--quality <quality>`: Specify the desired quality of the stream (e.g., 720, 1080).
- `--download`: Flag to indicate that the stream should be downloaded without asking the user.

### Example

To record the stream of the user `di_rubens` at 720p quality, run:

```bash
python3 src/main.py di_rubens --quality 720 --download
```