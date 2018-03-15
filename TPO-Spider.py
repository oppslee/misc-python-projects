# coding = utf-8
import sys
import urllib.request
import urllib.parse
from urllib.error import URLError
from urllib.error import HTTPError
from bs4 import BeautifulSoup
import json
from functools import reduce
from pathlib import Path
import time

def GetArticleSoup(articleId,questionId):
    '''
    articleId : int
    questionId : int
    request format: https://top.zhan.com/toefl/read/practice.html?workflow_id=0&article_id=53&scenario=13&index=0
    param workflow_id, don't touch it.
    article_id: specify which article
    scenario_id: don't touch it.
    index: specify which question, usually ranging from 0 to 13, sometime from 0 to 12.
    return: soup, or None
    '''
    workFlowId = 0
    workflowParam = urllib.parse.urlencode({"workflow_id":workFlowId}) 
    articleParam = urllib.parse.urlencode({"article_id":articleId})
    senarioId = 13
    senarioParam = urllib.parse.urlencode({"scenario_id":senarioId})
    indexParam = urllib.parse.urlencode({"index":questionId})
    url = "https://top.zhan.com/toefl/read/practice.html?{}&{}&{}&{}".format(workflowParam,articleParam,senarioParam,indexParam)
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

def GetPassageTitle(soup):
    '''
    return : string
    '''
    titleSoup = soup.find('span', class_='read_title')
    return titleSoup.string

def GetTotalQuestionNum(soup):
    '''
    return : int
    '''
    questionRangeSoup = soup.find('div', class_='question_title left')
    questionNumStr = questionRangeSoup.string
    if '14' in questionNumStr:
        return 14
    else:
        return 13

def GetPassageContent(soup):
    '''
    return: list of string
    '''
    passageSoup = soup.find('div', class_ = 'article allarticle hide')
    return str(passageSoup).split(r'<br/><br/>')
    # return passageSoup.contents

def GetQuestionTitle(soup):
    questionTitleSoup = soup.find('p', class_='q_tit')
    # questionTitSpanSoup = soup.find('span', class_='text')
    '''
    if (len(questionTitSpanSoup) > 1):
        return reduce(lambda x,y : x+' '+y, questionTitSpanSoup.strings)
    else:            
        return questionTitSpanSoup.stripped_string
    '''
    questionTitle = questionTitleSoup.get_text() 
    return questionTitle.strip()

def IsInsertionQuestion(soup):
    '''
    return : bool
    '''
    if soup.find('div', class_='inserted-sentence') != None :
        return True
    else:
        return False

def GetInsertionQuestion(soup):
    '''
    return: question title, string; inserted sentence, string; tip, string, indicating which paragraph
    '''
    questionTitleSoup = soup.find('div',class_='q_tit')
    # questionTitle = reduce(lambda x,y : x + ' ' + y, questionTitleSoup.strings) 
    questionTitle = questionTitleSoup.get_text()
    insertedSentenceSoup = soup.find('div', class_='inserted-sentence')
    insertedSentence = insertedSentenceSoup.string
    questionTipSoup = soup.find('div',class_='tips')
    questionTip = questionTipSoup.string
    print(questionTitle,insertedSentence,questionTip)
    return (questionTitle.strip(),insertedSentence.strip(),questionTip)

def IsSummaryQuestion(soup):
    '''
    return : bool
    '''
    if soup.find('div', class_='content-select clearfix') != None:
        return True
    else:
        False

def GetSummaryQuestionTitle(soup):
    '''
    return : question title
    '''
    sumQuestionTitSoup = soup.find('div', class_='title')
    # print(sumQuestionTitSoup.string)
    sumQuestionTit = sumQuestionTitSoup.get_text()
    return sumQuestionTit.strip()

def GetSummaryOptions(soup):
    '''
    return : list of string
    '''
    optionsSoup = soup.find_all('p', class_='hg-drag')
    # print(optionsSoup)
    options = []
    for o in optionsSoup:
        options.append(o.get_text().strip())
        # options.append(reduce(lambda x, y : x + " " + y, o.stripped_strings))
    print(options)
    return options

def GetOptions(soup):
    '''
    return : list of string
    '''
    optionsSoup = soup.find_all('p', class_='ops rad')
    options = []
    for opt in optionsSoup:
        options.append(opt.string)
    print(options)
    return options


def GetCurrentParagraph(soup):
    '''
    return: string
    '''
    parasSoup = soup.find('img', id="ParagraphAr")
    paras = str(parasSoup).split(r'<br/><br/>')
    return paras[0]



def TPO2Json():
    pass

