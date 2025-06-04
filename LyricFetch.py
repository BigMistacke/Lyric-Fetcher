from mutagen.easyid3 import EasyID3
from mutagen.id3 import ID3, USLT, ID3NoHeaderError
import lyricsgenius, re, os


genius = lyricsgenius.Genius("PUT YOUR GENIUS API TOKEN HERE")

#Remove the non-lyric preamble like number of contributors
def clean_lyrics(raw_lyrics):
    match = re.search(r'\[.*?\]', raw_lyrics)
    if match:
        return raw_lyrics[match.start():].strip()
    return raw_lyrics.strip()

#Recursively search all subfolders for mp3s
def run_fast_scandir(dir, ext):    # dir: str, ext: list
    subfolders, files = [], []

    for f in os.scandir(dir):
        if f.is_dir():
            subfolders.append(f.path)
        if f.is_file():
            if os.path.splitext(f.name)[1].lower() in ext:
                files.append(f.path)


    for dir in list(subfolders):
        sf, f = run_fast_scandir(dir, ext)
        subfolders.extend(sf)
        files.extend(f)
    return subfolders, files


def add_lyrics(folder):
    subfolders, files = run_fast_scandir(folder, [".mp3"])

    for filename in files:

        print("Working on " + filename)
        title = ""
        artist = ""
        needLyrics = True

        # Load basic metadata
        try:
            metadata = EasyID3(filename)
            title = metadata.get("title", ["Unknown Title"])[0]
            artist = metadata.get("artist", ["Unknown Artist"])[0]


            #Don't search for lyrics on an instrumental song'
            genre = metadata.get("genre", ["Unknown Genre"])

            if("Instrumental" in genre):
                needLyrics = False

        except Exception as e:
            print(f"Error reading metadata: {e}")


        # Check for existing lyrics using ID3
        try:
            tags = ID3(filename)
            lyrics_frames = tags.getall("USLT")
            if lyrics_frames:
                lyrics = lyrics_frames[0].text
                #Skip songs that already have lyrics
                needLyrics = False

        except Exception as e:
            print(f"Error reading lyrics for {title} - {artist}: {e}")


        if(needLyrics):
            try:
                try:
                    tags = ID3(filename)
                except ID3NoHeaderError:
                    tags = ID3()

                song = genius.search_song(title, artist)

                if song and song.lyrics:
                    raw_lyrics = song.lyrics
                    lyrics = clean_lyrics(raw_lyrics)

                    tags.setall("USLT", [USLT(encoding=3, lang='eng', desc='', text=lyrics)])
                    tags.save(filename)

            except Exception as e:
                print(f"Failed to update lyrics {title} - {artist}: {e}")



add_lyrics("PUT THE FOLDER WHERE YOUR MUSIC IS LOCATED HERE")




