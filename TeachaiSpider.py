# coding = utf-8
import sys
from urllib import request, parse
from urllib.error import URLError
from urllib.error import HTTPError
from bs4 import BeautifulSoup
import json
from functools import reduce
from pathlib import Path
import time

def getRequestHeaders():
    '''
    headers = {'Cookie': 'ASP.NET_SessionId=asztcqh12cu31sghkpniyhfi; MOKAO.CURRENT.USER1=9mCbWMX90IgirgrfeLy%2bcFLkMK1DFshl2t5cdcZowNmeZ3OszXzGKysUWJcP2j5ARCYsCi26qCaPU9YikPTZCdujYvc3kULPjqCQAjEUo%2bfDTC6INUBu4GYgI%2fImYD1dnayisEcFN1%2fusjj3IKF%2bHA5zEzqOFkHjZsPKyAV2evHxoE9zji4%2fw%2fLFUBrRH9RWcp7jEI1aMFEW4dIBP2oeq2WJNWHEz6l6UdEkZLUsS2tLq%2bzOJctRMYLK2BV%2fnF4uJU759AZRjtHEaMQPqWZl4H%2bZxs2regXy; 7fd305c0-040b-45f8-8d6a-c388ba59f280=2018-02-26 13:04:06; 117d5316-2172-4cab-bb9a-fb00116643db=2018-02-26 13:09:18; c0c1aae1-2e44-41b5-a6a4-1f7db7c8c0c2=2018-02-26 13:12:48; 75c93118-dcf3-41a8-9680-baa4f4710be5=2018-02-26 13:13:26; 2248dc76-611b-4f8e-9bdb-84b3b115ea28=2018-02-26 13:13:54; e013c2c0-bc7a-4f8c-9b6b-f693535c510a=2018-02-26 15:04:26; 07ec3652-af99-4fd4-8f0f-815854ab6a91=2018-02-26 15:16:40; 420aaa53-ef39-44ad-9368-52ac52c40c12=2018-02-26 15:28:36; 9ee598bf-5df6-4ee3-b93e-1575b51566e3=2018-02-26 15:41:34; 7e5d381d-b658-4293-80d5-1f5f5300541f=2018-02-27 11:25:21'}
    '''
    headers = {'Cookie': 'ASP.NET_SessionId=asztcqh12cu31sghkpniyhfi; MOKAO.CURRENT.USER1=9mCbWMX90IgirgrfeLy%2bcFLkMK1DFshl2t5cdcZowNmeZ3OszXzGKysUWJcP2j5ARCYsCi26qCaPU9YikPTZCdujYvc3kULPjqCQAjEUo%2bfDTC6INUBu4GYgI%2fImYD1dnayisEcFN1%2fusjj3IKF%2bHA5zEzqOFkHjZsPKyAV2evHxoE9zji4%2fw%2fLFUBrRH9RWcp7jEI1aMFEW4dIBP2oeq2WJNWHEz6l6UdEkZLUsS2tLq%2bzOJctRMYLK2BV%2fnF4uJU759AZRjtHEaMQPqWZl4H%2bZxs2regXy; a971fcd8-0e01-446f-b7e2-446142cc59ff=2018-03-13 13:54:01; 07b2ba80-a8fc-416e-be9c-c1a714712373=2018-03-13 17:33:52'}
    return headers

def getQuestionBaseURL():
    return "http://www.teachai.cn/exam/reading?"

def getAnswersBaseURL():
    return "http://www.teachai.cn/exam/result?"

