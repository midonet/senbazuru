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
@roles('all_servers')
def prune():

    run("""
#
# brute force logic, works on all servers
#

for IPERF in $(ps axufwww | grep -v grep | grep 'iperf -s' | awk '{print $2;}'); do
    kill -9 "${IPERF}"
done

for IPERF in $(ps axufwww | grep -v grep | grep 'iperf3 -s' | awk '{print $2;}'); do
    kill -9 "${IPERF}"
done

for NETNS in $(ip netns show); do
    echo "deleting netns ${NETNS}"
    ip netns delete "${NETNS}"
done

for LINK in $(ip link show | grep _DP | awk '{print $2;}' | sed 's,:,,g;'); do
    echo "deleting ip link ${LINK}"
    ip link delete "${LINK}"
    rm -fv "/tmp/${LINK}.lck"
done

service zookeeper stop
rm -rfv /var/lib/zookeeper/version-2

apt-get remove -y midonet-api
rm -rf /usr/share/midonet-api

apt-get remove -y tomcat7
rm -rf /var/log/tomcat7

apt-get remove --purge -y cassandra
rm -rf /etc/cassandra

apt-get remove --purge -y midolman
rm -rf /etc/midolman

apt-get remove --purge -y midonet-manager
rm -rf /var/www/html/midonet-manager

screen -wipe

service puppet stop

rm -v /etc/apt/sources.list.d/midonet*

apt-get clean

exit 0

""")

