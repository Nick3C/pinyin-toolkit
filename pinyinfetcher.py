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
                  dictnotpy=False,audiogen=False,endictsep="<br />",diclang="English"):

        plugindir = mw.pluginsFolder()
        plugindir = os.path.join(plugindir, "pinyin")

        #Create main dictionary (check for German option, otherwise use English)
        if diclang=="German":
            dictmain = os.path.join(plugindir,'dict-handedict.txt')
        else:
            dictmain = os.path.join(plugindir,'dict-cc-cedict.txt')
        #Then append / replace entries using supplemntary dictionary [some functionality requires this line!]
        dictsupp = os.path.join(plugindir,'dict-supplimentary.txt')
        #Finally append the user dictionary
        dictuser = os.path.join(plugindir,'dict-userdict.txt')
        
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
        if(dictnotpy):
            dictindexline = 1
        else:
            dictindexline = 0

        # This block builds an array in self.dictionary so that the resulting meaning can be looked up
        # The dictionary will be return pinyin or english depending on dictindexline
        # As they are built sequentially the sequence of increasing importance is: user, supp, main (as it need to be to work)
        self.dictionary = self.dictbuild(dictmain,dictindexline,self.dictionary,endictsep)
        self.dictionary = self.dictbuild(dictsupp,dictindexline,self.dictionary,endictsep)
        self.dictionary = self.dictbuild(dictuser,dictindexline,self.dictionary,endictsep)



    def dictbuild(self,dictfile,dictindexline,localdictionary,endictsep="<br />"):
        file = codecs.open(dictfile,"r",encoding='utf-8')
                
        for text in file :
            # first split simp, trad, and everything else
            line = text.split(None,2)       
            if len(line) == 3 :
                # then use the square bracket to split pinyin from meaning
                tempstring = line[2].split("]",1)
                #if this line of the dictionary has only pinyin (no english so split won't work) then define it as an array [bit of a fiddle] 
                if len(tempstring) < 2:
                    tempstring = [line[2],""]
                # tidy English so that it looks pretty [I think German doesn't need this, check]
                tempstring[1] = tempstring[1].strip("\n").replace("  "," ").replace(" /","/").replace("/ ","/").lstrip("/").rstrip("/").rstrip(" ")
                tmp = tempstring[1].split("/") 
                tempstring[1] = tempstring[1].replace("/",endictsep,(len(tmp)-2)).replace("/","")
                
                # save the dictionary value in the localdictionary array and then return it
                if dictindexline <= len(tempstring) :
                    localdictionary[ line[0] ] = tempstring[dictindexline].strip("[").strip("]")
                    # index traditional as well
                    if line[0] != line[1] :                    
                        localdictionary[ line[1] ] = tempstring[dictindexline].strip("[").strip("]")

        file.close()
        return localdictionary

    def getPinyin(self, sentence,wordlookuponly=False,colchar=False,removetones=False,audioextension=".mp3") :
        if sentence == None or len( sentence ) == 0 :
            return u""
        i=0;
        assert type(sentence)==unicode
        #strip html (otherwise formatting code breaks all lookups)
        sentence=re.sub('<(?!(?:a\s|/a|!))[^>]*>','',sentence)
        reading = u""
        #iterate through the text
        while i < len ( sentence ) :
            word = u""
            j=i+1
            
            # if in English/German mode and a word has already been found (i.e. a phrase) then return nothing
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
                    reading += " " + sentence[ i:j ] +5
                    #increment to the next character
                    i=j
                    break
                    
                else :
                    break
            if word != "" :
                #look up the pinyin and add it to the reading
                reading += self.dictionary[ word ]
                i+= len( word )            
            
                #if it's not the start of the line, pad between pinyin,
                #or after punctuation marks
                if( reading != "" ) :
                    reading += ' '


        if (colchar):        
            i=0
            assert type(reading)==unicode
            pinyinsplit = reading.split(" ")              
            reading=u""
            while i != len(pinyinsplit) :
                j=i+1
                t=1               
                while t < 6:
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

