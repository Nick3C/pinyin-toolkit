#################################################################################
###                   Mandarin-Chinese Pinyin Toolkit (PyKit)                 ### 
###                          Version 0.05 (__/06/2009)                        ###
#################################################################################
# A Plugin for the Anki Spaced Repition learning system <http://ichi2.net/anki/>#
# Copyright (C) 2009 Nicholas Cook & Max Bolingbroke                            #
# Free software Licensed under GNU GPL                                          #
#################################################################################

       YOU ARE STRONGLY ADVISED TO READ THE INSTALATION INSTRUCTIONS
         NOT DOING SO MAY MEAN YOU MISS OUT ON CORE PYKIT FEATURES


=== Features ====================================================================
The Pinyin Toolkit, or PyKit (pronounced 'Pie-Kit') adds many useful features to
Anki to assist the study of Mandarin. The aim of the project is to greatly enhance
the user-experience for students studying Chinese language.

PyKit's core features include:
 1) improved automatic pinyin generation using a dictionary to guess the reading
 2) colorization of pinyin according to tone (to assist visual learners)
 3) colorization of Hanzi according to tone (to assist visual learners)
 4) text-to-speech conversion to assist (auditory learners)
 5) advanced dictionary lookup for Chinese into Engish, German, and French
 6) machine-translation of non-dictionary words and phrases using online tools
 7) automatic transcription of measure words (MW) into their own field

A number of other smaller improvesments and conveniences are also included:
 -  option to chose either number or tone-mark output
 -  the automatic blanking of auto-generated fields when 
 -  shortcut support to change colors using control+Fx keys, matching the tones
 -  automatic downloading of a suitable voice audio-pack to use with text-to-speech
 -  automatic filling of empty fields in the deck with missing information
 -  much greater support of non-standard field names ( "Hanzi", 英语" and so on)
 -  support for user dictionaires (to customise translated or pinyin rendering)

 ... to be followed in the future by a raft of forthcoming features!


=== Installation ================================================================

1) download PyKit using Anki shared-plugin download feature
2) Ensure your model has the tag "Mandarin"
3) Ensure your model has fields that represent the following items:
        a) "Expression" i.e. "Chinese"
        b) "Reading" i.e. "Pinyin"
        c) "Meaning" i.e. "English", "German", "French" or you local language
  - PyKit is loaded 
  - You can change the name the pluhig looks for by editing "Pinyin Toolkit.py"

4) To use character colorization:
  - ensure your model has a field called "Color" to populate with colored characters
  - edit your models to use the new field
  - The best way to do this is:
        a) format questions with B&W characters
        b) show colored characters in answers where you are not testing reading or tones. 
  - You can also download the Kanji stroke order font to get limited stroke-order support
  - See: http://sites.google.com/site/nihilistorguk/

5) To activate sound tag generation:
  - ensure your model has a field called "Audio"
  - obtain audio files in the format "ni3.ogg", "hao3.ogg" (you can use .ogg, .wav and .mp3 files by default)
    * You can use "Tools" > "Download Mandarin sound samples" to automatically install a sample set
  - better quality audio can be found online. See the file "docs-audio.txt" for instructions
  - these files should be placed in your deck's media directory
  - finally, add your field to your card template  model %(Audio)s to the HTML generated from your model

* IT IS STRONGLY SUGGESTED YOU FOLLOW THE STEPS IN docs-audio.txt TO IMPROVE AUDIO SUPPORT! *

You will find many settings can be changed in "Pinyin Toolkit.py"
Features can also be turned on and off and the language settings varied.

If you plan not to use certain features then you should turn them off to decrease memory usage.


=== Feature Guide & Design Notes ================================================
[add commentary on why features are how they are]
This section provides some notes on development methodology and explains why some features have been implimented as they have.

1) Colorisation
Having studied Chinese for several years, it became apparnet to me that it was extremly difficult to remember the tone for a given Hanzi.

It came to be that it would be very useful to colorise the pinyin and the characters in order to remember them.
I looked on the internet to see if others had developed this idea. At the time I only came across 

Laowai Chinese (老外中文) have a blog article on colorization here:
http://laowaichinese.net/color-coded-tones-on-mdbg.htm (

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
=Complex Words=
[add details]


3) Pinyin Spacing
http://www.cjkware.com/2008/po1.html

