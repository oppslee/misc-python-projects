# coding = utf-8
import sys
import urllib.request
import urllib.parse
from urllib.error import URLError
from urllib.error import HTTPError
from bs4 import BeautifulSoup
from gtts import gTTS
import json
import xlwings as xw
from functools import reduce
from pathlib import Path
from string import Template


def File2Words(fileName):
    sht = xw.Book(fileName).sheets[0]
    words = list(filter(lambda x: x != None, sht[:,0].value))
    print("Number of words: {} Words are as followings: {}".format(len(words),words))
    return words

def GetResponseFromBingDict(word):
    '''
    '''
    word.replace(" ","+")
    # url = "http://cn.bing.com/dict/search?q="+word
    param = urllib.parse.urlencode({'q':word})
    url = "http://cn.bing.com/dict/search?{}".format(param)
    req = urllib.request.Request(url)
    try:
        response = urllib.request.urlopen(req)
        html = response.read().decode('utf-8')
        response.close()
        soup = BeautifulSoup(html,'html.parser')
        return soup
    except HTTPError as err:
        if hasattr(err,'reason'):
            print('We fail to reach a server.')
            print('Reason: ',err.reason)
            response.close()
            return None
        elif hasattr(err,'code'):
            print('The server could not fulfill the request.')
            print('Error code: ',err.code)
            response.close()
            return None
    except URLError as err:
        if hasattr(err,'reason'):
            print('We fail to reach a server.')
            print('Reason: ',err.reason)
            response.close()
            return None

def HasPronounciation(soup):
    if soup.find('div',class_='hd_prUS') != None and soup.find('div',class_='hd_pr') != None:
        return True
    else:
        return False

def GetPronounciation(soup):
    '''
    selector: body > div.contentPadding > div > div > div.lf_area > div.qdef > div.hd_area > div.hd_tf_lh > div > div.hd_prUS
    XPath: /html/body/div[1]/div/div/div[1]/div[1]/div[1]/div[2]/div/div[1]
    element: <div class="hd_prUS">美&nbsp;['pɑrs(ə)l] </div>
    selector: body > div.contentPadding > div > div > div.lf_area > div.qdef > div.hd_area > div.hd_tf_lh > div > div.hd_pr
    XPath: /html/body/div[1]/div/div/div[1]/div[1]/div[1]/div[2]/div/div[3]
    element: <div class="hd_pr">英&nbsp;['pɑː(r)s(ə)l] </div>
    '''
    if HasPronounciation(soup):
        prus = soup.find('div',class_='hd_prUS')
        pruk = soup.find('div',class_='hd_pr')
        # print("{} {}".format(prus.string,prbr.string))
        return {"prus":prus.string,"pruk":pruk.string}
    else:
        return {"prus":"","pruk":""}

def HasAuthDefinition(soup):
    if soup.find('div', class_='auth_area') != None:
        return True
    else:
        return False

