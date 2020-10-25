#!/usr/bin/python
import ChatJsonRefine
import TwitchChatGenerator
import os
import shutil

def downloadAndRender(path, outputPath, VOD, start, end, twitchConfig):
    print("Preparing downloads...")
    cleanup(path)
    print("Starting chat file download")
    retCode = downloadTwitchChatFile(path, VOD, twitchConfig["client_id"], twitchConfig["client_secret"], start, end)
    if retCode==500:
        return
    print("Refining chat files")
    retCode = ChatJsonRefine.refineComments(path, path+str(VOD)+".json", path+str(VOD)+".log")
    if retCode==500:
        cleanup(path)
        return
    print("Creating video")
    overlayInterval = {"interval": [0,end-start]}
    output_file, duration = TwitchChatGenerator.createChatImageFaster(path, outputPath, str(VOD)+".json", overlayInterval, start, VOD)
    print("Cleaning up...")
    cleanup(path)
    print("Finished!")

def downloadTwitchChatFile(path, v, cID, cSecret, startTime, endTime):
    retries = 5
    downloaded = False
    tcdjsoncmd = 'python ./tcd/chatdownloader.py --video ' + str(v) + ' --output ' + path + ' --client-id ' + cID + " --client-secret " + cSecret + ' --format json ' + ' --start_time ' + str(startTime) + " --video_length " + str(int(endTime-startTime))
    retCode = executeCommandWithRetries(tcdjsoncmd, retries)
    if retCode == 500:
        return 500
    tcdtxtcmd = 'python ./tcd/chatdownloader.py --video ' + str(v) + ' --output ' + path + ' --client-id ' + cID + " --client-secret " + cSecret + ' --format irc ' + ' --start_time ' + str(startTime) + " --video_length " + str(int(endTime-startTime))
    retCode = executeCommandWithRetries(tcdtxtcmd, retries)
    if retCode == 500:
        return 500


def executeCommandWithRetries(cmd, retries):
    downloaded = False
    while retries>0 and not downloaded:
        retCode = os.system(cmd)
        if retCode==0:
            downloaded = True
        else:
            print("Download failed!", retries, "more tries before giving up.")
            retries-=1
    if downloaded:
        return 200
    else:
        print("Download unsuccessful! Please make sure the VOD is valid and the chat has not expired by going to twitch.tv")
        return 500

def cleanup(path):
    if os.path.isdir(path):
        shutil.rmtree(path)

