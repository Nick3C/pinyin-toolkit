#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import re
import urllib
import urlparse
import zipfile

import pinyin.utils as utils


def cedictParser(page):
    m_date = re.search('Latest release\\: <strong>([0-9]{4})-([0-9]{2})-([0-9]{2}) ', page)
    m_page = re.search('<a href="([^"]*cedict_[^"]+_ts_utf-8_mdbg\\.zip)">', page)
    return utils.bind_none(m_page, lambda m_page: utils.bind_none(m_date, lambda m_date: (m_page.group(1), (int(m_date.group(1)), int(m_date.group(2)), int(m_date.group(3))))))

cedictUseful = lambda _: True # The zip contains a single file - the UTF8 dictionary. Perfect.

def handedictParser(page):
    return utils.bind_none(re.search('<a href="([^"]*handedict-([0-9]{8})\\.zip)">', page), lambda m: (m.group(1), splitRunOnDate(m.group(2))))

handedictUseful = lambda name: name.endswith("handedict_nb.u8")

def cfdictParser(page):
    return utils.bind_none(re.search('<a href="([^"]*cfdict-([0-9]{8})\\.zip)">', page), lambda m: (m.group(1), splitRunOnDate(m.group(2))))

cfdictUseful = lambda name: name.endswith("cfdict_nb.u8")

dictionaries = [("CEDICT", "http://usa.mdbg.net/chindict/chindict.php?page=cc-cedict", cedictParser, cedictUseful),
                ("HanDeDict", "http://www.chinaboard.de/chinesisch_deutsch.php?mode=dl&w=8", handedictParser, handedictUseful),
                ("CFDICT", "http://www.chinaboard.de/fr/cfdict.php?mode=dl&w=8", cfdictParser, cfdictUseful)]


def splitRunOnDate(date):
    return (int(date[0:4]), int(date[4:6]), int(date[6:8]))

def runOnDate(date_tuple):
    return "%04d%02d%02d" % date_tuple


if __name__ == '__main__':
    for name, url, parser, useful in dictionaries:
        print "Querying download page for", name
    
        # Download the contents of the download page itself
        f = urllib.urlopen(url)
        try:
            page = f.read()
        finally:
            f.close()
    
        # Search it for the relative url we care about
        parse_result = parser(page)
        if parse_result is None:
            raise IOError("Couldn't parse the download page for %s" % name)
    
        zip_relative_url, date = parse_result
        print "> Identified version", runOnDate(date), "at", zip_relative_url
    
        # Great - download the dictionary to the well-known location
        zip_path = utils.toolkitdir("pinyin", "dictionaries", name.lower() + "-" + runOnDate(date) + ".zip")
        if os.path.exists(zip_path):
            print "> Skipping download because it already exists"
        else:
            urllib.urlretrieve(urlparse.urljoin(url, zip_relative_url), zip_path)
            print "> Downloaded to", zip_path
        
        # Trim the zip files down to size by removing useless dictionaries:
        
        # a) Gather the information we actually want to keep
        sourcezip = zipfile.ZipFile(zip_path, "r")
        target = {}
        for name in sourcezip.namelist():
            if not useful(name):
                print "> Removing", name, "from file"
                continue
            
            target[name] = sourcezip.read(name)
        sourcezip.close()
        
        # b) Truncate the zip file and write back just that information
        targetzip = zipfile.ZipFile(zip_path, "w")
        for name, contents in target.items():
            targetzip.writestr(name, contents)
        targetzip.close()