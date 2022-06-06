import pandas as pd
from datetime import timedelta


def select_all(cursor, table):
    cols_query = 'SHOW COLUMNS FROM ' + table
    data_query = 'SELECT * FROM ' + table

    cursor.execute(cols_query)
    cols = cursor.fetchall()
    columns = [col[0] for col in cols]

    cursor.execute(data_query)
    data = cursor.fetchall()

    return columns, data


def get_data(conn, table):

    local_cursor = conn.cursor()

    columns, data = select_all(local_cursor, table)
    df = pd.DataFrame(data, columns=columns)

    local_cursor.close()

    return df

def get_key_list(cursor, insert_table):

    columns, data = select_all(cursor, insert_table)
    df = pd.DataFrame(data, columns=columns)

    return df['run_date']


def get_method(row, keys):

    if row['Date'] in str(keys):
        return 'update'
    return 'insert'


def insert_record(conn, table, date, miles):

    local_cursor = conn.cursor()

    insert_query = "INSERT INTO " + table + " (run_date, miles) VALUES ('" + str(date) + "', " + str(miles) + ")"
    local_cursor.execute(insert_query)
    conn.commit()

    local_cursor.close()


def update_record(conn, table, date, miles):

    local_cursor = conn.cursor()

    update_query = "UPDATE " + table + " SET miles = " + str(miles) + " WHERE run_date = '" + str(date) + "'"
    # update_query = "UPDATE " + table + " SET miles = " + str(miles) + " WHERE runDataID = " + str(ID)

    local_cursor.execute(update_query)
    conn.commit()

    local_cursor.close()


def update_database(conn, updates, inserts, insert_table):

    local_cursor = conn.cursor()

    keys = get_key_list(local_cursor, insert_table)

    for index, row in updates.iterrows():

        update_record(conn, insert_table, row['Date'], row['Miles'])

    for index, row in inserts.iterrows():

        insert_record(conn, insert_table, row['Date'], row['Miles'])
        
##        method = get_method(row, keys)
##
##        if method == 'insert':
##            insert_record(conn, insert_table, row['Date'], row['Miles'])
##        elif method == 'update':
##            update_record(conn, insert_table, row['Date'], row['Miles'])


