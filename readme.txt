########################################################################
###                   Mandarin-Chinese Pinyin Toolkit                ###
###                          Documentation                           ### 
########################################################################
A Plugin for the Anki Spaced Repition software <http://ichi2.net/anki/>

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

If you plan not to use features such as character colorisation or audio generation,
you can turn them off in the plugin settings section.



== Changelog ==

# Version 0.05 (_____/2009)  Nick Cook <nick@n-line.co.uk>  [http://www.n-line.co.uk]
#                            Max Bolingbroke <batterseapower@hotmail.com>
* Menu option to fill in any missing information the Toolkit can provide in the current deck
  - Shortcut key to regenerate all entries [control-g] as well?
* Heuristic detection of model fields with the appropriate meaning
* Can automatically download Mandarin sound samples via a menu option
* Automatic translate of non-dictionary phrase [can be customised]
  - see ____ for reference codes
* Add support for new CFDICT (French), note that it is still very limited and will use a hybrid with English
* MW added automatically if in dictionary
* Don't generate audio tags if sounds are missing
* Use a fifth tone audio sample in the form de5.mp3 if one is provided, but still fall back on de4.mp3 otherwise
  - Will also accept e.g. de.mp3 as a fifth tone audio sample if present
* Try several file extensions when we need a bit of audio, using the order: .mp3, .ogg, .wav
* Meanings dictionary - add "(1)" "(2)" "(3)" instead of simple line spaces
* Internal refactoring of code to remove the incidence of unreliable string manipulations, leading to bugfixes:
  - Remove space at the end of colored pinyin
  - Remove spaces between punctuation in pinyin
  - Remove the space between erhua "r" suffix and main word in pinyin
  - Prevent loss of punctuation when colorizing characters
* Squash bug that causes character colorisation to fail if audio generation off
* Added code testsuite

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

Bugs & Tweaks
- work out why some characters in dictionary can't be found:
    - 操你妈 in english
    - 生日 in German
- track down why HanDeDict doesn't always retrieve entries that are known to be there

Future Feature List
- where dictionary has measure words, automatically add them to a MW field and add "noun" to "Type" field
- where dictionary contains "to " automatically ass "verb" to a field called "Type"
- add a true pinyin mode and option switch (no breaks between sylabels in same words) [this will require a full index, as above]



== Licensing ==

Chinese-English CC-CEDICT, available at: <http://www.mdbg.net/chindict/chindict.php?page=cc-cedict>
Licensing of CC-CEDICT is Creative Commons Attribution-Share Alike 3.0 <http://creativecommons.org/licenses/by-sa/3.0/>

Chinese-German dictionary HanDeDict, available at: <http://www.chinaboard.de/chinesisch_deutsch.php?mode=dl>
Licensing of HanDeDict is  Creative Commons Attribution-Share Alike 2.0 Germany <http://creativecommons.org/licenses/by-sa/2.0/de/>

Chinese-French dictionary CFDICT, available at <http://www.chinaboard.de/cfdict.php?mode=dl>
Licensing of CFDICT is Creative Commons Attribution-Share Alike 2.5 French <http://creativecommons.org/licenses/by-sa/2.5/fr/>

Mandarin Sounds, available at: <http://www.chinese-lessons.com/download.htm
Licensing of Mandarin Sounds is Creative Commons Attribution-Noncommercial-No Derivative Works 3.0 United States <http://creativecommons.org/licenses/by-nc-nd/3.0/us/>