#!/usr/bin/python
#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
pinyinfetcher.py (formally pinyinconverter.py)

gets pinyin from chinese characters based on a modified version of the CC-cedict dictionary

relies on "pinyinmodifier.py" (a modified version of "pinyintones.py" from
http://www.robertyu.com/wikiperdido/Pinyin_Parser_for_MoinMoin )
to transform pinyin.

this class is written for a plugin addonfor the Anki srs flashcard software: www.ichi2.net/anki/

2009  modifications and additions by Nick Cook <nick@n-line.co.uk>
2008 by Brian Vaughan (http://brianvaughan.net)

"""

import os
from ankiqt import mw
import re
import codecs
import pinyinmodifier


"""
PinyinFetcher

Use an instance of this class to add pinyin to utf-8 chinese strings.

instantiation reads the dictionary file into memory, so, obviously, ideally
this will be read once, reused, and then eventually the instance will be
garbage collected.
"""
class PinyinFetcher :
    def __init__( self,
                  colorize = True,
                  tonify = True,
                  dictnotpy=False,audiogen=False,endictsep="<br />",dictlanguage="en"):

        plugindir = mw.pluginsFolder()
        plugindir = os.path.join(plugindir, "pinyin")
        dictsupp = os.path.join(plugindir,'dict-supplimentary.txt')
        dictuser = os.path.join(plugindir,'dict-userdict.txt')

        if (dictnotpy): # if in translate mode then determine which language to use
            dictindexline = 1
            if dictlanguage=="en":
                dictmain = os.path.join(plugindir,'dict-cc-cedict.txt')
            elif dictlanguage=="de":
                dictmain = os.path.join(plugindir,'dict-handedict.txt')
            elif dictlanguage=="fr":
                dictmain = os.path.join(plugindir,'dict-cfdict.txt')
            else: # if no dictionary for this language use pinyin only dictionary (faster)
                dictmain = os.path.join(plugindir,'dict-pinyin.txt')
        else: #use HanDeDict in blanked mode if just pinyin (more entries)
            dictindexline = 0
            dictmain = os.path.join(plugindir,'dict-cc-cedict.txt')

        #Create main dictionary (check for translateion language, otherwise use English)

        
        self.dictionary = dict()
          
        # Set up the options
        if( colorize ) :
            self.colorizer = pinyinmodifier.PinyinToneColorizer()
        else :
            self.colorizer = None
        if( tonify ) :
            self.tonifier = pinyinmodifier.PinyinToneFixer()
        else :
            self.tonifier = None      
        if( audiogen ) :
            self.AudioMod = pinyinmodifier.AudioMod()
        else :
            self.AudioMod = None
        
        # Set the index depending on whether Pinyin lookup (or Meaning lookup)
        self.dictionary = dict()


        # This block builds an array in self.dictionary so that the resulting meaning can be looked up
        # The dictionary will be return pinyin or english depending on dictindexline
        self.dictionary = self.dictbuild(dictmain,dictindexline,self.dictionary,endictsep)
        self.dictionary = self.dictbuild(dictuser,dictindexline,self.dictionary,endictsep)
        self.dictionary = self.dictbuild(dictsupp,dictindexline,self.dictionary,endictsep)


    def dictbuild(self,dictfile,dictindexline,localdictionary,lookuplang="pinyin"):
        file = codecs.open(dictfile,"r",encoding='utf-8')
                
        for text in file :            
            # cut around first space to get simplified and traditional entry   
            simptrad = text.split(None,1)
            if not len(simptrad)==2:
                continue
            # extract the pinyin
            pystartpos=text.find("[")+1
            pyendpos=text.find("]")
            pinyin=text[pystartpos:pyendpos]
            
            # extract the translation (from the second ] plus several few spaces
            translationstart=pyendpos+3 # (to jump over the "] /")
            translationend=len(text)-3
            translation=text[translationstart:translationend]

            
            # create an array containing the dictionary entry
            dictionaryitem=[simptrad[0],simptrad[1],pinyin,translation]


            n=dictindexline+2 #temp fix until I change the way it requests 
            localdictionary[dictionaryitem[0]] = dictionaryitem[n]
            localdictionary[dictionaryitem[1]] = dictionaryitem[n]


            """        
            # temporary transtition fiddle to make dictindexline work
            if dictindexline==1:
                lookuplang="english"
            else:
                lookuplang="pinyin" # i.e. lookup for 0, as before
            lookuplang="pinyin"
            

            if lookuplang=="pinyin":
                localdictionary[dictionaryitem[0]] = dictionaryitem[3]
                localdictionary[dictionaryitem[1]] = dictionaryitem[3]
            elif lookuplang=="swaphanzi":
                localdictionary[dictionaryitem[0]] = dictionaryitem[1]
                localdictionary[dictionaryitem[1]] = dictionaryitem[0]
            else: # assume lookup translation if another language code            
                localdictionary[dictionaryitem[0]] = dictionaryitem[4]
                localdictionary[dictionaryitem[1]] = dictionaryitem[4]
            """
        file.close()            
        return localdictionary

        """# Old version of code [very messy] 
        if len(simptrad) == 2 :
            # then use the square bracket to split pinyin from meaning
            tempstring = line[2].split("]",1)
            #if this line of the dictionary has only pinyin (no english so split won't work) then define it as an array [bit of a fiddle] 
            if len(tempstring) < 2:
                tempstring = [line[2],""]
            # tidy translated dictionary entry so that it looks pretty 
            tempstring[1] = tempstring[1].strip("\n").replace("  "," ").replace(" /","/").replace("/ ","/").lstrip("/").rstrip("/").rstrip(" ")
            tmp = tempstring[1].split("/") 
            tempstring[1] = tempstring[1].replace("/",endictsep,(len(tmp)-2)).replace("/","")
            
            
            
            # save the dictionary value in the localdictionary array and then return it
            if dictindexline <= len(tempstring) :
                localdictionary[ line[0] ] = tempstring[dictindexline].strip("[").strip("]")
                localdictionary[ line[1] ] = tempstring[dictindexline].strip("[").strip("]")
        """


    def getPinyin(self, sentence,wordlookuponly=False,colchar=False,removetones=False,audioextension=".mp3",dictlanguage="en") :
        if sentence == None or len( sentence ) == 0 :
            return u""
        reading = u""
        assert type(sentence)==unicode
        sentence=re.sub('<(?!(?:a\s|/a|!))[^>]*>','',sentence) #strip html (otherwise formatting code breaks all lookups)

        #iterate through the text
        i=0
        senlen = len(sentence)
        while i < senlen :
            word = u""
            j=i+1

            #if it's not the start of the line, pad between pinyin,
            #or after punctuation marks
            if i != 0:
                if i != senlen:
                    if( reading != "" ) :
                        reading += ' '

            if(wordlookuponly): 
                if reading != "": 
                    if i != 0:
                        reading = u""
                        return reading
                                                
            #look for progressively bigger multi-syllabic chinese words                
            while j <= len ( sentence ) :
                if self.dictionary.has_key( sentence[ i:j ] ) :
                    word = sentence[i:j]
                    #try again with a bigger word
                    j+=1

                #if it's a single character and not found it's likely whitespace or puncuation, add to reading
                # Add a space and a 5th tone so that it will be dealt with properly during colorisation
                # This needs to be done as otherwise pinyin and character colorisation will be out of step
                elif len ( sentence[ i:j ] ) == 1 :
                    word = sentence[ i:j ] +5
                    #increment to the next character
                    j+=1                    
                else :
                    break
            if word != "" :
                #look up the pinyin and add it to the reading
                reading += self.dictionary[ word ]
                i+= len( word )            
            

        if (colchar):        
            i=0
            assert type(reading)==unicode
            pinyinsplit = reading.split(" ")              
            reading=u""
            while i != len(pinyinsplit) :
                j=i+1
                t=1               
                while t < 6: # adds a tone number to each character followed by a space so that it can be recognised by the coloriser
                    s=str(t)
                    if pinyinsplit[i].endswith(s) :
                        reading += sentence[i:j] + s + " "
                    t+=1
                i+=1
            removetones=True  
            removespaces=True  
        if self.AudioMod != None:
            reading = self.AudioMod.Generate (reading,audioextension)
            return reading
        if self.colorizer != None:
            reading = self.colorizer.ColorizePinyin (reading)
        elif (colchar):
            
            reading = self.colorizer.ColorizePinyin (reading)
        if self.tonifier != None :
            reading = self.tonifier.ConvertPinyinToneNumbers(reading)
        # in pinyin (not character) do special substituion for the erhua (r) at ends of words
        reading = reading.replace(' r5 ','r')
        # DEBUGME - add a substitution for the colored erhua replacement
        if (removetones):
            reading = reading.replace("1 ","").replace("2 ","").replace("3 ","").replace("4 ","").replace("5 ","")
        
        reading = reading.replace('</span> ','</span>') # remove the invisible double spaces created by character colorisation
        return reading


