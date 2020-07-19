import json
import os
from progressbar import ProgressBar
from PIL import Image
import cairo
import subprocess
import math

#####CONSTANTS#######

COMMENT_SPACING = 10
LINE_SPACING = 10
ORIGIN_X = 0
ORIGIN_Y = 0
VIDEO_WIDTH = 1920
VIDEO_HEIGHT = 1080
FONT_SIZE = 20
Arial = "/Users/Vijay/Downloads/SampleMatches/Arial.ttf"
ArialBold = "/Users/Vijay/Downloads/SampleMatches/ArialBold.ttf"

#####CONSTANTS#######

def convert_rgba_to_hex(inp):
    try:
        rgba = inp[5:-1]
        rgba=rgba.split(",")
        red = str(hex(int(rgba[0])))[2:]
        if (len(red)==1):
            red="0"+red
        blue = str(hex(int(rgba[1])))[2:]
        if (len(blue)==1):
            blue="0"+blue
        green = str(hex(int(rgba[2])))[2:]
        if (len(green)==1):
            green="0"+green
        alpha = rgba[3]
        return "#"+red+blue+green,alpha
    except:
        return convert_rgb_to_hex(inp)

def convert_rgb_to_hex(rgb):
    rgb = rgb[4:-1]
    rgb=rgb.split(",")
    red = str(hex(int(rgb[0])))[2:]
    if (len(red)==1):
        red="0"+red
    blue = str(hex(int(rgb[1])))[2:]
    if (len(blue)==1):
        blue="0"+blue
    green = str(hex(int(rgb[2])))[2:]
    if (len(green)==1):
        green="0"+green
    return "#"+red+blue+green

def emote_width(filepath):
    width, height = Image.open(filepath).size
    return width

def create_video(videopath, width, height, duration, backgroundColor):
    #command = ["ffmpeg", "-t", str(duration), "-s", str(width)+"x"+str(height), "-f", "rawvideo", "-pix_fmt", "rgb24", "-r", "60", "-i", "/dev/zero", videopath]
    command = ["ffmpeg", "-t", str(duration), "-f", "lavfi", "-i", "color="+backgroundColor+":"+str(width)+"x"+str(height), "-pix_fmt", "rgb32", "-r", "30", videopath]
    subprocess.call(command)

def drawtext(inputFilter,startTime,endTime,font,text,yCoordinate,xCoordinate,color,outputFilter):
    text = text.replace("'","").replace("/","").replace(":","\:")
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
            outputFilter = outputFilter)

def drawimage(inputFilter,imageFilter,startTime,endTime,yCoordinate,xCoordinate,outputFilter,filetype):
    return "{inputFilter}{imageFilter}overlay=enable='between(t,{startTime},{endTime})':y={yCoordinate}-overlay_h:x={xCoordinate}{shortest} {outputFilter};".format(
        inputFilter=inputFilter,
        imageFilter=imageFilter,
        startTime=startTime,
        endTime=endTime,
        yCoordinate=yCoordinate,
        xCoordinate=xCoordinate,
        shortest=":shortest=1" if filetype=="gif" else "",
        outputFilter = outputFilter)

# def createChatImage(path,chatfile):
#     BadgesFolder = path+"badges/"
#     EmotesFolder = path+"emotes/"
#     with open(path+chatfile) as frontend_data:
#         data = json.load(frontend_data)

#     width, height = 10000, 10000
#     surface = skia.Surface(width, height)
#     canvas = surface.getCanvas()
    
#     data = skia.Data.MakeFromFileName('/Users/Vijay/Downloads/Emotes/5b7a13e7ed39d816f122ecb7.gif')
#     bytes(data)
#     memoryview(data)

#     image = skia.Image.DecodeToRaster(data)

#     canvas.drawBitmap(image, 100, 100, None)

#     chatImage = surface.makeImageSnapshot()
#     assert chatImage is not None

#     with open('example.png','w') as f:
#         f.write(str(chatImage.encodeToData()))

