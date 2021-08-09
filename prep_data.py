# script initializes data from a csv file containing all data upto now. the data is aggregated as daily values and saved in the parquet format
# for fast retrievel into pandas. in the app, this local data is read first, if it contains the data from yesterday, it is used as is, otherwise, 
# new data is fetched from data.bs and added to the pq, which then is uptodate for the next user.

import pandas as pd
import sqlalchemy as sql


def save_db_table(table_name: str, df: pd.DataFrame, fields: list):
    ok = False
    connect_string = 'sqlite:///delphi-bs.sqlite3'
    try:
        sql_engine = sql.create_engine(connect_string, pool_recycle=3600)
        db_connection = sql_engine.connect()
    except Exception as ex:
        print(ex)

    print(db_connection)
    try:
        if len(fields) > 0:
            df = df[fields]
        df.to_sql(table_name, db_connection, if_exists='append', chunksize=20000, index=False)
        ok = True
    except ValueError as vx:
        print(vx)
    except Exception as ex:
        print(ex)
    finally:
        db_connection.close()
        return ok

df = pd.read_excel("./import/t14-1-01.xlsx")
print(df.head())
ok = save_db_table('spitaeler',df,[])
print(ok)
