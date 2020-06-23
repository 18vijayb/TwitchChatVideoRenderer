import json
import os
from progressbar import ProgressBar
from PIL import Image
import cairo
import subprocess

def width(filepath):
    width, height = Image.open(filepath).size
    return width

def create_video(videopath, width, height, duration):
    command = ["ffmpeg", "-t", str(duration), "-s", str(width)+"x"+str(height), "-f", "rawvideo", "-pix_fmt", "rgb24", "-r", "60", "-i", "/dev/zero", videopath]
    subprocess.call(command)

def drawtext(inputFilter,startTime,endTime,font,text,yCoordinate,xCoordinate,fontSize,color,outputFilter):
    return "{inputFilter}drawtext=enable='between(t,{startTime},{endTime})':fontfile='{font}':text='{text}':y={yCoordinate}+{fontSize}-max_glyph_a:x={xCoordinate}:fontsize={fontSize}:fontcolor='{color}' {outputFilter};".format(
            inputFilter=inputFilter,
            startTime=startTime,
            endTime=endTime,
            font=font,
            text=text,
            yCoordinate=yCoordinate,
            xCoordinate=xCoordinate,
            fontSize=fontSize,
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

def createChatImage(path,chatfile):
    Arial = "/Users/Vijay/Downloads/SampleMatches/Arial.ttf"
    ArialBold = "/Users/Vijay/Downloads/SampleMatches/ArialBold.ttf"
    BadgesFolder = path+"badges/"
    EmotesFolder = path+"emotes/"
    video_width = 480
    video_height = 480
    duration = 20 #seconds
    fontSize = 20
    with open(path+chatfile) as frontend_data:
        data = json.load(frontend_data)

    surface = cairo.ImageSurface(cairo.FORMAT_RGB24,video_width,video_height)
    ctx = cairo.Context(surface)

    videopath = "/Users/Vijay/Downloads/SampleMatches/blank.mp4"
    create_video(videopath,video_width,video_height,duration)
    ffmpeg_command = ["ffmpeg", "-i", videopath, "-filter_complex", ""]

    ctx.set_font_size(fontSize)
    xCoordinate = 0
    yCoordinate = 0
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
        ffmpeg_command[-1]+=drawtext(lastFilter,0,5,ArialBold,username,yCoordinate,xCoordinate,fontSize,userColor,outputFilter)
        xCoordinate += dx
        lastFilter=outputFilter

        #Change font away from bold
        ctx.select_font_face("Arial",
                cairo.FONT_SLANT_NORMAL,
                cairo.FONT_WEIGHT_NORMAL)

        #Render colon and space after username
        xbearing, ybearing, width, height, dx, dy = ctx.text_extents(": ")
        outputFilter = "[colon{counter}]".format(counter=counter)
        ffmpeg_command[-1]+=drawtext(lastFilter,0,5,Arial,"\: ",yCoordinate,xCoordinate,fontSize,"#FFFFFF",outputFilter)
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
                    yCoordinate+=height+5
                    xCoordinate=0
                #render the word
                ffmpeg_command[-1]+=drawtext(lastFilter,0,5,Arial,text,yCoordinate,xCoordinate,fontSize,"#FFFFFF",outputFilter)
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

createChatImage("/tmp/tomo/customers/vjb-reqs/1xNpYtVFRCPSwDQDAQFz1ET8cqODoON6/","653723977.json")