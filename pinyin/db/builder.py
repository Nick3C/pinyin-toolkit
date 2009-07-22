#!/usr/bin/env python
# -*- coding: utf-8 -*-
import cjklib.build
import cjklib.dbconnector
import re
import shutil
import sqlalchemy
import tempfile
import os
import zipfile

from pinyin.logger import log
import pinyin.utils


class DBBuilder(object):
    wantgroups = [
        # Dictionaries - do NOT include the _Words tables: we want the full meanings only:
        'CEDICT', 'CFDICT', 'HanDeDict',
        # Some basic Mandarin data:
        'CharacterPinyin', 'PinyinSyllables', 'PinyinInitialFinal',
        # All ShapeLookupData:
        #'Strokes', 'StrokeOrder', 'CharacterDecomposition',
        #'LocaleCharacterVariant', 'StrokeCount', 'ComponentLookup',
        #'CharacterVariant', 'ZVariants'
      ]

    cjkdatapath = pinyin.utils.toolkitdir("pinyin", "vendor", "cjklib", "cjklib", "data")

    builtdatabasepath = property(lambda self: os.path.join(self.dictionarydatapath, "cjklib.db"))

    def __init__(self, satisfiers):
        self.satisfiers = satisfiers
        self.dictionarydatapath = tempfile.mkdtemp()
        self.cjkdbbuilder = None
    
    def __del__(self):
        try:
            log.info("Cleaning up temporary dictionary builder directory")
            shutil.rmtree(self.dictionarydatapath)
        except IOError:
            pass
    
    def build(self):
        # [1/4]: copy and extract necessary files into a location cjklib can deal with
        log.info("Copying in dictionary data")
        for requirement, satisfier in self.satisfiers:
            satisfier(os.path.join(self.dictionarydatapath, requirement))
        
        # [2/4]: setup the database builder with a standard set of requirements
        log.info("Initializing builder")
        database = cjklib.dbconnector.DatabaseConnector.getDBConnector(sqlalchemy.engine.url.URL("sqlite", database=self.builtdatabasepath))
        self.cjkdbbuilder = cjklib.build.DatabaseBuilder(
            dbConnectInst=database,
            # We need to turn quiet on, because Anki throws a hissy fit if you write to stderr
            quiet=True, rebuildExisting=False, noFail=False,
            dataPath=[self.dictionarydatapath, self.cjkdatapath],
            prefer=['CharacterVariantBMPBuilder', 'CombinedStrokeCountBuilder',
                    'CombinedCharacterResidualStrokeCountBuilder',
                    'HanDeDictFulltextSearchBuilder', 'UnihanBMPBuilder'])
        
        # [3/4]: build the database
        log.info("Building the cjklib database: the target file is %s", self.builtdatabasepath)
        self.cjkdbbuilder.build(DBBuilder.wantgroups)
        
        # [4/4]: clean up, so that we don't get errors if (when) the temporary database is deleted
        database.connection.close()
        del database.connection
        database.engine.dispose()
        del database.engine


def getSatisfiers():
    dictionarydir = lambda *components: pinyin.utils.toolkitdir("pinyin", "dictionaries", *components)
    
    def fileSource(path):
        def inner():
            source = dictionarydir(path)
            if os.path.exists(source):
                return path, os.path.getmtime(source), lambda target: shutil.copyfile(source, target)
            else:
                return None
        
        return inner
    
    def plainArchiveSource(path, pathinzip):
        def inner():
            zipsource = dictionarydir(path)
            if not(os.path.exists(zipsource)):
                return None
            
            def go(target):
                sourcezip = zipfile.ZipFile(zipsource, "r")
            
                targetfile = open(target, 'w')
                try:
                    targetfile.write(sourcezip.read(os.path.join(*pathinzip)))
                finally:
                    targetfile.close()
            
            return path + ":" + pathinzip, os.path.getmtime(zipsource), go
        
        return inner
    
    def timestampedArchiveSource(pathpattern, pathinzippattern):
        def inner():
            path, timestamp = None, None
            for file in os.listdir(dictionarydir()):
                match = re.match(pathpattern % "(.+)", file)
                if match:
                    path, timestamp = match.group(0), match.group(1)
                    break
            
            if path is None:
                return None
            
            return plainArchiveSource(path, [pizp % timestamp for pizp in pathinzippattern])
        
        return inner
    
    requirements = {
        "cedict_ts.u8" : [fileSource("cedict_ts.u8"), plainArchiveSource("cedict_1_0_ts_utf-8_mdbg.zip", ["cedict_ts.u8"]),
                          plainArchiveSource("shipped.zip", ["cedict_ts.u8"])],
        "handedict.u8" : [fileSource("handedict_nb.u8"), timestampedArchiveSource("handedict-%s.zip", ["handedict-%s", "handedict_nb.u8"]),
                          plainArchiveSource("shipped.zip", ["handedict_nb.u8"])],
        "cfdict.u8"    : [fileSource("cfdict_nb.u8"), timestampedArchiveSource("cfdict-%s.zip", ["cfdict-%s", "cfdict_nb.u8"]),
                          plainArchiveSource("shipped.zip", ["cfdict_nb.u8"])],
        "Unihan.txt"   : [fileSource("Unihan.txt"), plainArchiveSource("Unihan.zip", ["Unihan.txt"]),
                          plainArchiveSource("shipped.zip", ["Unihan.txt"])]
      }
    
    maxtimestamp = 0
    satisfiers = []
    for requirement, sources in requirements.items():
        success = False
        for source in sources:
            timestampsatisfier = source()
            if timestampsatisfier:
                satisfiedby, timestamp, satisfier = timestampsatisfier
                log.info("The requirement for %s was satisified by %s (with a timestamp of %d)", requirement, satisfiedby, timestamp)
                
                maxtimestamp = max(maxtimestamp, timestamp)
                satisfiers.append((requirement, satisfier))
                
                success = True
                break
        
        if not(success):
            raise IOError("Couldn't satisfy our need for '%s' during dictionary generation" % requirement)
    
    return maxtimestamp, satisfiers

if __name__ == "__main__":
    DBBuilder(getSatisfiers()[1]).build()