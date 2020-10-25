# TwitchChatVideoRenderer

## About
The code will generate an equivalent video of twitch chat, with Twitch, BTTV, and FFZ emotes included. All it requires is a twitch json file, which can be downloaded with TCD.

TCD: https://github.com/PetterKraabol/Twitch-Chat-Downloader

## Usage
How to use (only linux machines):
1. [Install FFmpeg](https://ffmpeg.org/download.html). I prefer using [homebrew](https://brew.sh/). Simply `brew install ffmpeg`
2. Python interpreter and pip. Install dependencies with `pip install -r requirements.txt`
3. Twitch dev credentials - client-id and client-secret - from [here](https://dev.twitch.tv/console/apps/). Make an account, create a dummy app, and grab the credentials. FYI: These credentials allow you to download ANY VOD chat.

`python TCVR.py --help for more detailed info`

`python TCVR.py --client_id {YOUR CLIENT ID} --client_secret {YOUR CLIENT SECRET} --output {OUTPUT DIRECTORY} --video {Twitch VOD ID} --start_time {START TIME OF CHAT} --duration {DURATION OF CHAT}`

You only need client_secret and client_id on first run. After that you only need VOD id is the minimum parameter requirement.

To fine tune your video, check out ChatSettings.py

## More Information

FFmpeg processing time varies by CPU. It takes me about 2 minutes to generate a 5 minute chat file.

The code will generate an equivalent video of twitch chat, with emotes and all. All it requires is a twitch json file, which can be downloaded with TCD.

Open any issues if you have questions or email me. This is part of a bigger project.

Leave a star if it works for you!
