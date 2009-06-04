import os

from pinyin.logger import log
import pinyin.media
import pinyin.utils

class AnkiMediaManager(object):
    def __init__(self, mw):
        self.mw = mw
    
    def mediadir(self):
        return os.path.join(pinyin.utils.pinyindir(), "media")

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
