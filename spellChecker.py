# Tarun Paravasthu, 7/25/22 
# Runs a spell check on JSON API calls and files
# Contains functions SpellCheck, SpellCheckMult, and helper methods _SP_Helper and getJSONValues

import multiprocessing
from spellchecker import SpellChecker
from datetime import datetime
import os 
import json
from concurrent.futures import ProcessPoolExecutor
import re
from itertools import repeat
import requests
from multiprocessing import Event

default="sp_result_" + datetime.now().strftime("%d_%m_%Y_%H_%M_%S") +".txt"

'''
Main Function SpellCheck()
Parameters: input, arg for type of input, unflag file with reserved words (optional), output for file output file(optional)
args:
m(default)--input is a text file with multiple urls in it
s--input is a single url
fs--input is a single local json file name
ms--input is a text file with multiple json file names in it

Note: majority of run time is in finding corrections for wrong words and size of unflag file
'''
def SpellCheck(input, arg='m', unflag=None, output=default):
    if arg=='m': _SP_Mult(input, unflag, output)
    if arg=='s': _SP_Single(input, unflag, output)
    if arg=='fs':_SP_Single(input, unflag, output, f=True)
    if arg=='fm': _SP_Mult(input, unflagFN=unflag, outputFN=output, F=True)
    

# Given a url, makes an api call and runs a spell check on the json file 
# Parameters:input file name, name of file with words to ignore (optional), output file name (optional)
def _SP_Single(url, unflagFN=None, outputFN=default, f=False):
    output=open(outputFN, 'w', encoding='utf-8')
    print(url, file=output, end="")
    print(_SP_Helper(url, unflagFN, f=f), file=output)
    output.close()
    
# Given a text file with urls, uses multiprocessing to run a spell check on all of them
# Parameters:input file name, name of file with words to ignore (optional), output file name (optional)
def _SP_Mult(inputFN, unflagFN=None, outputFN=default, F=False):

    # Reads text file with APIs/files                         (format?)
    f=open(inputFN)                                     
    r=f.read();
    f.close()
    urls=r.split()
    
    output=open(outputFN, 'w', encoding='utf-8')
    with ProcessPoolExecutor(max_workers=multiprocessing.cpu_count()) as executor:                
        results=executor.map(_SP_Helper, urls, repeat(unflagFN), repeat(F))
        for n,result in enumerate(results):
            print(f"File {n+1}: {urls[n]}",file=output, end="")
            print(result, file=output)
    output.close()

# Gets a JSON file from an API and runs a spellcheck on it, returns string with results
# Parameters: url of API, List of words to unflag
def _SP_Helper(url, unflag, f):
    
    # Gets json file from API
    if not f:
        dic=_call_API(url)
        if isinstance(dic,str): return dic                      #for error messages
    else:
        try:
            f=open(url)
            dic=json.load(f)
            f.close()
        except Exception as e:
            return e
    
    
    result=""

    # Creates and organizes a list of words and a list of keys
    keyList, wordList=_getJSONValues(dic)
    keyList, wordList=filter_words(keyList, wordList)
    
    #adds special words to the dictionary
    spell = SpellChecker()
    if unflag!=None: spell.word_frequency.load_text_file(unflag)
    
    #runs spell checker and puts misspelled words in a list
    misspelled=list(spell.unknown(wordList))
    count=len(misspelled)
    if count==0: return "No mistakes\n"
             
    # creates output string   
    result+=f" ({count})\n"  
    repeats={}
    for i,word in enumerate(wordList):
        if word in misspelled:
            try:
                corr=repeats[word]
            except:
                corr=spell.correction(word)
                temp={word:corr}
                repeats.update(temp)
            
            result+=f"{word.ljust(20)} {corr.ljust(20)}Key:{keyList[i]}\n"
    return result

# removes urls and special characters, splits "words" that contain spaces or other seperators
# Parameters: list of words, list of keys
def filter_words(keyList, wordList):
    regex='http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
    rem="0123456789{}[]&$%#\+\-@"
    n=0
    
    while(n<len(wordList)):
        wordList[n]=wordList[n].lower()        
        
        # Custom
        if keyList[n]=='field_name':
            del keyList[n]
            del wordList[n]
            continue

        # Filters out urls
        urls=re.findall(regex,wordList[n])
        for u in urls:
            wordList[n]=wordList[n].replace(u, '')

        # Splits words and removes special characters
        Words=re.split(r'[-/_;:,."=|!()\s]\s*',wordList[n])
        Words=[x for x in Words if not (len(x)<=1 or any(z in x for z in rem))]
        for j in range(len(Words)):                                             #special case
            Words[j]=Words[j].replace('?','')


        k=keyList[n]
        if len(Words)==1 and wordList[n]==Words[0]:
            n+=1
        else:
            del wordList[n]
            del keyList[n]
            for word in Words:  
                wordList.insert(n,word)
                keyList.insert(n, k)
                n+=1
    
    return keyList,wordList

# Makes a get call to the given url, catches errors and retries in case of error 502(last part untested)
def _call_API(url):
    try:
        r=requests.get(url)
        if r.status_code!=200:
            count=0
            while r.status_code==502 or count==3:
                e=Event()
                e.wait(60)
                r=requests.get(url)
                count+=1
            if r.status_code==200:  return r
            else: return f"\nError {r.status_code}"
        else: return r.json() 
    except:
        return "\nUnknown Error: Check url"

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
                Words.append(str(inner_obj))            #never executes
                Keys.append('[Error: No Key]')
    return Keys,Words

    
# Main method to run tests in, prints time
import time
def main():
    start=time.perf_counter()
    # SpellCheck("astros.json", arg='fs', unflag='saved_strings.txt', output='Trash\\trash.txt')
    # SpellCheck("http://api.open-notify.org/astros.json", arg='s', unflag='saved_strings.txt', output='Trash\\trash.txt')
    SpellCheck("input.txt", arg='fm', unflag='saved_strings.txt')
    
    print(time.perf_counter()-start)
if __name__=="__main__":
    main()
