import json
import os
from tqdm import tqdm
from PIL import Image, ImageFont
import subprocess
import math
from timeit import default_timer as timer
from os import listdir
from os.path import isfile, join

#####CONSTANTS#######

from ChatSettings import COMMENT_SPACING, NO_EMOTE_COMMENT_SPACING, LINE_SPACING 
from ChatSettings import TEXT_COLOR, FONT_SIZE, ENGLISH_REGULAR_FONT_FILE, ENGLISH_BOLD_FONT_FILE, REGULAR_FONT_FILE, BOLD_FONT_FILE
from ChatSettings import CHAT_WIDTH, CHAT_HEIGHT
from ChatSettings import IMAGE_ADJUST, SMALL_EMOTE_SIZE, ORIGIN_X, ORIGIN_Y, INDIVIDUAL_DURATIONS 

REGULAR_FONT = ImageFont.truetype(REGULAR_FONT_FILE, FONT_SIZE)
BOLD_FONT = ImageFont.truetype(BOLD_FONT_FILE, FONT_SIZE)
ENGLISH_REGULAR_FONT = ImageFont.truetype(ENGLISH_REGULAR_FONT_FILE, FONT_SIZE)
ENGLISH_BOLD_FONT = ImageFont.truetype(ENGLISH_BOLD_FONT_FILE, FONT_SIZE)

def isEnglish(s):
    try:
        s.encode(encoding='utf-8').decode('ascii')
    except UnicodeDecodeError:
        return False
    else:
        return True

def emote_width(filepath):
    width, height = Image.open(filepath).size
    return width


def emote_height(filepath):
    width, height = Image.open(filepath).size
    return height

def create_video(blankvideo,video, width, height, duration):
    command = ["ffmpeg", "-t", str(duration), "-f", "lavfi", "-i", "color=0x000000:"+str(width)+"x"+str(height+ORIGIN_Y), "-r", "30","-pix_fmt",  "yuv420p", "-loglevel","quiet", video]
    subprocess.call(command)


def drawtext(inputFilter, startTime, endTime, font, text, yCoordinate, xCoordinate, color, outputFilter):
    text = text.replace("\'", "").replace("\\", "").replace(":", "\:")
    return "{inputFilter}drawtext=enable='between(t,{startTime},{endTime})':fontfile='{font}':text='{text}':y={yCoordinate}-max_glyph_a:x={xCoordinate}:fontsize={FONT_SIZE}:fontcolor='{color}' {outputFilter};".format(
        inputFilter=inputFilter,
        startTime=startTime,
        endTime=endTime,
        font=font,
        text=text,
        yCoordinate=yCoordinate,
        xCoordinate=xCoordinate,
        FONT_SIZE=FONT_SIZE,
        color=color,
        outputFilter=outputFilter)


def drawimage(inputFilter, imageFilter, startTime, endTime, yCoordinate, xCoordinate, outputFilter, filetype,
              smallEmote):
    return "{inputFilter}{imageFilter}overlay=enable='between(t,{startTime},{endTime})':y={yCoordinate}-overlay_h+{heightAdjust}:x={xCoordinate}{shortest} {outputFilter};".format(
        inputFilter=inputFilter,
        imageFilter=imageFilter,
        startTime=startTime,
        endTime=endTime,
        heightAdjust=0 if smallEmote else IMAGE_ADJUST,
        yCoordinate=yCoordinate,
        xCoordinate=xCoordinate,
        shortest=":shortest=1" if filetype == "gif" else "",
        outputFilter=outputFilter)


def createTimeToCommentIndexMap(comments, video_start):
    commentMap = dict()
    index = 0
    for comment in comments:
        time = math.floor(comment["content_offset_seconds"])
        if not time in commentMap:
            commentMap[time] = list()
        commentMap[time].append(index)
        index += 1
    return commentMap