def getTestLinkList():
    '''
    return: list of string, or None. 
    url: http://www.teachai.cn/exam

    each label <div class="item">, has 10 or so test links.
    each link to the passage test has the label http://www.teachai.cn/exam/prereading?name=Effects of the Commercial Revolution&exam=2aed38a0-eb1d-4ea9-9d47-9f4c5f7133d6
    we are interested in the "exam" part by which we can access the test.
    each link to the passage has label <p class="name"> and/or <p class="time">, indicating the name of the passage and the time of the test.
    
    '''
    url = "http://www.teachai.cn/exam"
    req = request.Request(url,headers=getRequestHeaders())
    time.sleep(2)
    try:
        with request.urlopen(req) as rsp:
            html = rsp.read().decode('utf-8')
        soup = BeautifulSoup(html,'html.parser')
        itemSoupList = soup.find_all('div', class_='item')
        linkList = []
        for itemSoup in itemSoupList:
            links = itemSoup.find_all('a')
            for link in links:
                linkStr = link.get('href')
                linkList.append(linkStr.split('&')[-1])
        print("Number of passage: {}".format(len(linkList)))
        print(linkList)
        return linkList
    except HTTPError as err:
        print("HTTP Error code: {}, reason: {}".format(err.code,err.reason))
        return None
    except URLError as err:
        print("URL Error reason: {}".format(err.reason))
        return None

def getPassage(testLink):
    '''
    testLink: string, the "exam=xxxxxx" part of the url, the whole url: http://www.teachai.cn/exam/reading?testlink
    
    title: <h2 class="view-text-r-tit">Effects of the Commercial Revolution</h2>
    
    return: list of string, each string element in the list is a paragraph.
    '''
    
    req = request.Request(getQuestionBaseURL()+testLink,headers=getRequestHeaders())
    # print(req.full_url)
    time.sleep(2)
    try:
        with request.urlopen(req) as rsp:
            html = rsp.read().decode('utf-8')
        soup = BeautifulSoup(html,'html.parser')
        passageSoup = soup.find('div',class_='view-text-r-main view-padding')
        # print(passageSoup.contents)
        passage = passageSoup.contents
        passage = [paragraph.string for paragraph in passage]
        passage = list((filter(lambda x: x != None,passage)))
        # print(passage)
        title = soup.find('h2', class_='view-text-r-tit').string
        return (title, passage)
    except HTTPError as err:
        print("HTTP Error code: {}, reason: {}".format(err.code,err.reason))
        return None
    except URLError as err:
        print("URL Error reason: {}".format(err.reason))
        return None


def isItemInRange(testLink, itemId):
    '''
    itemId: int, specifying the question number
    return: bool
    determine whether or not the itemId is in the range of the question number.
    '''
    
    req = request.Request(getQuestionBaseURL()+testLink+"&article={}".format(1)+"&item={}".format(itemId),headers=getRequestHeaders())
    # time.sleep(2)
    print(req.full_url)
    try:
        with request.urlopen(req) as f:
            pass
        print("ItemId = {} is in the range..".format(itemId))
        return True
    except HTTPError as err:
        if err.code == 500:
            return False
        else:
            return False

def isInsertQuestion(testLink, itemId):
    
    req = request.Request(getQuestionBaseURL()+testLink+"&article={}".format(1)+"&item={}".format(itemId),headers=getRequestHeaders())
    # print(req.full_url)
    # time.sleep(2)
    with request.urlopen(req) as rsp:
        html = rsp.read().decode('utf-8')
    soup = BeautifulSoup(html,'html.parser')
    if soup.find('div',class_='view-text-r-main view-padding').find('span',class_='strong-insert js-scrollto') != None:
        print("question {} is a insert sentence question".format(itemId))
        return True
    else:
        return False

def isSummaryQuestion(testLink, itemId):
    
    req = request.Request(getQuestionBaseURL()+testLink+"&article={}".format(1)+"&item={}".format(itemId),headers=getRequestHeaders())
    # print(req.full_url)
    # time.sleep(2)
    with request.urlopen(req) as rsp:
        html = rsp.read().decode('utf-8')
    soup = BeautifulSoup(html,'html.parser')
    if soup.find('div',class_='view-text-r-main view-padding') == None: # No passage on the right of the screen
        print("question {} is a summary question".format(itemId))
        return True
    else:
        return False

