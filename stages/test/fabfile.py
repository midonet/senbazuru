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
# this only works if the midonet gws also run agents with namespaces
#

@parallel
@roles('midonet_gateways')
def test():
    puts(green("testing connectivity into overlay on MidoNet gw on %s" % env.host_string))

    for midonet_agent in metadata.roles["midonet_agents"]:
        run("""
HOST_STRING="%s"
FIRST_IP="%s"
DEBUG="%s"
MAXPAIRS="%s"

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

for i in $(seq "$(( ${k} ))" "$(( ${k} + ${MAXPAIRS} ))"); do
    IP="$(dec2ip $(( $(ip2dec ${FIRST_IP}) + ${k} )))"

    ping -c1 "${IP}"; RC1="$?"

    if [[ ! "0" == "${RC1}" ]]; then
        sleep 1

        ping -c1 "${IP}"; RC2="$?"

        if [[ ! "0" == "${RC2}" ]]; then
            sleep 2

            ping -c1 "${IP}"; RC3="$?"
        fi
    fi

    if [[ "0" == "${RC1}" || "0" == "${RC2}" || "0" == "${RC3}" ]]; then
        echo "${IP} is pingable from the gw, testing iperf"

        iperf3 -c "${IP}" -p 80 -n4M
    else
        echo "ERROR: could not ping ${IP} from gw ${HOST_STRING}"
        exit 1
    fi

    k="$(( ${k} + 1 ))"
done

exit 0

""" % (
        env.host_string,
        CIDR(metadata.servers[midonet_agent]['network'])[0],
        metadata.config['debug'],
        metadata.config['maxpairs']
    ))

