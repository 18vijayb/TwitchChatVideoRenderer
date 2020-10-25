import json
import requests
from tqdm import tqdm
import os
import random
from PIL import Image
from os import listdir
from os.path import isfile, join
import subprocess

from ChatSettings import EMOTE_HEIGHT_SCALE, BADGE_HEIGHT_SCALE
EMOTE_HEIGHT_SCALE = 42 #In pixels
BADGE_HEIGHT_SCALE = 28 #In pixels

def downloadToFolder(url,folder,emoteName,fileType, isBadge):
    imagepath = folder+emoteName+"."+fileType
    initimagepath = folder+emoteName+"init."+fileType
    with open(initimagepath, 'wb') as handle:
        response = requests.get(url, stream=True)

        if not response.ok:
            print ("An error occurred with the emote",emoteName,"with url",url)
        for block in response.iter_content(1024):
            if not block:
                break
            handle.write(block)
    width, height = Image.open(initimagepath).size
    if (isBadge):
        multiplier = BADGE_HEIGHT_SCALE/height
    else:
        multiplier = EMOTE_HEIGHT_SCALE/height
    width = int(multiplier*width)
    height = int(multiplier*height)
    if (fileType=="gif"):
        resize_gif_command = ["ffmpeg", "-hide_banner", "-v", "warning", "-loglevel", "quiet", "-i", initimagepath, "-filter_complex", "[0:v] scale="+str(height)+":-1:flags=lanczos,split [a][b]; [a] palettegen=reserve_transparent=on:transparency_color=ffffff [p]; [b][p] paletteuse", imagepath]
        subprocess.call(resize_gif_command)
    else:
        image = Image.open(initimagepath)
        new_image = image.resize((width, height))
        new_image.save(imagepath)


def getBTTVEmoteDict(channelName):
    bttvEmotes = requests.get("https://api.betterttv.net/2/channels/{channel}".format(channel=channelName)).json()
    bttvGlobalEmotes = requests.get("https://api.betterttv.net/2/emotes").json()
    emoteDict = dict()
    if not "emotes" in bttvGlobalEmotes:
        return emoteDict
    for emote in bttvGlobalEmotes["emotes"]:
        emoteDict[emote["code"]] = dict()
        emoteDict[emote["code"]]["url"]="https://cdn.betterttv.net/emote/{id}/2x".format(id=emote["id"])
        emoteDict[emote["code"]]["type"]=emote["imageType"]
        emoteDict[emote["code"]]["id"]=emote["id"]
    if not "emotes" in bttvEmotes:
        return emoteDict
    for emote in bttvEmotes["emotes"]:
        emoteDict[emote["code"]] = dict()
        emoteDict[emote["code"]]["url"]="https://cdn.betterttv.net/emote/{id}/2x".format(id=emote["id"])
        emoteDict[emote["code"]]["type"]=emote["imageType"]
        emoteDict[emote["code"]]["id"]=emote["id"]
    return emoteDict

def getFFZEmoteDict(channelName):
    ffzEmotes = requests.get("http://api.frankerfacez.com/v1/room/{channel}".format(channel=channelName)).json()
    emoteDict = dict()
    if not "sets" in ffzEmotes:
        return emoteDict
    for emoteSet in ffzEmotes["sets"]:
        for emote in ffzEmotes["sets"][emoteSet]["emoticons"]:
            emoteDict[emote["name"]]=dict()
            # if "3" in emote["urls"]:
            #     url="https:"+emote["urls"]["3"]
            if "2" in emote["urls"]:
                url="https:"+emote["urls"]["2"]
            else:
                url="https:"+emote["urls"]["1"]
            emoteDict[emote["name"]]["url"] = url
            emoteDict[emote["name"]]["id"] = emote["id"]
            if ".png" in url.lower():
                emoteDict[emote["name"]]["type"]="png"
            else:
                emoteDict[emote["name"]]["type"]="gif"
    return emoteDict 

