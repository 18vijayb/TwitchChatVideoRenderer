import ChatJsonRefine
import TwitchChatGenerator
import os
import shutil
import Config

path = "/Users/Vijay/Downloads/tempdir/"
VOD = 774267721
start = 50
end = 100

overlayInterval = {
    "interval": [
        55,
        65
    ],
    "chatCoordinates": {
        "widthScale": 0.3,
        "heightScale": 0.8
    },
    "backgroundRGBA": "rgba(255,255,255,0.7)",
    "textRGB": "rgb(255,255,255)"
}

def main():
    cleanup(path,VOD)
    downloadTwitchChatFile(path, VOD, Config.client_id, Config.client_secret, start, end)
    ChatJsonRefine.refineComments(path, path+str(VOD)+".json", path+str(VOD)+".log")
    TwitchChatGenerator.createChatImageFaster(path, str(VOD)+".json", overlayInterval, start, VOD)
    cleanup(path,VOD)
    print("Finished!")
    #TODO: Create a config file, containing the things that we want to adjust for the chat (e.g. font size, actual font

def downloadTwitchChatFile(path, v, cID, cSecret, startTime, endTime):
    tcdjsoncmd = 'python ./tcd/chatdownloader.py --video ' + str(v) + ' --output ' + path + ' --client-id ' + cID + " --client-secret " + cSecret + ' --format json ' + ' --start_time ' + str(startTime) + " --video_length " + str(int(endTime-startTime))
    print("Downloading chat file json")
    osRetJsonCode = os.system(tcdjsoncmd)
    tcdtxtcmd = 'python ./tcd/chatdownloader.py --video ' + str(v) + ' --output ' + path + ' --client-id ' + cID + " --client-secret " + cSecret + ' --format irc ' + ' --start_time ' + str(startTime) + " --video_length " + str(int(endTime-startTime))
    print("Downloading chat file txt")
    osRetTxtCode = os.system(tcdtxtcmd)

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

