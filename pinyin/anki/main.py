import os

import pinyin.dictionaryonline
import pinyin.dictionary

import hooks
import updater
import utils
import notifier


class PinyinToolkit(object):
    def __init__(self, mw, config):
        # Test internet connectivity by performing a gTrans call.
        # If this call fails then translations are disabled until Anki is restarted.
        # This prevents a several second delay from occuring when changing a field with no internet
        if (config.fallbackongoogletranslate):
            config.fallbackongoogletranslate = pinyin.dictionaryonline.gCheck(config.dictlanguage)
        
        # Store the configuration and mw
        self.mw = mw
        self.config = config
        
        # Build notifier
        self.notifier = notifier.AnkiNotifier()
        
        # Build the updater
        dictionary = pinyin.dictionary.PinyinDictionary.load(config.dictlanguage, needmeanings=utils.needmeanings(config))
        availablemedia = self.discovermedia()
        self.updater = updater.FieldUpdater(self.config, dictionary, availablemedia, self.notifier)
    
    def installhooks(self):
        # Install all hooks
        for hookbuilder in [hooks.FocusHook, hooks.SampleSoundsHook, hooks.MissingInformationHook]:
            hookbuilder(self.mw, self.notifier, self.config, self.updater).install()
    
        # Tell Anki about the plugin
        self.mw.registerPlugin("Mandarin Chinese Pinyin Toolkit", 4)
    
    def discovermedia(self):
        try:
            available_media = {}
    
            # Media comes from two sources:
            #  1) Media copied into the media directory by the user. We detect this by looking
            #     at the filename. If it is in the format foo5.extension then it is a candidate sound.
            mediaDir = self.mw.deck.mediaDir()
            if mediaDir:
                # An accessible mediaDir exists - look through it for files
                available_media.update(dict([(filename, filename) for filename in os.listdir(mediaDir)]))
        
            #  2) Media imported into the media directory by Anki. We detect this by consulting the media
            #     database and looking for files whose original path had the foo5.extension format.
            for orig_path, filename in self.mw.deck.s.all("select originalPath, filename from media"):
                # Note that originalPath is a FULL path so need to call os.path.basename on it
                available_media[os.path.basename(orig_path)] = filename
        except IOError:
            available_media = {}
        
        return available_media