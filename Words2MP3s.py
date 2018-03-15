# coding = utf-8
import sys
import xlwings as xw
from gtts import gTTS
from pathlib import Path

def Word2MP3(word):
    # gTTS() funciton, in a try...except.
    word.replace("'", "") # one's -> ones
    word.replace("\\","") # one\'s -> one's
    word.replace("/"," ") # one/two -> one two
    wordMP3File = Path(word+'.mp3')
    if wordMP3File.is_file():
        pass
    else:
        tts = gTTS(word,'en',False) 
        tts.save(word+'.mp3')
    print(word + " done!")

def File2Words(fileName):
    sht = xw.Book(fileName).sheets[0]
    numWords = 0
    for i in range(10000):
        if sht[i,0].value == None:
            break
        else:
            numWords += 1
    words = sht[0:numWords,0].value
    print(words)
    return set(words)

if __name__ == '__main__':
    fileName = sys.argv[1]
    words = File2Words(fileName)
    # better load all the words from all the excel, 
    # put all the words in a set to eliminate duplicates.
    # then put the set in a pickle file, so that interrupted conversion process can resume with ease.
    # then convert the elements in the set to MP3 files.
    for w in words:
        Word2MP3(w)
    print("all done!")