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
        log.info("Initalizing media located at %s", ziplocation)
        self.__name = name
        self.__zip = zipfile.ZipFile(ziplocation)
    
    def extractand(self, handler):
        # Get a temporary path and then create a subdirectory into which to extract.
        # The reasoning behind this is that the way we signal to the MediaPack which
        # pack something is in, is by the directory name it was imported from!
        baseextractdirpath = tempfile.mkdtemp()
        extractdirpath = os.path.join(baseextractdirpath, self.__name)
        os.mkdir(extractdirpath)
        
        # Extract the ZIP into a new directory
        log.info("Extracting media into %s", extractdirpath)
        for info in self.__zip.infolist():
            # Create the directory
            extractfilepath = os.path.join(extractdirpath, info.filename)
            utils.ensuredirexists(os.path.dirname(extractfilepath))
            
            # Extract the file
            file = open(extractfilepath, 'wb')
            file.write(self.__zip.read(info.filename))
            file.close()
            
            # Give the file to the handler
            handler(extractfilepath)
        
        # Blast the temporary directory and its extracted files
        log.info("Deleting extracted files from %s", extractdirpath)
        shutil.rmtree(extractdirpath)

class MediaPack(object):
    def __init__(self, name, media):
        # Normalize capitalisation for ease of lookup
        self.name = name
        self.media = dict([(name.lower(), filename) for name, filename in media.items()])
    
    def __str__(self):
        return self.name
    
    def __repr__(self):
        return "MediaPack(%s, %s)" % (repr(self.name), repr(self.media))
    
    def __eq__(self, other):
        if other == None:
            return False
        
        return self.name == other.name and self.media == other.media
    
    def __ne__(self, other):
        return not(self == other)
    
    def mediafor(self, basename, audioextensions):
        # Check all possible extensions in order of priority
        for extension in audioextensions:
            name = (basename + extension).lower()
            if name in self.media:
                return self.media[name]
        
        # No suitable media existed!
        return None
    
    @classmethod
    def discovermanualpacks(cls, mediadircontents):
        if not(mediadircontents):
            return []
        
        # We detect membership of the pack by looking at the filename. If
        # it is in the format foo5.extension then it is a candidate sound.
        # (Actually, we just add all files, because it doesn't do any harm to have too many)
        media = {}
        for filename in mediadircontents:
            log.info("Discovered %s -> %s (manual media)", filename, filename)
            media[filename] = filename
        
        # Return the pack, if we found any media at all
        if len(media) > 0:
            return [MediaPack("Manual", media)]
        else:
            return []
    
    @classmethod
    def discoverimportedpacks(cls, mediadircontents, mediaindex):
        # Normalize case from the directory listing so that the removal check works reliably
        if mediadircontents != None:
            mediadircontents = [os.path.normcase(mediadircontent) for mediadircontent in mediadircontents]
        
        # Iterate over files and pluck them out into this dictionary of dictionaries
        known_pack_contents = {}
        for orig_path, filename in mediaindex:
            # Note that orig_path is a FULL path so need to call os.path.basename on it
            orig_dir, orig_filename = os.path.split(orig_path)
            orig_containing_dir = os.path.basename(os.path.normpath(orig_dir))
            
            # Remove the file from consideration for the manual media lookup stage
            try:
                # If we couldn't list the media directory we aren't going to add any manual
                # packs, so it's alright not to remove it from the list of paths (and we couldn't anyway).
                if mediadircontents != None:
                    # NB: we can only do this reliably because we normalized the case above
                    mediadircontents.remove(os.path.normcase(filename))
            except:
                # Tried to remove the file from the directory listing, but it's not actually
                # in the list.  This means that the database entry is actually out of date and
                # we should ignore it
                log.info("Out of date database entry for %s -> %s", orig_filename, filename)
                continue
            
            # If we can't determine a pack name, default it to Imported:
            if orig_containing_dir == None or orig_containing_dir.strip('.') == '':
               orig_containing_dir = "Imported"
            
            # Find the pack if we already have it:
            if orig_containing_dir in known_pack_contents:
                # An old pack: obtain the contents so far
                pack_contents = known_pack_contents.get(orig_containing_dir)
            else:
                # A new pack: create an empty dictionary of files to start adding to
                pack_contents = {}
                known_pack_contents[orig_containing_dir] = pack_contents
            
            # Save this bit of media
            log.info("Discovered %s -> %s (imported media for %s)", orig_filename, filename, orig_containing_dir)
            pack_contents[orig_filename] = filename
        
        # Turn the pack contents into some actual packs and return them:
        return mediadircontents, [MediaPack(pack_name, pack_contents) for pack_name, pack_contents in known_pack_contents.items()]
    
    @classmethod
    def discover(cls, mediadircontents, mediaindex):
        # Media comes from two sources:
        #  1) Media imported into the media directory by Anki. We detect this by consulting the media
        #     database and looking for files whose original path had the foo5.extension format.
        #     NB: we don't want include files that we can attribute to an imported pack to the Manual one,
        #     so this method returns the REMAINING files in the contents.
        mediadircontents, importedpacks = cls.discoverimportedpacks(mediadircontents, mediaindex)
        
        #  2) Media copied into the media directory by the user. All of the sounds from this
        #     location are added to one pack, which is called Manual.
        return cls.discovermanualpacks(mediadircontents) + importedpacks