def refineComments(path,file, chattxtfile):
    EmotesFolder = path+"/emotes/"
    BadgesFolder = path+"/badges/"
    os.mkdir(EmotesFolder)
    os.mkdir(BadgesFolder)
    with open(file) as chatjson:
        data = json.load(chatjson)
    with open(chattxtfile) as txtfile:
        txt = txtfile.read()
    txtLower = txt.lower()
    channelID = data["video"]["user_id"]
    channelName = data["video"]["user_name"].lower()
    channelBadges = requests.get("https://badges.twitch.tv/v1/badges/channels/{channel_id}/display?language=en".format(channel_id=channelID)).json()
    globalBadges = requests.get("https://badges.twitch.tv/v1/badges/global/display").json()
    bttvEmotes = getBTTVEmoteDict(channelName)
    ffzEmotes = getFFZEmoteDict(channelName)
    userDictionary = dict()
    emoteDictionary = dict()
    emoteDictionary["twitch_emotes"] = dict()
    emoteDictionary["bttv_emotes"] = dict()
    emoteDictionary["ffz_emotes"] = dict()
    downloaded = set()
    if len(data["comments"]):
        print("There is no chat in the specified duration! Can't render video :(")
        return 500
    for comment in tqdm(data["comments"]):
        comment.pop("_id")
        comment.pop("channel_id", None)
        comment.pop("content_id", None)
        comment.pop("content_type", None)
        comment.pop("created_at", None)
        comment.pop("source", None)
        comment.pop("state", None)
        comment.pop("updated_at", None)
        comment["commenter"] = comment["commenter"]["name"]
        commenter = comment["commenter"]
        userStartIndex = txtLower.find(commenter)
        if (userStartIndex != -1):
            userEndIndex = len(commenter) + userStartIndex
            comment["commenter"] = txt[userStartIndex:userEndIndex]
        userDictionary[commenter] = dict()
        if not "user_color" in comment["message"]:
            colors = ["#FF0000","#39FF14","#00FFFF","#FF6700","#FF1493","#7E481C","#FFCC22","#006994","#FFCC00"]
            color = random.choice(colors)
            userDictionary[commenter]["color"] = color
            comment["message"]["user_color"] = color
        else:
            userDictionary[commenter]["color"] = comment["message"]["user_color"]

        comment["message"].pop("is_action", None)
        comment["message"].pop("user_notice_params", None)
        message = comment["message"]
        if ("user_badges" in message):
            badgeList = list()
            for badge in message["user_badges"]:
                badgeName = "{id}_{version}".format(id=badge["_id"],version=badge["version"])
                if badge["_id"] in channelBadges["badge_sets"] and badge["version"] in channelBadges["badge_sets"][badge["_id"]]["versions"]:
                    badgeURL = channelBadges["badge_sets"][badge["_id"]]["versions"][badge["version"]]["image_url_2x"]
                    #badge["badge_image"] = badgeURL
                else:
                    badgeURL = globalBadges["badge_sets"][badge["_id"]]["versions"][badge["version"]]["image_url_2x"]
                    #badge["badge_image"] = badgeURL
                badgeList.append(badgeURL)
                if not badgeName in downloaded:
                    downloadToFolder(badgeURL,BadgesFolder,badgeName,"png",True)
                    downloaded.add(badgeName)
            userDictionary[commenter]["badges"] = badgeList
        newFragmentList = []
        for fragment in message["fragments"]:
            if "emoticon" in fragment:
                emoteURL = "https://static-cdn.jtvnw.net/emoticons/v1/{emoticon_id}/2.0".format(emoticon_id=fragment["emoticon"]["emoticon_id"])
                #fragment["emoticon"]["img"] = emoteURL
                emoteId = fragment["emoticon"]["emoticon_id"]
                emoteName = fragment["text"]
                if not emoteId in downloaded:
                    downloadToFolder(emoteURL,EmotesFolder,emoteId,"png", False)
                    downloaded.add(emoteId)
                emoteDictionary["twitch_emotes"][emoteName] = emoteURL
                newFragmentList.append(fragment)
            else:
                words = fragment["text"].split()
                for word in words:
                    if word in bttvEmotes:
                        emoticon = dict()
                        emoticon["emoticon"] = dict()
                        emoticon["text"] = word
                        emoticon["emoticon"]["id"]=bttvEmotes[word]["id"]
                        #emoticon["emoticon"]["img"]=bttvEmotes[word]["url"]
                        emoticon["emoticon"]["type"]=bttvEmotes[word]["type"]
                        emoteDictionary["bttv_emotes"][word]=bttvEmotes[word]["url"]
                        newFragmentList.append(emoticon)
                        if not bttvEmotes[word]["id"] in downloaded:
                            downloadToFolder(bttvEmotes[word]["url"],EmotesFolder,str(bttvEmotes[word]["id"]),bttvEmotes[word]["type"], False)
                            downloaded.add(bttvEmotes[word]["id"])
                    elif word in ffzEmotes:
                        emoticon = dict()
                        emoticon["emoticon"] = dict()
                        emoticon["text"] = word
                        emoticon["emoticon"]["id"]=ffzEmotes[word]["id"]
                        #emoticon["emoticon"]["img"]=ffzEmotes[word]["url"]
                        emoticon["emoticon"]["type"]=ffzEmotes[word]["type"]
                        emoteDictionary["ffz_emotes"][word]=ffzEmotes[word]["url"]
                        newFragmentList.append(emoticon)
                        if not ffzEmotes[word]["id"] in downloaded:
                            downloadToFolder(ffzEmotes[word]["url"],EmotesFolder,str(ffzEmotes[word]["id"]),ffzEmotes[word]["type"], False)
                            downloaded.add(ffzEmotes[word]["id"])
                    else:
                        text = dict()
                        text["text"] = word
                        newFragmentList.append(text)
                    text = dict()
                    text["text"] = " "
                    newFragmentList.append(text)
        if newFragmentList[-1]["text"]==" ":
            message["fragments"]=newFragmentList[:-1]
        else:
            message["fragments"]=newFragmentList
    FrontEndInformation = dict()
    FrontEndInformation["Emoticons"] = emoteDictionary
    FrontEndInformation["UserInfo"] = userDictionary
    with open(path+"ChatDictionary.json", 'w') as outfile:
        json.dump(FrontEndInformation,outfile)
    with open(file, 'w') as outfile:
        json.dump(data, outfile)
    for f in listdir(EmotesFolder):
        if (isfile(join(EmotesFolder, f)) and ("init" in f)):
            os.remove(EmotesFolder+f)
    
    for f in listdir(BadgesFolder):
        if (isfile(join(BadgesFolder, f)) and ("init" in f)):
            os.remove(BadgesFolder+f)

    return 200