3) Third Tone Sandhi
There is no support for the third tone sandhi.
Future support is planned for (3,3) tone sandhis but not (3,3,3) because of the relevance of context.
This support will only be for audio.
Past experiments have suggested that using a light yellow color to show the change to 2 in (3,3) has a negative impact on memory.
In the future a test may be carried on out using a lighter green color instead.

4) Other Tone Sandhis
Unsupported
DEBUG

5) erhua
The idea is that the space should be removed where there is an erhua, eg nǐ men2r [which is best passed to the lookup engine as menr2]. This creates a complication when coloring characters. For even more fun the er character isn't always an erhua, for example "er zi" where it is a separate sylabul and must not be merged. I didn't mean anything about the neutral tone [that was just a convenient way to have the character colorisation not break]. Also erhua are not necessarily  the end because we may be dealing with a phrase.
DEBUG

6) True Pinyin
DEBUG

                              == Audo-Blanking ==
DEBUG

                            == User Dictionaries ==
                            
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

Version 0.05   (05/06/2009)  Max Bolingbroke <batterseapower@hotmail.com>
                             Nick Cook <nick@n-line.co.uk>  [http://www.n-line.co.uk]

* Large-scale re-write and optimisation of the code by Max Bolingbroke (many thanks!)
* Automatic translation of non-dictionary words & phrase [can be used for almost any language]
* Add [limited] support for new CFDICT (French) and create a third distribution
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
  - Prevent loss of punctuation when colorizing characters
* Squash bug that means character colorisation to fail if audio generation off
* Added code testsuite
* Many smaller modifications to improve usability
* Pinyin is recognised and colored anywhere in the text
* Improved documentation


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


=== Bug-Hunting To-Do-List & Future Development Plans ===========================

                                  == Bug Fix ==

- audio generation breaks if deck has space/hyphen in the filename (thus deck dir)
  * I think we decided this is a capitalisation issue.  Does it work now?
- erhua needs serious overhaul
- capitalisation of pinyin in the meaning field not consistent with reading

                               == Mods & Tweaks ==

* look at getting Anki to start loading second audio file before first audio file has finishedplaying as this will dramatically reduce gap between words and make phrass sounds more natural
* Don't change from add window to main Anki window on faliure to find audio files
* attempt to reduce memory footprint
* move two options from Tools menu to Tools -> Advanced (rarely used functions, probably each only once per deck)
  - I think we should have a Tools -> PyKit submenu with both things on
* have audio downloader rename the 4 5th tone audio files
  - Not sure we need to do this - the audio generation already looks for files with me.mp3 names as tone 5
* Change pinyin recognition to a regex expression http://www.stud.uni-karlsruhe.de/~uyhc/zh-hans/node/108
* erhua changes
* audio error could be improved by:
    * finish the auto-fill even if there is an error
    * not make the add window disappear from the taskbar (and focus change to anki)
* [I think we should ship all dictionaries in one package in future]
  - Agreed
* as a result of the above... we can use the english dictionary to do a MW lookup even in German, French and other languages
  - Sure. I think it would make sense for us to preprocess the dictionaries so we have these files:
    * dict-pinyin.txt (just the pinyin)
    * dict-en.txt, dict-fr.txt, dict-de.txt (just the language-specific meanings, excluding measure words)
    * dict-mws.txt (just the measure words)
  - Only dict-pinyin.txt would have to include both simplified and traditional characters, all the others could save space by
    e.g. just including traditional
* add feature to audio file full words before breaking down to sylabuls [eg "怎么样, first check: "zěn me yàng")
  - I am aware that probability of a match gets less exponentialy less likely with length but have the chance to build large sound packs from various open source projects [see builging dictionary below]
  - I've been thinking about this as well. I think it will be easy to do this once I implement my proposed fix for Erhua.
    
                      == Future Development Plans (simple) ==

* Character order doesn't match numeral order for Arabic numerals.
* In addition there are other troubles such as 335 being looked up as 33, 5.
* I never could decide what to do about years eg 2000 could be either two thousand or 200年
* We could always color number in colored characters differently
* Consider how other dictionaries can be usefully used:
    - very useful but not sure if good for this: http://www.nciku.com
    - (audio? too few?) http://en.wiktionary.org/wiki/他们 / http://upload.wikimedia.org/wikipedia/commons/Zh-t%C4%81men.ogg
* dictionary update auto-downloads
* add shortcut key to force regenerate all fields
  - More accessible as a menu option
* tone sandhi rule IN SOUND GEN ONLY, so that a (3,3) -> (2,3) but not affect (3,3,3 [too complex to do based on other sandhi as they are context specific])
  - note: Nick tested this using a yellow color for pinyin (to show change to 2nd tone) didn't work and interfered with memory; perhaps could try again with a (very slightly) lighter green color but maybe better justnot to do this.
* look at borrowing code from the "Allows numbers to match pinyin tone mark.pyc" plugin, seems much more efficient tone mark generation
* dictionary lookup to allow traditional / chinese reverse lookup [onfocus from field.ChineseSimp populates field.ChineseTrad and onfocus from ChineseTrad populates fieldChineseSimp [google translate can already do this, but needs internet]
  - Will bloat memory requirements
  - maybe we can just use google translate then. we just set to and from to be chinese simp and trad (this is probably better overall actually)
* merge Nick's tone colorisation plugin into this plugin (lets you change the tone colors using ctrl+F1 through to Ctrl+F5 [dictionary is not perfect and chanees need to be made. Seems better to have the feature built-in.
* [side-issue] port the code from Kanji Graph plugin into this plugin [adds a graph showing how many unique hanzi in deck over time] (can't simply change fields, uses Japanese specific functions)

                == Future [non-trivial / unimportant changes] ==
                
* Consider incorporating python library for Chinese: http://code.google.com/p/cjklib/
    - would give Cantonese, IPA, Gwoyeu (partial Wade-Giles) and a ton of other functionality
* support for Japanese using CEDICT (format is almost identical as EDICT is the parent of CEDICT, itself the parent of CC-CEDICT, et al)
* selective blanking feature. Save the PREVIOUS (post-lookup) value of each field somewhere when filling the fields (perhaps in hidden html) then, When doing a lookup check see if there is a change from the previous lookup value and the current value (i.e. if they have not been edited). If not edited then blank and replace, if edited then leve alone.
* add a config tab to the Anki preferences window
* where dictionary contains "to " automatically as "verb" to a field called "Type"
* dictionary lookup to allow traditional / chinese reverse lookup [onfocus from field.ChineseSimp populates field.ChineseTrad and onfocus from ChineseTrad populates fieldChineseSimp

= Future Development [big, non-trivial, and/or unimportant changes] =
* auto-submit card as entry to CC-CEDICT, HanDeDict, and CFDICT from within Anki
* similarity search, no entry and <5 character then suggest from dict (search for other entry that 2 or more of same characters; MDBG online does this now)
* enhanced auto-blanking selective blanking feature. Save the PREVIOUS values of each field somewhere when filling the fields [possibly in hidden html in each filled field]. When doing a lookup check see if there is a change from the previous lookup value and the current value (i.e. if they have not been edited). If not edited then blank and replace, if edited then leve alone.
* add a config tab to the Anki preferences window
* consider viability of using English deck for MW lookup no matter what other settings are [planned distribution of all dicts]
* Impliment True Pinyin
* tone sandhi rule IN SOUND GEN ONLY, so that a (3,3) -> (2,3) but not affect (3,3,3 

                  == Highly Experimental Future Development ==
                          [in case we ever get bored!] 
                          
* support for other romanisation systems:
    - wade giles
    - Gwoyeu Romatzyh - http://home.iprimus.com.au/richwarm/gr/gr.htm#whatisgr
    - (bopomofo)
    - IPA
    - Cantonese
* add dictionary for GR version of CEDICT (big5 only, no unicode) http://home.iprimus.com.au/richwarm/gr/gr.htm#grdict
* Pinyin experiments
    - trial using superscript tone marks as per http://www.pinyinology.com/gr/gr2.html
    - trial Place names to have many first letter caps [incorrect in pinyin] http://www.pinyinology.com/pinyin/signs3/signs3.html and http://www.pinyinology.com/pinyin/transition.html
    - tone change rules:
        - tone sandhi
        - yi1 (一) changes 
        - bu4 (不) changes
        - third tone high/low rules
  - bopomofo conversion [easy but not that useful]
* Consider errors in CC-CEDICT http://www.stud.uni-karlsruhe.de/~uyhc/node/152
    - Consider errors in HanDeDict http://www.stud.uni-karlsruhe.de/~uyhc/zh-hans/content/consistency-check-handedict-unihan-pinyin-pronunciations
    - Consider cross-check script

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

