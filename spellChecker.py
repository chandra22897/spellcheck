# requires pyspellchecker library (pip install pyspellchecker)
# Contains two functions, SpellChecker checks one file, SpellCheckerF checks a folder of files

# SpellChecker function, checks spelling of values in a file
# Parameters: Name of file, values to exclude (optional), output file(optional), file number (shouldn't be edited)
def SpellChecker(fileName, unflag=None, outputFile="sp_result.txt", num=-1): 
    from spellchecker import SpellChecker

    #create lists for words, list for keys and boolean if json
    wordList=[]
    
    isJson=False
    keyList=[]
    f=open(fileName)
    if(num>0): 
        output=open(outputFile, "a")  
        print("\n", file=output)
    else:output=open(outputFile, "w")

    if(num!=-1):
        print("File", num+1, fileName, file=output)


    #for plain text files without formatting
    if (fileName[len(fileName)-4:]==".txt"):
        
        
        s=f.read()
        wordList=s.split(" ")
        f.close()

    #for json files
    elif (fileName[len(fileName)-5:]==".JSON"):           
        isJson=True
        import json
        
        dic=json.load(f)                               #dictionary containing list containing dictionary
        f.close()

        for i in dic:
            # wordList.append(i)                         
            for j in dic[i][0]:
                keyList.append(j)
                wordList.append(dic[i][0][j])
        
        #in case of multiple words 
        n=0
        while(n<len(wordList)):
            
            str=wordList[n]
            L=wordList[n].split()
            
            if(len(L)>1):
                i=len(L)-1
               
                while (i>=0):                  
                    wordList.insert(n,L[i]) 
                    keyList.insert(n,keyList[n])                  
                    i-=1
                wordList.remove(str)        
                keyList.remove(keyList[n])
            n+=1

    # Error message
    else:
        print("File type not supported", file=output)
        return

    #Run spellcheck on word wordList
    
    spell = SpellChecker(distance=1)
    spell = SpellChecker()

    #adds special words to the dictionary
    if(unflag!=None):
        spell.word_frequency.load_words(unflag)
    
    #runs spell checker and puts misspelled words in a list
    misspelled=list(spell.unknown(wordList))              

    # creates output             
    if(isJson): 
        mpKeys=[]
        for i, word in enumerate(misspelled):
            
            try:                                                
                mpKeys.append(keyList[wordList.index(word)])                    
            except(ValueError):
                mpKeys.append(keyList[wordList.index(word.capitalize())]) 
            
            
            print(misspelled[i].ljust(20), spell.correction(misspelled[i]).ljust(20), "Key: ", mpKeys[i], sep="", file=output)
          
    else:
        for i, word in enumerate(misspelled):
            print(misspelled[i].ljust(20), spell.correction(misspelled[i]),sep="", file=output)

    output.close()
    return misspelled
 
# Runs SpellChecker() on each file in a folder
# Parameters: Name of folder, words to exclude (optional), output file(optional)
def SpellCheckerF(folderName, unflag=None, outputFile="sp_result.txt"):
    import os 
    for n,file in enumerate(os.scandir(folderName)):
        SpellChecker(file.path, unflag=unflag, num=n, outputFile=outputFile)
  



