# requires pyspellchecker library (pip install pyspellchecker)
# Contains three functions, SpellCheck checks one file, SpellCheckF checks a folder of files. SpellCheckHelp is used in the other functions

from spellchecker import SpellChecker
from datetime import datetime
import os 
import json
import concurrent.futures
import re

# SpellChecker function, checks spelling of values in a file and returns string of results
# Parameters: Name of file, values to exclude (optional)
def SpellCheckHelp(fileName, unflag=None): 
    # creates spellchecker object
    spell = SpellChecker()

    #create lists for words, list for keys and boolean if json
    result=""
    
    wordList=[]
    
    isJson=False
    keyList=[]

    f=open(fileName, encoding='utf-8')
    
    if (fileName[len(fileName)-4:]==".txt"):                       #could cause out of bounds error          
        s=f.read()
        wordList=re.split(r"[-/_;:,.!?\s()]\s*",s)                     
        f.close()

    #for json files
    elif (fileName[len(fileName)-5:]==".JSON" or fileName[len(fileName)-5:]==".json"):           
        isJson=True
        
        
        dic=json.load(f)                               
        f.close()
        
        keyList,wordList=getJSONValues(dic)
 
        n=0
        while(n<len(wordList)):
            wordList[n]=wordList[n].lower()              
            Words=re.split(r"[-/_;:,.!?\s()]\s*",wordList[n])
            if (len(Words)>1):
                k=keyList[n]

                del wordList[n]
                del keyList[n]
                for word in reversed(Words):
                    
                    wordList.insert(n,word)
                    keyList.insert(n, k)            
            n+=1

    # Error message
    else:
        return "File type not supported\n"


    #adds special words to the dictionary
    if(unflag!=None):
        spell.word_frequency.load_words(unflag)
    
    #runs spell checker and puts misspelled words in a list
    misspelled=list(spell.unknown(wordList))
    
    if len(wordList)==0 or wordList[0]=="": return "No mistakes\n"
    
    # creates output             
    if(isJson): 
        mpKeys=[]
        for i, word in enumerate(misspelled):
            mpKeys.append(keyList[wordList.index(word)])
            result+=f"{misspelled[i].ljust(20)} {spell.correction(misspelled[i]).ljust(20)}Key:{mpKeys[i]}\n"
    
    else:
        for i, word in enumerate(misspelled):
            result+=f"{misspelled[i].ljust(20)} {spell.correction(misspelled[i]).ljust(20)}\n"
    
    return result

# Runs a spell check on a file and prints results to a file
# Parameters: Name of file, words to exclude(optional), name of output file(optional)
def SpellCheck(fileName, unflag=None, outputFile=None):
    if outputFile==None:
        outputFile="sp_result_" + datetime.now().strftime("%d_%m_%Y_%H_%M_%S") +".txt"
    output=open(outputFile, 'w')
    print(SpellCheckHelp(fileName, unflag=unflag), file=output)
    output.close()



# Runs a spell check on each file in a folder and returns an output file
# Parameters: Name of folder, words to exclude(optional), name of output file(optional)
def SpellCheckF(folderName, unflag=None, outputFile=None):
    if outputFile==None:
        outputFile="sp_result_" + datetime.now().strftime("%d_%m_%Y_%H_%M_%S") +".txt"
    output=open(outputFile, 'w')
    
    files=os.scandir(folderName)
   
    str_files=[]
    for f in files:
        str_files.append(f.path)

    with concurrent.futures.ThreadPoolExecutor() as executor:
        results=executor.map(lambda p:SpellCheckHelp(p, unflag=unflag), str_files)
        for n,result in enumerate(results):
            print(f"File {n+1}: {str_files[n]}",file=output)
            print(result, file=output)
    output.close()

    # with concurrent.futures.ProcessPoolExecutor() as executor:                #trying to use multiprocessing, getting Broken Process Error
    #     results=executor.map(SpellCheckHelp, str_files)
    #     for n,result in enumerate(results):
    #         print(f"File {n+1}: {str_files[n]}",file=output)
    #         print(result, file=output)
    # output.close()


# Reads values from a JSON Dictionary, outputs a list of values and a list of keys
# Parameters: Converted JSON file. Words and Keys should be empty.
def getJSONValues(Obj, Words=[], Keys=[]):
    if isinstance(Obj, dict):
        for inner_obj_key in Obj.keys():
            if isinstance(Obj[inner_obj_key], dict) or isinstance(Obj[inner_obj_key], list):
                getJSONValues(Obj[inner_obj_key], Words, Keys)
            else:
                Words.append(str(Obj[inner_obj_key]))
                Keys.append(inner_obj_key)
    if isinstance(Obj, list):
        for inner_obj in Obj:
            if isinstance(inner_obj, dict) or isinstance(inner_obj, list):
                getJSONValues(inner_obj, Words, Keys)
            else:
                Words.append(str(inner_obj))
    return Keys,Words


# For testing and comparing to parallel processing 
def SpellCheckerSeq(folderName):

    output=open("Trash\\trash.txt", 'w')
    for n,file in enumerate(os.scandir(folderName)):
        print("File", n+1, file.path, file=output)
        print(SpellCheckHelp(str(file.path)), file=output)
        # print(file.path)
    output.close()
    
