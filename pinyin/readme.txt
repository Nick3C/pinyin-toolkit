########################################################################
###                   Mandarin-Chinese Pinyin Toolkit                ### 
########################################################################
A Plugin for the Anki Spaced Repition learning system <http://ichi2.net/anki/>
Copyright (C) 2009 Nicholas Cook & Max Bolingbroke
Free software Licensed under GNU GPL

== Features ==
The Pinyin Toolkit adds several useful features for Mandarin users:
1 improved pinyin generation using a dictionary to guess the likely reading
2 output tone marks instead of numbers
3 colorize pinyin according to tone mark to assist visual learners
4 look up the meaning of characters in English, German, or French (and/or use google translate for other languages)
5 colorize character according to tone to assist visual learners [if enabled]
6 generate the appropriate "[sound:ni2.ogg][sound:hao3.ogg]" tags to give rudimentary text-to-speech [if enabled]
7 lookup the Measure Word for a character from CC-CEDICT (just English version for now)

The plugin replaces standard Mandarin generation, so there is no need to rename your model or model tags.
Features 1 to 4 will work automatically out of the box. Features 5 and 6 are optional extras that require enabling.

To add your own dictionary entries, create a file called "dict-userdict.txt" in the pinyin/ subdirectory with the entries
in the same format as the other dictionaries i.e.:
<simplified-without-spaces> <traditional-without-spaces> [<pinyin> ... <pinyin>] /<meaning>/.../<meaning>/

Entries should be separated by spaces. Here are some examples:
一一 一一 [yi1 yi1] /one by one/one after another/
一共 一共 [yi1 gong4] /altogether/

Note that you can omit the meaning and surrounding "/"s if you don't want to include meaning data, but everything else is required:
一一 一一 [yi1 yi1]
一共 一共 [yi1 gong4]


== Installation ==
1) download using Anki shared-plugin download feature
2) Ensure your model has the tag "Mandarin"
3) Ensure your model has the fields:
  - "Expression" or "Hanzi"
  - "Reading" or "Pinyin"
  - "Meaning" or "Definition"
  - If you don't like any of these names, you can add more options by editing the settings
4) To activate character colorization:
  - ensure your model has a field called "Color", "Colour" or "Colored Hanzi" to populate with colored characters
  - edit your models to use the new field
  - The best way to do this is test on plain characters, but show colored characters in answers or where you are not testing reading or tones. 
5) To activate sound tag generation:
  - ensure your model has a field called "Audio", "Sound" or "Spoken"
  - obtain audio files in the format "ni3.ogg", "hao3.ogg" (you can use .ogg, .wav and .mp3 files by default)
    * You can download such files at <http://www.chinese-lessons.com/download.htm>, or use the Tools > Download Mandarin sound samples
      menu option to automatically download and install them
    * Alternatively, you can copy your own files directly into the media directory, or import them using Anki. It's advisable to keep a copy,
      as Anki wipes them in media checks.  Commercial software (such as Wenlin) includes high quality versions you can use.
  - finally, add a substitution like %(Audio)s to the HTML generated from your model

If you plan not to use features such as character colorisation or audio generation,
you should turn them off in the settings section.



== Changelog ==

# Version 0.05 (__/06/2009)  Max Bolingbroke <batterseapower@hotmail.com>
#                            Nick Cook <nick@n-line.co.uk>  [http://www.n-line.co.uk]
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

# Version 0.04 (19/05/2009)  Nick Cook <nick@n-line.co.uk>  [http://www.n-line.co.uk]
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

# Version 0.03[r] (12/05/2009)  Nick Cook <nick@n-line.co.uk>  [http://www.n-line.co.uk]
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

# Version 0.02.5[r] (21/03/2009)   Nick Cook <nick@n-line.co.uk>   [http://www.n-line.co.uk]
* Dictionary updated to use adapted version of CC-CEDICT
* entries increasing from 44,783 to 82,941

# Version 0.02[r] (03/2009)   Damien Elmes  [http://ichi2.net/]
* Ported to Anki 0.9.9.6 and tidied up
* Brian Vaughan no longer maintaing plugin

# Version 0.01[r] (2008)    Brian Vaughan [http://brianvaughan.net]
* Original release

"[r]" means "Retroactive Version Number"



== Bug-Hunting To-Do-List & Future Development Plans ==

= Bug Fix =
- I get a prompt on one of my decks that there is no audio when there is
- doesn't cut mw from dict entry after copying to the MW field [you don't want it in the entry and in the measure word field, only one of them] should do only if successfuly put in mw field
- [earlier today, unchekd in latest] previously mentioned bug on 生日 etc in German version now returns pinyin of "生 rì" and no German translation
    - due to dictionary not findifn the first character (or an earlier one) so abandoning the lookup.
    - solution provisionally started in code
