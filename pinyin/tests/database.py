# Globally shared database connection
database = cjklib.dbconnector.DatabaseConnector.getDBConnector(sqlalchemy.engine.url.URL("sqlite", database=toolkitdir("pinyin", "db", "cjklib.db")))
