# Tarun Paravasthu, 7/19/22
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

# Given a url, makes an api call and runs a spell check on the json file 
# Parameters:input file name, name of file with words to ignore (optional), output file name (optional)
def SpellCheck(url, unflagFN=None, outputFN=OPFN):
    # Makes a list of special words to ignore             (can make this an API call as well if needed)
    if unflagFN==None: UF_List=[]
    else:
        u=open(unflagFN, encoding='utf-8')
        st=u.read()
        u.close()
        UF_List=st.split()

    # prints output to text file
    output=open(outputFN, 'w', encoding='utf-8')
    print(f"{url}:\n", file=output)
    print(_SP_Helper(url, UF_List), file=output)
    output.close()
    
# Given a text file with urls, uses multiprocessing to run a spell check on all of them
# Parameters:input file name, name of file with words to ignore (optional), output file name (optional)
def SpellCheckMult(inputFN, unflagFN=None, outputFN=OPFN):

    # Reads text file with APIs                         (format?)
    f=open(inputFN)                                     
    r=f.read();
    urls=r.split()
    
    # Makes a list of special words to ignore
    if unflagFN==None: UF_List=[]
    else:
        u=open(unflagFN, encoding='utf-8')
        st=u.read()
        u.close()
        UF_List=st.split()
    
    # Checks for bad urls
    for a in urls:
        try: requests.get(a)
        except: urls.remove(a)
    
    output=open(outputFN, 'w', encoding='utf-8')
    with ProcessPoolExecutor() as executor:                
        results=executor.map(_SP_Helper, urls, repeat(UF_List))
        for n,result in enumerate(results):
            print(f"File {n+1}: {urls[n]}\n",file=output)
            print(result, file=output)
    output.close()

# Gets a JSON file from an API and runs a spellcheck on it, returns string with results
# Parameters: url of API, List of words to unflag
def _SP_Helper(url, UF_List):
    
    # Gets json file from API
    r=requests.get(url)
    if r.status_code!=200:
        return f"Error {r.status_code}{OPFN}"
    dic=r.json()

    result=""
    keyList, wordList=_getJSONValues(dic)
   
    regex='http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
    n=0
    while(n<len(wordList)):
        wordList[n]=wordList[n].lower()        
        
        urls=re.findall(regex,wordList[n])
        for u in urls:
            wordList[n]=wordList[n].replace(u, '')
        Words=re.split(r'[-/_;:,."=!?()\s]\s*',wordList[n])
        if (len(Words)>1):
            k=keyList[n]
            del wordList[n]
            del keyList[n]
            for word in reversed(Words):
                if not any(x in word for x in r"/\\{}[]()$%#+-"):      
                    wordList.insert(n,word)
                    keyList.insert(n, k)  
                
        n+=1
    
    #adds special words to the dictionary
    spell = SpellChecker()
    spell.word_frequency.load_words(UF_List)
    
    #runs spell checker and puts misspelled words in a list
    
    misspelled=list(spell.unknown(wordList))
    if len(misspelled)==0: return "No mistakes\n"
    # print(len(misspelled))

    # creates output string            
    for i,word in enumerate(wordList):
        if word in misspelled:  
            result+=f"{word.ljust(20)} {spell.correction(word).ljust(20)}Key:{keyList[i]}\n"
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
    SpellCheck("http://api.open-notify.org/astros.json" , outputFN="Trash\\trash.txt",unflagFN="special.txt")
    # SpellCheck("http://api.open-notify.org/astros.json" ,outputFN="Trash\\trash.txt")
    # SpellCheck("https://www.reddit.com/r/Wallstreetbets/top.json?limit=10&t=year" ,outputFN="Trash\\trash.txt")
    # SpellCheckMult("input.txt" ,outputFN="Trash\\trash.txt")


if __name__=="__main__":
    main()
