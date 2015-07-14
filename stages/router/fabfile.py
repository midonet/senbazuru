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
def router():
    puts(green("configuring midonet virtual router (using cli on %s)" % env.host_string))

    run("""

midonet-cli -e 'router list' | grep 'name alexrouter' || midonet-cli -e 'router add name alexrouter'

ROUTER_ID="$(midonet-cli -e 'router list' | grep alexrouter | awk '{print $2;}')"

if [[ "" == "${ROUTER_ID}" ]]; then
    echo "could not find alexrouter"
    exit 1
else
    echo "using router id: ${ROUTER_ID}"
fi

ROUTER_PORT_ID="$(midonet-cli -e "router ${ROUTER_ID} port list" | grep "172.16.0.1" | awk '{print $2;}')"

if [[ "" == "${ROUTER_PORT_ID}" ]]; then
    ROUTER_PORT_ID="$(midonet-cli -e "router ${ROUTER_ID} add port address 172.16.0.1 net 172.16.0.0/12")"
fi

BRIDGE_ID="$(midonet-cli -e 'bridge list' | grep 'alexbridge' | grep 'state up' | head -n1 | awk '{print $2;}')"

if [[ "" == "${BRIDGE_ID}" ]]; then
    echo "bridge alexbridge does not exist or problem with midonet api, cannot continue."
    exit 1
fi

BRIDGE_PORT_ID="$(midonet-cli -e "bridge ${BRIDGE_ID} port create" | grep -v 'Syntax error')"

if [[ "" == "${BRIDGE_PORT_ID}" ]]; then
    echo "could not create bridge port"
    exit 1
fi

# tickle that bridge where it wants to be tickled: that vport
midonet-cli -e "router ${ROUTER_ID} port ${ROUTER_PORT_ID} set peer ${BRIDGE_PORT_ID}"

# routing to the veth ips ingress
midonet-cli -e "router ${ROUTER_ID} route add type normal weight 100 src 0.0.0.0/0 dst 172.16.0.0/12 gw 0.0.0.0 port ${ROUTER_PORT_ID}"

# lb routing ingress
midonet-cli -e "router ${ROUTER_ID} route add type normal weight 100 src 0.0.0.0/0 dst 10.0.0.0/8 gw 0.0.0.0 port ${ROUTER_PORT_ID}"

exit 0

""")

    for midonet_gateway in metadata.roles["midonet_gateways"]:
        run("""
UPLINK_NETWORK="%s"
UPLINK="%s"
OVERLAY="%s"

ROUTER_ID="$(midonet-cli -e 'router list' | grep alexrouter | awk '{print $2;}')"

if [[ "" == "${ROUTER_ID}" ]]; then
    echo "could not find alexrouter"
    exit 1
else
    echo "using router id: ${ROUTER_ID}"
fi

#
# create the port for this gw
#
PORT_ID="$(midonet-cli -e "router ${ROUTER_ID} port list" | grep "${OVERLAY}" | awk '{print $2;}')"

if [[ "" == "${PORT_ID}" ]]; then
    PORT_ID="$(midonet-cli -e "router ${ROUTER_ID} add port address ${OVERLAY} net ${UPLINK_NETWORK}/24")"
fi

if [[ "" == "${PORT_ID}" ]]; then
    echo "port id is empty, cannot continue"
    exit 1
fi

#
# add the local route to the iface network
#
COMMAND="router ${ROUTER_ID} route add type normal weight 100 src 0.0.0.0/0 dst ${UPLINK_NETWORK}/24 gw 0.0.0.0 port ${PORT_ID}"

echo "running command: ${COMMAND}"

midonet-cli -e "${COMMAND}"

#
# add one of the possible default routes via out of this gw, it will SNAT after that
#
COMMAND="router ${ROUTER_ID} route add type normal weight 200 src 0.0.0.0/0 dst 0.0.0.0/0 gw ${UPLINK} port ${PORT_ID}"

echo "running command: ${COMMAND}"

midonet-cli -e "${COMMAND}"

exit 0

""" % (
        metadata.servers[midonet_gateway]["uplink_network"],
        metadata.servers[midonet_gateway]["uplink"],
        metadata.servers[midonet_gateway]["overlay"]
    ))