if __name__ == "__main__":
    import unittest
    
    class MediaPackTest(unittest.TestCase):
        def testNormalizeCase(self):
            self.assertEquals(MediaPack("Manual", {"A" : "b"}), MediaPack("Manual", {"a" : "b"}))
            self.assertNotEquals(MediaPack("Manual", {"A" : "b"}), MediaPack("Manual", {"A" : "B"}))
        
        def testDiscoverNothing(self):
            self.assertEquals(MediaPack.discover(None, []), [])
        
        def testDiscoverManual(self):
            self.assertEquals(MediaPack.discover(["hello.mp3", "world.ogg"], []),
                              [MediaPack("Manual", {"hello.mp3" : "hello.mp3", "world.ogg" : "world.ogg"})])
        
        def testDiscoverManualNormalizedCase(self):
            self.assertEquals(MediaPack.discover(["hElLLo.mp3", "world.oGg"], []),
                              [MediaPack("Manual", {"helllo.mp3" : "hElLLo.mp3", "world.ogg" : "world.oGg"})])
    
        def testDiscoverImported(self):
            self.assertEquals(MediaPack.discover(["HASH1.mp3", "HASH2.ogg"], [("hello.mp3", "HASH1.mp3"), ("world.ogg", "HASH2.ogg")]),
                              [MediaPack("Imported", {"hello.mp3" : "HASH1.mp3", "world.ogg" : "HASH2.ogg"})])
        
        def testDiscoverImportedFromDirectory(self):
            self.assertEquals(MediaPack.discover(["HASH1.mp3", "HASH2.ogg"], [(os.path.join("foo", "hello.mp3"), "HASH1.mp3"), (os.path.join("foo", "world.ogg"), "HASH2.ogg")]),
                              [MediaPack("foo", {"hello.mp3" : "HASH1.mp3", "world.ogg" : "HASH2.ogg"})])
        
        def testDiscoverImportedFromSeveralDirectories(self):
            self.assertEquals(MediaPack.discover(["HASH1.mp3", "HASH2.ogg"], [(os.path.join("bar", "hello.mp3"), "HASH1.mp3"), (os.path.join("foo", "world.ogg"), "HASH2.ogg")]),
                              [MediaPack("foo", {"world.ogg" : "HASH2.ogg"}), MediaPack("bar", {"hello.mp3" : "HASH1.mp3"})])
        
        def testDiscoverImportedFromDeepDirectory(self):
            self.assertEquals(MediaPack.discover(["HASH1.mp3"], [(os.path.join(os.path.join("foo", "bar"), "hello.mp3"), "HASH1.mp3")]),
                              [MediaPack("bar", {"hello.mp3" : "HASH1.mp3"})])
        
        def testDiscoverDiscardInvalidImportedFiles(self):
            self.assertEquals(MediaPack.discover(["HASH1.mp3"], [(os.path.join("foo", "hello.mp3"), "HASH1.mp3"), (os.path.join("foo", "world.ogg"), "HASH2.ogg")]),
                              [MediaPack("foo", {"hello.mp3" : "HASH1.mp3"})])
        
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
    
    unittest.main()
