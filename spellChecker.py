# Tarun Paravasthu, 7/20/22 
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
from multiprocessing import Event


OPFN="sp_result_" + datetime.now().strftime("%d_%m_%Y_%H_%M_%S") +".txt"

def SpellCheck(input, howMany='m', unflag=None, output=OPFN):
    if howMany=='m': _SP_Mult(input, unflag, output)
    if howMany=='s': _SP_Single(input, unflag, output)

# Given a url, makes an api call and runs a spell check on the json file 
# Parameters:input file name, name of file with words to ignore (optional), output file name (optional)
def _SP_Single(url, unflagFN=None, outputFN=OPFN):
    # Makes a list of special words to ignore             
    UF_List=_make_UF_List(unflagFN)

    # prints output to text file
    output=open(outputFN, 'w', encoding='utf-8')
    print(url, file=output, end="")
    print(_SP_Helper(url, UF_List), file=output)
    output.close()
    
# Given a text file with urls, uses multiprocessing to run a spell check on all of them
# Parameters:input file name, name of file with words to ignore (optional), output file name (optional)
def _SP_Mult(inputFN, unflagFN=None, outputFN=OPFN):

    # Reads text file with APIs                         (format?)
    f=open(inputFN)                                     
    r=f.read();
    urls=r.split()
    
    # Makes a list of special words to ignore
    UF_List=_make_UF_List(unflagFN)
    
    output=open(outputFN, 'w', encoding='utf-8')
    with ProcessPoolExecutor() as executor:                
        results=executor.map(_SP_Helper, urls, repeat(UF_List))
        for n,result in enumerate(results):
            print(f"File {n+1}: {urls[n]}",file=output, end="")
            print(result, file=output)
    output.close()

# Gets a JSON file from an API and runs a spellcheck on it, returns string with results
# Parameters: url of API, List of words to unflag
def _SP_Helper(url, UF_List):
    
    # Gets json file from API
    dic=_call_API(url)
    if isinstance(dic,str): return dic

    result=""
    keyList, wordList=_getJSONValues(dic)
    
    # Organizes List
    regex='http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
    n=0
    
    while(n<len(wordList)):
        wordList[n]=wordList[n].lower()        
        
        # Filters out urls
        urls=re.findall(regex,wordList[n])
        for u in urls:
            wordList[n]=wordList[n].replace(u, '')
        
        # Splits values with multiple words and filters out words with numbers or special characters
        Words=re.split(r'[-/_;:,."=!?()\s]\s*',wordList[n])
        
        rem=r"0123456789/\\{}[]()&$%_#\+\-"
        Words=[x for x in Words if not (x=='' or any(z in x for z in rem))]
        
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
    count=len(misspelled)
    if count==0: return "No mistakes\n"

    # creates output string   
    result+=f" ({count})\n"  
    for i,word in enumerate(wordList):
        if word in misspelled:  
            result+=f"{word.ljust(20)} {spell.correction(word).ljust(20)}Key:{keyList[i]}\n"
    return result

# Makes a post call to the given url, catches errors and retries in case of error 502
def _call_API(url):
    try:
        # r=requests.get(url)
        r=requests.post(url)
        if r.status_code!=200:
            count=0
            while r.status_code==502 or count==3:
                e=Event
                e.wait(60)
                r=requests.post(url)
                count+=1
                
            return f"\nError {r.status_code}"
        else: return r.json() 
    except:
        return "\nUnknown Error: Check url"

# Takes text file and creates a list of words
def _make_UF_List(filename):
    if filename==None: UF_List=[]
    else:
        u=open(filename, encoding='utf-8')
        st=u.read()
        u.close()
        UF_List=st.split()
    return UF_List

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

# Given a list and element, returns a list of all indices which contain the element
def get_index_positions(list_of_elems, element):
    index_pos_list = []
    index_pos = 0
    while True:
        try:
            index_pos = list_of_elems.index(element, index_pos)
            index_pos_list.append(index_pos)
            index_pos += 1
        except ValueError as e:
            break
    return index_pos_list

# Main method to run tests in
def main():
    
    SpellCheck("input.txt")
    

if __name__=="__main__":
    main()
