#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import urllib
import shutil
import tempfile
import zipfile

from logger import log
import utils

class MediaDownloader(object):
    def __init__(self):
        # Where shall we save downloaded files?
        self.__cachedir = os.path.join(utils.pinyindir(), "media")
        
        # Ensure the cache exists
        log.info("Initialising cache directory at %s", self.__cachedir)
        utils.ensuredirexists(self.__cachedir)
    
    def download(self, zipurl, downloadprompt=None):
        # First check the cache to see if we have the download already
        cachepath = self.urlcachepath(zipurl)
        if os.path.exists(cachepath):
            log.info("Found %s in the cache at %s", zipurl, cachepath)
            return Media(cachepath)
        
        # Can we actually write to the cache?
        if utils.canwriteto(cachepath):
            # We CAN write to the cache - download straight into it
            log.info("Have write access to cache - downloading into it")
            downloadto = cachepath
        else:
            # Use a temporary path instead, the user doesn't have enough permissions
            log.info("No write access to cache - downloading to temporary location")
            downloadto = tempfile.mktemp()

        # Actually do the download and return the result
        if downloadprompt:
            downloadprompt()
        urllib.urlretrieve(zipurl, downloadto)
        return Media(downloadto)
    
    def urlcachepath(self, url):
        # What the hell, just use a hash of the URL. Not meant to be human readable anyway.
        return os.path.join(self.__cachedir, utils.md5(url))

class Media(object):
    def __init__(self, ziplocation):
        log.info("Initalizing media located at %s", ziplocation)
        self.__zip = zipfile.ZipFile(ziplocation)
    
    def extractand(self, handler):
        # Extract the ZIP into a new directory
        extractdirpath = tempfile.mkdtemp()
        log.info("Extracting media into %s", extractdirpath)
        for info in self.__zip.infolist():
            # Create the directory
            extractfilepath = os.path.join(extractdirpath, info.filename)
            utils.ensuredirexists(os.path.dirname(extractfilepath))
            
            # Extract the file
            file = open(extractfilepath, 'w')
            file.write(self.__zip.read(info.filename))
            file.close()
            
            # Give the file to the handler
            handler(extractfilepath)
        
        # Blast the temporary directory and its extracted files
        log.info("Deleting extracted files from %s", extractdirpath)
        shutil.rmtree(extractdirpath)