- if atempt to use without audio I get the popup but the download will not start; toolbar option does not start audio download either
Nick specific bugs:
    - sound generation broken in my version
    - maybe a windows bug
    - MW lookup totally broken
    


= Mods & Tweaks =
* move two options from Tools menu to Tools -> Advanced (rarely used functions, probably each only once per deck)
* change pinyin recognition to regex instead of length check
* erhua changes
* have audio downloader rename the 4 5th tone audio files
* Change pinyin recognition to a regex expression http://www.stud.uni-karlsruhe.de/~uyhc/zh-hans/node/108

= Future Development (simple) =
* dictionary update auto-downloads
* where dictionary contains "to " automatically as "verb" to a field called "Type"
* shortcut key to force regenerate all fields
* look at borrowing code from the "Allows numbers to match pinyin tone mark.pyc" plugin, seems much more efficient tone mark generation
* merge Nick's tone colorisation plugin into this plugin (lets you change the tone colors using ctrl+F1 through to Ctrl+F5 [dictionary is not perfect and chanees need to be made. Seems better to have the feature built-in.
* [side-issue] port the code from Kanji Graph plugin into this plugin [adds a graph showing how many unique hanzi in deck over time] (can't simply change fields, uses Japanese specific functions)

= Future Development [big, non-trivial, and/or unimportant changes] =
* auto-submit card as entry to CC-CEDICT, HanDeDict, and CFDICT from within Anki
* enhanced auto-blanking selective blanking feature. Save the PREVIOUS values of each field somewhere when filling the fields [possibly in hidden html in each filled field]. When doing a lookup check see if there is a change from the previous lookup value and the current value (i.e. if they have not been edited). If not edited then blank and replace, if edited then leve alone.
* add a config tab to the Anki preferences window
* consider viability of using English deck for MW lookup no matter what other settings are [planned distribution of all dicts]
* Impliment True Pinyin
* dictionary lookup to allow traditional / chinese reverse lookup [onfocus from field.ChineseSimp populates field.ChineseTrad and onfocus from ChineseTrad populates fieldChineseSimp
* tone sandhi rule IN SOUND GEN ONLY, so that a (3,3) -> (2,3) but not affect (3,3,3 


= Highly Experimental Future Development =
[in case we ever get bored!] 
- Consider python library for Chinese: http://www.stud.uni-karlsruhe.de/~uyhc/zh-hans/content/announcing-eclectus-han-character-dictionary
- Pinyin experiments
    - trial using superscript tone marks as per http://www.pinyinology.com/gr/gr2.html
    - trial Place names to have many first letter caps [incorrect in pinyin] http://www.pinyinology.com/pinyin/signs3/signs3.html and http://www.pinyinology.com/pinyin/transition.html
    - tone change rules:
        - tone sandhi
        - yi1 (一) changes 
        - bu4 (不) changes
        - third tone high/low rules
  - bopomofo conversion [easy but not that useful]
- Consider errors in CC-CEDICT http://www.stud.uni-karlsruhe.de/~uyhc/node/152
    - Consider errors in HanDeDict http://www.stud.uni-karlsruhe.de/~uyhc/zh-hans/content/consistency-check-handedict-unihan-pinyin-pronunciations
    - Consider cross-check script


== Notes on Design == [add commentary on why features are how they are]
This section provides some notes on development methodology and explains why some features have been implimented as they have.

1) Colorisation
Having studied Chinese for several years, it became apparnet to me that it was extremly difficult to remember the tone for a given Hanzi.
DEBUG

2) Text-to-Speech
DEBUG

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

7) Audo-Blanking
DEBUG


== Licensing ==
-Pinyin Toolkit-
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

-Dictionaries-
Chinese-English CC-CEDICT, available at: <http://www.mdbg.net/chindict/chindict.php?page=cc-cedict>
Licensing of CC-CEDICT is Creative Commons Attribution-Share Alike 3.0 <http://creativecommons.org/licenses/by-sa/3.0/>

Chinese-German dictionary HanDeDict, available at: <http://www.chinaboard.de/chinesisch_deutsch.php?mode=dl>
Licensing of HanDeDict is  Creative Commons Attribution-Share Alike 2.0 Germany <http://creativecommons.org/licenses/by-sa/2.0/de/>

Chinese-French dictionary CFDICT, available at <http://www.chinaboard.de/cfdict.php?mode=dl>
Licensing of CFDICT is Creative Commons Attribution-Share Alike 2.5 French <http://creativecommons.org/licenses/by-sa/2.5/fr/>

-Audio Files-
Mandarin Sounds, available at: <http://www.chinese-lessons.com/download.htm
Licensing of Mandarin Sounds is Creative Commons Attribution-Noncommercial-No Derivative Works 3.0 United States <http://creativecommons.org/licenses/by-nc-nd/3.0/us/>