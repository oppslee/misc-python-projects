#! /usr/bin/env python
#coding=utf-8
from nltk.corpus import wordnet as wn
import string as str
from xlrd import open_workbook
from xlwt import Workbook
from tempfile import TemporaryFile
import urllib2
import urllib
import re
import sys
import time
from HTMLParser import HTMLParser

def readWords(filename):
    wb = open_workbook(filename)
    sheet = wb.sheet_by_index(0)
    print(sheet.name)
    print(sheet.nrows)
    print(sheet.ncols)
    words = []
    
    for row_index in range(sheet.nrows):
        try:
            # word = sheet.cell(row_index,0).value.encode('ascii')
            word = sheet.cell(row_index,0).value.encode('utf8')
            words.append(word)
        except UnicodeEncodeError:
            print("Opps! French!")
    
    return words

class EtymParser(HTMLParser):
    '''
    Note this class, I am damn glad that I came to such a solution for parsing verbatim data.
    '''
    def __init__(self):
        HTMLParser.__init__(self)
        self.etymology = []
        self.count = 0
        
    def handle_starttag(self,tag,attrs):
        '''
        if (tag == 'dd'):
            for name,value in attrs:
                if (name == 'class') and (value == 'highlight'):
                    print(self.get_starttag_text())
        '''
        pass
    def handle_endtag(self,tag):
		# print("Hit an end tag: %s"%tag)
		pass	
    
    def handle_entity(self,name):
        pass
    
    def handle_data(self,data):
        # print("%d: %s"%(self.count,data)) # From this, It is clear that the begging of etymology starts from count=106, and the last 45 counts are not parts of the etymology.
        self.count += 1
        self.etymology.append(data)

def requestEtymology(word):
    url = "http://www.etymonline.com/index.php?allowed_in_frame=0&search=%s&searchmode=term"%word
    print(url)
    etym_list = []

    try:
        time.sleep(2)
        response = urllib2.urlopen(url)
    except urllib2.HTTPError,e:
        print(e.code)
    except urllib2.URLError,e:
        print(e.reason)
    else:
        html = response.read()
        response.close() # this seems work when socket doesn't response, error 10054
        parser = EtymParser()
        parser.feed(html)
        etym_list = parser.etymology
    
    return str.join(etym_list[106:-46],'')

if __name__ == '__main__':
    
    book = Workbook('utf8')
    sheet = book.add_sheet('barron etymology')
    
    words = readWords('b3500.xls')
    index = 0
    
    for index in range(3000,len(words)):
        etymology = requestEtymology(words[index])
        sheet.write(index,0,etymology)
        
    book.save(sys.argv[1])
    book.save(TemporaryFile())