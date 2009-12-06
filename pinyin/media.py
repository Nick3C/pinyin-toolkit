#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import re
import urllib
import shutil
import tempfile
import zipfile

from logger import log
import utils


def downloadAndInstallMandarinSounds(notifier, mediamanager, config):
    log.info("Downloading Mandarin sound pack")
    
    try:
        # Download ZIP, using cache if necessary
        downloader = MediaDownloader(mediamanager.mediadir())
        the_media = downloader.download("Chinese-Lessons.com Mandarin Sounds", config.mandarinsoundsurl,
                                        lambda: notifier.info("Downloading the sounds - this might take a while!"))
    except IOError, e:
        notifier.exception("Error while downloading the sound pack: are you connected to the internet?")
        return

    try:
        # Install each file from the ZIP into our media folder
        the_media.installpack(mediamanager.mediadir())
    except zipfile.BadZipfile, e:
        notifier.exception("The downloaded sound pack appeared to be corrupt")
        return

    # Tell the user we are done
    exampleAudioField = config.candidateFieldNamesByKey['audio'][0]
    notifier.info("Finished installing Mandarin sounds! These sound files will be used automatically as long as you have "
                  + " the: <b>" + exampleAudioField + "</b> field in your deck, and the text: <b>%(" + exampleAudioField + ")s</b> in your card template")

class MediaDownloader(object):
    def __init__(self, mediadir):
        # Where shall we save downloaded files?
        self.__cachedir = os.path.join(mediadir, "downloads")
        
        # Ensure the cache exists
        log.info("Initialising cache directory at %s", self.__cachedir)
        utils.ensuredirexists(self.__cachedir)
    
    def download(self, name, zipurl, downloadprompt=None):
        # First check the cache to see if we have the download already
        cachepath = self.urlcachepath(zipurl)
        if os.path.exists(cachepath):
            log.info("Found %s in the cache at %s", zipurl, cachepath)
            return DownloadedMedia(name, cachepath)
        
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
        if downloadprompt is not None:
            downloadprompt()
        urllib.urlretrieve(zipurl, downloadto)
        return DownloadedMedia(name, downloadto)
    
    def urlcachepath(self, url):
        # What the hell, just use a hash of the URL. Not meant to be human readable anyway.
        return os.path.join(self.__cachedir, utils.md5(url))

class DownloadedMedia(object):
    def __init__(self, name, zippath):
        log.info("Initalizing downloaded media %s located at %s", name, zippath)
        self.name = name
        self.zippath = zippath
    
    def installpack(self, mediadir):
        # Work out the pack directory we want to extract to
        packpath = utils.mkdirfallback(mediadir, self.name)
        log.info("Extracting downloaded media into %s", packpath)
        
        # Extract the ZIP into a new directory
        thezip = zipfile.ZipFile(self.zippath)
        for info in thezip.infolist():
            # Create the directory
            extractfilepath = os.path.join(packpath, info.filename)
            utils.ensuredirexists(os.path.dirname(extractfilepath))
            
            # Extract the file. NB: must use binary mode - this important for for Windows!
            file = open(extractfilepath, 'wb')
            file.write(thezip.read(info.filename))
            file.close()

class MediaPack(object):
    def __init__(self, packpath, media):
        self.packpath = packpath
        
        # Normalize capitalisation for ease of lookup
        self.media = dict([(name.lower(), filename) for name, filename in media.items()])
    
    def __str__(self):
        return self.name
    
    def __repr__(self):
        return "MediaPack(%s, %s)" % (repr(self.packpath), repr(self.media))
    
    def __eq__(self, other):
        if other == None:
            return False
        
        return self.name == other.name and self.packpath == other.packpath and self.media == other.media
    
    def __ne__(self, other):
        return not(self == other)
    
    name = property(lambda self: os.path.basename(self.packpath))
    
    def summarize(self, audioextensions):
        # Summarize the counts of files per extension
        extensioncounts = [(extension, len([() for filename in self.media.values() if os.path.splitext(filename)[1].lower() == extension.lower()])) for extension in audioextensions]
        formattedcounts = [str(count) + " " + extension + " " + utils.pluralize("file", count) for extension, count in extensioncounts if count > 0]
        
        if len(formattedcounts) > 0:
            # Only include brackets around the extension counts in this case
            return self.name + " (" + ", ".join(formattedcounts) + ")"
        else:
            return self.name
    
    def mediafor(self, basename, audioextensions):
        # Check all possible extensions in order of priority
        for extension in audioextensions:
            name = (basename + extension).lower()
            if name in self.media:
                return self.media[name]
        
        # No suitable media existed!
        return None
    
    @classmethod
    def frompath(cls, packpath):
        media = {}
        for filename in os.listdir(packpath):
            media[filename] = os.path.join(packpath, filename)
        
        log.info("Discovered %d media files in the pack at %s", len(media), packpath)
        return MediaPack(packpath, media)

# Use to discover files in the media directory that are not referenced in the media
# database. If this is true, the user has just copied them in - and we consider
# such things "legacy" sounds that should be replaced with a true media pack.
def discoverlegacymedia(mediadircontents, mediaindex):
    # If the media directory was inacessible for any reason, just give up
    if mediadircontents == None:
        log.info("Couldn't discover legacy media because the media directory was not accessible")
        return None
    
    # Normalize case from the directory listing so that the removal check works reliably
    mediadircontents = [os.path.normcase(mediadircontent) for mediadircontent in mediadircontents]
    
    # Iterate over files and pluck them out into this dictionary of dictionaries
    for orig_path, filename in mediaindex:
        # Remove the file from consideration for the manual media lookup stage
        try:
            # NB: we can only do this reliably because we normalized the case above
            mediadircontents.remove(os.path.normcase(filename))
        except:
            # Tried to remove the file from the directory listing, but it's not actually
            # in the list.  This means that the database entry is actually out of date and
            # we should ignore it
            log.info("Out of date database entry for %s -> %s", orig_path, filename)
            continue
    
    # Return the remaining files
    return mediadircontents

"""
# initial work on an importer for the SWAC audio files
# This might be useful: http://polyglotte.tuxfamily.org/autres/anki_swac_en.html

def SWACimport(dir):
    swacurl="http://download.shtooka.net/cmn-balm-hsk1_ogg.tar"
    
    # 1 - Download te zip file 

    # 2 - unzip to media dir
    
    # 3 - open the index file
    
    packdir="C:\Nick\Language\Mandarin Sound Files\Swac" # testdir
    tagfile = "index.tags.txt"
    fullpath = os.path.join(packdir, tagfile)
    
    
    # 4 - scan through the index file and put the file names and piniyn into variables
    
    # regex should match the filename and put it into group(1)
    # and output pinyin to group(3)
    lineregex = re.compile(r"[[](.+)[]].+SWAC_ALPHAIDX=(.+)", re.MULTILINE)
    
    #open file for reading
    file = codecs.open(fullpath, "r", encoding='utf-8')
   
    matches = re.search(file)
    matches.group(1)
    matches.group(3)

    file.close()    
    
    # 4 - remove tones from pinin variable
    
    # 5 - rename & move the files to the main directory 
    
    os.rename(tagfull, pinyinname)
"""