def createTimeToCommentIndexMap(comments, video_start):
    commentMap = dict()
    index = 0
    for comment in comments:
        time = math.ceil(comment["content_offset_seconds"]-video_start)
        if not time in commentMap:
            commentMap[time] = list()
        commentMap[time].append(index)
        index+=1
    return commentMap



def determineMessageHeight(comment, video_width,video_height, ctx, path):
    xCoordinate = ORIGIN_X
    totalHeight = 0
    maxheight = 0
    multiline = False
    username = comment["commenter"]

    ctx.select_font_face("Arial",
                cairo.FONT_SLANT_NORMAL,
                cairo.FONT_WEIGHT_BOLD)
    
    if "user_badges" in comment["message"]:
        for badge in comment["message"]["user_badges"]:
            badge_path = path+"badges/"+badge["_id"] + "_" + badge["version"] + ".png"
            dx = emote_width(badge_path)
            xCoordinate += dx
            xbearing, ybearing, width, height, dx, dy = ctx.text_extents(" ")
            xCoordinate += dx

    #Get username width/height
    xbearing, ybearing, width, height, dx, dy = ctx.text_extents(username)
    maxheight = max(maxheight,height)
    xCoordinate += dx

    #Change font away from bold
    ctx.select_font_face("Arial",
            cairo.FONT_SLANT_NORMAL,
            cairo.FONT_WEIGHT_NORMAL)

    #Render colon and space after username
    xbearing, ybearing, width, height, dx, dy = ctx.text_extents(": ")
    xCoordinate += dx
    maxheight = max(maxheight,height)

    #Render fragments of message
    for fragment in comment["message"]["fragments"]:
        if "emoticon" in fragment:
            if not "id" in fragment["emoticon"]:
                emote_path = path+"emotes/"+str(fragment["emoticon"]["emoticon_id"])+".png"
            else:
                emote_path = path+"emotes/"+str(fragment["emoticon"]["id"])+"."+fragment["emoticon"]["type"]
            dx = emote_width(emote_path)
        else:
            text = fragment["text"]
            xbearing, ybearing, width, height, dx, dy = ctx.text_extents(text)
        
        #check if out of bounds
        if (xCoordinate+dx)>video_width:
            totalHeight+=maxheight
            xCoordinate=ORIGIN_X
            maxheight=height
            multiline = True
        else:
            maxheight = max(maxheight,height)
        xCoordinate += dx
    return totalHeight+maxheight

def render_comments(timeInVideo,timeInChatFile,timeToComments,comments,heights,video_width, video_height,inputFilter,ctx,counter,textcolor,emotelist, duration,path):
    xCoordinate = ORIGIN_X
    yCoordinate = ORIGIN_Y + video_height
    command = ""
    index = 0
    lastFilter=inputFilter

    while True:
        while not timeInChatFile in timeToComments and timeInChatFile>0:
            timeInChatFile-=1
        index-=1
        numCommentsAtTime = len(timeToComments[timeInChatFile])
        if index+numCommentsAtTime<0:
            index=-1
            timeInChatFile -= 1
            while not timeInChatFile in timeToComments and timeInChatFile>0:
                timeInChatFile-=1
            if timeInChatFile == 0:
                return heights,lastFilter,command,counter,emotelist
        commentIndex = timeToComments[timeInChatFile][index]
        comment = comments[commentIndex]
        if not commentIndex in heights:
            heights[commentIndex]=determineMessageHeight(comment,video_width,video_height,ctx,path)
            print("HEIGHT OF",comment["message"]["body"],"IS",heights[commentIndex])
        yCoordinate -= heights[commentIndex]
        lastFilter,comment_command,counter,emotelist = render_comment(comment,timeInVideo,xCoordinate,yCoordinate,lastFilter,ctx,counter,textcolor, video_width,emotelist, duration,path)
        command+=comment_command
        yCoordinate -= COMMENT_SPACING
        if yCoordinate<ORIGIN_Y:
            return heights,lastFilter,command,counter,emotelist

