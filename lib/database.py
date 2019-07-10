"""
HXEB database class
"""

import pymssql


class Database:
    def __init__(self, config):
        self.conn = pymssql.connect(
            host=config.HXEB_DB_HOST,
            user=config.HXEB_DB_USER,
            password=config.HXEB_DB_PASSWORD,
            database=config.HXEB_DB_NAME,
        )

    def cursor(self):
        return self.conn.cursor(as_dict=True)

    def read_sql(self, sql):
        cursor = self.cursor()
        cursor.execute(sql)
        data = cursor.fetchall()
        cursor.close()

        return data
