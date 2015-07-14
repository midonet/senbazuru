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
@roles('cassandra')
def cassandra():
    puts(green("installing cassandra on %s" % env.host_string))

    cs = []

    for cshost in metadata.roles['cassandra']:
        cs.append("'%s'" % metadata.servers[cshost]['internal_ip'])

    args = {}

    args['seeds'] = "[%s]" % ",".join(cs)
    args['seed_address'] = "'%s'" % metadata.servers[env.host_string]['internal_ip']

    Puppet.apply('midonet::cassandra', args, metadata)

    Daemon.poll('org.apache.cassandra.service.CassandraDaemon')

