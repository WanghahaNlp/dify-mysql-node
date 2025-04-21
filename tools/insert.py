# encoding=utf-8
"""
@File: insert.py
@Time: 2025-04-21 15:54:03
@Author: WangLei 
@Version: v1.0
@Desc: 新增数据

# TODO: 代表项目该完成的尚未完成的任务或者功能。
# FIXME: 代表项目中的问题或者bug, 需要修复。
# HACK: 代表一种临时解决方案, 代码质量较低, 需要在未来优化。
# * 强调该注释, 或者作为层次标记。
# ? 表示疑问, 需要进一步确认的内容。
# ! 表示警告, 可能有风险, 需要注意
"""
import json
from collections.abc import Generator
from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage
from loguru import logger
from typing import Any
from tools.mysql_client import MySQLClient
from tools.utils import get_config


class MysqlInsert(Tool):
    def __init__(self, runtime, session):
        super().__init__(runtime, session)
        try:
            credentials = self.runtime.credentials or runtime.credentials
            self.db_config = get_config(credentials)
        except Exception as e:
            logger.error(f"Failed to initialize database conn: {str(e)}")

    def _invoke(self, tool_parameters: dict[str, Any]) -> Generator[ToolInvokeMessage]:
        result = self.insert(**tool_parameters)
        yield self.create_json_message(result)

    def insert(self, db_name: str, table_name: str, formula: str, **kwargs):
        """插入数据"""
        try:
            mysql = MySQLClient(**self.db_config, db_name=db_name, table_name=table_name)
            data = json.loads(formula)
            id = mysql.insert(data)
        except json.decoder.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON: {str(e)}")
            return {"error": "Invalid JSON format"}
        except Exception as e:
            logger.error(f"Failed to insert data: {str(e)}")
            return {"error": str(e)}
        return {"id": id}