def isNormalQuestion(testLink, itemId):
    if isInsertQuestion(testLink, itemId) == False and isSummaryQuestion(testLink,itemId) == False:
        print("question {} is normal question..".format(itemId))
        return True
    else:
        print("question {} is not normal question..".format(itemId))
        return False

def getNormalQuestion(testLink, itemId):
    '''
    return: (string, string list), or None
    '''
    req = request.Request(getQuestionBaseURL()+testLink+"&article={}".format(1)+"&item={}".format(itemId),headers=getRequestHeaders())
    # print(req.full_url)
    time.sleep(2)
    try:
        with request.urlopen(req) as rsp:
            html = rsp.read().decode('utf-8')
        soup = BeautifulSoup(html,'html.parser')
        questionSoup = soup.find('div',class_='qa')
        qstTitleSoup = questionSoup.find('p',class_="question g-f16")
        # print(qstTitleSoup.contents)
        qstTitle = reduce(lambda x, y: x+ y, qstTitleSoup.strings)
        print(qstTitle)
        optionListSoup = questionSoup.find('ul',class_="g-kmf-form answers-radio js-kmf-form radio js-answers")
        options = optionListSoup.find_all('div',class_="clearfix content-text")
        # print(options)
        choices = []
        for o in options:
            # print(o.get_text().replace('\n',''))
            # print(reduce(lambda x,y: x+y,o.strings))
            choice = reduce(lambda x,y: x + ' ' + y,o.stripped_strings).replace('\n','')
            print(choice)
            choices.append(choice)
        print(choices)
        return (qstTitle, choices)
    except HTTPError as err:
        print(err.code)
        print(err.reason)
        return None
    except URLError as err:
        print(err.reason)
        return None

def getInsertQuestion(testLink, itemId):
    
    req = request.Request(getQuestionBaseURL()+testLink+"&article={}".format(1)+"&item={}".format(itemId),headers=getRequestHeaders())
    # print(req.full_url)
    time.sleep(2)
    try:
        with request.urlopen(req) as rsp:
            html = rsp.read().decode('utf-8')
        soup = BeautifulSoup(html,'html.parser')
        questionSoup = soup.find('div',class_='qa')
        qInstruction = questionSoup.find('p',class_='question g-f16').get_text()
        print(qInstruction)
        qSentence = questionSoup.find('p',class_='view-read-use').get_text()
        print(qSentence)
        return (qInstruction, qSentence)
    except HTTPError as err:
        print("HTTP Error code: {}, reason: {}".format(err.code,err.reason))
        return None
    except URLError as err:
        print("URL Error reason: {}".format(err.reason))
        return None

def getSummaryQuestion(testLink, itemId):
    '''
    return: (brief summary, choices)
    breif summary: string
    choices: string list
    '''
    req = request.Request(getQuestionBaseURL()+testLink+"&article={}".format(1)+"&item={}".format(itemId),headers=getRequestHeaders())
    # print(req.full_url)
    time.sleep(2)
    with request.urlopen(req) as rsp:
        html = rsp.read().decode('utf-8')
    soup = BeautifulSoup(html,'html.parser')
    print("when item = {}, it is a summary question".format(itemId))
    briefSummary = soup.find('p', class_='question g-f16').string
    print(briefSummary)
    itemList = soup.find('div',class_='item-choice-answers').find_all('div',class_='clearfix')
    choices = []
    for item in itemList:
        choice = item.find('i',class_='option').get_text() + item.find('p',class_='main').get_text()
        # print(choice)
        choices.append(choice)
    return (briefSummary,choices)

