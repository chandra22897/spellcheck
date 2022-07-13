# Tarun Paravasthu, 7/11/22
# Runs a spell check on JSON API calls
# Contains functions SpellCheck, SpellCheckMult, and helper methods _SP_Helper and getJSONValues

from spellchecker import SpellChecker
from datetime import datetime
import os 
import json
from concurrent.futures import ProcessPoolExecutor
import re
from itertools import repeat
import requests

OPFN="sp_result_" + datetime.now().strftime("%d_%m_%Y_%H_%M_%S") +".txt"

# Given a uri, makes an api call and runs a spell check on the json file 
# Parameters:input file name, name of file with words to ignore (optional), output file name (optional)
def SpellCheck(uri, unflagFN=None, outputFN=OPFN):
    # Makes a list of special words to ignore             (can make this an API call as well if needed)
    if unflagFN==None: UF_List=[]
    else:
        u=open(unflagFN, encoding='utf-8')
        st=u.read()
        u.close()
        UF_List=re.split(r"[-/_;:,.!?\s()]\s*",st)

    # prints output to txt file
    output=open(outputFN, 'w', encoding='utf-8')
    print(f"{uri}:\n", file=output)
    print(_SP_Helper(uri, UF_List), file=output)
    output.close()
    
# Given a JSON file with uris, uses multiprocessing to run a spell check on all of them
# Parameters:input file name, name of file with words to ignore (optional), output file name (optional)
def SpellCheckMult(inputFN, unflagFN=None, outputFN=OPFN):

    # Reads JSON file with APIs                         (format?)
    f=open(inputFN)                                     
    dic=json.load(f)                               
    f.close()
    uris=_getJSONValues(dic)[1]
    
    # Makes a list of special words to ignore
    if unflagFN==None: UF_List=[]
    else:
        u=open(unflagFN, encoding='utf-8')
        st=u.read()
        u.close()
        UF_List=re.split(r"[-/_;:,.!?\s()]\s*",st)
    
    # Checks for bad uris
    for a in uris:
        try: requests.get(a)
        except: uris.remove(a)
    
    output=open(outputFN, 'w', encoding='utf-8')
    with ProcessPoolExecutor() as executor:                
        results=executor.map(_SP_Helper, uris, repeat(UF_List))
        for n,result in enumerate(results):
            print(f"File {n+1}: {uris[n]}\n",file=output)
            print(result, file=output)
    output.close()

# Gets a JSON file from an API and runs a spellcheck on it, returns string with results
# Parameters: uri of API, List of words to unflag
def _SP_Helper(uri, UF_List):
    
    # Gets json file from API
    r=requests.get(uri)
    dic=r.json()

    result=""
    keyList, wordList=_getJSONValues(dic)

    regex = r"(?i)\b((?:https?://|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,4}/)(?:[^\s()<>]+|\(([^\s()<>]+|(\([^\s()<>]+\)))*\))+(?:\(([^\s()<>]+|(\([^\s()<>]+\)))*\)|[^\s`!()\[\]{};:'\".,<>?«»“”‘’]))"
    n=0
    while(n<len(wordList)):
        wordList[n]=wordList[n].lower()        
        
        urls=re.findall(regex,wordList[n])
        for u in urls:
            wordList[n]=wordList[n].replace(u[0], '')
                

        Words=re.split(r"[-/_;:,.!?\s()]\s*",wordList[n])
        if (len(Words)>1):
            k=keyList[n]
            del wordList[n]
            del keyList[n]
            for word in reversed(Words):      
                wordList.insert(n,word)
                keyList.insert(n, k)  
        n+=1
    
    #adds special words to the dictionary
    spell = SpellChecker()
    spell.word_frequency.load_words(UF_List)
    
    #runs spell checker and puts misspelled words in a list
    misspelled=list(spell.unknown(wordList))
   
    if len(misspelled)==0: return "No mistakes\n"
    
    # creates output             
    mpKeys=[]
    for i, word in enumerate(misspelled):
        mpKeys.append(keyList[wordList.index(word)])   
        result+=f"{misspelled[i].ljust(20)} {spell.correction(misspelled[i]).ljust(20)}Key:{mpKeys[i]}\n"
    return result
    
# Given a JSON dictionary, recursively returns a list of keys and a list of values. Words and Keys should not be changed
def _getJSONValues(Obj, Words=[], Keys=[]):
    if isinstance(Obj, dict):
        for inner_obj_key in Obj.keys():
            if isinstance(Obj[inner_obj_key], dict) or isinstance(Obj[inner_obj_key], list):
                _getJSONValues(Obj[inner_obj_key], Words, Keys)
            else:
                Words.append(str(Obj[inner_obj_key]))
                Keys.append(inner_obj_key)
    if isinstance(Obj, list):
        for inner_obj in Obj:
            if isinstance(inner_obj, dict) or isinstance(inner_obj, list):
                _getJSONValues(inner_obj, Words, Keys)
            else:
                Words.append(str(inner_obj))
    return Keys,Words


# Main method to run tests in
def main():
    # SpellCheck("http://api.open-notify.org/astros.json" ,outputFN="Trash\\trash.txt")
    SpellCheck("https://www.reddit.com/r/Wallstreetbets/top.json?limit=10&t=year" ,outputFN="Trash\\trash.txt")
    # SpellCheckMult("API.json" ,outputFN="Trash\\trash.txt")


if __name__=="__main__":
    main()