def GetAuthDefinition(soup):
    '''
    权威英汉双解: 词性,中文释义, 英文定义, 例句
    first find <div class="auth_area">
    
    # complicated dict type for every a word's lemma
    example: {"enemp":None,"cnemp":None} # example sentence within certain lemma
    lemma: {"pos":None,"endef":None,"cndef":None,"examples":[]} # a lemma of a word
    authDef: {"lemmas":[]} # authDef = {"lemmas": [lemma, lemma, lemma ....]}
    '''

    authDef = {"lemmas":[]}
    if HasAuthDefinition(soup):
        authArea = soup.find('div', class_='auth_area')
        allDefSeg = authArea.find_all('div',class_='each_seg')
        for defSeg in allDefSeg:
            pos = defSeg.find('div',class_='pos')
            allDefs = defSeg.find_all('div',class_='se_lis')
            for eachDef in allDefs:
                lemmaIdx = allDefs.index(eachDef)
                defOrder = eachDef.find('div',class_='se_d')
                compDef = eachDef.find('span',class_='comple')
                enDef = eachDef.find('span',class_='val')
                cnDef = eachDef.find('span',class_='bil')
                if compDef != None: # a lemma has composite definition
                    # print("{} [{}] {} {}".format(defOrder.string,compDef.string,enDef.string,cnDef.string))
                    authDef["lemmas"].append({"pos":pos.string,"endef":compDef.string + " " + enDef.string,"cndef":cnDef.string,"examples":[]})
                else:
                    # print("{} {} {}".format(defOrder.string,enDef.string,cnDef.string))
                    authDef["lemmas"].append({"pos":pos.string,"endef":enDef.string,"cndef":cnDef.string,"examples":[]})
                allExSegs = eachDef.find_next_sibling('div',class_='li_exs')
                if allExSegs != None: # a lemma has example sentences
                    for eachExSeg in allExSegs:
                        allSnts = eachExSeg.find_all('div',class_='li_ex')
                        for eachSnt in allSnts:
                            enSnt = eachSnt.find('div',class_='val_ex')
                            cnSnt = eachSnt.find('div',class_='bil_ex')
                            # print("[#.] {} {}".format(enSnt.string,cnSnt.string))
                            authDef["lemmas"][lemmaIdx]["examples"].append({"enemp":enSnt.string,"cnemp":cnSnt.string})
                else:
                    authDef["lemmas"][lemmaIdx]["examples"] = []
        return authDef
    else:
        return {"lemmas":[]}

def HasSimpleDefinition(soup):
    headAreaSoup = soup.find('div',class_='hd_area')
    if headAreaSoup == None:
        return False
    else:
        simpleDefSoup = headAreaSoup.find_next('span',class_='def')
        if simpleDefSoup != None:
            return True
        else:
            return False

def GetSimpleDefinition(soup):
    '''
    获得简明英汉释义
    first find <div class="hd_area"> header area
    find next <ul> area
    '''
    # simpleDefsDict = { "simpledefs": ["simpleDefString","simpleDefString",.... ] }
    simpleDefsDict = {"simpledefs":[]}
    if HasSimpleDefinition(soup):
        headAreaSoup = soup.find('div',class_='hd_area')
        simpleAreaSoup = headAreaSoup.find_next('ul')
        simpleDefsSoup = simpleAreaSoup.find_all('li')
        for sd in simpleDefsSoup[:-1]: # eliminate [网络] definition
            if sd.strings != None:
                simpleDefString = reduce(lambda x,y: x+ ' ' +y,sd.strings)
                # print(simpleDefString)
                simpleDefsDict["simpledefs"].append(simpleDefString)
        return simpleDefsDict
    else:
        return {"simpledefs":[]}

def HasSyononyms(soup):
    if soup.find('div',id='synoid') != None:
        return True
    else:
        return False

def GetSynonyms(soup):
    '''
    {"synonyms": [ {"pos":None, "synos":[""]},{"pos":None,} ]}
    '''
    synonymEntry = {"synonyms":[]}
    if HasSyononyms(soup):
        synoSoups = soup.find('div',id='synoid').find_all('div',class_='df_div2') # a list
        for synoSoup in synoSoups:
            posIdx = synoSoups.index(synoSoup)
            pos = synoSoup.find('div',class_='de_title1').string
            synonymEntry["synonyms"].append({"pos":pos.string,"synos":[]})
            synos = synoSoup.find_all('span',class_='p1-4')
            for s in synos:
                synonymEntry["synonyms"][posIdx]["synos"].append(s.string)
                # print(s.string)
        return synonymEntry
    else:
        return {"synonyms":[]}

def HasAntonyms(soup):
    if soup.find('div',id='antoid') != None:
        return True
    else:
        return False

def GetAntonyms(soup):
    '''
    {"antonyms": [ {"pos":"v.", "antos":[a1,a2,a3...]},{"pos":"n.","antos":[a1,a2,...]} ]}
    '''
    antonymEntry = {"antonyms":[]}
    if HasAntonyms(soup):
        antoSoups = soup.find('div',id='antoid').find_all('div',class_='df_div2') # a list
        for antoSoup in antoSoups:
            posIdx = antoSoups.index(antoSoup)
            pos = antoSoup.find('div',class_='de_title1').string
            antonymEntry["antonyms"].append({"pos":pos.string,"antos":[]})
            antos = antoSoup.find_all('span',class_='p1-4')
            for a in antos:
                antonymEntry["antonyms"][posIdx]["antos"].append(a.string)
                # print(a.string)
        return antonymEntry
    else:
        return {"antonyms":[]}

