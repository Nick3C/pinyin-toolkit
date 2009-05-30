#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
pinyinmodifier.py

Parser class to diacritical marks to numbered pinyin and add tone colorization.
* 2009 modifications by Nick Cook <nick@n-line.co.uk> (http://www.n-line.co.uk)
  - new colorization feature
  - new audio generation feature [still buggy]
* 2008 modifications by Brian Vaughan (http://brianvaughan.net)
* 2007 originaly version by Robert Yu http://www.robertyu.com

in turn Inspired by Pinyin Joe's Word macro (http://pinyinjoe.com)
"""

import codecs

class PinyinToneFixer :
    def __init__(self) :
        #
        # definitions
        # For the pinyin tone rules (which vowel?), see
        # http://www.pinyin.info/rules/where.html
        #
        # map (final) constanant+tone to tone+constanant
        self.mapConstTone2ToneConst={'n1':'1n',
                        'n2':'2n',
                        'n3':'3n',
                        'n4':'4n',
                        'ng1':'1ng',
                        'ng2':'2ng',
                        'ng3':'3ng',
                        'ng4':'4ng',
                        'r1':'1r',
                        'r2':'2r',
                        'r3':'3r',
                        'r4':'4r'}

        #
        # map vowel+vowel+tone to vowel+tone+vowel
        self.mapVowelVowelTone2VowelToneVowel={'ai1':'a1i',
                                  'ai2':'a2i',
                                  'ai3':'a3i',
                                  'ai4':'a4i',
                                  'ao1':'a1o',
                                  'ao2':'a2o',
                                  'ao3':'a3o',
                                  'ao4':'a4o',
                                  'ei1':'e1i',
                                  'ei2':'e2i',
                                  'ei3':'e3i',
                                  'ei4':'e4i',
                                  'ou1':'o1u',
                                  'ou2':'o2u',
                                  'ou3':'o3u',
                                  'ou4':'o4u'}

        # map vowel-number combination to unicode hex equivalent
        self.mapVowelTone2Unicode={'a1':u'\u0101',
                      'a2':u'\u00e1',
                      'a3':u'\u01ce',
                      'a4':u'\u00e0',
                      'e1':u'\u0113',
                      'e2':u'\u00e9',
                      'e3':u'\u011b',
                      'e4':u'\u00e8',
                      'i1':u'\u012b',
                      'i2':u'\u00ed',
                      'i3':u'\u01d0',
                      'i4':u'\u00ec',
                      'o1':u'\u014d',
                      'o2':u'\u00f3',
                      'o3':u'\u01d2',
                      'o4':u'\u00f2',
                      'u1':u'\u016b',
                      'u2':u'\u00fa',
                      'u3':u'\u01d4',
                      'u4':u'\u00f9',
                      'v1':u'\u01db',
                      'v2':u'\u01d8',
                      'v3':u'\u01da',
                      'v4':u'\u01dc',
                      'u:1':u'\u01db',
                      'u:2':u'\u01d8',
                      'u:3':u'\u01da',
                      'u:4':u'\u01dc'}

        #don't want "5"'s in output for neutral tone
        self.remove5thToneNumber = {
                      'a5':u'a',
                      'e5':u'e',
                      'i5':u'i',
                      'o5':u'o',
                      'u5':u'u',
                      'v5':u'\u01D6',
                      'u:5':u'\u01D6',
                      'n5':u'n',
                      'g5':u'g',
                      'r5':u'r'}

    """
    Convert pinyin text with tone numbers to pinyin with diacritical marks
    over the appropriate vowel.

    In:  input text.  Must be unicode type.
    Out:  utf-8 copy of lineIn, tone markers replaced with diacritical marks
          over the appropriate vowels

    For example:
    xiao3 long2 tang1 bao1 -> xiǎo lóng tāng bāo

    x='xiao3 long2 tang1 bao4'
    y=PinyinToneFixer().ConvertPinyinToneNumbers(x)
    """
    def ConvertPinyinToneNumbers(self, lineIn):

        #
        # make sure input is unicode
        assert type(lineIn)==unicode
        lineOut=lineIn


        #
        # first transform
        for (x,y) in self.mapConstTone2ToneConst.items():
            lineOut=lineOut.replace(x,y)

        #
        # second transform
        for (x,y) in self.mapVowelVowelTone2VowelToneVowel.items():
            lineOut=lineOut.replace(x,y)


        # remove "5"s for qing sheng.. needs to be done before fancy
        #characters are added.
        for (x,y) in self.remove5thToneNumber.items():
            lineOut=lineOut.replace(x,y)


        #
        # third transform
        for (x,y) in self.mapVowelTone2Unicode.items():
            lineOut=lineOut.replace(x,y)

        return lineOut

class PinyinToneColorizer :
    def ColorizePinyin(self, lineIn):
        tonecolor=["black","#ff0000","#ffaa00","#00aa00","#0000ff","#545454","#ffff00"]       
        lineOut= ""
        assert type(lineIn)==unicode
        tmpsplit = lineIn.split()
        i = 0 
        while i != len(tmpsplit) :
            t=1
            while t < 6:
                s=str(t)
                if tmpsplit[i].endswith(s) :
                    lineOut += '<span style="color:' + tonecolor[t] + '">' + tmpsplit[i] + ' </span>'
                t+=1
            i+=1
            if i < len(tmpsplit) :
                lineOut += ' '
        return lineOut 

class AudioMod :
    def Generate(self, lineIn,audioextension='.mp3'):
        assert type(lineIn)==unicode
        lineOut = u""
        tmpsplit = lineIn.split()
        i = 0      
        while i != len(tmpsplit) :
            tmplen=len(tmpsplit[i])
            # replace 5 with 4 in order to deal with lack of '[xx]5.ogg's
            if tmpsplit[i].endswith('5') :
                tmpsplit[i] = tmpsplit[i].replace('5','4')
            # remove the 儿 （r) from pinyin [too complicated to handle automatically]
            if tmpsplit[i]=="r5":                
                tmpsplit[i]=""                                  
            # only generate for word between 2 and 6 characters (pinyin length)
            if tmplen >=2:
                if tmplen <=6 :
                    #[add feature here] check if exist(file):
                    lineOut += '[sound:' + tmpsplit[i] + audioextension +']'
            i+=1

        return lineOut
    