def render_comment(comment,startTime,xCoordinate,yCoordinate,inputFilter,ctx,counter,textcolor, video_width, emotelist, duration,path):
    command = ""
    lastFilter=inputFilter
    if startTime+1 >= duration-1:
        endTime = startTime+2
    else:
        endTime=startTime+1
    if not "user_color" in comment["message"]:
        userColor = "#FFFFFF"
    else:
        userColor = comment["message"]["user_color"]
    username = comment["commenter"]
    #Change font to bold
    ctx.select_font_face("Arial",
                    cairo.FONT_SLANT_NORMAL,
                    cairo.FONT_WEIGHT_BOLD)

    if "user_badges" in comment["message"]:
        for badge in comment["message"]["user_badges"]:
            outputFilter = "[badge{counter}]".format(counter=counter)
            badge_path = path + "badges/"+badge["_id"] + "_" + badge["version"] + ".png"
            outputFilter = "[username{counter}]".format(counter=counter)
            if not badge_path in emotelist:
                emotelist.append(badge_path)
                imagefilter = "[{index}:v]".format(index=len(emotelist))
            else:
                imagefilter = "[{index}:v]".format(index=emotelist.index(badge_path)+1)
            dx = emote_width(badge_path)
            command+=drawimage(lastFilter,imagefilter,startTime,endTime,yCoordinate,xCoordinate,outputFilter,"png")
            xCoordinate += dx
            lastFilter = outputFilter
            xbearing, ybearing, width, height, dx, dy = ctx.text_extents(" ")
            xCoordinate += dx
            counter += 1

    #Render username
    xbearing, ybearing, width, height, dx, dy = ctx.text_extents(username)
    outputFilter = "[username{counter}]".format(counter=counter)
    command+=drawtext(lastFilter,startTime,endTime,ArialBold,username,yCoordinate,xCoordinate,userColor,outputFilter)
    xCoordinate += dx
    lastFilter=outputFilter

    #Change font away from bold
    ctx.select_font_face("Arial",
            cairo.FONT_SLANT_NORMAL,
            cairo.FONT_WEIGHT_NORMAL)

    #Render colon and space after username
    xbearing, ybearing, width, height, dx, dy = ctx.text_extents(": ")
    outputFilter = "[colon{counter}]".format(counter=counter)
    command+=drawtext(lastFilter,startTime,endTime,Arial,": ",yCoordinate,xCoordinate,textcolor,outputFilter)
    lastFilter = outputFilter
    xCoordinate += dx

    #Render fragments of message
    for fragment in comment["message"]["fragments"]:
        outputFilter = "[fragment{counter}]".format(counter=counter)
        if "emoticon" in fragment:
            if not "id" in fragment["emoticon"]:
                emote_path = path + "emotes/"+str(fragment["emoticon"]["emoticon_id"])+".png"
                filetype="png"
            else:
                emote_path = path + "emotes/"+str(fragment["emoticon"]["id"])+"."+fragment["emoticon"]["type"]
                filetype=fragment["emoticon"]["type"]
            if not emote_path in emotelist:
                emotelist.append(emote_path)
                imagefilter = "[{index}:v]".format(index=len(emotelist))
            else:
                imagefilter = "[{index}:v]".format(index=emotelist.index(emote_path)+1)
            dx = emote_width(emote_path)
            if (xCoordinate+dx)>video_width:
                yCoordinate+=height+LINE_SPACING
                xCoordinate=ORIGIN_X
            command+=drawimage(lastFilter,imagefilter,startTime,endTime,yCoordinate,xCoordinate,outputFilter,filetype)
        else:
            text = fragment["text"]
            xbearing, ybearing, width, height, dx, dy = ctx.text_extents(text)
            #check if out of bounds
            if (xCoordinate+dx)>video_width:
                yCoordinate+=height+LINE_SPACING
                xCoordinate=ORIGIN_X
            #render the word
            command+=drawtext(lastFilter,startTime,endTime,Arial,text,yCoordinate,xCoordinate,textcolor,outputFilter)
        xCoordinate += dx
        lastFilter=outputFilter
        counter+=1
    return lastFilter,command,counter, emotelist

