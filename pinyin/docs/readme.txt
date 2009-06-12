#################################################################################
###                   Mandarin-Chinese Pinyin Toolkit (PyKit)                 ### 
###                          Version 0.05 (__/06/2009)                        ###
###                           pinyintoolkit@gmail.com                         ###
#################################################################################
# A Plugin for the Anki Spaced Repition learning system <http://ichi2.net/anki/>#
# Copyright (C) 2009 Nicholas Cook & Max Bolingbroke                            #
# Free software Licensed under GNU GPL                                          #
#################################################################################

       YOU ARE STRONGLY ADVISED TO READ THE INSTALATION INSTRUCTIONS
         NOT DOING SO MAY MEAN YOU MISS OUT ON CORE PYKIT FEATURES

=== Contact Info ================================================================
Email (to all authors):                pinyintoolkit@gmail.com    
Website:                               http://batterseapower.github.com/pinyin-toolkit/

=== Features ====================================================================
The Pinyin Toolkit, or PyKit (pronounced 'Pie-Kit') adds many useful features to
Anki to assist the study of Mandarin. The aim of the project is to greatly enhance
the user-experience for students studying Chinese language.

PyKit's core features include:
 1) improved automatic pinyin generation using a dictionary to guess the reading
 2) colorization of pinyin according to tone              (to assist visual learners)
 3) colorization of Hanzi according to tone               (to assist visual learners)
 4) text-to-speech conversion and 'multi-voice' support   (to assist auditory learners)
 5) advanced hybrid locl/dictionary lookup for Engish, German, and (limited) French
 6) generic web-based lookup for any other language
 7) automatic transcription of measure words (MW) into their own field
 8) mass-fill to populate any missing data from any fact in the deck
 9) Hanzi graph (shows the number of unique characters learned) [ported from Kanzi Graph]

A number of other smaller improvesments and conveniences are also included:
 -  support for a large number of field-names ('Hanzi','Pinyin',etc) and the ability to customise
 -  addition of meaning index numbers for dictionary entries
 -  option to chose either number or tone-mark output
 -  the automatic blanking of auto-generated fields if there is no expression 
 -  shortcut support to change colors using control+Fx keys, matching the tones
 -  automatic downloading of a suitable voice audio-pack to use with text-to-speech
 -  much greater support of non-standard field names ( "Hanzi", 英语" and so on)
 -  support for user dictionaires (to customise translated or pinyin rendering)

 ... to be followed in the future by a raft of forthcoming features!


=== QuickStart (New Deck) =======================================================

1) Click on Anki's "File" -> "Download" -> "Shared Plugin" and select "Pinyin Toolkit"
   Restart Anki to enable plugin.

3) Click on Anki's "File" -> "Download" -> "Shared Deck" and select Pinyin Toolkit simple or advanced.

4) Click on Anki's "Tools" -> "Pinyin Toolkit" -> "Preferences" click "Audio" and then "Install Free Mandarin Sound Pack"


   Edit your cards and start studying!
   

* IT IS STRONGLY SUGGESTED YOU FOLLOW THE STEPS IN docs-audio.txt TO IMPROVE AUDIO SUPPORT! *



=== Full Installation (Customise Deck) ==========================================

It is recomended that you experiment with the sample deck first, as in the QuickStart.
This allows you to understand how to best use the new features.

1) Click on Anki's "File" -> "Download" -> "Shared Plugin" and select "Pinyin Toolkit"
2) Ensure your model has the tag "Mandarin"
3) Ensure your model has fields that represent the following items:
        a) "Expression" i.e. "Expression", "Hanzi", "Chinese", "汉字", "中文"
        b) "Reading" i.e. "Reading", "Pinyin", "PY", "拼音"
        c) "Meaning" i.e. "Definition", "English", "German", "French", "意思", "翻译", "英语", "法语", "德语"

4) To use character colorization:
  - ensure your model has a field called "Color" to populate with colored characters
  - edit your models to use the new field
  - The best way to do this is:
        a) format questions with B&W characters
        b) show colored characters in answers where you are not testing reading or tones. 
  - You can also download the Kanji stroke order font to get limited stroke-order support (http://sites.google.com/site/nihilistorguk/)

5) To activate sound tag generation:
  - ensure your model has a field called "Audio"
  - obtain audio files in the format "ni3.ogg", "hao3.ogg" (you can use .ogg, .wav and .mp3 files by default)
    * You can use "Tools" > "Download Mandarin sound samples" to automatically install a sample set
  - better quality audio can be found online. See the file "getaudio.txt" for instructions
  - these files should be placed in "[AnkiPluginDirectory]/pinyin/media/[ChooseAName]".
    If you use the builtin option to download the Mandarin Sounds they will be automatically installed here.
  - finally, add your field to your card template  model %(Audio)s to the HTML generated from your model


*** IT IS STRONGLY SUGGESTED YOU FOLLOW THE STEPS IN getaudio.txt TO IMPROVE AUDIO SUPPORT! ***


