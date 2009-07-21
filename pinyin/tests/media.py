# -*- coding: utf-8 -*-

import unittest

from pinyin.media import *


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
