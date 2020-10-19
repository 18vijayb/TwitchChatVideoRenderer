import os
def downloadTwitchChatFile(path, v, cID, cSecret, startTime, endTime):
    tcdjsoncmd = 'python ./tcd/chatdownloader.py --video ' + str(v) + ' --output ' + path + ' --client-id ' + cID + " --client-secret " + cSecret + ' --format json ' + ' --start_time ' + str(startTime) + " --video_length " + str(int(endTime-startTime))
    print("Downloading chat file")
    osRetJsonCode = os.system(tcdjsoncmd)
    

downloadTwitchChatFile("/Users/Vijay/Downloads", 770808731, 0, 1000000)

