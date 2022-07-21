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
from collections import Counter
OPFN="sp_result_" + datetime.now().strftime("%d_%m_%Y_%H_%M_%S") +".txt"

# Main Function
def SpellCheck(input, typeArg=0, unflag=None, output=OPFN):
    if typeArg==0: _SP_Single(input, unflag, output)
    if typeArg==1: _SP_Mult(input, unflag, output)
    


# Given a url, makes an api call and runs a spell check on the json file 
# Parameters:input file name, name of file with words to ignore (optional), output file name (optional)
def _SP_Single(url, unflagFN=None, outputFN=OPFN):
    # Makes a list of special words to ignore             (can make this an API call as well if needed)
    UF_List=_make_UF_List(unflagFN)

    # prints output to text file
    output=open(outputFN, 'w', encoding='utf-8')
    print(f"{url}:\n", file=output)
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
        return f"Error {r.status_code}"
    dic=r.json()

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
    if len(misspelled)==0: return "No mistakes\n"
    count=Counter(wordList)
    # print (len(misspelled))

    # creates output string
    repeats=[]
    for i,word in enumerate(wordList):
        if word in misspelled and word not in repeats:
            repeats.append(word)
            wordStr=f"{word} ({count[word]})"
            inds=get_index_positions(wordList, word)
            keyStr=""
            
            for j,ind in enumerate(inds):
              if j>0: keyStr+=", "
              keyStr+=keyList[ind]
            result+=f"{wordStr.ljust(20)} {spell.correction(word).ljust(20)}Keys:{keyStr}\n"
    return result

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
            # Search for item in list from indexPos to the end of list
            index_pos = list_of_elems.index(element, index_pos)
            # Add the index position in list
            index_pos_list.append(index_pos)
            index_pos += 1
        except ValueError as e:
            break
    return index_pos_list


# Main method to run tests in
def main():
    
    SpellCheck("input.txt",typeArg=1)


if __name__=="__main__":
    main()
