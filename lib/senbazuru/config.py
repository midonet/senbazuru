#!/usr/bin/python -Werror

#
# Copyright (c) 2015 Midokura SARL, All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

import os
import sys
import yaml

from fabric.api import *

class Config(object):

    def __init__(self, configfile):
        self._config = self.__set_config(configfile)
        self._roles = self.__set_roles(configfile)
        self._servers = self.__set_servers(configfile)

        self.__prepare()

        if os.environ["DEBUG"] <> "":
            for server in self._servers:
                sys.stderr.write("server: %s\n" % server)
                for kv in self._servers[server]:
                    sys.stderr.write("__init__ server: [[%s]] - key: [[%s]] - value: [[%s]]\n" % (server, kv, self._servers[server][kv]))

        self.__setup_fabric_env()

        if os.environ["DEBUG"] <> "":
            self.__dumpconfig()

    def __dumpconfig(self):
        for role in sorted(self._roles):
            sys.stderr.write("role: %s\n" % role)
        sys.stderr.write("\n")

        for server in self._servers:
            sys.stderr.write("server: %s\n" % server)
            for kv in self._servers[server]:
                sys.stderr.write("__dumpconfig server: [[%s]] - key: [[%s]] - value: [[%s]]\n" % (server, kv, self._servers[server][kv]))

        for server in sorted(self._servers):
            if 'ip' in self._servers[server]:
                sys.stderr.write("server: %s (%s)\n" % (server, self._servers[server]['ip']))
            else:
                sys.stderr.write("ERROR: server %s has no ip property\n" % server)
                sys.exit(1)

            for role in sorted(self._roles):
                if server in self._roles[role]:
                    sys.stderr.write("server role: %s\n" % role)
            sys.stderr.write("\n")

    @classmethod
    def __read_from_yaml(cls, yamlfile, section_name):
        with open(yamlfile, 'r') as yaml_file:
            yamldata = yaml.load(yaml_file.read())

        if yamldata and section_name in yamldata:
            if os.environ["DEBUG"] <> "":
                print
                print yamldata[section_name]
                print
            return yamldata[section_name]
        else:
            return {}

    def __set_config(self, configfile):
        return self.__read_from_yaml(configfile, 'config')

    def __set_roles(self, configfile):
        return self.__read_from_yaml(configfile, 'roles')

    def __set_servers(self, configfile):
        return self.__read_from_yaml(configfile, 'servers')

    def __prepare_config(self):
        defaults = {}

        defaults["nameserver"] = "8.8.8.8"
        defaults["parallel"] = True

        defaults["underlay_mtu"] = 9000
        defaults["overlay_mtu"] = 8950

        defaults["iperf3_througput_test_sequence"] = "400M 40M 4M"
        defaults["iperf3_test_iterations"] = "2 4 6"
        defaults["iperf3_retry_factor"] = 1000
        defaults["iperf3_retry_wait"] = 10

        if self._config['debug'] == True:
            defaults["maxpairs"] = 20
        else:
            defaults["maxpairs"] = 1000

        for overloading_key in defaults:
            if overloading_key not in self._config:
                overloading_value = defaults[overloading_key]
                self._config[overloading_key] = overloading_value

    def __prepare_roles(self):
        self._roles['all_servers'] = []

        for server in self._servers:
            if server not in self._roles['all_servers']:
                self._roles['all_servers'].append(server)

    def __prepare_servers(self):
        for role in self._roles:
            for server in self._roles[role]:
                if server not in self._servers:
                    self._servers[server] = {}
                if 'roles' not in self._servers[server]:
                    self._servers[server]['roles'] = []
                if role not in self._servers[server]['roles']:
                    self._servers[server]['roles'].append(role)

        for server in self._servers:
            for global_config_key in self._config:
                if global_config_key not in self._servers[server]:
                    value = self._config[global_config_key]
                    self._servers[server][global_config_key] = value

    def __prepare(self):
        self.__prepare_config()
        self.__prepare_roles()
        self.__prepare_servers()

    def __setup_fabric_env(self):
        env.use_ssh_config = True
        env.port = 22
        env.connection_attempts = 5
        env.timeout = 5
        env.parallel = self._config["parallel"]
        env.roledefs = self._roles

    @property
    def config(self):
        return self._config

    @property
    def roles(self):
        return self._roles

    @property
    def servers(self):
        return self._servers