def createChatImage(path,chatfile, overlayInterval, video_start, index):
    BadgesFolder = path+"badges/"
    EmotesFolder = path+"emotes/"
    startTime = overlayInterval["interval"][0]
    endTime = overlayInterval["interval"][1]
    video_width = int(overlayInterval["chatCoordinates"]["widthScale"]*VIDEO_WIDTH)
    video_height = int(overlayInterval["chatCoordinates"]["heightScale"]*VIDEO_HEIGHT)
    duration = endTime-startTime
    textcolor = convert_rgb_to_hex(overlayInterval["textRGB"])
    backgroundColor,alpha = convert_rgba_to_hex(overlayInterval["backgroundRGBA"])
    with open(path+chatfile) as chat:
        data = json.load(chat)
    timesToComments = createTimeToCommentIndexMap(data["comments"],video_start)
    surface = cairo.ImageSurface(cairo.FORMAT_RGB24,1000,1000)
    ctx = cairo.Context(surface)
    input_video = path+"blank"+str(index)+".mp4"
    output_video = path+"chat"+str(index)+".mp4"
    if os.path.exists(input_video):
        os.remove(input_video)
    if os.path.exists(output_video):
        os.remove(output_video)
    create_video(input_video,video_width,video_height,duration, backgroundColor)
    ctx.set_font_size(FONT_SIZE)
    xCoordinate = ORIGIN_X
    yCoordinate = ORIGIN_Y
    counter = 0
    lastFilter = "[0:v]"
    heights = dict()
    script = ""
    emotelist = list()
    for time in range(0,math.floor(duration)):
        timeInChatFile = time + math.ceil(startTime)
        heights,outputFilter,current_command,counter,emotelist = render_comments(time,timeInChatFile,timesToComments,data["comments"],heights,video_width, video_height,lastFilter,ctx,counter,textcolor,emotelist,duration,path)
        script += current_command
        lastFilter = outputFilter
    script = script[:-1]
    with open(path+"script.txt","w") as script_file:
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
    ffmpeg_command.extend(["-filter_complex_script", path+"script.txt","-map",lastFilter,output_video])
    #print(ffmpeg_command)
    subprocess.call(ffmpeg_command)
    return output_video,duration

def overlayChats(path, overlayfile, chatfile, startTime, input_video):
    with open(path+overlayfile) as frontend_data:
        data = json.load(frontend_data)
    index = 1
    ffmpeg_command = ["ffmpeg", "-i", input_video]
    script = ""
    lastFilter = "[0:v]"
    for overlayInterval in data["finalOverlayIntervals"]:
        if overlayInterval["type"]=="chat":
            chat_video,duration = createChatImage(path,chatfile,overlayInterval,startTime, index)
            ffmpeg_command.extend(["-i", chat_video])
            chatStart = overlayInterval["interval"][0]
            chatX = overlayInterval["chatCoordinates"]["xScale"]*VIDEO_WIDTH
            chatY = overlayInterval["chatCoordinates"]["yScale"]*VIDEO_HEIGHT
            outputFilter = "[overlayedVideo{index}]".format(index=index)
            script+="[{index}:v]setpts=PTS+{chatStart}/TB[overlay{index}];{lastFilter}[overlay{index}]overlay=enable=gte(t\,{duration}):y={chatY}:x={chatX}:eof_action=pass,format=yuv420p{outputFilter};".format(
                index=index,
                lastFilter=lastFilter,
                chatStart=chatStart,
                duration=duration,
                chatX=chatX,
                chatY=chatY,
                outputFilter=outputFilter
            )
            lastFilter=outputFilter
            index+=1
    script=script[:-1]
    ffmpeg_command.extend(["-filter_complex", script, "-map", lastFilter, "-map", "0:a?", "-c:v", "libx264", "-crf", "27", "-c:a", "copy", path+"new.mp4"])
    print(ffmpeg_command)
    subprocess.call(ffmpeg_command)
    

overlayChats("./","SampleOverlayIntervals.json", "658271026.json", 2700, "/Users/Vijay/Downloads/SampleMatches/apextest.mp4")