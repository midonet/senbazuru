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
def iperf():
    puts(green("testing iperf runs into overlay on MidoNet gw on %s" % env.host_string))

    for midonet_agent in metadata.roles["midonet_agents"]:

        retries = []

        for r in range(1, int(metadata.config['iperf3_retry_factor'])):
            retries.append("%i" % r)

        run("""
MAXPAIRS="%s"

X_THROUGHPUT="%s"

X_ITERATIONS="%s"

X_RETRIES="%s"

X_RETRY_WAIT="%s"

TARGET="10.0.0.10"

TIMESTAMP="$(date +%%s)"

BASEDIR="/tmp/senbazuru/iperf3/${TIMESTAMP}"

mkdir -pv "${BASEDIR}/sh"
mkdir -pv "${BASEDIR}/json"
mkdir -pv "${BASEDIR}/stderr"

for THROUGHPUT in ${X_THROUGHPUT}; do
    for ITERATIONS in ${X_ITERATIONS}; do
        for i in $(seq 1 "$(( ${MAXPAIRS} * ${ITERATIONS} ))"); do
            H="hostname_$(hostname -f)"
            T="throughput_${THROUGHPUT}"
            M="maxpairs_${MAXPAIRS}"
            I="iterations_${ITERATIONS}__iteration_${i}"
            Q="date_$(date +%%s)"
            FILENAME="${H}__${T}__${M}__${I}__${Q}"

            SCRIPT="${BASEDIR}/sh/${FILENAME}.sh"

            cat >"${SCRIPT}" <<EOF
#!/bin/bash

for j in ${X_RETRIES}; do
    iperf3 \
        -c "${TARGET}" \
        -p 80 \
        -n${THROUGHPUT} \
        --json \
        --reverse \
        --verbose \
        --zerocopy \
        --no-delay \
        --get-server-output \
        --format m \
            1>"${BASEDIR}/json/iperf3__lb_${TARGET}_80__${FILENAME}.json" \
            2>"${BASEDIR}/stderr/iperf3__lb_${TARGET}_80__${FILENAME}.stderr" && \
    exit 0

    sleep "${X_RETRY_WAIT}"
done

exit 0

EOF

            chmod 0755 "${SCRIPT}"

            screen -d -m -- "${SCRIPT}"

            sleep 1
        done
    done
done

""" % (
        metadata.config['maxpairs'],
        metadata.config['iperf3_througput_test_sequence'],
        metadata.config['iperf3_test_iterations'],
        " ".join(retries),
        metadata.config['iperf3_retry_wait']
    ))