You can customise the plugin by selecting "Tools" -> "Pinyin Toolkit" -> "Preferences"
If you plan not to use certain features then you should turn them off to decrease memory usage.


=== Feature Guide & Design Notes ================================================
This section provides some notes on development methodology and explains why some features have been implimented as they have.
It is just an outline at present and needs to be rewritten properly and expanded.

1) Colorisation
Having studied Chinese for several years, it became apparnet to me that it was extremly difficult to remember the tone for a given Hanzi.

It came to be that it would be very useful to colorise the pinyin and the characters in order to remember them.
I looked on the internet to see if others had developed this idea. At the time I only came across:
     Laowai Chinese (老外中文) http://laowaichinese.net/color-coded-tones-on-mdbg.htm

Some time after implementing this for my own studies MDBG started offering the feature in CEDICT http://www.mdbg.net/


2) Text-to-Speech
One of the main ideas behind the PyKit is that it is much easier to learn a language when you can hear it.
Mandarin is an idea language for text-to-speech conversion because there are a relatively small number of unique sounds (around a thousand)

The plugin allows the user to download the Chinese-Lessons Sample audio files automatically.
However, there are better audio fles available if you are prepared to look for them.
To save you some time you can find a list giving this information to you below.

=Mono-sylabic=
ChineseLessons.com                  [n=1,189]   .mp3    [average quality]          http://www.chinese-lessons.com/download.htm
ChinesePod.com free pinyin tool     [n=1,627]   .mp3    [licensing restrictions]   http://chinesepod.com/resources/pronunciation
SWAC Audio Files                    [n=1,000]   .ogg    [need renaming script]     http://swac-collections.org/download.php
WenLin Audio Files                  [n=1,675]   .wav    [commercial license]       http://www.wenlin.com/

The reccommended audio files are the ChinesePod.com files. They are distributed freely at the above link but licensing prevents us from including them.
If you want to upgrade to these files then go to the webpage, download the files (keep a copy!) and place them in your media directory, replacing any files there already. 

In the future PyKit will support complex word packs such as "ni2hao3.ogg" but for now the information below is just for reference.

If you have multiple audio packs installed Pinyin Toolkit will choose the best one for this piniyn.
If there are several possible media packs then a random choice will be made (allowing you to have different voices in your deck).


3) Third Tone Sandhi
There is limited support for the third tone Sandhi.
(3,3) is turned into (2,3) in audio.
Some attempt is made to deal with (3,3,3) however it is likely to be wrong (as it is largely based on context).

Future support will include using a lighter green for the tone sandhi and support for other tone change rules.


4) erhua
erhua receives special treatemnt and will be merged with the word it is attched to.
Obviously there is no audio support for erhua [sorry!]


5) Auto-Blanking
DEBUGME


6) Dictionary Notes
    CC-CEDICT

    HanDeDict and CFDICT
    note the two versions, cfdict_nb.u8 and cfdict.u8 and cfdict_nb.u8 (the former has examples the latter doesn't)
    for now we are using cfdict_nb.u8 as we have no support for examples (it is handled well by the Chinese Example Plugin)

See also the licensing section below.



7) Pinyin Spacing
At present pinyin is spaced by sound units. There are future plans to support correctly spaced words and True Pinyin mode.

Reference:  http://www.cjkware.com/2008/po1.html


8) User Dictionaries
                            
To add your own dictionary entries, create a file called "dict-userdict.txt" in the pinyin/ subdirectory
Copy the format of the other dictionaires, i.e:
    <simplified-without-spaces> <traditional-without-spaces> [<pinyin> ... <pinyin>] /<meaning>/.../<meaning>/

Entries should be separated by spaces.

Here are some examples:
一一 一一 [yi1 yi1] /one by one/one after another/
一共 一共 [yi1 gong4] /altogether/

Note that you can omit the meaning and surrounding "/"s but everything else is required:
一一 一一 [yi1 yi1]
一共 一共 [yi1 gong4]


=== Changelog ===================================================================
===       The authors can be contacted at: pinyintoolkit@gmail.com            ===

Development Version:             http://batterseapower.github.com/pinyin-toolkit/


