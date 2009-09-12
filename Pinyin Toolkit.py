#!/usr/bin/env python
# -*- coding: utf-8 -*-

########################################################################
###                   Mandarin-Chinese Pinyin Toolkit                ### 
########################################################################
"""
A Plugin for the Anki Spaced Repition learning system <http://ichi2.net/anki/>

    Mandarin-Chinese Pinyin Toolkit
    Copyright (C) 2009 Nicholas Cook & Max Bolingbroke

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
"""

if __name__ != "__main__":
    # Initialize the toolkit
    import pinyin.anki.main as main
    from ankiqt import mw
    
    # Save a reference to the toolkit onto the mw, preventing garbage collection of PyQT objects
    mw.pinyintoolkit = main.PinyinToolkit(mw)
else:
    print "This is a plugin for the Anki Spaced Repition learning system and cannot be run directly."
    print "Please download Anki from <http://ichi2.net/anki/>"
