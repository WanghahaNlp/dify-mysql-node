# encoding=utf-8
"""
@File: main.py
@Time: 2025-04-17 10:45:39
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
from dify_plugin import Plugin, DifyPluginEnv
from dify_plugin.config.config import DifyPluginEnv, InstallMethod
from dify_plugin.core.entities.plugin.setup import PluginConfiguration
from dify_plugin.core.plugin_registration import PluginRegistration
from dify_plugin.core.plugin_executor import PluginExecutor
from dify_plugin.core.server.io_server import IOServer
from dify_plugin.core.server.router import Router
from dify_plugin.core.utils.yaml_loader import load_yaml_file
from dify_plugin.entities.agent import AgentStrategyProviderConfiguration
from dify_plugin.entities.endpoint import EndpointProviderConfiguration
from dify_plugin.entities.model.provider import ModelProviderConfiguration
from dify_plugin.entities.tool import ToolProviderConfiguration


class PluginRegistrationPlug(PluginRegistration):
    def _load_plugin_configuration(self):
        """
        load basic plugin configuration from manifest.yaml
        """
        try:
            file = load_yaml_file("manifest.yaml")
            self.configuration = PluginConfiguration(**file)

            for provider in self.configuration.plugins.tools:
                fs = load_yaml_file(provider)
                tool_provider_configuration = ToolProviderConfiguration(**fs)
                self.tools_configuration.append(tool_provider_configuration)
            for provider in self.configuration.plugins.models:
                fs = load_yaml_file(provider)
                model_provider_configuration = ModelProviderConfiguration(**fs)
                self.models_configuration.append(model_provider_configuration)
            for provider in self.configuration.plugins.endpoints:
                fs = load_yaml_file(provider)
                endpoint_configuration = EndpointProviderConfiguration(**fs)
                self.endpoints_configuration.append(endpoint_configuration)
            for provider in self.configuration.plugins.agent_strategies:
                fs = load_yaml_file(provider)
                agent_provider_configuration = AgentStrategyProviderConfiguration(**fs)
                self.agent_strategies_configuration.append(agent_provider_configuration)

        except Exception as e:
            raise ValueError(f"Error loading plugin configuration: {str(e)}") from e


class MyPlugin(Plugin):
    def __init__(self, config):
        # load plugin configuration
        self.registration = PluginRegistrationPlug(config)

        if InstallMethod.Local == config.INSTALL_METHOD:
            request_reader, response_writer = self._launch_local_stream(config)
        elif InstallMethod.Remote == config.INSTALL_METHOD:
            request_reader, response_writer = self._launch_remote_stream(config)
        elif InstallMethod.Serverless == config.INSTALL_METHOD:
            request_reader, response_writer = self._launch_serverless_stream(config)
        else:
            raise ValueError("Invalid install method")

        # set default response writer
        self.default_response_writer = response_writer

        # initialize plugin executor
        self.plugin_executer = PluginExecutor(config, self.registration)

        IOServer.__init__(self, config, request_reader, response_writer)
        Router.__init__(self, request_reader, response_writer)

        # register io routes
        self._register_request_routes()


plugin = MyPlugin(DifyPluginEnv(MAX_REQUEST_TIMEOUT=120))

if __name__ == '__main__':
    plugin.run()
