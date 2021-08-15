
import sqlite3
from sqlite3 import Error
import pandas as pd
import numpy as np


DB_FILE_PATH = "delphi-bs.sqlite3"
conn = sqlite3.connect(DB_FILE_PATH)

def get_data(filename):
    df = pd.read_csv(filename, sep=';')
    df = df[['Jahr','Gemeinde','Geschlecht','Staatsangehoerigkeit','Anzahl']]
    #df = df.groupby(['datum'])['PREC [mm]'].agg(['sum']).reset_index()
    #df.rename(columns = {'sum': 'prec_mm'}, inplace=True)
    print(df.head())
    #df.to_parquet('./data/prec.pq')
    
    return df

def complete_data(df):
    #df = df.rename(columns={"staatsangehoerigkeit":"nationalitaet"})
    #df['alter_agg_10'] = 0
    #df['alter_agg_3'] = 0
    df['Ausland_Schweiz'] = np.where(df['Staatsangehoerigkeit'] == 'Schweiz', 'CH', 'Ausl')
    print(df.head())
    return df

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

    except Error as err:
        print(err)

        if sqlite3_conn is not None:
            sqlite3_conn.close()


def insert_values_to_table(table_name, df):
    """
    Open a csv file with pandas, store its content in a pandas data frame, change the data frame headers to the table
    column names and insert the data to the table
    :param table_name: table name in the database to insert the data into
    :param csv_file: path of the csv file to process
    :return: None
    """

    conn = connect_to_db(DB_FILE_PATH)

    if conn is not None:
        c = conn.cursor()

        # Create table if it is not exist
        # c.execute('CREATE TABLE IF NOT EXISTS ' + table_name +
        #          '(rank        INTEGER,'
        #          'title        VARCHAR,'
        #          'genre        VARCHAR,'
        #          'description  VARCHAR,'
        #          'director     VARCHAR,'
        #          'actors       VARCHAR,'
        #          'year_release INTEGER,'
        #          'runTime      INTEGER,'
        #          'rating       DECIMAL,'
        #          'votes        INTEGER,'
        #          'revenue      DECIMAL,'
        #          'metascore    INTEGER)')


        #df.columns = get_column_names_from_db_table(c, table_name)
        print(df.columns)

        df.to_sql(name=table_name, con=conn, if_exists='replace', index=False)

        conn.close()
        print('SQL insert process finished')
    else:
        print('Connection to database failed')


def get_column_names_from_db_table(sql_cursor, table_name):
    """
    Scrape the column names from a database table to a list
    :param sql_cursor: sqlite cursor
    :param table_name: table name to get the column names from
    :return: a list with table column names
    """

    table_column_names = 'PRAGMA table_info(' + table_name + ');'
    sql_cursor.execute(table_column_names)
    table_column_names = sql_cursor.fetchall()

    column_names = list()

    for name in table_column_names:
        column_names.append(name[1])

    return column_names


if __name__ == '__main__':
    df = get_data("./import/100126.csv")
    df = complete_data(df)
    insert_values_to_table('bevoelkerung', df)

