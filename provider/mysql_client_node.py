# encoding=utf-8
"""
@File: mysql_client_node.py
@Time: 2025-04-17 09:34:14
@Author: WangLei 
@Version: v1.0
@Desc: Mysql的连接器

# TODO: 代表项目该完成的尚未完成的任务或者功能。
# FIXME: 代表项目中的问题或者bug, 需要修复。
# HACK: 代表一种临时解决方案, 代码质量较低, 需要在未来优化。
# * 强调该注释, 或者作为层次标记。
# ? 表示疑问, 需要进一步确认的内容。
# ! 表示警告, 可能有风险, 需要注意
"""
from dify_plugin import ToolProvider
from dify_plugin.errors.tool import ToolProviderCredentialValidationError
from loguru import logger
from tools.mysql_client import MySQLClient
from tools.utils import get_config
from typing import Any


class MysqlClientNodeProvider(ToolProvider):
    def _validate_credentials(self, credentials: dict[str, Any]) -> None:
        try:
            db_config = get_config(credentials)
            flag, message = MySQLClient(**db_config).test_connect()
            if not flag:
                raise ToolProviderCredentialValidationError(
                    f"Failed to connect to MySQL: {message}"
                )
            else:
                logger.info(
                    f"Successfully connected to MySQL: {db_config['host']}:{db_config['port']}"
                )
        except Exception as e:
            raise ToolProviderCredentialValidationError(str(e))