def HasCollocations(soup):
    if soup.find('div',id='colid') != None:
        return True
    else:
        return False

def GetCollocations(soup):
    '''
    {"collocations": [ {"pos":"v.+n.", "colls":[c1,c2,c3...]},{"pos":"n.+adj.","colls":[c1,c2,...]} ]}
    c1, c2, c3...: string, like "excert influence"
    '''
    collocationEntry = {"collocations":[]}
    if HasCollocations(soup):
        collSoups = soup.find('div',id='colid').find_all('div',class_='df_div2') # a list
        for collSoup in collSoups:
            posIdx = collSoups.index(collSoup)
            pos = collSoup.find('div',class_='de_title2').string
            collocationEntry["collocations"].append({"pos":pos.string,"colls":[]})
            colls = collSoup.find_all('span',class_='p1-4')
            for c in colls:
                collocationEntry["collocations"][posIdx]["colls"].append(c.string)
                # print(c.string)
        return collocationEntry
    else:
        return {"collocations":[]}   

def RetrunEmptyEntry(word):
    '''
    simpleDefs = {"simpledefs":["def1","def2",....]}
    example = {"enemp":None,"cnemp":None} # example sentence
    lemma = {"pos":None,"endef":None,"cndef":None,"examples":[example, example,....]} # a lemma of a word
    authDef = {"lemmas":[lemma, lemma, lemma, .....]}
    '''
    wordEntry = {"word":word,"prus":None,"prbr":None,"lemmas":[],"simpledefs":[]} # a word entry, with word/pronounciation/lemmas/examples
    return wordEntry

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

def BuildCompleteWordEntry(word):
    '''
    synonyms: {"synonyms":[{"pos": "v.","synos":[s1,s2,s3...]},{"pos":"n.","synos":[s1,s2,...]}]}
    antonyms: {"antonyms":[{"pos": "v.","synos":[a1,a2,a3...]},{"pos":"n.","antos":[a1,a2,...]}]}
    collocations: {"collocations":[{"pos":"v.+adj.","colls":[c1,c2,c3,...],{"pos":"v.+adj.","colls":[c1,c2,...]}]}
    simpleDefs: {"simpledefs":["def1","def2",....]}
    example: {"enemp":None,"cnemp":None} # example sentence
    lemma: {"pos":None,"endef":None,"cndef":None,"examples":[example, example,....]} # a lemma of a word
    authDef: {"lemmas":[lemma, lemma, lemma, .....]}
    wordEntry: {"word":None,"prus":None,"prbr":None,"lemmas":[],"simpledefs":[],"synonyms":[],"antonyms":[],"collocations":[]} # a word entry, with word/pronounciation/lemmas/examples
    '''
    wordEntry = {}
    wordEntry.update({"word":word})
    soup = GetResponseFromBingDict(word)
    if soup == None: # No response from dict.bing.com
        return wordEntry.update({"prus":None,"prbr":None,"lemmas":[],"simpledefs":[],"synonyms":[],"antonyms":[],"collocations":[]})
    else:
        wordEntry.update(GetPronounciation(soup))
        wordEntry.update(GetAuthDefinition(soup))
        wordEntry.update(GetSimpleDefinition(soup))
        wordEntry.update(GetSynonyms(soup))
        wordEntry.update(GetAntonyms(soup))
        wordEntry.update(GetCollocations(soup))
        print(wordEntry)
        return wordEntry

def BuildWordEntries(wordsFileName):
    words = File2Words(wordsFileName)
    wordEntries = list(map(BuildCompleteWordEntry,words[0:10]))
    return wordEntries

def DumpWordEntries2JsonFile(wordEntries,jsonFileName):
    '''
    words = [wordEntry, wordEntry,.....]
    dump the words into a json file
    '''
    fp = open(jsonFileName,'w')
    json.dump(wordEntries,fp)
    fp.close()

