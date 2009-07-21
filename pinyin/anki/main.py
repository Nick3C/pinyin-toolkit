#!/usr/bin/env python
# -*- coding: utf-8 -*-

from PyQt4.QtGui import QDialog

import cjklib.dbconnector
import os
import shutil
import sqlalchemy

import pinyin.config
import pinyin.db.builder
import pinyin.forms.builddb
import pinyin.forms.builddbcontroller
from pinyin.logger import log
import pinyin.updater

import hooks
import mediamanager
import notifier
import utils

import statsandgraphs

hookbuilders = hooks.hookbuilders + [
    statsandgraphs.HanziGraphHook
  ]

class PinyinToolkit(object):
    def __init__(self, mw):
        # Right, this is more than a bit weird. The basic issue is that if we were
        # to just initialize() RIGHT NOW then we will hold the Python import lock,
        # because Anki __import__s its plugins. This ABSOLUTELY KILLS us when we
        # come to e.g. build the database on a background thread, because that code
        # naturally wants to import some stuff, but it doesn't hold the lock!
        #
        # To work around this issue, we carefully schedule initialization (and database
        # construction) for a time when Anki will not have caused us to hold the import lock.
        #
        # Debugging this was a fair bit of work!
        from anki.hooks import addHook
        addHook("init", lambda: self.initialize(mw))
    
    def initialize(self, mw):
        log.info("Pinyin Toolkit is initializing")
        
        # Build basic objects we use to interface with Anki
        thenotifier = notifier.AnkiNotifier()
        themediamanager = mediamanager.AnkiMediaManager(mw)
        
        # Open up the database
        database = self.openDatabase(mw, thenotifier)
        if database is None:
            # Eeek! Database building failed, so we better turn off the toolkit
            log.error("Database construction failed: disabling the Toolkit")
            return
        
        # Try and load the settings from the Anki config database
        settings = mw.config.get("pinyintoolkit")
        if settings is None:
            # Initialize the configuration with default settings
            config = pinyin.config.Config()
            utils.persistconfig(mw, config)
            
            # TODO: first-run activities:
            #  1) Guide user around the interface and what they can do
            #  2) Link to getting started guide
        else:
            # Initialize the configuration with the stored settings
            config = pinyin.config.Config(settings)
        
        # Build the updaters
        updaters = {
            'expression' : pinyin.updater.FieldUpdaterFromExpression(thenotifier, themediamanager, config, database),
            'reading'    : pinyin.updater.FieldUpdaterFromReading(config),
            'meaning'    : pinyin.updater.FieldUpdaterFromMeaning(config),
            'audio'      : pinyin.updater.FieldUpdaterFromAudio(thenotifier, themediamanager, config)
          }
        
        # Finally, build the hooks.  Make sure you store a reference to these, because otherwise they
        # get garbage collected, causing garbage collection of the actions they contain
        self.hooks = [hookbuilder(mw, thenotifier, themediamanager, config, updaters) for hookbuilder in hookbuilders]
        for hook in self.hooks:
            hook.install()
    
        # Tell Anki about the plugin
        mw.registerPlugin("Mandarin Chinese Pinyin Toolkit", 4)
        self.registerStandardModels()
    
    def openDatabase(self, mw, notifier):
        timestamp, satisfiers = pinyin.db.builder.getSatisfiers()
        dbpath = pinyin.utils.toolkitdir("pinyin", "db", "cjklib.db")
        
        if not(os.path.exists(dbpath)):
            # MUST rebuild
            compulsory = True
        elif os.path.getmtime(dbpath) < timestamp:
            # SHOULD rebuild
            compulsory = False
        else:
            # Do nothing
            compulsory = None
        
        if compulsory is not None:
            # We at least have the option to rebuild the DB: setup the builder
            dbbuilder = pinyin.db.builder.DBBuilder(satisfiers)
            
            # Show the form, which kicks off the builder and may give the user the option to cancel
            builddb = pinyin.forms.builddb.BuildDB(mw)
            # NB: VERY IMPORTANT to save the useless controller reference somewhere. This prevents the
            # QThread it spawns being garbage collected while the thread is still running! I hate PyQT4!
            _controller = pinyin.forms.builddbcontroller.BuildDBController(builddb, notifier, dbbuilder, compulsory)
            if builddb.exec_() == QDialog.Accepted:
                # Successful completion of the build process: replace the existing database, if any
                shutil.copyfile(dbbuilder.builtdatabasepath, dbpath)
            elif compulsory:
                # Eeek! The dialog was "rejected" despite being compulsory. This can only happen if there
                # was an error while building the database. Better give up now!
                return None
        
        # Finally, start the database connection to the (possibly fresh) DB
        return cjklib.dbconnector.DatabaseConnector.getDBConnector(sqlalchemy.engine.url.URL("sqlite", database=dbpath))
    
    def registerStandardModels(self):
        # This code was added at the request of Damien: one of the changes in the next
        # Anki version will be to make language-specific toolkits into plugins.
        #
        # The code sets up a 'template' model for users. We probably want to customize
        # this eventually, but for now it's a duplicate of the old code from Anki.
        
        import anki.stdmodels
        from anki.models import Model, CardModel, FieldModel

        # Mandarin
        ##########################################################################

        def MandarinModel():
           m = Model(_("Mandarin"))
           f = FieldModel(u'Expression')
           f.quizFontSize = 72
           m.addFieldModel(f)
           m.addFieldModel(FieldModel(u'Meaning', False, False))
           m.addFieldModel(FieldModel(u'Reading', False, False))
           m.addCardModel(CardModel(u"Recognition",
                                    u"%(Expression)s",
                                    u"%(Reading)s<br>%(Meaning)s"))
           m.addCardModel(CardModel(u"Recall",
                                    u"%(Meaning)s",
                                    u"%(Expression)s<br>%(Reading)s",
                                    active=False))
           m.tags = u"Mandarin"
           return m

        anki.stdmodels.models['Mandarin'] = MandarinModel
