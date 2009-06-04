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
        if downloadprompt:
            downloadprompt()
        urllib.urlretrieve(zipurl, downloadto)
        return DownloadedMedia(name, downloadto)
    
    def urlcachepath(self, url):
        # What the hell, just use a hash of the URL. Not meant to be human readable anyway.
        return os.path.join(self.__cachedir, utils.md5(url))

class DownloadedMedia(object):
    def __init__(self, name, ziplocation):
        log.info("Initalizing downloaded media %s located at %s", name, ziplocation)
        self.__name = name
        self.__zip = zipfile.ZipFile(ziplocation)
    
    def installpack(self, mediadir):
        # Work out the pack directory we want to extract to
        packpath = utils.mkdirfallback(mediadir, self.__name)
        log.info("Extracting downloaded media into %s", packpath)
        
        # Extract the ZIP into a new directory
        for info in self.__zip.infolist():
            # Create the directory
            extractfilepath = os.path.join(packpath, info.filename)
            utils.ensuredirexists(os.path.dirname(extractfilepath))
            
            # Extract the file. NB: must use binary mode - this important for for Windows!
            file = open(extractfilepath, 'wb')
            file.write(self.__zip.read(info.filename))
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
            log.info("Discovered media %s in %s", filename, packpath)
            media[filename] = os.path.join(packpath, filename)
        
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

if __name__ == "__main__":
    import unittest
    
    class MediaPackTest(unittest.TestCase):
        def testNormalizeCase(self):
            self.assertEquals(MediaPack("Manual", {"A" : "b"}), MediaPack("Manual", {"a" : "b"}))
            self.assertNotEquals(MediaPack("Manual", {"A" : "b"}), MediaPack("Manual", {"A" : "B"}))
        
        def testName(self):
            self.assertEquals(MediaPack(os.path.join("foo", "bar"), {}).name, "bar")
        
        def testMediaForCase(self):
            pack = MediaPack("Example", {"fOo.mP3" : "REsuLT"})
            self.assertEquals(pack.mediafor("foo", [".mp3"]), "REsuLT")
            self.assertEquals(pack.mediafor("fOo", [".mp3"]), "REsuLT")
            self.assertEquals(pack.mediafor("foo", [".mP3"]), "REsuLT")
        
        def testMediaForExtensionSearch(self):
            pack = MediaPack("Example", {"foo.mp3" : "MP3RESULTFOO"})
            self.assertEquals(pack.mediafor("foo", [".mp3"]), "MP3RESULTFOO")
            self.assertEquals(pack.mediafor("foo", [".ogg", ".mp3"]), "MP3RESULTFOO")
            self.assertEquals(pack.mediafor("foo", [".junk", ".mp3"]), "MP3RESULTFOO")
        
        def testMediaForExtensionPriority(self):
            pack = MediaPack("Example", {"bar.mp3" : "MP3RESULTBAR", "bar.ogg" : "OGGRESULTBAR"})
            self.assertEquals(pack.mediafor("bar", [".mp3"]), "MP3RESULTBAR")
            self.assertEquals(pack.mediafor("bar", [".ogg"]), "OGGRESULTBAR")
            self.assertEquals(pack.mediafor("bar", [".ogg", ".mp3"]), "OGGRESULTBAR")
            self.assertEquals(pack.mediafor("bar", [".mp3", ".ogg"]), "MP3RESULTBAR")
    
        def testMediaForMissing(self):
            self.assertEquals(MediaPack("Example", {}).mediafor("hi", [".mp3"]), None)
        
        def testFromPath(self):
            def do(path):
                # Create enclosing directory
                packpath = os.path.join(path, "My Pack")
                os.mkdir(packpath)
                
                # Fill with dummy files
                for file in ["test.mp3", "BaZ.mP3", "nonsense"]:
                    utils.touch(os.path.join(packpath, file))
                
                # Ensure that we have a sane pack
                pack = MediaPack.frompath(packpath)
                self.assertEquals(pack.name, "My Pack")
                self.assertEquals(pack.packpath, packpath)
                self.assertEquals(pack.mediafor("test", [".mp3"]), os.path.join(packpath, "test.mp3"))
                self.assertEquals(pack.mediafor("BaZ", [".mp3"]), os.path.join(packpath, "BaZ.mP3"))
                self.assertEquals(pack.mediafor("nonsense", [".mp3"]), None)
            
            # Create a temporary directory with which to do our test
            utils.withtempdir(do)
        
    class LegacyMediaTest(unittest.TestCase):
        def testDiscoverNothing(self):
            self.assertEquals(discoverlegacymedia(None, []), None)
        
        def testAllLegacy(self):
            self.assertEquals(discoverlegacymedia(["hello.mp3", "world.ogg"], []), ["hello.mp3", "world.ogg"])
        
        def testDontMessWithCase(self):
            self.assertEquals(discoverlegacymedia(["hElLLo.mp3", "world.oGg"], []), ["hElLLo.mp3", "world.oGg"])
    
        def testNotLegacy(self):
            self.assertEquals(discoverlegacymedia(["HASH1.mp3", "HASH2.ogg"], [("hello.mp3", "HASH1.mp3"), ("world.ogg", "HASH2.ogg")]), [])
        
        def testNotLegacyImportedFromDirectory(self):
            self.assertEquals(discoverlegacymedia(["HASH1.mp3", "HASH2.ogg"], [(os.path.join("foo", "hello.mp3"), "HASH1.mp3"), (os.path.join("foo", "world.ogg"), "HASH2.ogg")]), [])
        
        def testNotLegacyImportedFromSeveralDirectories(self):
            self.assertEquals(discoverlegacymedia(["HASH1.mp3", "HASH2.ogg"], [(os.path.join("bar", "hello.mp3"), "HASH1.mp3"), (os.path.join("foo", "world.ogg"), "HASH2.ogg")]), [])
        
        def testDiscardInvalidImportedFiles(self):
            self.assertEquals(discoverlegacymedia(["HASH1.mp3"], [(os.path.join("foo", "hello.mp3"), "HASH1.mp3"), (os.path.join("foo", "world.ogg"), "HASH2.ogg")]), [])
    
    unittest.main()