def determineMessageHeight(comment, video_width, video_height, path):
    xCoordinate = ORIGIN_X
    totalHeight = 0
    username = comment["commenter"]

    if "user_badges" in comment["message"]:
        for badge in comment["message"]["user_badges"]:
            badge_path = path + "badges/" + badge["_id"] + "_" + badge["version"] + ".png"
            dx = emote_width(badge_path)
            xCoordinate += dx
            dx, height = BOLD_FONT.getsize(" ")
            xCoordinate += dx

    # Get username width/height
    if (isEnglish(username)):
        dx, height = BOLD_FONT.getsize(username)
    else:
        dx, height = ENGLISH_BOLD_FONT.getsize(username)
    xCoordinate += dx

    # Render colon and space after username
    dx, height = BOLD_FONT.getsize(": ")
    xCoordinate += dx

    if isEnglish(comment["message"]["body"]):
        fontToUse = REGULAR_FONT
    else:
        fontToUse = ENGLISH_REGULAR_FONT

    # Render fragments of message
    lineheights = list()
    hasEmote = False
    for fragment in comment["message"]["fragments"]:
        if "emoticon" in fragment:
            hasEmote = True
            if not "id" in fragment["emoticon"]:
                emote_path = path + "emotes/" + str(fragment["emoticon"]["emoticon_id"]) + ".png"
            else:
                emote_path = path + "emotes/" + str(fragment["emoticon"]["id"]) + "." + fragment["emoticon"]["type"]
            dx = emote_width(emote_path)
        else:
            text = fragment["text"]
            dx, height = fontToUse.getsize(text)

        # check if out of bounds
        if (xCoordinate + dx) > video_width:
            if hasEmote:
                totalHeight += COMMENT_SPACING
                lineheights.append(COMMENT_SPACING)
                hasEmote = False
            else:
                totalHeight += NO_EMOTE_COMMENT_SPACING
                lineheights.append(NO_EMOTE_COMMENT_SPACING)
            xCoordinate = ORIGIN_X
        xCoordinate += dx
    return totalHeight + (COMMENT_SPACING if hasEmote else NO_EMOTE_COMMENT_SPACING), lineheights


def render_comments(timeInVideo, timeInChatFile, timeToComments, comments, heights, video_width, video_height,
                    inputFilter, counter, textcolor, emotelist, duration, path, userInfo):
    xCoordinate = ORIGIN_X
    yCoordinate = ORIGIN_Y + video_height
    command = ""
    lastFilter = inputFilter
    minimum = min(timeToComments.keys())
    index = 0
    firstIteration = True

    while True:
        index -= 1
        if ((not firstIteration) and ((index * -1) > numCommentsAtTime)):
            timeInChatFile -= 1
            index = -1
        firstIteration = False
        while not timeInChatFile in timeToComments and timeInChatFile >= minimum:
            timeInChatFile -= 1
            index = -1
        if timeInChatFile < minimum:
            return heights, lastFilter, command, counter, emotelist
        numCommentsAtTime = len(timeToComments[timeInChatFile])
        commentIndex = timeToComments[timeInChatFile][index]
        comment = comments[commentIndex]
        if not commentIndex in heights:
            heights[commentIndex] = determineMessageHeight(comment, video_width, video_height, path)
        yCoordinate -= heights[commentIndex][0] + LINE_SPACING
        lastFilter, comment_command, counter, emotelist = render_comment(comment, timeInVideo, xCoordinate, yCoordinate,
                                                                         lastFilter, counter, textcolor,
                                                                         video_width, emotelist, duration, path, userInfo, heights[commentIndex][1])
        command += comment_command
        # yCoordinate -= LINE_SPACING
        if yCoordinate < ORIGIN_Y:
            return heights, lastFilter, command, counter, emotelist


