import ChatJsonRefine
import TwitchChatGenerator
import os
import shutil
import Config

path = "/Users/Vijay/Downloads/tempdir/"
VOD = 778143013
start = 150
end = 200

overlayInterval = {
    "interval": [
        30,
        40
    ],
    "chatCoordinates": {
        "widthScale": 0.3,
        "heightScale": 0.8
    },
    "textRGB": "rgb(255,255,255)"
}

def main():
    print("Preparing downloads...")
    cleanup(path,VOD)
    print("Starting chat file download")
    retCode = downloadTwitchChatFile(path, VOD, Config.client_id, Config.client_secret, start, end)
    if retCode==500:
        return
    print("Refining chat files")
    ChatJsonRefine.refineComments(path, path+str(VOD)+".json", path+str(VOD)+".log")
    print("Creating video")
    TwitchChatGenerator.createChatImageFaster(path, str(VOD)+".json", overlayInterval, start, VOD)
    print("Cleaning up...")
    cleanup(path,VOD)
    print("Finished!")
    #TODO: Create a config file, containing the things that we want to adjust for the chat (e.g. font size, actual font

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

def cleanup(path, VOD):
    if (os.path.exists(path+"foo2.txt")):
        os.remove(path+"foo2.txt")
    if (os.path.exists(path+"script.txt")):
        os.remove(path+"script.txt")
    if (os.path.isdir(path+"emotes")):
        shutil.rmtree(path+"emotes")
    if (os.path.isdir(path+"badges")):
        shutil.rmtree(path+"badges")
    if (os.path.exists(path+str(VOD)+".json")):
        os.remove(path+str(VOD)+".json")
    if (os.path.exists(path+str(VOD)+".log")):
        os.remove(path+str(VOD)+".log")
    if (os.path.exists(path+"ChatDictionary.json")):
        os.remove(path+"ChatDictionary.json")

main()

