########################################################################
###                   Mandarin-Chinese Pinyin Toolkit                ### 
########################################################################
A Plugin for the Anki Spaced Repition learning system <http://ichi2.net/anki/>
Copyright (C) 2009 Nicholas Cook & Max Bolingbroke
Free software Licensed under GNU GPL

== About This Plugin ==
The Pinyin Toolkit adds several useful features for Mandarin users:
1 improved pinyin generation using a dictionary to guess the likely reading
2 output tone marks instead of numbers
3 colorize pinyin according to tone mark to assist visual learners
4 look up the meaning of characters in English, German, or French (and/or use google translate for other languages)
5 colorize character according to tone to assist visual learners [if enabled]
6 generate the appropriate "[sound:ni2.ogg][sound:hao3.ogg]" tags to give rudimentary text-to-speech [if enabled]

The plugin replaces standard Mandarin generation, so there is no need to rename your model or model tags.
Features 1 to 4 will work automatically out of the box. Features 5 and 6 are optional extras that require enabling.

To add your own dictionary entries, create a file called "dict-userdict.txt" in the pinyin/ subdirectory with the entries
in the same format as the other dictionaries i.e.:
<simplified-without-spaces> <traditional-without-spaces> [<pinyin> ... <pinyin>] /<meaning>/.../<meaning>/

Entries should be separated by spaces. Here are some examples:
一一 一一 [yi1 yi1] /one by one/one after another/
一共 一共 [yi1 gong4] /altogether/

Note that you can omit the meaning and surrounding / if you don't want to include meaning data, but everything else is required.


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




  - ensure your model has a field called "Audio"
  - obtain audio files in the format "ni3.ogg", "hao3.ogg" a sample set can be obtained 
  - note that commercial software (such as Wenlin) includes higher quality versions you can use
  - place the files in your deck's media directory (keep a copy, as Anki wipes them in media checks)
  - finally, add a substitution like %(Audio)s to the HTML generated from your model

If you plan not to use features such as character colorisation or audio generation,
you should turn them off in the settings section.



== Changelog ==

# Version 0.05 (__/06/2009)  Max Bolingbroke <batterseapower@hotmail.com>
#                            Nick Cook <nick@n-line.co.uk>  [http://www.n-line.co.uk]
* Large-scale re-write and optimisation of the code by Max Bolingbroke (many thanks!)
* Automatic translation of non-dictionary words & phrase [can be used for almost any language]
* Add [limited] support for new CFDICT (French)
* MW added automatically if in dictionary [only applies to English]
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

Vital fix-issues
- sound generation broken in my version [even after your changes earlier today] It may be a windows related bug. I note there is now a media directory in the pinyin dir. I presume this is unintentional?
- I have tried to do something to improve MW generation. I am still not very happy with the consequences of multiple measure words and wasn't able to test the code after breaking it :$
- doesn't cut mw from dict entry after copying to the MW field [you don't want it in the entry and in the measure word field, only one of them] should do only if successfuly put in mw field
- [earlier today, unchekd in latest] previously mentioned bug on 生日 etc in German version now returns pinyin of "生 rì" and no German translation
    - 操你妈 in english [now works]
    - 生日 in German
- track down why HanDeDict doesn't always retrieve entries that are known to be there

- the pinyin object's def init could be improved using a regex check rather than the final number. I had worked on this previously but it was complex so I dropped it.
- erhua issue (see below)

Comments
* I think I have fixed google translate, it works in the python shell but I managed to break something else before I could confirm in Anki
* I think you may have misunderstood my comment on the neutral tone and erhua. The idea is that the space should be removed where there is an erhua, eg nǐ men2r [which is best passed to the lookup engine as menr2]. This creates a complication when coloring characters. For even more fun the er character isn't always an erhua, for example "er zi" where it is a separate sylabul and must not be merged. I didn't mean anything about the neutral tone [that was just a convenient way to have the character colorisation not break]. Also erhua are not necessarily  the end because we may be dealing with a phrase.
* Is there an check on whether a file exists before loading the dictionaries? I think there should be, I added dict-userdict.txt to the .ignore file and plan not to distribute it in future (so that it is not overwritten when installing)
* i don't see why separating traditional and simplified saves space. I used to have code doing that but I realised it was pointless. If they differ then a new entryis needed, if they are the same then the latter will just overwrite the former. The code will do nothing but slow-down the dictionary init
* There was a good reason for me not using the folder structure you have chosen on git: my format allowed a hard-link for the plugin in the anki directory, then the GIT repositories could be stored and maintained from there. Is this such a bad idea?
* In any event, I think that the readme is better placed in the plugin dir, it keeps the files tidy and prevents it being overwritten by other plugin readmes.
* I am not too sure what to do about the traditional / simplified inconsistancy. I can't think of *any* situation where it matter. Even if we do a "swap simplified and traditional" then it should still be fine to do this. Although I guess if they have mixed form sentences that might cause problems.
* I do thing that lowercase pinyin is a very sensible choice. unless we implement true pinyin (no space between the pinyin of multi-character words) it looks horrible. Even then it may look strange with color. Audio also must have lowercase (linux systems being caps-sensative)
* we still have a problem with the audio in those Mandarin sounds not matching standard pinyin. Perhaps we could rename the non-matching ones after downloading them? I think "me.mp3" was one (should be "me4.mp3") there are a few more as I recall

Future [big, non-trivial, and/or unimportant changes]
* add shortcut key to force regenerate all fields
* dictionary lookup to allow traditional / chinese reverse lookup [onfocus from field.ChineseSimp populates field.ChineseTrad and onfocus from ChineseTrad populates fieldChineseSimp
* tone sandhi rule IN SOUND GEN ONLY, so that a (3,3) -> (2,3) but not affect (3,3,3 [too complex, varies on meaning])
* selective blanking feature. Save the PREVIOUS values of each field somewhere when filling the fields [possibly in hidden html in each filled field]. When doing a lookup check see if there is a change from the previous lookup value and the current value (i.e. if they have not been edited). If not edited then blank and replace, if edited then leve alone.
* store the settings in a separate file config.ini (to have a ver number and be renamed to config.bak on each upgrade if new settings added)
* add a config tab to the Anki preferences window
* look at borrowing code from the "Allows numbers to match pinyin tone mark.pyc" plugin, seems much more efficient tone mark generation
* where dictionary contains "to " automatically as "verb" to a field called "Type"
* add a true pinyin mode and option switch (no breaks between sylabels in same words) [this will require a full index, as above]


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