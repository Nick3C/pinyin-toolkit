#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import logging

import utils

# Output to file
logfilepath = os.path.join(utils.pinyindir(), "../Pinyin Toolkit.log")

try:
    # Try to use a rotating file if possible:
    import logging.handlers
    loghandler = logging.handlers.RotatingFileHandler(logfilepath, encoding="UTF-8", maxBytes=40000, backupCount=0)
except ImportError:
    # Delete the log file first to make sure it doesn't grow /too/ much
    try:
        os.remove(logfilepath)
    except IOError, e:
        # Happens in event of some quite serious problem, I guess :-)
        pass
    except OSError, e:
        # Happens in event of file not existing
        pass
    
    # Fall back on non-rotating handler
    loghandler = logging.FileHandler(logfilepath, encoding="UTF-8")

# Format quite verbosely, so we can grep for WARN
loghandler.setFormatter(logging.Formatter(u"%(asctime)s - %(levelname)s - %(message)s"))

# Create logger with that handler
log = logging.getLogger('Pinyin Toolkit')
log.setLevel(utils.debugmode() and logging.DEBUG or logging.WARNING)
log.addHandler(loghandler)
