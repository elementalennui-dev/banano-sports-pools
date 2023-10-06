import pandas as pd
from sqlalchemy import create_engine, inspect
from config import POSTGRES_URL
from database_helpers.nflDatabaseHelper import NFLDatabase
from database_helpers.rwcDatabaseHelper import RWCDatabase
from database_helpers.cwcDatabaseHelper import CWCDatabase
from database_helpers.mlbDatabaseHelper import MLBDatabase

class DataBaseHelper():

    def __init__(self):
        self.engine = create_engine(POSTGRES_URL)
        self.nfl = NFLDatabase(self.engine)
        self.rwc = RWCDatabase(self.engine)
        self.cwc = CWCDatabase(self.engine)
        self.mlb = MLBDatabase(self.engine)

    def writeDeposit(self, insert_df, table):
        conn = self.engine.connect()
        insert_df.to_sql(table, con=conn, if_exists="append", index=False)
        conn.close()
        return({"ok": True})

    def checkBlockExists(self, table, block):
        conn = self.engine.connect()

        inspector_gadget = inspect(self.engine)
        tables = inspector_gadget.get_table_names()
        table_exists = table in tables

        if table_exists:
            query = f"SELECT count(*) as block_exists from {table} where block = '{block}';"
            df2 = pd.read_sql(query, con=conn)
            block_exists = df2["block_exists"].values[0]

            if block_exists > 0:
                return ({"ok": False, "message": "Block already exists in database."})
            else:
                return ({"ok": True, "message": "Block is valid."})
        else:
            return ({"ok": True, "message": "Table doesn't exist in the database."})