def render_comment(comment, startTime, xCoordinate, yCoordinate, inputFilter, counter, textcolor, video_width,
                   emotelist, duration, path, userInfo, lineheights):
    command = ""
    lastFilter = inputFilter
    endTime = startTime + 1
    username = comment["commenter"]
    userColor = userInfo[username.lower()]["color"]

    if "user_badges" in comment["message"]:
        for badge in comment["message"]["user_badges"]:
            outputFilter = "[badge{counter}]".format(counter=counter)
            badge_path = path + "badges/" + badge["_id"] + "_" + badge["version"] + ".png"
            outputFilter = "[username{counter}]".format(counter=counter)
            if not badge_path in emotelist:
                emotelist.append(badge_path)
                imagefilter = "[{index}:v]".format(index=len(emotelist))
            else:
                imagefilter = "[{index}:v]".format(index=emotelist.index(badge_path) + 1)
            dx = emote_width(badge_path)
            command += drawimage(lastFilter, imagefilter, startTime, endTime, yCoordinate, xCoordinate, outputFilter,
                                 "png", emote_height(badge_path) < SMALL_EMOTE_SIZE)
            xCoordinate += dx
            lastFilter = outputFilter
            dx, height = BOLD_FONT.getsize(" ")
            xCoordinate += dx
            counter += 1

    # Render username
    if (isEnglish(username)):
        dx, height = BOLD_FONT.getsize(username)
        fontToUse = BOLD_FONT_FILE
    else:
        dx, height = ENGLISH_BOLD_FONT.getsize(username)
        fontToUse = ENGLISH_BOLD_FONT
    outputFilter = "[username{counter}]".format(counter=counter)
    command += drawtext(lastFilter, startTime, endTime, fontToUse, username, yCoordinate, xCoordinate, userColor,
                        outputFilter)
    xCoordinate += dx
    lastFilter = outputFilter

    # Render colon and space after username
    dx, height = BOLD_FONT.getsize(": ")
    outputFilter = "[colon{counter}]".format(counter=counter)
    command += drawtext(lastFilter, startTime, endTime, BOLD_FONT_FILE, ": ", yCoordinate, xCoordinate, textcolor,
                        outputFilter)
    lastFilter = outputFilter
    xCoordinate += dx

    if isEnglish(comment["message"]["body"]):
        fontFileToUse = REGULAR_FONT_FILE
        fontToUse = REGULAR_FONT
    else:
        fontFileToUse = ENGLISH_REGULAR_FONT_FILE
        fontToUse = ENGLISH_REGULAR_FONT

    lineheightindex = 0
    # Render fragments of message
    for fragment in comment["message"]["fragments"]:
        outputFilter = "[fragment{counter}]".format(counter=counter)
        if "emoticon" in fragment:
            if not "id" in fragment["emoticon"]:
                emote_path = path + "emotes/" + str(fragment["emoticon"]["emoticon_id"]) + ".png"
                filetype = "png"
            else:
                emote_path = path + "emotes/" + str(fragment["emoticon"]["id"]) + "." + fragment["emoticon"]["type"]
                filetype = fragment["emoticon"]["type"]
            if not emote_path in emotelist:
                emotelist.append(emote_path)
                imagefilter = "[{index}:v]".format(index=len(emotelist))
            else:
                imagefilter = "[{index}:v]".format(index=emotelist.index(emote_path) + 1)
            dx = emote_width(emote_path)
            if (xCoordinate + dx) > video_width:
                yCoordinate += lineheights[lineheightindex]
                xCoordinate = ORIGIN_X
                lineheightindex += 1
            command += drawimage(lastFilter, imagefilter, startTime, endTime, yCoordinate, xCoordinate, outputFilter,
                                 filetype, emote_height(emote_path) < SMALL_EMOTE_SIZE)
        else:
            text = fragment["text"]
            dx, height = fontToUse.getsize(text)
            # check if out of bounds
            if (xCoordinate + dx) > video_width:
                yCoordinate += lineheights[lineheightindex]
                xCoordinate = ORIGIN_X
                lineheightindex += 1
            # render the word
            command += drawtext(lastFilter, startTime, endTime, fontFileToUse, text, yCoordinate, xCoordinate, textcolor,
                                outputFilter)
        xCoordinate += dx
        lastFilter = outputFilter
        counter += 1
    return lastFilter, command, counter, emotelist


