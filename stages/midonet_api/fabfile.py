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
def midonet_api():
    puts(green("installing MidoNet api on %s" % env.host_string))

    if metadata.servers[env.host_string]['ip'] <> metadata.servers[env.host_string]['internal_ip']:
        run("""
API_IP="%s"

ifconfig eth0:1 ${API_IP}/32 up

""" % metadata.servers[env.host_string]['ip'])

    zk = []

    for zkhost in metadata.roles['zookeeper']:
        zk.append("{'ip' => '%s', 'port' => '2181'}" % metadata.servers[zkhost]['internal_ip'])

    args = {}

    args['zk_servers'] = "[%s]" % ",".join(zk)
    args['keystone_auth'] = "false"
    args['vtep'] = "true"
    args['api_ip'] = "'%s'" % metadata.servers[env.host_string]['ip']

    run("""
echo 1 > /proc/sys/net/ipv6/conf/all/disable_ipv6

apt-get remove --purge -y midonet-api; echo
apt-get remove --purge -y tomcat7; echo
apt-get remove --purge -y tomcat6; echo
""")

    Puppet.apply('midonet::midonet_api', args, metadata)

    run("""

cat >/etc/default/tomcat7 <<EOF
TOMCAT7_USER=tomcat7
TOMCAT7_GROUP=tomcat7
JAVA_OPTS="-Djava.awt.headless=true -Xmx128m -XX:+UseConcMarkSweepGC -Djava.net.preferIPv4Stack=true -Djava.security.egd=file:/dev/./urandom"
EOF

#
# thanks to @Jan for finding this
#
sed -i 's,org.midonet.api.auth.MockAuthService,org.midonet.cluster.auth.MockAuthService,g;' /usr/share/midonet-api/WEB-INF/web.xml

rm -rfv /var/log/tomcat7/*

service tomcat7 restart

""")
