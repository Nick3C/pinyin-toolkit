#!/usr/bin/env python
# -*- coding: utf-8 -*-
import re
import urllib
import urlparse

import pinyin.utils as utils


def cedictParser(page):
    m_date = re.search('Latest release\\: <strong>([0-9]{4})-([0-9]{2})-([0-9]{2}) ', page)
    m_page = re.search('<a href="([^"]*cedict_[^"]+_ts_utf-8_mdbg\\.zip)">', page)
    return utils.bind_none(m_page, lambda m_page: utils.bind_none(m_date, lambda m_date: (m_page.group(1), (int(m_date.group(1)), int(m_date.group(2)), int(m_date.group(3))))))

def handedictParser(page):
    return utils.bind_none(re.search('<a href="([^"]*handedict-([0-9]{8})\\.zip)">', page), lambda m: (m.group(1), splitRunOnDate(m.group(2))))

def cfdictParser(page):
    return utils.bind_none(re.search('<a href="([^"]*cfdict-([0-9]{8})\\.zip)">', page), lambda m: (m.group(1), splitRunOnDate(m.group(2))))

dictionaries = [("CEDICT", "http://usa.mdbg.net/chindict/chindict.php?page=cc-cedict", cedictParser),
                ("HanDeDict", "http://www.chinaboard.de/chinesisch_deutsch.php?mode=dl&w=8", handedictParser),
                ("CFDICT", "http://www.chinaboard.de/fr/cfdict.php?mode=dl&w=8", cfdictParser)]


def splitRunOnDate(date):
    return (int(date[0:4]), int(date[4:6]), int(date[6:8]))

def runOnDate(date_tuple):
    return "%04d%02d%02d" % date_tuple


if __name__ == '__main__':
    for name, url, parser in dictionaries:
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
        urllib.urlretrieve(urlparse.urljoin(url, zip_relative_url), zip_path)
        print "> Downloaded to", zip_path