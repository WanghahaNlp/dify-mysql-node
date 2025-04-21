# encoding=utf-8
"""
@File: utils.py
@Time: 2025-04-17 09:32:16
@Author: WangLei 
@Version: v1.0
@Desc: 新建项目

# TODO: 代表项目该完成的尚未完成的任务或者功能。
# FIXME: 代表项目中的问题或者bug, 需要修复。
# HACK: 代表一种临时解决方案, 代码质量较低, 需要在未来优化。
# * 强调该注释, 或者作为层次标记。
# ? 表示疑问, 需要进一步确认的内容。
# ! 表示警告, 可能有风险, 需要注意
"""
from typing import Any, Tuple


def get_config(credentials: dict[str, Any]) -> Tuple[dict[str, Any], dict[str, Any]]:
    if credentials.get("db_host") == "localhost" or credentials.get("db_host") == "0.0.0.0":
        credentials["db_host"] = "127.0.0.1"
    db_config = {
        "host": credentials.get("db_host"),
        "port": credentials.get("db_port"),
        "username": credentials.get("db_user"),
        "password": credentials.get("db_password")
    }
    # 检查配置完整性
    missing_fields = [key for key, value in db_config.items() if not value]
    if missing_fields:
        raise ValueError(
            f"Missing required configuration fields: {', '.join(missing_fields)}"
        )

    return db_config
