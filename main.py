import random 
import yaml
import tweepy
import time
import lyricsgenius
from collections import defaultdict
from googletrans import Translator

#Getting conf keys (Private file and settings)
conf = yaml.load(open('credentials.yml'), Loader=yaml.FullLoader)

#Genius API config
genius_access_token = conf['genius']['access_token']
genius = lyricsgenius.Genius(genius_access_token)
genius.verbose = False # Turn off status messages
genius.remove_section_headers = False # Remove section headers (e.g. [Chorus]) from lyrics when searching
genius.skip_non_songs = False # Include hits thought to be non-songs (e.g. track lists)
genius.excluded_terms = ["(Remix)", "(Live)"] # Exclude songs with these words in their title

#Tweepy API config
consumer_key = conf['tweepy']['consumer']['key']
consumer_secret = conf['tweepy']['consumer']['secret']
access_token = conf['tweepy']['access_token']
access_token_secret = conf['tweepy']['access_token_secret']
auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
auth.set_access_token(access_token, access_token_secret)
api = tweepy.API(auth)

#Get the most popular song of an artist
def getPopularSong(artist):
    songs = genius.search_artist(artist, max_songs=1)
    return songs.songs[0].title

#Get the chorus of a song
def getChorus(song):
    parts = song.split("|")
    artist = parts[0] 
    title = parts[1] 
    lyric = genius.search_song(title, artist)
    chorus = ""
    if lyric != None:
        lines = lyric.lyrics.splitlines()
        found = False
        for line in lines:
            if(found):
                chorus += "\n"+line 
            if line.strip() == "[Refrão]" and not found:
                found = True
            if len(line.strip()) == 0 and found:
                found = False
                break
        if len(chorus.strip()) == 0:
            strofes = []
            Dict = defaultdict(lambda: 0)
            cur = ""
            for line in lines:
                if len(line) > 0:
                    if(line[0] != "["):
                        cur += line+"\n"
                if len(line.strip()) == 0:
                    strofes.append(cur)
                    Dict[cur.replace(" ", "").lower()] = Dict[cur.replace(" ", "").lower()] + 1
                    cur = ""
            mmax = 0
            key = -1
            for idx, val in enumerate(strofes):
                edS = val.replace(" ", "").lower()
                if(Dict[edS] > mmax):
                    mmax = Dict[edS]
                    key = idx
                
            if key >= 0:
                chorus = strofes[key]
    return chorus.strip()

#Making a Tweet
def tweetar(text):
    global canSleep
    canSleep = True
    api.update_status(text)

#Main function
def run():
    found = False
    while not found:
        global songs
        if(len(songs) == 0):
            exit()
        #Get a random song, then removes it from the list
        song = random.choice(songs)
        songs.remove(song)
        #Get the Chorus of the song, if any
        chorus = getChorus(song)
        translator = Translator()
        #Translating the Chorus to English
        translation = translator.translate(chorus).text.strip()
        #Checking if the lenght of the tweet is less than 200 and if the Chorus exists (greater than 0)
        tLen = len(translation) + len(song) 
        if tlen < 200 and len(translation) > 0:
            tweetar(translation+"\n"+song)
            found = True

#Preparing set of songs to search on the Genius API
with open("songs.txt") as f:
        songs = f.readlines()
songs = [x.strip() for x in songs]
canSleep = False
while True:
    run()
    #Making the bot sleep for 1 hour
    if canSleep:
        canSleep = False
        time.sleep(3600)
