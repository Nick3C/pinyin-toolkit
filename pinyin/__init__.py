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
import utils
import weakcache

#import anki # Don't import the anki submodule because it imports lots of anki stuff,
             # and if we're running from the command line it won't be available
import forms