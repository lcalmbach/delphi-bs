import pandas as pd
import sqlalchemy as sql
import sqlite3

conn = ''

def connect_to_db(db_file):
    """
    Connect to an SQlite database, if db file does not exist it will be created
    :param db_file: absolute or relative path of db file
    :return: sqlite3 connection
    """
    sqlite3_conn = None
    
    
    try:
        sqlite3_conn = sqlite3.connect(db_file)
        return sqlite3_conn
    except:
        print('error')
        if sqlite3_conn is not None:
            sqlite3_conn.close()

def execute_non_query(cmd: str, cn)-> bool:
    """
    Executes a stored procedure, without a return value. it can only be applied to 
    the local database
    """

    ok = False
    _cursor = cn.cursor()
    try:
        _cursor.execute(cmd)
        conn.commit()
        ok = True
    except Exception as ex:
        pass
    return ok
    
    
def execute_query(query: str, cn) -> pd.DataFrame:
    """
    Executes a query and returns a dataframe with the results
    """

    ok= False
    result = None
    try:
        result = pd.read_sql_query(query, cn)
        ok = True
    except Exception as ex:
        print(ex)

    return result


def get_single_value(qry, conn, col) -> str:
    df = execute_query(qry, conn)
    return(df[col][0])

def get_distinct_values(column_name, table_name, dataset_id, criteria):
    """
    Returns a list of unique values from a defined code column.
    """
    criteria = (' AND ' if criteria > '' else '') + criteria
    query = f"SELECT {column_name} FROM {table_name} where dataset_id = {dataset_id} {and_expression} group by {column_name} order by {column_name}"
    result = execute_query(query, conn)
    result = result[column_name].tolist()
    return result
