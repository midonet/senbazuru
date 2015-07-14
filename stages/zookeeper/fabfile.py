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
from senbazuru.utils import Daemon

from fabric.api import env,parallel,roles,run
from fabric.colors import green
from fabric.utils import puts

metadata = Config(os.environ["CONFIGFILE"])

@parallel
@roles('zookeeper')
def zookeeper():
    puts(green("installing zookeeper on %s" % env.host_string))

    zk = []

    zkid = 1
    myid = 1

    for zkhost in sorted(metadata.roles['zookeeper']):
        # construct the puppet module params
        zk.append("{'id' => '%s', 'host' => '%s'}" % (zkid, metadata.servers[zkhost]['internal_ip']))

        # are we the current server?
        if env.host_string == zkhost:
            # then this is our id
            myid = zkid

        zkid = zkid + 1

    args = {}

    args['servers'] = "[%s]" % ",".join(zk)
    args['server_id'] = "%s" % myid

    Puppet.apply('midonet::zookeeper', args, metadata)

    Daemon.poll('org.apache.zookeeper.server.quorum', 60)

    for zkhost in sorted(metadata.roles['zookeeper']):
        run("""
IP="%s"
echo ruok | nc "${IP}" 2181 | grep imok
""" % metadata.servers[zkhost]['internal_ip'])