def example2Markdown(example):
    '''
    example: {"enemp":"some example","cnemp":"some chinese example"}
    '''
    return "\n>>【例】{enemp} {cnemp}".format(enemp=example["enemp"],cnemp=example["cnemp"])

def examples2Markdown(examples):
    '''
    {"examples":[exampl1,example2]}
    '''
    if len(examples) != 0:
        return reduce(lambda x,y: x+y,list(map(example2Markdown,examples)))
    else:
        return ""

def lemma2Markdown(lemma):
    '''
    arg: lemma: {"pos":"v.","endef":"some def","cndef":"some def","examples":[example, example,....]} 
    return: latexSeg, a string
    '''
    if len(lemma["examples"]) != 0:
        return "{pos} {endef} {cndef} {examples}".format(pos=lemma["pos"],endef=lemma["endef"],cndef=lemma["cndef"],examples=examples2Markdown(lemma["examples"]))
    else:
        return "{pos} {endef} {cndef}".format(pos=lemma["pos"],endef=lemma["endef"],cndef=lemma["cndef"])

def lemmas2Markdown(lemmas):
    '''
    authDef: {"lemmas":[lemma,lemma, lemma,...]} 
    '''
    if len(lemmas) != 0:
        lemmasMd = ""
        for lemma in lemmas:
            lemmasMd += "\n> {}. ".format(lemmas.index(lemma)+1) + lemma2Markdown(lemma) + " "
        return lemmasMd
    else:
        return ""

def simpleDefs2Markdown(simpleDefs):
    '''
    {"simpledefs":["def1","def2",....]}
    '''
    if len(simpleDefs) != 0:
        simpleDefsMd = ""
        for simpleDef in simpleDefs:
            simpleDefsMd += "\n> {}. {}\n".format(simpleDefs.index(simpleDef)+1,simpleDef)
        return simpleDefsMd
    else:
        return ""

def synonym2Markdown(synonym):
    '''
    {"pos": "v.","synos":[s1,s2,s3...]}
    '''
    return "\n> {pos} {synos}".format(pos=synonym["pos"],synos=reduce(lambda x,y:x+", "+y,synonym["synos"]))

def synonyms2Markdown(synonyms):
    '''
    synonyms: {"synonyms":[{"pos": "v.","synos":[s1,s2,s3...]},{"pos":"n.","synos":[s1,s2,...]}]}
    '''
    if len(synonyms) != 0:
        return "{}".format(reduce(lambda x,y:x+y,list(map(synonym2Markdown,synonyms))))
    else:
        return ""

def antonym2Markdown(antonym):
    '''
    {"pos": "v.","antos":[a1,a2,a3...]
    '''
    return "\n> {pos} {antos}".format(pos=antonym["pos"],antos=reduce(lambda x,y:x+", "+y,antonym["antos"]))

def antonyms2Markdown(antonyms):
    '''
    {"antonyms":[{"pos": "v.","synos":[a1,a2,a3...]},{"pos":"n.","antos":[a1,a2,...]}]}
    '''
    if len(antonyms) != 0:
        return "{}".format(reduce(lambda x,y:x+" "+y, list(map(antonym2Markdown,antonyms))))
    else:
        return ""

def collocation2Markdown(collocation):
    '''
    collocation:: {"pos":"v.+adj.","colls":[c1,c2,c3,...]}
    '''
    return "\n>{pos} {colls}".format(pos=collocation["pos"],colls=reduce(lambda x,y:x+", "+y,collocation["colls"]))

def collocations2Markdown(collocations):
    '''
    {"collocations":[collocation1, collocation2]}
    '''
    if len(collocations) != 0:
        return "{}".format(reduce(lambda x,y:x+y,list(map(collocation2Markdown,collocations))))
    else:
        return ""

