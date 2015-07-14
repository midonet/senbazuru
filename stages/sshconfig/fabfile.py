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

metadata = Config(os.environ["CONFIGFILE"])

env.warn_only = True
env.connection_attempts = 2
env.timeout = 2
env.skip_bad_hosts = True
env.warn_only = False

def sshconfig():
    puts(red("writing ssh config to %s" % os.environ["SSHCONFIG"]))

    f = open(os.environ["SSHCONFIG"], 'w')

    q = open("%s/%s" % (os.environ["TMPDIR"], "servers.txt"), 'w')

    for server in sorted(metadata.servers):
        hostname = server
        fqdn = "%s.%s" % (server, metadata.config["domain"])
        ip = metadata.servers[server]["ip"]

        puts(green("writing entry for %s (%s)" % (fqdn, ip)))

        q.write("%s\n" % ip)

        f.write("""#
# ssh config for server %s (%s)
#
Host %s
    User root
    ServerAliveInterval 2
    KeepAlive yes
    ConnectTimeout 30
    TCPKeepAlive yes
    Hostname %s

Host %s
    User root
    ServerAliveInterval 2
    KeepAlive yes
    ConnectTimeout 30
    TCPKeepAlive yes
    Hostname %s

""" % (fqdn, ip, server, ip, fqdn, ip))

    f.close()

    q.close()
