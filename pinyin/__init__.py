import sys
import os

# Set up the path Python uses to look for import packages to
# include the 3rd-party dependencies we have folded in
import utils

# cjklib uses standard library functions from Python 2.5: we emulate
# them until Anki upgrades
if sys.version_info[0:2] < (2, 5):
    sys.path.append(os.path.join(utils.toolkitdir(), "pinyin", "vendor", "python25"))
sys.path.append(os.path.join(utils.toolkitdir(), "pinyin", "vendor", "cjklib"))

import config
import dictionary
import languages
import logger
import media
import meanings
import mocks
import numbers
import pinyin
import statistics
import transformations
import weakcache

#import anki # Don't import the anki submodule because it imports lots of anki stuff,
             # and if we're running from the command line it won't be available
import forms