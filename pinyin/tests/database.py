import cjklib.dbconnector
import sqlalchemy

import pinyin.utils


# Globally shared database connection
url = sqlalchemy.engine.url.URL("sqlite", database=pinyin.utils.toolkitdir("pinyin", "db", "cjklib.db"))
database = cjklib.dbconnector.DatabaseConnector.getDBConnector(url)
