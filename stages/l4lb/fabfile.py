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

from netaddr import IPNetwork as CIDR

metadata = Config(os.environ["CONFIGFILE"])

#
# thanks to http://docs.midonet.org/docs/operation-guide/2015.06/content/l4lb_configuration.html for making this easy to program.
#
@parallel
@roles('midonet_api')
def l4lb():
    puts(green("configuring l4 TCP load balancer (using cli on %s)" % env.host_string))

    for midonet_agent in metadata.roles["midonet_agents"]:
        run("""
HOST_STRING="%s"
FIRST_IP="%s"
DEBUG="%s"
MAXPAIRS="%s"

ROUTER_ID="$(midonet-cli -e 'router list' | grep alexrouter | awk '{print $2;}')"

if [[ "" == "${ROUTER_ID}" ]]; then
    echo "could not find alexrouter"
    exit 1
else
    echo "using router id: ${ROUTER_ID}"
fi

LB_ID="$(midonet-cli -e 'load-balancer list' | grep 'state up' | head -n1 | awk '{print $2;}')"

if [[ "" == "${LB_ID}" ]]; then
    LB_ID="$(midonet-cli -e 'load-balancer create')"
fi

echo "using load balancer id: ${LB_ID}"

midonet-cli -e "router ${ROUTER_ID} set load-balancer ${LB_ID}"

POOL_ID="$(midonet-cli -e "load-balancer ${LB_ID} list pool" | head -n1 | awk '{print $2;}')"

if [[ "" == "${POOL_ID}" ]]; then
    POOL_ID="$(midonet-cli -e "load-balancer ${LB_ID} create pool lb-method ROUND_ROBIN")"
fi

midonet-cli -e "load-balancer ${LB_ID} pool ${POOL_ID} show"

#
# add the ips of the veth pairs of the agents
#

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

for i in $(seq "$(( ${k} ))" "$(( ${k} + ${MAXPAIRS} ))"); do
    IP="$(dec2ip $(( $(ip2dec ${FIRST_IP}) + ${k} )))"

    midonet-cli -e "load-balancer ${LB_ID} pool ${POOL_ID} create member address ${IP} protocol-port 80"

    k="$(( ${k} + 1 ))"
done

midonet-cli -e "load-balancer ${LB_ID} pool ${POOL_ID} list vip" | grep "10.0.0.10" || \
    midonet-cli -e "load-balancer ${LB_ID} pool ${POOL_ID} create vip address 10.0.0.10 persistence SOURCE_IP protocol-port 80"

""" % (
        env.host_string,
        CIDR(metadata.servers[midonet_agent]['network'])[0],
        metadata.config['debug'],
        metadata.config['maxpairs']
    ))

