import os
import logging

import utils

# Output to file
logfilepath = os.path.join(utils.pinyindir(), "../Pinyin Toolkit.log")

try:
    # Try to use a rotating file if possible:
    import logging.handlers
    loghandler = logging.handlers.RotatingFileHandler(logfilepath, maxBytes=40000, backupCount=0)
except ImportError:
    # Fall back on non-rotating handler
    loghandler = logging.FileHandler(logfilepath)

# Create logger with that handler
log = logging.getLogger('Pinyin Toolkit')
log.addHandler(loghandler)