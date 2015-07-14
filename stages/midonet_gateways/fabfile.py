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
@roles('midonet_gateways')
def midonet_gateways():
    puts(green("configuring MidoNet gw on %s" % env.host_string))

    run("""
# this has to be a /24. because.
UPLINK_NETWORK="%s"

# ip to use for the local uplink, hardcoded to /24. live with it.
UPLINK="%s"

# same here, this ip will be used by the midonet router port.
OVERLAY="%s"

OVERLAY_MTU="%s"

ROUTER_ID="$(midonet-cli -e 'router list' | grep alexrouter | awk '{print $2;}')"

if [[ "" == "${ROUTER_ID}" ]]; then
    echo "could not find alexrouter"
    exit 1
else
    echo "using router id: ${ROUTER_ID}"
fi

HOST_ID="$(midonet-cli -e 'host list' | grep "name $(hostname)" | grep "alive true" | awk '{print $2;}')"

if [[ "" == "${HOST_ID}" ]]; then
    echo "could not find this host being alive in host list in midonet"
    echo "check hostname of this host and midonet-cli -e host list"
    exit 1
else
    echo "using host id: ${HOST_ID}"
fi

ip a | grep "uplink" || ip link add "uplink" type veth peer name "overlay"

ifconfig uplink "${UPLINK}/24" up; ifconfig uplink
ifconfig overlay up; ifconfig overlay

ip link set dev uplink mtu ${OVERLAY_MTU}
ip link set dev overlay mtu ${OVERLAY_MTU}

route add -net 172.16.0.0/12 gw "${OVERLAY}"
route add -net 10.0.0.0/8 gw "${OVERLAY}"
route -n

echo 1 > /proc/sys/net/ipv4/ip_forward

iptables -t nat -v -I POSTROUTING -o eth0 -j MASQUERADE

PORT_ID="$(midonet-cli -e "router ${ROUTER_ID} port list" | grep "${OVERLAY}" | awk '{print $2;}')"

if [[ "" == "${PORT_ID}" ]]; then
    echo "port is not existing for this gw, we cannot continue here."
    exit 1
fi

echo "binding virtual router port to this gw"

midonet-cli -e "host ${HOST_ID} add binding port router ${ROUTER_ID} port ${PORT_ID} interface overlay"

mm-dpctl --add-if "overlay" midonet

exit 0

""" % (
        metadata.servers[env.host_string]["uplink_network"],
        metadata.servers[env.host_string]["uplink"],
        metadata.servers[env.host_string]["overlay"],
        metadata.config['overlay_mtu']
    ))

