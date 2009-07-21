#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re

from logger import log
from model import *
import utils

class MeaningFormatter(object):
    embeddedchineseregex = re.compile(r"(?:(?:([^\|\[\s]+)\|([^\|\[\s]+)(?:\s*\[([^\]]*)\])?)|(?:([^\|\[\s]+)\s*\[([^\]]*)\]))")
    
    def __init__(self, simplifiedcharindex, prefersimptrad):
        self.simplifiedcharindex = simplifiedcharindex
        self.prefersimptrad = prefersimptrad
    
    def parsedefinition(self, raw_definition, tonedchars_callback=None):
        log.info("Parsing the raw definition %s", raw_definition)
        
        # Default the toned characters callback to something sensible
        if tonedchars_callback is None:
            tonedchars_callback = lambda characters: [Word(Text(characters))]
        
        meanings, measurewords = [], []
        for definition in raw_definition.strip().lstrip("/").rstrip("/").split("/"):
            # Remove stray spaces
            definition = definition.strip()
            
            # Detect measure-word ness
            if definition.startswith("CL:"):
                ismeasureword = True
                
                # Measure words are comma-seperated
                for mw in definition[3:].strip().split(","):
                    # Attempt to parse the measure words as structured data
                    match = self.embeddedchineseregex.match(mw)
                    if match is None:
                        log.info("Could not parse the apparent measure word %s", mw)
                        continue
                    
                    # They SHOULD have pinyin information
                    characterswords, pinyinwords = self.formatmatch(match, tonedchars_callback)
                    if characterswords is None or pinyinwords is None:
                        log.info("The measure word %s was missing some information in the dictionary", mw)
                        continue
                    
                    measurewords.append((characterswords, pinyinwords))
            else:
                words = []
                for ismatch, thing in utils.regexparse(self.embeddedchineseregex, definition):
                    if ismatch:
                        # A match - we can append a representation of the words it contains
                        (characterwords, pinyinwords) = self.formatmatch(thing, tonedchars_callback)
                        
                        # Put the resulting words right into the output in a human-readable format
                        words.extend(characterwords)
                        if pinyinwords is not None:
                            words.append(Word(Text(" - ")))
                            words.extend(pinyinwords)
                    else:
                        # Just a string: append it as a list of tokens, trying to extract any otherwise-unmarked
                        # pinyin in the sentence for colorisation etc
                        words.append(Word(*tokenize(thing, forcenumeric=True)))
                
                meanings.append(words)
            
        return meanings, measurewords
    
    def formatmatch(self, match, tonedchars_callback):
        if match.group(4) != None:
            # A single character standing by itself, with no | - just use the character
            character = match.group(4)
        elif self.prefersimptrad == "simp":
            # A choice of characters, and we want the simplified one
            character = match.group(1 + self.simplifiedcharindex)
        else:
            # A choice of characters, and we want the traditional one
            character = match.group(1 + (1 - self.simplifiedcharindex))
        
        if match.group(4) != None:
            # Pinyin tokens (if any) will be present in single-character match case
            rawpinyin = match.group(5)
        else:
            # Pinyin tokens (if any) will be present in conjunctive character match case
            rawpinyin = match.group(3)
        
        if rawpinyin != None:
            # There was some pinyin for the character after it - include it
            pinyintokens = tokenizespaceseperated(rawpinyin)
            return ([Word(*(tonedcharactersfromreading(character, pinyintokens)))], [Word.spacedwordfromunspacedtokens(pinyintokens)])
        else:
            # Look up the tone for the character so we can display it more nicely, as in the other branch
            return (tonedchars_callback(character), None)
