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

from senbazuru.config import Config

from fabric.api import *
from fabric.operations import reboot
from fabric.colors import red, green, yellow
from fabric.utils import puts

from netaddr import IPNetwork as CIDR

metadata = Config(os.environ["CONFIGFILE"])

#
# http://blog.scottlowe.org/2013/09/04/introducing-linux-network-namespaces/
#

@parallel
@roles('midonet_agents')
def vethpairs():
    puts(red("patching veth cables on %s" % env.host_string))

    run("""
HOST_STRING="%s"
FIRST_IP="%s"
DEBUG="%s"
MAXPAIRS="%s"

OVERLAY_MTU="%s"

if [[ "True" == "${DEBUG}" ]]; then
    XDEBUG='True'
else
    XDEBUG=''
fi

ip2dec () {
    local a b c d ip=$@
    IFS=. read -r a b c d <<< "$ip"
    printf '%%d' "$((a * 256 ** 3 + b * 256 ** 2 + c * 256 + d))"
}

dec2ip () {
    local ip dec=$@
    for e in {3..0}
    do
        ((octet = dec / (256 ** e) ))
        ((dec -= octet * 256 ** e))
        ip+=$delim$octet
        delim=.
    done
    printf '%%s' "$ip"
}

# start at ip .20 in the 1024 block
k=20

BRIDGE="$(midonet-cli -e 'bridge list' | grep 'alexbridge' | head -n1 | awk '{print $2;}')"
HOSTID="$(midonet-cli -e 'host list' | grep "name $(hostname) alive true" | head -n1 | awk '{print $2;}')"

if [[ "" == "${BRIDGE}" ]]; then
    echo "could not get bridge id from midonet cli"
    exit 1
fi

if [[ "" == "${HOSTID}" ]]; then
    echo "could not get host id from midonet cli"
    exit 1
fi


for i in $(seq -w "$(( ${k} ))" "$(( ${k} + ${MAXPAIRS} ))"); do
    DATAPATH="${HOST_STRING}_${i}_DP"
    VPORT="${HOST_STRING}_${i}_VP"

    if [[ -f "/tmp/${DATAPATH}.lck" ]]; then
        continue
    fi

    IP="$(dec2ip $(( $(ip2dec ${FIRST_IP}) + ${k} )))"

    for j in $(seq 1 "${i}"); do
        echo -n '.'
    done

    echo " ${VPORT}"

    test -n "${XDEBUG}" && echo "DEBUG0: using IP: ${IP} for vport ${VPORT}"

    # create the namespace for the vport
    ip netns list | grep -- "${VPORT}" 1>/dev/null || ip netns add "${VPORT}"

    test -n "${XDEBUG}" && ip netns exec "${VPORT}" ip a | awk '{print "DEBUG1: '${VPORT}': " $0;}'

    # create the veth pair, one end belongs into the midonet datapath, one end belongs into the namespace
    ip link show | grep -- "${DATAPATH}:" 1>/dev/null || ip link add "${DATAPATH}" type veth peer name "${VPORT}"

    # one datapath to bind them all
    ip link set "${DATAPATH}" up
    ip link set dev "${DATAPATH}" mtu ${OVERLAY_MTU}

    # banish the vport device into a special namespace to avoid cluttering the tcp/ip stack of the host
    ip link show | grep -- "${VPORT}" 1>/dev/null && ip link set "${VPORT}" netns "${VPORT}"

    # rename device to eth0
    ip netns exec "${VPORT}" ip a | grep "${VPORT}" 1>/dev/null && ip netns exec "${VPORT}" ip link set dev "${VPORT}" name eth0

    ip netns exec "${VPORT}" ip link set lo up
    ip netns exec "${VPORT}" ip a | grep '127.0.0.1' 1>/dev/null || ip netns exec "${VPORT}" ip addr add 127.0.0.1 dev lo

    ip netns exec "${VPORT}" ip link set eth0 up
    ip netns exec "${VPORT}" ip link set dev eth0 mtu ${OVERLAY_MTU}

    # set the ip on the eth0 device in the namespace
    ip netns exec "${VPORT}" ip a | grep "${IP}" 1>/dev/null || ip netns exec "${VPORT}" ip addr add ${IP}/12 dev eth0

    # one router to route them all
    ip netns exec "${VPORT}" ip route | grep "172.16.0.1" 1>/dev/null || ip netns exec "${VPORT}" ip route add default via 172.16.0.1

    test -n "${XDEBUG}" && ip netns exec "${VPORT}" ip a | awk '{print "DEBUG2: '${VPORT}': " $0;}'
    test -n "${XDEBUG}" && ip netns exec "${VPORT}" ip route | awk '{print "DEBUG2: '${VPORT}': " $0;}'

    screen -d -m -- ip netns exec "${VPORT}" iperf3 --json -s -p 80

    PORT="$(midonet-cli -e "bridge ${BRIDGE} port create")"

    if [[ "" == "${PORT}" ]]; then
        echo "failed to create port on bridge, something is wrong - breaking out of loop"
        exit 1
    fi

    midonet-cli -e "host ${HOSTID} add binding port bridge ${BRIDGE} port ${PORT} interface ${DATAPATH}"

    touch "/tmp/${DATAPATH}.lck"

    k="$(( ${k} + 1 ))"
done

test -n "${XDEBUG}" && ip a
test -n "${XDEBUG}" && ip route

exit 0

""" % (
        env.host_string,
        CIDR(metadata.servers[env.host_string]['network'])[0],
        metadata.config['debug'],
        metadata.config['maxpairs'],
        metadata.config['overlay_mtu']
    ))

