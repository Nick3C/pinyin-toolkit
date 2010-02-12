import os

import anki.media

from pinyin.logger import log
import pinyin.media
import pinyin.utils

class AnkiMediaManager(object):
    def __init__(self, mw):
        self.mw = mw
    
    def mediadir(self):
        # Create the plugin media directory, or later code that tries to
        # e.g. enumerate the contents will get a nasty shock (see bug #31).
        themediadir = pinyin.utils.toolkitdir("pinyin", "media")
        pinyin.utils.ensuredirexists(themediadir)
        return themediadir

    def discovermediapacks(self):
        packs = []
        themediadir = self.mediadir()
        for packname in os.listdir(themediadir):
            # Skip the download cache directory
            if packname.lower() == "downloads":
                continue
            
            # Only try and process directories as packs:
            packpath = os.path.join(themediadir, packname)
            if os.path.isdir(packpath):
                log.info("Considering %s as a media pack", packname)
                packs.append(pinyin.media.MediaPack.frompath(packpath))
            else:
                log.info("Ignoring the file %s in the media directory", packname)
        
        return packs
    
    def importtocurrentdeck(self, file):
        return self.mw.deck.addMedia(file)

    def alreadyimported(self, file):
        return os.path.exists(os.path.join(self.mw.deck.mediaDir(create=False), anki.media.mediaFilename(file)))