Version 0.05   (05/06/2009)  Max Bolingbroke <batterseapower@hotmail.com>
                             Nick Cook       <nick@n-line.co.uk>            [http://www.n-line.co.uk]

* Large-scale re-write and optimisation of the code by Max Bolingbroke (many thanks!)
* Automatic translation of non-dictionary words & phrase [can be used for almost any language]
* Add [limited] support for new CFDICT (French)
* All distributions will now include all dictionaries for simplicity. Unwanted dictionaries can be deleted.
* MW with pinyin added automatically to your deck if in dictionary (if enabled) only applies to English version
* Dictionary definition and measure word have their simplified/traditional variant selected according
  to user preferences
* Don't generate audio tags if sounds are missing
* Use a fifth tone audio sample if one is provided, otherwise switch to 4th tone
* Try several file extensions when we need a bit of audio, using the order: .mp3, .ogg, .wav
* Optional entry-number indictaors in translations such as "(1)" "(2)" "(3)"
* Internal refactoring of code to remove the incidence of unreliable string manipulations, leading to bugfixes:
  - Remove space at the end of colored pinyin
  - Remove spaces between punctuation in pinyin
  - Remove the space between erhua "r" suffix and main word in pinyin
  - Prevent loss of punctuation when colorizing charactersne
* erhua and third tone sandhi now handled properly
* line-index support and seperator support added for dictionary lookup
* ported KanjiGraph to Hanzigraph
* Squash bug that means character colorisation to fail if audio generation off
* Pinyin is recognised and colored anywhere in the text
* Added code testsuite
* Preferences window now used for config
* Many smaller modifications to improve usability
* Improved documentation & launch of website


Version 0.04   (19/05/2009)  Nick Cook <nick@n-line.co.uk>  [http://www.n-line.co.uk]

* Two versions are now being distributed: English (using CC-CEDICT) and German (using HanDeDict)
   - Thanks to Rainer Menes for suggesting use of HanDeDict
* New character colorization feature
   - If enabled, colored hanzi will be generated and placed in a field called "Color"
   - to get the benefit of this you should alter models in a way to make use of colored Hanzi
* Fix to give better handle the formatting of dictionary entries
   - customisable dictionary meaning separator (defaults to line break)
* more reliable sound tag generation
* automatic blanking feature if hanzi field is emptied and de-focused (makes input faster)
   - audio field is ignored if longer than 40 characters (i.e. if Anki has improved or recorded audio) [a better way to do this is in the works]
* strip html from expression field before doing anything (prevents formating bugs)
* several minor fixes and improvements to general usage


Version 0.03   (12/05/2009)  Nick Cook <nick@n-line.co.uk>  [http://www.n-line.co.uk]

* Simplified and traditional generation now happens each lookup (no need to chose one or the other)
* automatic English generation from dictionary
  - English will only be generated for exact matches (words) not phrases
* automatic colorization of pnyin by tone
* Text-to-speech feature (automatic auto generation)
* support for turning off new features
* tidy code (remove unused & rationalise messy bits)
* update dictionary to latest CC-CEDICT
  - fix bug from 谁 [actually bug is no longer relevant under new directory structure]
  - fix problems with pinyin generation of "v"/"u:"
* rearrange to more logical filenames (pinyinfetcher.py etc)
* change dictionary structure for better management, easier updates, and to allow new features
   - split dictionary into 3 parts (CC-CEDICT, supplementary, and user) [entries prioritised from latter to former]
   - supplementary dictionary contains previously hard-coded entries and new data such as numbers

Version 0.02.5 (21/03/2009)   Nick Cook <nick@n-line.co.uk>  [http://www.n-line.co.uk]
* Dictionary updated to use adapted version of CC-CEDICT
* entries increasing from 44,783 to 82,941

Version 0.02   (03/2009)   Damien Elmes  [http://ichi2.net/]
* Ported to Anki 0.9.9.6 and tidied up
* Brian Vaughan no longer maintaing plugin

Version 0.01   (2008)    Brian Vaughan [http://brianvaughan.net]
* Original release

NOTE: Version 0.01 to 0.03 had version numbers assigned retroactively.


=== Licensing ===================================================================

                             == PyKit==

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.

                              == Dictionaries ==
                              
Chinese-English CC-CEDICT, available at: <http://www.mdbg.net/chindict/chindict.php?page=cc-cedict>
Licensing of CC-CEDICT is Creative Commons Attribution-Share Alike 3.0 <http://creativecommons.org/licenses/by-sa/3.0/>

Chinese-German dictionary HanDeDict, available at: <http://www.chinaboard.de/chinesisch_deutsch.php?mode=dl>
Licensing of HanDeDict is  Creative Commons Attribution-Share Alike 2.0 Germany <http://creativecommons.org/licenses/by-sa/2.0/de/>

Chinese-French dictionary CFDICT, available at <http://www.chinaboard.de/cfdict.php?mode=dl>
Licensing of CFDICT is Creative Commons Attribution-Share Alike 2.5 French <http://creativecommons.org/licenses/by-sa/2.5/fr/>

Japanese-English dictionary EDICT, available at <http://www.csse.monash.edu.au/~jwb/j_edict.html>
Licensing of EDICT is Createive Commons Attribut-Share Alike 3.0 Unported <http://www.edrdg.org/edrdg/licence.html>

                               == Audio Files ==
                               
Mandarin Sounds, available at: <http://www.chinese-lessons.com/download.htm>
Licensing of Mandarin Sounds is Creative Commons Attribution-Noncommercial-No Derivative Works 3.0 United States <http://creativecommons.org/licenses/by-nc-nd/3.0/us/>

SWAC Audio Collection, available at: <http://creativecommons.org/licenses/by/2.0/fr/deed.en_US>
Licensing is Creative Commons Attribution 2.0 France <http://creativecommons.org/licenses/by/2.0/fr/deed.en_US>

