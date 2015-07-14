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
from senbazuru.utils import Puppet

from fabric.api import env,parallel,roles,run
from fabric.colors import green
from fabric.utils import puts

metadata = Config(os.environ["CONFIGFILE"])

@parallel
@roles('midonet_api')
def tunnelzone():
    puts(green("adding all hosts to tunnelzone vxlan (using cli on %s)" % env.host_string))

    run("""
midonet-cli -e 'tunnel-zone list' | grep 'alexzone' || midonet-cli -e 'tunnel-zone create name alexzone type vxlan'
""")

    servers = []

    for server in metadata.roles['midonet_agents']:
        servers.append(server)

    for server in metadata.roles['midonet_gateways']:
        servers.append(server)

    for server in servers:
        run("""
HOST="%s"
IP="%s"

ZONE="$(midonet-cli -e 'tunnel-zone list' | grep 'alexzone' | awk '{print $2;}')"

ID="$(midonet-cli -e 'host list' | grep "name ${HOST} alive true" | awk '{print $2;}')"

if [[ "" == "${ID}" ]]; then
    echo "host ${HOST} not found in midonet, agent not running?"
    exit 1
fi

EXISTS="$(midonet-cli -e "tunnel-zone ${ZONE} member list" | grep "host ${ID} address ${IP}")"

if [[ "" == "${EXISTS}" ]]; then
    midonet-cli -e "tunnel-zone ${ZONE} add member host ${ID} address ${IP}"
fi

""" % (server, metadata.servers[server]['internal_ip']))

