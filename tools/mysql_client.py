from sqlalchemy import create_engine, MetaData, Table
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError
import sqlalchemy.pool
import time


class MySQLClient:
    def __init__(self, host, port, username, password, db_name="", table_name="", timeout=5):
        self.host = host
        self.port = port
        self.username = username
        self.password = password

        self.db_name = db_name
        self.table_name = table_name

        self.timeout = timeout
        self.engine_cache = {}  # 每个 dbname 缓存独立 engine

    def test_connect(self):
        try:
            engine = create_engine(
                f"mysql+pymysql://{self.username}:{self.password}@{self.host}:{self.port}",
                connect_args={"connect_timeout": self.timeout}
            )
            with engine.connect():
                return True, "true"
        except Exception as e:
            return False, str(e)


    def __connect__(self, db_name):
        if db_name not in self.engine_cache:
            self.engine_cache[db_name] = create_engine(
                f"mysql+pymysql://{self.username}:{self.password}@{self.host}:{self.port}/{db_name}",
                # 连接池
                poolclass=sqlalchemy.pool.NullPool,
                # 连接池会导致连接超时，导致连接失败
                connect_args={"connect_timeout": self.timeout}
            )

        engine = self.engine_cache[db_name]
        Session = sessionmaker(bind=engine)
        session = Session()
        return session

    def insert(self, data: dict):
        """插入数据"""
        session = self.__connect__(self.db_name)
        try:
            metadata = MetaData()
            metadata.reflect(bind=session.bind)
            table = metadata.tables.get(self.table_name)
            if table is None:
                raise ValueError(f"Table '{self.table_name}' not found in database '{self.db_name}'")

            insert_stmt = table.insert().values(**data)
            result = session.execute(insert_stmt)
            session.commit()
            return result.inserted_primary_key[0]  # 返回主键 ID
        except SQLAlchemyError as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def delete(self, data: dict):
        session = self.__connect__(self.db_name)
        try:
            metadata = MetaData()
            metadata.reflect(bind=session.bind)
            table = metadata.tables.get(self.table_name)
            if table is None:
                raise ValueError(f"Table '{self.table_name}' not found in database '{self.db_name}'")

            delete_stmt = table.delete().where(table.c.id == data["id"])
            result = session.execute(delete_stmt)
            session.commit()
            return result.rowcount  # 返回删除的行数
        except SQLAlchemyError as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def _lambda(self, table, column: str, value, operators: str):
        if operators == "==":
            return table.c[column] == value
        elif operators == "!=":
            return table.c[column] != value
        elif operators == ">":
            return table.c[column] > value
        elif operators == "<":
            return table.c[column] < value
        elif operators == ">=":
            return table.c[column] >= value
        elif operators == "<=":
            return table.c[column] <= value
        elif operators == "between":
            if not isinstance(value, list) or len(value) != 2:
                raise ValueError("Value for 'between' operator must be a list of two elements.")
            return table.c[column].between(value[0], value[1])
        elif operators == "in":
            if not isinstance(value, list):
                raise ValueError("Value for 'in' operator must be a list.")
            return table.c[column].in_(value)
        elif operators == "like":
            return table.c[column].like(value)
        elif operators == "ilike":
            return table.c[column].ilike(value)
        elif operators == "raw":
            if not isinstance(value, str):
                raise ValueError("Value for 'raw' operator must be a string.")
            # 这里假设 raw 是一个 SQL 表达式
            return eval(value)
        else:
            raise ValueError(f"Unsupported operator: {operators}")

    def select(self, data: list):
        """
        data = [['id', '==', '12'], ["name", "like", "%dify%"]]
        # 比较运算符
        "==", "!=", ">", "<", ">=", "<="

        # 特殊操作符
        "between"  # 区间查询
        "in"       # 包含查询
        "like"     # 模糊查询（区分大小写）
        "ilike"    # 模糊查询（不区分大小写）
        "raw"      # 原生SQL表达式
        [
            ["name", "==", "dify"],
            ["age", ">", 18],
            ["age", "<", 30],
            ["age", "between", [18, 30]],
            ["name", "in", ["dify", "dify2"]],
            ["name", "like", "%dify%"],
            ["name", "ilike", "%dify%"],
            ["raw", "id > 10"]
        ]
        """
        session = self.__connect__(self.db_name)
        try:
            metadata = MetaData()
            metadata.reflect(bind=session.bind)
            table = metadata.tables.get(self.table_name)
            if table is None:
                raise ValueError(f"Table '{self.table_name}' not found in database '{self.db_name}'")

            condition = [self._lambda(table, key, value, operators) for key, operators, value in data]
            select_stmt = table.select().where(*condition)
            result = session.execute(select_stmt).fetchall()
            result = [dict(row._mapping) for row in result] if result else []
            return result
        except SQLAlchemyError as e:
            session.rollback()
            raise e
        finally:
            session.close()
