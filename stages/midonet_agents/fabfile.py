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
@roles('midonet_agents', 'midonet_gateways')
def midonet_agents():
    puts(green("installing MidoNet agent on %s" % env.host_string))

    zk = []

    for zkhost in metadata.roles['zookeeper']:
        zk.append("{'ip' => '%s', 'port' => '2181'}" % metadata.servers[zkhost]['internal_ip'])

    cs = []

    for cshost in metadata.roles['cassandra']:
        cs.append("'%s'" % metadata.servers[cshost]['internal_ip'])

    args = {}

    args['zk_servers'] = "[%s]" % ",".join(zk)
    args['cassandra_seeds'] = "[%s]" % ",".join(cs)

    Puppet.apply('midonet::midonet_agent', args, metadata)

    run("""

cat >/tmp/buffer.json <<EOF
agent {
    datapath {
        max_flow_count=200000
        send_buffer_pool_buf_size_kb=2048
        send_buffer_pool_initial_size=2048
        send_buffer_pool_max_size=4096
    }
}
EOF

# TODO mn-conf set -t default < /tmp/buffer.json

""")

    #
    # modify the init script to allow higher number of open files
    #
    run("""
SCRIPT="/usr/share/midolman/midolman-start-senbazuru"

cat >/etc/init/senbazuru.conf <<EOF
description "Midolman with more open files"
start on runlevel [2345]
stop on runlevel [016]
respawn
respawn limit 2 120
kill timeout 5
umask 022
console none
pre-start script
    exec /usr/share/midolman/midolman-prepare
end script
script
    exec ${SCRIPT}
end script
EOF

chmod 0755 /etc/init/senbazuru.conf

cat >"${SCRIPT}" <<EOF
#!/bin/bash
set -e
ulimit -n 1000000
/usr/share/midolman/midolman-start
EOF

chmod 0755 "${SCRIPT}"

service midolman restart

""")