def WordEntry2Markdown(wordEntry):
    '''
    synonyms: {"synonyms":[{"pos": "v.","synos":[s1,s2,s3...]},{"pos":"n.","synos":[s1,s2,...]}]}
    antonyms: {"antonyms":[{"pos": "v.","synos":[a1,a2,a3...]},{"pos":"n.","antos":[a1,a2,...]}]}
    collocations: {"collocations":[{"pos":"v.+adj.","colls":[c1,c2,c3,...]},{"pos":"v.+adj.","colls":[c1,c2,...]}]}
    simpleDefs: {"simpledefs":["def1","def2",....]}
    example: {"enemp":"something","cnemp":"something"} # example sentence
    lemma: {"pos":"","endef":"","cndef":None,"examples":[example, example,....]} # a lemma of a word
    authDef: {"lemmas":[lemma, lemma, lemma, .....]}
    wordEntry: {"word":"something","prus":"something","prbr":"something","lemmas":[],"simpledefs":[],"synonyms":[],"antonyms":[],"collocations":[]} # a word entry, with word/pronounciation/lemmas/examples
    '''
    word = wordEntry["word"] # string
    prus = wordEntry["prus"] # string
    pruk = wordEntry["pruk"] # string
    lemmas = wordEntry["lemmas"] # list
    simpleDefs = wordEntry["simpledefs"] # list
    synonyms = wordEntry["synonyms"] # list
    antonyms = wordEntry["antonyms"] # list
    collocations = wordEntry["collocations"] # list
    # consider each field exist or not, there are 2^7 cases. Damn!!!
    wholeDefMd = "**{word}**".format(word=word)
    if prus != "" and pruk != "":
        wholeDefMd += " {ipa1}, {ipa2}".format(ipa1=prus, ipa2=pruk)
    elif prus != "" and pruk == "":
        wholeDefMd += " {ipa1}".format(ipa1=prus)
    elif prus == "" and pruk != "":
        wholeDefMd += " {ipa2}".format(ipa2=prus)
    else:
        pass
    
    if lemmas != [] and simpleDefs != []:
        wholeDefMd += "\n\n【定义】: {lemmas}".format(lemmas=lemmas2Markdown(lemmas))
    elif lemmas == [] and simpleDefs !=[]:
        wholeDefMd += "\n\n【简明】: {simpleDefs}".format(simpleDefs=simpleDefs2Markdown(simpleDefs))
    else:
        pass

    if collocations != []:
        wholeDefMd += "\n\n【搭配】: {collocations}".format(collocations=collocations2Markdown(collocations))
    else:
        pass
    
    if synonyms != []:
        wholeDefMd += "\n\n【同】: {synonyms}".format(synonyms=synonyms2Markdown(synonyms))
    else:
        pass
    
    if antonyms != []:
        wholeDefMd += "\n\n【反】: {antonyms}".format(antonyms=antonyms2Markdown(antonyms))
    else:
        pass
    # print(wholeDefMd)
    return wholeDefMd+"\n--------------------------------\n"

def BuildMarkdownVocabBook(wordsFile,markdownFile):
    words = File2Words(wordsFile)
    jsonWordEntries = list(map(BuildCompleteWordEntry,words))
    MdWordEntries = list(map(WordEntry2Markdown,jsonWordEntries))
    MdWordEntries = ["`{}`. {}".format(MdWordEntries.index(entry)+1,entry) for entry in MdWordEntries]
    fp = open(markdownFile,mode="w",encoding="utf8")
    for entry in MdWordEntries:
        print(entry)
        fp.write(entry)
    fp.close()

def AddPr2Excel(excelFile):
    sht = xw.Book(excelFile).sheets[0]
    words = list(filter(lambda x: x != None, sht[:,0].value))
    wordsNum = len(words)
    for i in range(wordsNum):
        soup = GetResponseFromBingDict(words[i])
        if soup != None:
            if HasPronounciation(soup):
                prus,prbr = GetPronounciation(soup)
                sht[i,1].value = prus + prbr 

if __name__ == "__main__":
    # wordEntries = BuildWordEntries(sys.argv[1])
    # DumpWordEntries2JsonFile(wordEntries,sys.argv[2])
    # AddPr2Excel(sys.argv[1])
    
    # sys.argv[1], excel file contains words
    # sys.argv[2], markdown file
    BuildMarkdownVocabBook(sys.argv[1],sys.argv[2])