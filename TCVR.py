#!/usr/bin/env python
import argparse
import os
import json
from DownloadAndRender import downloadAndRender

configFile = "./config.json"
tempDir = "./tempdir/"

def main():
    parser = argparse.ArgumentParser(description='Renders a replay of Twitch Chat')
    parser.add_argument('--client_id', type=str, help='Twitch Client Id')
    parser.add_argument('--client_secret', type=str, help='Twitch Client Secret')
    parser.add_argument('--output', type=str, help='Output directory', default='./ChatVideos/')
    parser.add_argument('--video', type=int, help='Twitch VOD Id')
    parser.add_argument('--start_time', type=int, help='Start time in seconds', default=0)
    parser.add_argument('--duration', type=int, help='Duration of chat', default=10)

    args = parser.parse_args()

    twitchConfig = {}

    if args.video == None:
        print("ERROR: Must provide a Twitch VOD id! You can find it in the URL of the twitch VOD you are interested in.")
        return

    if args.client_id == None and args.client_secret == None:
        if os.path.exists(configFile):
            with open(configFile) as config:
                twitchConfig = json.load(config)
        else:
            print("ERROR: Must provide a client-id and client-secret on first use!")
            print("You can get one here: https://dev.twitch.tv/console/apps")
            return
    else:
        twitchConfig["client_id"]=args.client_id
        twitchConfig["client_secret"]=args.client_secret
        with open(configFile, 'w') as config:
            json.dump(twitchConfig,config)

    start = args.start_time
    end = start+args.duration
    if args.output[-1]!="/":
        path=args.output+"/"
    else:
        path=args.output
    if not os.path.isdir(path):
        os.mkdir(path)
    downloadAndRender(tempDir, args.output, args.video, start, end, twitchConfig)    

if __name__ == "__main__":
    main()