# IP Camera Discord Bot

This is a Discord bot written in Python that allows you to take snapshots from various types of IP cameras and RTSP streams. The bot also includes features for searching camera dorks and getting location information using the ipinfo.io API.

## Features

- Take snapshots from IP cameras and RTSP streams
- Search for camera dorks using DuckDuckGo
- Display location information (country, region, city, timezone) based on the camera's IP address (ipinfo token needed)
- Generate Google Maps links for camera locations

## Requirements

- Python 3.7 or later
- Discord.py library
- Requests library
- Pillow library
- pytz library
- opencv-python library
- duckduckgo_search library

## Usage

1. Clone the repository or download the source code.
2. Install the required Python libraries.
3. Set your Discord bot token in the `DISCORD_TOKEN` variable.
4. Set your Discord server's guild ID in the `YOUR_GUILD_ID` variable.
5. Run the script: `python bot.py`

## Commands

- `/url base_url:http://example.com image_path:/path/to/image token:YOUR_TOKEN`: Snapshot of any IP camera.
- `/rtsp rtsp_url:rtsp://example.com/stream token:YOUR_TOKEN`: Snapshot of an RTSP camera.
- `/mobotix ip:192.168.1.100 port:80 token:YOUR_TOKEN`: Snapshot of a Mobotix camera.
- `/search search:camera_dork amount:10`: Search for camera dorks using DuckDuckGo.

## Note

- This bot is intended for educational and security research purposes only. Please use it responsibly and respect the privacy of others.
- The bot requires appropriate permissions to upload files and send messages in the Discord server.
- Replace `YOUR_TOKEN` with your actual token from ipinfo.io for location information.
- Btw this is demo version of full version. That means I removed most of the functions xd but ye, have fun.

## License

This project is licensed under the [MIT License](LICENSE).
