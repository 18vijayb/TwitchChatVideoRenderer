import json
import os
from progressbar import ProgressBar
from PIL import Image
import cairo
import subprocess

#####CONSTANTS#######

COMMENT_SPACING = 10
LINE_SPACING = 5
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
        rgba=rgba.split(", ")
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
        return "#"+red+blue+green+"@",alpha
    except:
        return convert_rgb_to_hex(inp)

def convert_rgb_to_hex(rgb):
    rgb = rgb[4:-1]
    rgb=rgb.split(", ")
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

def width(filepath):
    width, height = Image.open(filepath).size
    return width

def create_video(videopath, width, height, duration, backgroundColor):
    #command = ["ffmpeg", "-t", str(duration), "-s", str(width)+"x"+str(height), "-f", "rawvideo", "-pix_fmt", "rgb24", "-r", "60", "-i", "/dev/zero", videopath]
    command = ["ffmpeg", "-t", str(duration), "-f", "lavfi", "-i", "color=c="+backgroundColor+":"+str(width)+"x"+str(height), "-pix_fmt", "rgb32", "-r", "60", videopath]
    subprocess.call(command)

def drawtext(inputFilter,startTime,endTime,font,text,yCoordinate,xCoordinate,color,outputFilter):
    return "{inputFilter}drawtext=enable='between(t,{startTime},{endTime})':fontfile='{font}':text='{text}':y={yCoordinate}+{FONT_SIZE}-max_glyph_a:x={xCoordinate}:FONT_SIZE={FONT_SIZE}:fontcolor='{color}' {outputFilter};".format(
            inputFilter=inputFilter,
            startTime=startTime,
            endTime=endTime,
            font=font,
            text=text,
            yCoordinate=yCoordinate,
            xCoordinate=xCoordinate,
            fontSize=FONT_SIZE,
            color=color,
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

def determineMessageHeight(comment, video_width,video_height, ctx):
    xCoordinate = ORIGIN_X
    totalHeight = 0
    maxHeight = 0
    username = comment["commenter"]

    ctx.select_font_face("Arial",
                cairo.FONT_SLANT_NORMAL,
                cairo.FONT_WEIGHT_BOLD)
    
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
            emote_path = fragment["emoticon"]["id"]+"."+fragment["emoticon"]["type"]
            dy = width(emote_path)
        else:
            text = fragment["text"]
            xbearing, ybearing, width, height, dx, dy = ctx.text_extents(text)
        
        #check if out of bounds
        if (xCoordinate+dx)>video_width:
            totalHeight+=maxheight+LINE_SPACING
            xCoordinate=ORIGIN_X
            maxheight=height
        else:
            maxheight = max(maxheight,height)
        xCoordinate += dx
    return totalheight


def createChatImage(path,chatfile, overlayInterval, startTime):
    BadgesFolder = path+"badges/"
    EmotesFolder = path+"emotes/"
    startTime = overlayInterval["interval"][0]
    endTime = overlayInterval["interval"][1]
    video_width = overlayInterval["chatCoordinates"]["widthScale"]*VIDEO_WIDTH
    video_height = overlayInterval["chatCoordinates"]["heightScale"]*VIDEO_HEIGHT
    duration = endTime-startTime
    textcolor = convert_rgb_to_hex(overlayInterval["textRGB"])
    backgroundColor,alpha = convert_rgba_to_hex(overlayInterval["backgroundRGBA"])
    with open(path+chatfile) as chat:
        data = json.load(chat)

    surface = cairo.ImageSurface(cairo.FORMAT_RGB24,video_width,video_height)
    ctx = cairo.Context(surface)

    videopath = "/Users/Vijay/Downloads/SampleMatches/blank.mp4"
    create_video(videopath,video_width,video_height,duration, backgroundColor)
    ffmpeg_command = ["ffmpeg", "-i", videopath, "-filter_complex", ""]
    return
    ctx.set_font_size(FONT_SIZE)
    xCoordinate = ORIGIN_X
    yCoordinate = ORIGIN_Y
    counter = 0
    fragmentCounter = 0
    lastFilter = "[0:v]"
    for comment in data["comments"]:
        if not "user_color" in comment["message"]:
            userColor = "#FFFFFF"
        else:
            userColor = comment["message"]["user_color"]
        username = comment["commenter"]
        #Change font to bold
        ctx.select_font_face("Arial",
                     cairo.FONT_SLANT_NORMAL,
                     cairo.FONT_WEIGHT_BOLD)

        #Render username
        xbearing, ybearing, width, height, dx, dy = ctx.text_extents(username)
        outputFilter = "[username{counter}]".format(counter=counter)
        ffmpeg_command[-1]+=drawtext(lastFilter,0,5,ArialBold,username,yCoordinate,xCoordinate,userColor,outputFilter)
        xCoordinate += dx
        lastFilter=outputFilter

        #Change font away from bold
        ctx.select_font_face("Arial",
                cairo.FONT_SLANT_NORMAL,
                cairo.FONT_WEIGHT_NORMAL)

        #Render colon and space after username
        xbearing, ybearing, width, height, dx, dy = ctx.text_extents(": ")
        outputFilter = "[colon{counter}]".format(counter=counter)
        ffmpeg_command[-1]+=drawtext(lastFilter,0,5,Arial,"\: ",yCoordinate,xCoordinate,textcolor,outputFilter)
        lastFilter = outputFilter
        xCoordinate += dx

        #Render fragments of message
        for fragment in comment["message"]["fragments"]:
            if "emoticon" in fragment:
                pass
            else:
                text = fragment["text"]
                xbearing, ybearing, width, height, dx, dy = ctx.text_extents(text)
                outputFilter = "[fragment{counter}]".format(counter=fragmentCounter)
                #check if out of bounds
                if (xCoordinate+dx)>video_width:
                    yCoordinate+=height+LINE_SPACING
                    xCoordinate=ORIGIN_X
                #render the word
                ffmpeg_command[-1]+=drawtext(lastFilter,0,5,Arial,text,yCoordinate,xCoordinate,"#FFFFFF",outputFilter)
                xCoordinate += dx
                lastFilter=outputFilter
                fragmentCounter+=1
        break
        # yCoordinate = height+yCoordinate+10
    ffmpeg_command[-1] = ffmpeg_command[-1][:-1]
    ffmpeg_command.append("-map")
    ffmpeg_command.append(lastFilter)
    ffmpeg_command.append(path+"output.mp4")
    #print(ffmpeg_command)
    subprocess.call(ffmpeg_command)

def overlay_chats(path, overlayfile, chatfile, startTime):
    with open(path+overlayfile) as frontend_data:
        data = json.load(frontend_data)
    for overlayInterval in data["finalOverlayIntervals"]:
        if overlayInterval["type"]=="chat":
            createChatImage(path,chatfile,overlayInterval,startTime)
            break
    

overlay_chats("./","SampleOverlayINtervals.json", "658271026.json")