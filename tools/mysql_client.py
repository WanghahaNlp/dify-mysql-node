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
                return True, ""
        except SQLAlchemyError as e:
            return False, str(e)
        except Exception as e:
            return False, str(e)
        finally:
            engine.dispose()

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

    def select(self, data: dict):
        session = self.__connect__(self.db_name)
        try:
            metadata = MetaData()
            metadata.reflect(bind=session.bind)
            table = metadata.tables.get(self.table_name)
            if table is None:
                raise ValueError(f"Table '{self.table_name}' not found in database '{self.db_name}'")

            condition = [table.c[key] == value for key, value in data.items()]
            select_stmt = table.select().where(*condition)
            result = session.execute(select_stmt).fetchall()
            result = [dict(row._mapping) for row in result] if result else []
            return result
        except SQLAlchemyError as e:
            session.rollback()
            raise e
        finally:
            session.close()
