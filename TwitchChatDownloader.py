import os
def downloadTwitchChatFile(path, v, cID, cSecret, startTime, endTime)
    tcdjsoncmd = 'tcd --video ' + str(v) + ' --output ' + path + ' --client-id ' + cID + " --client-secret " + cSecret + ' --format json ' + ' --start_time ' str(startTime) + " --video_length " + str(int(endTime-startTime))
    try:
        print("Downloading chat file")
        osRetJsonCode = os.system(tcdjsoncmd + teecmd)
    except:
        print("An error occurred with the chat file download!")

downloadTwitchChatFile("/Users/Vijay/Downloads", 770808731)

