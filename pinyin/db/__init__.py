import cjklib.dbconnector
import sqlalchemy

import pinyin.utils
from pinyin.logger import log


dbpath = pinyin.utils.toolkitdir("pinyin", "db", "cjklib.db")

database = pinyin.utils.Thunk(lambda: cjklib.dbconnector.DatabaseConnector.getDBConnector({ "url" : sqlalchemy.engine.url.URL("sqlite", database=dbpath) }))