def Article2Md(articleId):
    soup = GetArticleSoup(articleId,0)
    questionNum = GetTotalQuestionNum(soup)
    title = GetPassageTitle(soup)
    print(title)
    md = "## {}\n\n".format(title)
    paragraphs = GetPassageContent(soup)
    for p in paragraphs:
        md = md + "{}\n\n".format(p)

    for i in range(questionNum):
        time.sleep(5)
        print("go to question {}".format(i+1))
        soup = GetArticleSoup(articleId,i)
        if IsInsertionQuestion(soup):
            print("Inserted Question..")
            currentParagraph = GetCurrentParagraph(soup)
            md = md + "{}\n\n".format(currentParagraph)
            questionTitle,insertedSentence,questionTip = GetInsertionQuestion(soup)
            md = md + "{}. {}\n\n{}\n{}\n\n".format(i+1,questionTitle,insertedSentence, questionTip)
        elif IsSummaryQuestion(soup):
            print("Summary Question..")
            summaryQuestion = GetSummaryQuestionTitle(soup)
            md = md + "{}. {}\n".format(i+1, summaryQuestion)
            sumOptions = GetSummaryOptions(soup)
            for o in sumOptions:
                md = md + "* {}\n".format(o)
            md = md + "\n"
        else:
            print("Normal Question..")
            currentParagraph = GetCurrentParagraph(soup)
            md = md + "{}\n\n".format(currentParagraph)
            question = GetQuestionTitle(soup)
            md = md + "{}. {}\n".format(i+1,question)
            options = GetOptions(soup)
            for o in options:
                md = md + "* {}\n".format(o)
            md = md + "\n"
    
    return md

def DumpMd(md,fileName):
    '''
    md : string, markdown string for a passage
    fileName: string
    '''
    with open(fileName,'a', encoding='utf-8') as fp:
        fp.write(md)
    fp.close()
    return None

if __name__ == '__main__':
    '''
    for articleId in [1,2,3]:
        md = Article2Md(articleId)
        DumpMd(md,'tpo1.md')
    for articleId in [18,19,20]:
        md = Article2Md(articleId)
        DumpMd(md,'tpo2.md')
    for articleId in [35,36,37]:
        md = Article2Md(articleId)
        DumpMd(md,'tpo3.md')
    for articleId in [52,53,54]:
        md = Article2Md(articleId)
        DumpMd(md,'tpo4.md')
    for articleId in [69,70,71]:
        md = Article2Md(articleId)
        DumpMd(md,'tpo5.md')
    '''

        
    '''
    # TPO1-TPO34, the article id pattern, tpo number increase 1, article id number increase 17.
    for tpoId in range(34):
        for articleId in range(1,4):
            md = Article2Md(17*tpoId+articleId)
            DumpMd(md, 'tpo{}.md'.format(tpoId+1))
    '''

    '''
    for articleId in [917,918,919]:
        md = Article2Md(articleId)
        DumpMd(md,'tpo35.md')
    
    for articleId in [951,952,953]:
        md = Article2Md(articleId)
        DumpMd(md,'tpo36.md')

    for articleId in [985,986,987]:
        md = Article2Md(articleId)
        DumpMd(md,'tpo37.md')
    
    
    for articleId in [968,969,970]:
        md = Article2Md(articleId)
        DumpMd(md,'tpo38.md')
    

    for articleId in [934,935,936]:
        md = Article2Md(articleId)
        DumpMd(md,'tpo39.md')

    
    for articleId in [611,612,613]:
        md = Article2Md(articleId)
        DumpMd(md,'tpo40.md')
    
    for articleId in [628,629,630]:
        md = Article2Md(articleId)
        DumpMd(md,'tpo41.md')
    for articleId in [628+17,629+17,630+17]:
        md = Article2Md(articleId)
        DumpMd(md,'tpo42.md')
    
    for articleId in [628+17*2,629+17*2,630+17*2]:
        md = Article2Md(articleId)
        DumpMd(md,'tpo43.md')
    for articleId in [628+17*3,629+17*3,630+17*3]:
        md = Article2Md(articleId)
        DumpMd(md,'tpo44.md')
    
    for articleId in [628+17*4,629+17*4,630+17*4]:
        md = Article2Md(articleId)
        DumpMd(md,'tpo45.md')
    for articleId in [628+17*5,629+17*5,630+17*5]:
        md = Article2Md(articleId)
        DumpMd(md,'tpo46.md')
    for articleId in [628+17*6,629+17*6,630+17*6]:
        md = Article2Md(articleId)
        DumpMd(md,'tpo47.md')
    for articleId in [628+17*7,629+17*7,630+17*7]:
        md = Article2Md(articleId)
        DumpMd(md,'tpo48.md')
    '''

    '''
    for articleId in [900,901,902]:
        md = Article2Md(articleId)
        DumpMd(md,'tpo49.md')
    
    for articleId in [1278,1279,1280]:
        md = Article2Md(articleId)
        DumpMd(md,'tpo50.md')
    
    for articleId in [1295,1296,1297]:
        md = Article2Md(articleId)
        DumpMd(md,'tpo51.md')
    
    for articleId in [1312,1313,1314]:
        md = Article2Md(articleId)
        DumpMd(md,'tpo52.md')

    for articleId in [1334,1335,1336]:
        md = Article2Md(articleId)
        DumpMd(md,'tpo53.md')

    '''

    '''
    # TPO35 ~, top number increase 1, article id number increase 34
    # the first article id of tpo 35 is 917.
    for tpoId in range(37,40):
        for articleId in range(3):
            md = Article2Md(917+(tpoId-35)*34+articleId)
            DumpMd(md,'tpo{}.md'.format(tpoId))
    '''

    for articleId in [968,969,970]:
        md = Article2Md(articleId)
        DumpMd(md,'tpo38.md')