def createChatImage(path,chatfile, overlayInterval, video_start, index, startTime, endTime):
    BadgesFolder = path+"badges/"
    EmotesFolder = path+"emotes/"
    video_width = CHAT_WIDTH
    video_height = CHAT_HEIGHT
    duration = endTime-startTime
    textcolor = TEXT_COLOR
    with open(path + chatfile) as chat:
        data = json.load(chat)
    with open(path + "ChatDictionary.json") as chatdict:
        userInfo = json.load(chatdict)["UserInfo"]
    timesToComments = createTimeToCommentIndexMap(data["comments"], video_start)
    input_video = path + "blank" + str(index) + ".mp4"
    input_video_trans = path + "blanktrans" + str(index) + ".mov"
    output_video_name = "chat" + str(index) + ".mp4"
    output_video = path + output_video_name
    if os.path.exists(input_video):
        os.remove(input_video)
    if os.path.exists(output_video):
        os.remove(output_video)
    create_video(input_video_trans, input_video, video_width, video_height, duration)
    xCoordinate = ORIGIN_X
    yCoordinate = ORIGIN_Y
    counter = 0
    lastFilter = "[0:v]"
    script = ""
    heights = dict()
    emotelist = list()
    #We append a set of chats at each second of the video
    for time in range(0,math.ceil(duration)):
        #The time in the chat file is the time in the current chat interval (time), startTime of the overlay interval (startTime), and the start time provided by the user (video_start)
        timeInChatFile = math.floor(time + startTime + video_start)
        heights, outputFilter, current_command, counter, emotelist = render_comments(time, timeInChatFile,
                                                                                     timesToComments, data["comments"],
                                                                                     heights, video_width, video_height,
                                                                                     lastFilter, counter,
                                                                                     textcolor, emotelist, duration,
                                                                                     path, userInfo)
        script += current_command
        lastFilter = outputFilter
    script += "{lastFilter}crop=x=0:y={ORIGIN_Y}:h={height}[cropped]".format(
        lastFilter=lastFilter,
        ORIGIN_Y = ORIGIN_Y,
        height = video_height
    )
    lastFilter = "[cropped]"
    #script = script[:-1]
    with open(path + "script.txt", "w") as script_file:
        script_file.write(script)
    ffmpeg_command = ["ffmpeg", "-i", input_video]
    for i in range(len(emotelist)):
        if ".gif" in emotelist[i]:
            ffmpeg_command.append("-ignore_loop")
            ffmpeg_command.append("0")
            ffmpeg_command.append("-i")
            ffmpeg_command.append(emotelist[i])
        else:
            ffmpeg_command.append("-i")
            ffmpeg_command.append(emotelist[i])
    ffmpeg_command.extend(
        ["-filter_complex_script", path + "script.txt", "-map", lastFilter, "-loglevel", "quiet", "-nostats", "-c:v", "libx264", "-pix_fmt",  "yuv420p", output_video])
    subprocess.call(ffmpeg_command)
    return output_video_name, duration

def createChatImageFaster(path,outputPath,chatfile,overlayInterval,startTime, VOD):
    overlayStart = overlayInterval["interval"][0]
    overlayEnd = overlayInterval["interval"][1]
    overallDuration = overlayEnd-overlayStart
    time = overlayStart
    finalOutputVid = outputPath+str(VOD)+".mp4"
    if os.path.exists(finalOutputVid):
        index = 2
        finalOutputVid = outputPath+str(VOD)+"_"+str(index)+".mp4"
        while os.path.exists(finalOutputVid):
            index += 1
            finalOutputVid = outputPath+str(VOD)+"_"+str(index)+".mp4"

    smallerIndex = 0
    vidList = []
    pbar = tqdm(initial=time, total=overlayEnd)
    while time < overlayEnd:
        if (time+INDIVIDUAL_DURATIONS >overlayEnd):
            output_vid,duration = createChatImage(path,chatfile, overlayInterval, startTime, smallerIndex, time, overlayEnd)
        else:
            output_vid,duration = createChatImage(path,chatfile, overlayInterval, startTime, smallerIndex, time, time+INDIVIDUAL_DURATIONS)
        vidList.append(output_vid)
        time+=duration
        pbar.update(duration)
        smallerIndex+=1
    pbar.close()
    for vid in vidList:
        subprocess.call("echo file "+vid + " >> "+path+"foo2.txt", shell=True)
    
    ffmpeg_command5 = ["ffmpeg", "-f", "concat", "-safe", "0", "-i", path+"foo2.txt", "-c", "copy", "-loglevel", "warning", finalOutputVid]
    subprocess.call(ffmpeg_command5)
    for vid in vidList:
        os.remove(path+vid)
    for f in listdir(path):
        if isfile(join(path, f)) and ("mp4" in f) and ("blank" in f):
            os.remove(path+f)
    return finalOutputVid, overallDuration
