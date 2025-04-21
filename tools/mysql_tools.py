from collections.abc import Generator
from typing import Any
import json
from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage
from loguru import logger
from tools.utils import get_config
from tools.mysql_client import MySQLClient


class MysqlClientNodeTool(Tool):
    def __init__(self, runtime, session):
        super().__init__(runtime, session)
        try:
            credentials = self.runtime.credentials or runtime.credentials
            self.db_config = get_config(credentials)
        except Exception as e:
            logger.error(f"Failed to initialize database conn: {str(e)}")

    def _invoke(self, tool_parameters: dict[str, Any]) -> Generator[ToolInvokeMessage]:
        result = getattr(self, tool_parameters["func"])(**tool_parameters)
        yield self.create_json_message(result)

    def insert(self, db_name: str, table_name: str, formula: str, **kwargs):
        mysql = MySQLClient(**self.db_config, db_name=db_name, table_name=table_name)
        data = json.loads(formula)
        id = mysql.insert(data)
        return {"id": id}

    def delete(self, db_name: str, table_name: str, formula: str, **kwargs):
        mysql = MySQLClient(**self.db_config, db_name=db_name, table_name=table_name)
        data = json.loads(formula)
        id = mysql.delete(data)
        return {"id": id}