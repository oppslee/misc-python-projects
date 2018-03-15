# coding = utf-8
import json
import sys
import re
import xlwings as xw

def File2JsonData(jsonFileName): 
    jsonFile = open(jsonFileName,'rb')
    jsonData = json.loads(jsonFile.read())
    jsonFile.close()
    return jsonData

def JsonQuestionTest2Excel(jsonData,excelFile):
    '''
    选择题抽查模式下, 隐藏的json应答.
    [{
        "id": "27715735",
        "word_id": "11940",
        "word_meaning_id": "0",
        "question_id": "126328",
        "question": {
            "question": "What has allowed us to become confident enthusiasts in this new <u>ever-shifting</u> world?",
            "passage": null,
            "question_id": "126328",
            "choices": [
                {
                    "content": "strange",
                    "is_correct": "0",
                    "id": "456788"
                },
                {
                    "content": "dainty",
                    "is_correct": "0",
                    "id": "456789"
                },
                {
                    "content": "excess",
                    "is_correct": "0",
                    "id": "456790"
                },
                {
                    "content": "constantly changing",
                    "is_correct": "1",
                    "id": "456787"
                }
            ]
        },
        ...,
        ...,
        ]
    '''
    workbook = xw.Book()
    activeSheet = workbook.sheets['Sheet1']
    vocabSize = len(jsonData)

    # \s Matches any whitespace character; this is equivalent to the class [ \t\n\r\f\v].
    # \S Matches any non-whitespace character; this is equivalent to the class [^ \t\n\r\f\v].
    # \w Matches any alphanumeric character; this is equivalent to the class [a-zA-Z0-9_].
    p = re.compile('<u>[\w\s\S]+</u>')
    numChoices = len(jsonData[1]['question']['choices'])
    for i in range(vocabSize):
        question = jsonData[i]['question']['question']
        activeSheet[i,1].value = question
        print("Question: ", question)

        passage = jsonData[i]['question']['passage']
        if passage != None:
            activeSheet[i,2].value = passage

        # l,r = p.search(question).span()
        # word = question[l+3:r-4]
        # activeSheet[i,0].value = word
        # print("Word: ", word)

        choices = []
        for n in range(numChoices):
            choices.append(jsonData[i]['question']['choices'][n]['content'])
            activeSheet[i,3+n].value = jsonData[i]['question']['choices'][n]['content']
        print("Choices: ", choices)

        keys = ['A','B','C','D','E']
        for index in range(numChoices):
            isCorrect = jsonData[i]['question']['choices'][index]["is_correct"]
            if isCorrect == "1":
                key = keys[index]
                activeSheet[i,3+numChoices].value = key
                print("Key: ", key)
                break
    workbook.save(excelFile)

def JsonSelfTest2Excel(jsonData,excelFile):
    '''
    普通自抽模式下, json应答.
    [
        {
            "word": "abase",
            "chinese": "【动】使（地位、身份等）降低，屈辱",
            "look": "1",
            "id": "27732464",
            "word_id": "3438"
        },
        ...,
        ...,
        ...
    ]
    '''
    workbook = xw.Book()
    activeSheet = workbook.sheets['Sheet1']
    vocabSize = len(jsonData)

    for i in range(vocabSize):
        word = jsonData[i]["word"]
        definition = jsonData[i]["chinese"]
        print(word, definition.replace('<br>','\n'))
        activeSheet[i,0].value = word
        activeSheet[i,1].value = definition
    workbook.save(excelFile)


def JsonSelfTest2Txt(jsonData, txtFile):
    vocabSize = len(jsonData)
    with open(txtFile,'a',encoding='utf-8') as f:
        for i in range(vocabSize):
            word = jsonData[i]["word"]
            definition = jsonData[i]["chinese"]
            f.write("{}\t{}\n".format(word,definition.replace('<br>','##')))

if __name__ == '__main__':
    jsonFile = sys.argv[1]
    jsonData = File2JsonData(jsonFile)
    # excelFile = sys.argv[2]
    txtFile = sys.argv[2]
    if sys.argv[3] == 'q': # json from question mode
        JsonQuestionTest2Excel(jsonData,excelFile)
    elif sys.argv[3] == 'a': # json from aotu mode
        # JsonSelfTest2Excel(jsonData,excelFile)
        JsonSelfTest2Txt(jsonData,txtFile)