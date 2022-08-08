import sqlalchemy
import pandas as pd
from datetime import datetime


class Database:
    """
    Wrapper for sqlalchemy, pymysql, and pandas.
    """

    def __init__(self, host, database, user, password):
        self.host = host
        self.database = database
        self.user = user
        self.password = password
        self.engine = None
        # self.conn = None

        self.open()

    def open(self):
        try:
            self.engine = sqlalchemy.create_engine(f"mysql+pymysql://{self.user}:{self.password}@{self.host}/{self.database}")
            # self.conn = self.engine.connect()
        except Exception as e:
            print(f"Error connecting to database: {e}")
            return

    # def close(self):
        # self.conn.close()

    @staticmethod
    def get_where_clause(where: dict = None):
        where_clause = " WHERE "
        if where is None:
            return ""

        where_clause += " AND ".join([f"{key} = {value}" for key, value in where.items()])
        return where_clause

    @staticmethod
    def get_by_clause(clause_type: str, columns: list):
        if columns is None:
            return ""

        columns = ", ".join(columns)
        by_clause = f"{clause_type} BY {columns}"

        return by_clause

    def get(self, table: str, columns: list, where: dict = None,
            order_by: list = None, group_by: list = None) -> pd.DataFrame:
        """
        Retrieves data from a table.
        :param table: Target table
        :param columns: Columns to be retrieved
        :param where: Filter conditions
        :param order_by: Sort
        :param group_by: Organize
        :return: pandas DataFrame (empty if no rows returned, None on error)
        """
        columns = ", ".join(columns)
        where_clause = self.get_where_clause(where)
        order_by_clause = self.get_by_clause("ORDER", order_by)
        group_by_clause = self.get_by_clause("GROUP", group_by)

        query = f"SELECT {columns} FROM {table} {where_clause} {group_by_clause} {order_by_clause}"

        try:
            with self.engine.begin() as conn:
                df = pd.read_sql(query, con=conn)
        except sqlalchemy.exc.OperationalError as e:
            print(f"Error retrieving data: {e}")

        return df

    def get_max_value(self, table: str, column: str, where: dict = None):
        df = self.get(table, [f"MAX({column})"], where)
        return df.iloc[0][0]

    def insert(self, table: str, data: pd.DataFrame):

        try:
            with self.engine.connect() as conn:
                data.to_sql(table, con=conn, if_exists="append", index=False)
        except sqlalchemy.exc.OperationalError as e:
            # self.open()
            print(f"Error inserting records: {e}")

    def update(self, stage_table: str, stored_proc: str, data: pd.DataFrame):

        try:
            with self.engine.begin() as conn:
                data.to_sql(stage_table, con=conn, if_exists="replace", index=False)
        except sqlalchemy.exc.OperationalError as e:
            # self.open()
            print(f"Error inserting records: {e}")

        query = f"CALL {stored_proc}"

        with self.engine.begin() as conn:
            conn.execute(query, autocommit=True)

    def query(self, query):
        """
        catch-all for queries without a specific method.
        """
        with self.engine.begin() as conn:
            rows = pd.read_sql(query, con=conn)

        return rows

    # custom method specific to RT
    def update_run_table(self, table: str, stage_table: str,
                         stored_proc: str, data: pd.DataFrame, cutoff_date: datetime):
        inserts = data[data["run_date"] > cutoff_date]
        updates = data[data["run_date"] <= cutoff_date]

        self.insert(table, inserts)
        self.update(stage_table, stored_proc, updates)


