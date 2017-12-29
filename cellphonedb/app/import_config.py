import os
import warnings

import yaml


class AppConfig():
    def __init__(self, environment=None, support=None, load_defaults=None):

        self.config_parameters = self._get_config_parameters(environment, support, load_defaults)

        self.config = self._load_config()

    def _get_config_parameters(self, environment=None, support=None, load_defaults=None):
        config_parameters = {}
        config_keys = [{'env_key': 'APP_ENV', 'default': 'local', 'dict_key': 'environment'},
                       {'env_key': 'APP_CONF_SUPPORT', 'default': 'yaml', 'dict_key': 'support'},
                       {'env_key': 'APP_LOAD_DEFAULTS', 'default': 'true', 'dict_key': 'load_defaults'}]

        for config_key in config_keys:
            if locals()[config_key['dict_key']]:
                config_parameters[config_key['dict_key']] = locals()[config_key['dict_key']]
            elif os.environ.get(config_key['env_key']):
                config_parameters[config_key['dict_key']] = os.environ.get(config_key['env_key'])
            else:
                warnings.warn(
                    '{} not defined, setted to {} by default'.format(config_key['env_key'], config_key['default']))
                config_parameters[config_key['dict_key']] = config_key['default']

        return config_parameters

    def _load_yaml(self, yaml_name):
        with open(yaml_name, 'r') as stream:
            try:
                return yaml.load(stream)
            except yaml.YAMLError as exec:
                print(exec)

    def _merge_configs(self, config_base, new_config):
        config = {**config_base, **new_config}
        for key in config_base:
            if isinstance(config_base[key], dict) and key in new_config:
                config[key] = self._merge_configs(config_base[key], new_config[key])

        return config

    def _load_config(self) -> dict:
        config = {}
        if self.config_parameters['load_defaults']:
            config = self._load_yaml('cellphonedb/config/{}.yml'.format('base_config'))
        if self.config_parameters['environment']:
            custom_config = self._load_yaml('cellphonedb/config/{}.yml'.format(self.config_parameters['environment']))
            config = self._merge_configs(config, custom_config)

        return config

    def _build_sqlalchemy_database_uri(self, database_config):
        return '{}://{}:{}@{}:{}/{}'.format(database_config['adapter'], database_config['user'],
                                            database_config['password'], database_config['host'],
                                            database_config['port'], database_config['db_name'])

    def flask_config(self):
        if self.config_parameters['support'] == 'yaml':
            flask_config = self._flask_config_from_yaml(self.config_parameters['environment'],
                                                        self.config_parameters['load_defaults'])
        elif self.config_parameters['support'] == 'environment_vars':
            flask_config = self._flask_config_from_environment_vars(self.config_parameters['load_defaults'])
        else:
            raise Exception('Non valid support defined {yaml,environment_vars}')

        return flask_config

    def _flask_config_from_environment_vars(self, load_defaults):
        flask_config = {}
        if load_defaults:
            flask_config = self._flask_config_from_yaml(None, load_defaults)

        config_keys = ['SECRET_KEY', 'SQLALCHEMY_DATABASE_URI', 'API_PREFIX', 'DEBUG', 'SQLALCHEMY_TRACK_MODIFICATIONS']

        for config_key in config_keys:
            if os.environ.get(config_key):
                flask_config[config_key] = os.environ.get(config_key)
        return flask_config

    def _flask_config_from_yaml(self, environment, load_defaults):

        flask_config = {
            'SECRET_KEY': self.config['flask']['secret_key'],
            'SQLALCHEMY_DATABASE_URI': self._build_sqlalchemy_database_uri(self.config['database']),
            'API_PREFIX': self.config['api']['prefix'],
            'DEBUG': self.config['flask']['secret_key'],
            'SQLALCHEMY_TRACK_MODIFICATIONS': self.config['flask']['sqlalchemy_track_modifications']
        }
        return flask_config