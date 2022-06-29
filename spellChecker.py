# requires pyspellchecker library (pip install pyspellchecker)
# Contains three functions, SpellCheck checks one file, SpellCheckF checks a folder of files. SpellCheckHelp is used in the other functions.

from spellchecker import SpellChecker
from datetime import datetime
import os 
import json
import concurrent.futures

# SpellChecker function, checks spelling of values in a file and returns string of results
# Parameters: Name of file, values to exclude (optional), output file(optional)
def SpellCheckHelp(fileName, unflag=None): 
    #create lists for words, list for keys and boolean if json
    result=""
    
    wordList=[]
    
    isJson=False
    keyList=[]

    f=open(fileName)
    
    if (fileName[len(fileName)-4:]==".txt"):
        s=f.read()
        wordList=s.split(" ")
        f.close()

    #for json files
    elif (fileName[len(fileName)-5:]==".JSON"):           
        isJson=True
        
        
        dic=json.load(f)                               
        f.close()

        for i in dic:
            # wordList.append(i)                         
            for j in dic[i][0]:
                keyList.append(j)
                wordList.append(dic[i][0][j])
        
        #in case of multiple words 
        n=0
        while(n<len(wordList)):
            
            st=wordList[n]
            L=wordList[n].split()
            
            if(len(L)>1):
                i=len(L)-1
               
                while (i>=0):                  
                    wordList.insert(n,L[i]) 
                    keyList.insert(n,keyList[n])                  
                    i-=1
                wordList.remove(st)        
                keyList.remove(keyList[n])
            n+=1

    # Error message
    else:
        return "File type not supported\n"

    # creates spellchecker object
    spell = SpellChecker()

    #adds special words to the dictionary
    if(unflag!=None):
        spell.word_frequency.load_words(unflag)
    
    #runs spell checker and puts misspelled words in a list
    misspelled=list(spell.unknown(wordList))              
    if misspelled[0]=='': return "No mistakes\n"
    
    # creates output             
    if(isJson): 
        mpKeys=[]
        for i, word in enumerate(misspelled):
            
            try:                                                
                mpKeys.append(keyList[wordList.index(word)])                    
            except(ValueError):
                mpKeys.append(keyList[wordList.index(word.capitalize())]) 
            
            
            result+=f"{misspelled[i].ljust(20)} {spell.correction(misspelled[i]).ljust(20)}Key:{mpKeys[i]}\n"
          
    else:
        for i, word in enumerate(misspelled):
            result+=f"{misspelled[i].ljust(20)} {spell.correction(misspelled[i]).ljust(20)}\n"
    
    return result

def SpellCheck(fileName, unflag=None, outputFile=None):
    if outputFile==None:
        outputFile="sp_result_" + datetime.now().strftime("%d_%m_%Y_%H_%M_%S") +".txt"
    output=open(outputFile, 'w')
    print(SpellCheckHelp(fileName, unflag=unflag), file=output)
    output.close()



# Runs SpellChecker() on each file in a folder and returns an output file. Uses multithreading.
# Parameters: Name of folder, words to exclude (optional), output file(optional)
def SpellCheckF(folderName, unflag=None, outputFile=None):
    if outputFile==None:
        outputFile="sp_result_" + datetime.now().strftime("%d_%m_%Y_%H_%M_%S") +".txt"
    output=open(outputFile, 'w')
    
    files=os.scandir("New Folder")
   
    str_files=[]
    for f in files:
        str_files.append(f.path)

    with concurrent.futures.ThreadPoolExecutor() as executor:
        results=executor.map(lambda p:SpellCheckHelp(p, unflag=unflag), str_files)
        for n,result in enumerate(results):
            print(f"File {n+1}: {str_files[n]}",file=output)
            print(result, file=output)
    output.close()
            
            
       
