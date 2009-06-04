#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import urllib
import shutil
import tempfile
import zipfile

from logger import log
import utils

def downloadAndInstallMandarinSounds(notifier, mediamanager, config):
    log.info("Downloading Mandarin sound pack")
        
    # Download ZIP, using cache if necessary
    downloader = MediaDownloader(mediamanager.mediadir())
    the_media = downloader.download("Mandarin Sounds", config.mandarinsoundsurl,
                                    lambda: notifier.info("Downloading the sounds - this might take a while!"))

    # Install each file from the ZIP into our media folder
    the_media.installpack(mediamanager.mediadir())

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
    
    class MediaDownloaderTest(unittest.TestCase):
        def testDownload(self):
            def do(path):
                # Initial download: should be prompted about the time usage
                gotprompt, downloaded = self.download(path, "Example Name", "http://www.google.com")
                self.assertTrue(gotprompt)
                self.assertEquals(downloaded.name, "Example Name")
                
                # Second download: should NOT be prompted due to getting the same file again
                gotprompt, downloadedagain = self.download(path, "Example Name", "http://www.google.com")
                self.assertFalse(gotprompt)
                self.assertEquals(downloadedagain.name, "Example Name")
                self.assertEquals(downloadedagain.zippath, downloaded.zippath)
            
            utils.withtempdir(do)
        
        def testDownloadToSecuredLocation(self):
            # TODO: work out a way to drop privileges so I can write this test
            return
            
            import sys
            if sys.platform == "win32":
                # Can't run this test on Windows
                return
            
            def do(path):
                # Make the path inaccessible
                import pwd
                rootuid = pwd.getpwnam("root")[2]
                os.chown(path, rootuid, rootuid)
                
                # Initial download: should be prompted about the time usage
                gotprompt, downloaded = self.download(path, "Example Name", "http://www.google.com")
                self.assertTrue(gotprompt)
                self.assertEquals(downloaded.name, "Example Name")
            
                # Second download: SHOULD be prompted because we couldn't cache the file last time
                gotprompt, downloadedagain = self.download(path, "Example Name", "http://www.google.com")
                self.assertTrue(gotprompt)
                self.assertEquals(downloadedagain.name, "Example Name")
                self.assertNotEquals(downloadedagain.zippath, downloaded.zippath)
            
            utils.withtempdir(do)
        
        # Helpers
        def download(self, path, name, zipurl):
            gotprompt = [False]
            def prompted():
                gotprompt[0] = True
            
            downloaded = MediaDownloader(path).download(name, zipurl, downloadprompt=prompted)
            return gotprompt[0], downloaded
    
    class DownloadedMediaTest(unittest.TestCase):
        binarycontents = "".join([chr(n) for n in range(0, 255)])
        
        def testInstallPack(self):
            def do(path):
                DownloadedMedia("Example Pack", self.createZipFile(path)).installpack(path)
                
                # Verify the basic file system layout
                packpath = os.path.join(path, "Example Pack")
                self.assertEquals(os.listdir(packpath), ["a.mp3", "b.mp3", "binary", "nested"])
                self.assertEquals(os.listdir(os.path.join(packpath, "nested")), ["c.mp3"])
                
                # Verify file contents
                self.assertEquals(utils.filecontents(os.path.join(packpath, "a.mp3")), "hello!")
                self.assertEquals(utils.filecontents(os.path.join(packpath, "b.mp3")), "world!")
                self.assertEquals(utils.filecontents(os.path.join(packpath, "binary")), self.binarycontents)
                self.assertEquals(utils.filecontents(os.path.join(packpath, "nested", "c.mp3")), "^_^")
            
            utils.withtempdir(do)
        
        def testInstallPackTwice(self):
            def do(path):
                downloaded = DownloadedMedia("Example Pack", self.createZipFile(path))
                
                downloaded.installpack(path)
                self.assertTrue(os.path.exists(os.path.join(path, "Example Pack")))
                self.assertFalse(os.path.exists(os.path.join(path, "Example Pack 1")))
                
                downloaded.installpack(path)
                self.assertTrue(os.path.exists(os.path.join(path, "Example Pack 1")))
            
            utils.withtempdir(do)
        
        # Helpers
        def createZipFile(self, path):
            zippath = os.path.join(path, "junk.zip")
            
            thezip = zipfile.ZipFile(zippath, 'w')
            thezip.writestr("a.mp3", "hello!")
            thezip.writestr("b.mp3", "world!")
            thezip.writestr("binary", self.binarycontents)
            thezip.writestr(os.path.join("nested", "c.mp3"), "^_^")
            thezip.close()
            
            return zippath
    
    class MediaPackTest(unittest.TestCase):
        def testNormalizeCase(self):
            self.assertEquals(MediaPack("Manual", {"A" : "b"}), MediaPack("Manual", {"a" : "b"}))
            self.assertNotEquals(MediaPack("Manual", {"A" : "b"}), MediaPack("Manual", {"A" : "B"}))
        
        def testName(self):
            self.assertEquals(MediaPack(os.path.join("foo", "bar"), {}).name, "bar")
        
        def testSummarize(self):
            pack = MediaPack("Example", { "a": "a.mp3", "b" : "b.mP3", "c" : "c.oGG" })
            self.assertEquals(pack.summarize([".mp3", ".ogg"]), "Example (2 .mp3 files, 1 .ogg file)")
            self.assertEquals(pack.summarize([".mp3"]), "Example (2 .mp3 files)")
            self.assertEquals(pack.summarize([".junk"]), "Example")
        
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