def getStarParagraphs(testLink, itemId):
    '''
    return: string list, or None

    find <div class="view-text-r-main view-padding">
    find <p>, return multiple html elements.
    find <span class="strong-star js-scrollto">♦</span>, find its next sibling html element.
    there may be more than one <span class="strong-star js-scrollto">♦</span>
    '''
    passage = getPassage(testLink)
    req = request.Request(getQuestionBaseURL()+testLink+"&article={}".format(1)+"&item={}".format(itemId),headers=getRequestHeaders())
    # print(req.full_url)
    time.sleep(2)
    with request.urlopen(req) as rsp:
        html = rsp.read().decode('utf-8')
    soup = BeautifulSoup(html,'html.parser')
    # we may have more than one starred paragraphs.
    starParaListSoup = soup.find('div',class_='view-text-r-main view-padding').find('p').find_all('span',class_='strong-star js-scrollto')
    if len(starParaListSoup) == 0:
        print("This question has no corresponding starred paragraphs...")
        return None
    else:
        print("there are {} starred paragraphs..".format(len(starParaListSoup)))
        # print(starParaListSoup)
        starParas = []
        for starp in starParaListSoup:
            starp.next_sibling.string
            for paragraph in passage:
                if starp.next_sibling.string in paragraph: 
                    starParas.append(starp.next_sibling.string)
        print(starParas)
        return starParas

def getInsertParagraphs(testLink, itemId):
    '''
    return: string list, or None
    '''
    time.sleep(2)
    req = request.Request(getQuestionBaseURL()+testLink+"&article={}".format(1)+"&item={}".format(itemId),headers=getRequestHeaders())
    # print(req.full_url)
    
    with request.urlopen(req) as rsp:
        html = rsp.read().decode('utf-8')
    soup = BeautifulSoup(html,'html.parser')
    passageSoup = soup.find('div',class_='view-text-r-main view-padding')
    allInsertSignsSoup = passageSoup.find_all('span',class_='strong-insert js-scrollto')
    # print(allInsertSignsSoup)
    # print(type(allInsertSignsSoup))
    firstSent = allInsertSignsSoup[0].next_sibling.string
    lastSent = allInsertSignsSoup[3].previous_sibling.string

    for paragraph in passage:
        if firstSent in paragraph:
            paraOfFirstSent = paragraph
        if lastSent in paragraph:
            paraOfLastSent = paragraph
    
    if paraOfFirstSent != paraOfLastSent:
        return [paraOfFirstSent,paraOfLastSent]
    else:
        return [paraOfFirstSent]

def getAnswerKeys(testLink):
    '''
    http://www.teachai.cn/exam/result?exam=5b152516-9ecb-40bf-a901-620e612793c9&code=e21dc4f2-6d7e-45e5-81fa-0ae13da82a2d
    '''
    pass

def getTest(testLink):
    getPassage(testLink)
    for itemId in range(1,15):
        if isItemInRange(testLink, itemId):
            if isInsertQuestion(testLink, itemId):
                getInsertQuestion(testLink, itemId)
                getInsertParagraphs(testLink, itemId)
            elif isSummaryQuestion(testLink, itemId):
                getSummaryQuestion(testLink, itemId)
            else:
                getNormalQuestion(testLink, itemId)
                getStarParagraphs(testLink, itemId)
        else:
            print("Get the whole test done!")
            break

def convertPassage2Markdown(testLink):
    title, passage = getPassage(testLink)
    print("title:{}".format(title))
    md = "# {}\n\n".format(title)
    for p in passage:
        print("paragraph:{}".format(p))
        md = md + "{}\n\n".format(p)
    md = md + "------------------------\n\n"
    return md

def convertTest2Markdown(testLink):
    md = convertPassage2Markdown(testLink)
    return None


def dumpMd(md, fileName):
    with open(fileName,'a', encoding='utf-8') as fp:
        fp.write(md)
    return None



if __name__ == '__main__':
    testLinkList = getTestLinkList()
    for testLink in testLinkList[0:2]:
        print("=============")
        # md = convertPassage2Markdown(testLink)
        # dumpMd(md,"TeaChai-GenuineTests.md")
        getTest(testLink)