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

from senbazuru.config import Config

from fabric.api import env,parallel,roles,run
from fabric.colors import green
from fabric.utils import puts

metadata = Config(os.environ["CONFIGFILE"])

@parallel
@roles('midonet_manager')
def midonet_manager():

    if "OS_MIDOKURA_REPOSITORY_USER" in os.environ:
        puts(green("installing MidoNet Manager on %s" % env.host_string))

        run("""
API_IP="%s"
dpkg --configure -a
apt-get install -y -u midonet-manager

#
# midonet manager 1.9.3
#
cat >/var/www/html/midonet-manager/config/client.js <<EOF
{
  "api_host": "http://${API_IP}:8080",
  "login_host": "http://${API_IP}:8080",
  "api_namespace": "midonet-api",
  "api_version": "1.8",
  "api_token": false,
  "poll_enabled": true,
  "agent_config_api_host": "http://${API_IP}:8459",
  "agent_config_api_namespace": "conf",
  "trace_api_host": "http://${API_IP}:8080",
  "traces_ws_url": "ws://${API_IP}:8460"
}
EOF

service apache2 restart

""" % metadata.servers[metadata.roles['midonet_api'][0]]['ip'])

    else:
        puts(yellow("MidoNet Manager is only available in MEM"))

