#!/usr/bin/python -Werror

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

from fabric.api import *

class Daemon(object):
    def __init__(self, configfile):
        pass

    @classmethod
    def poll(cls, daemon_string, timeout=15):
        run("""
DAEMON_STRING="%s"
TIMEOUT="%i"

#
# this was in zookeeper first before we moved it here, dont worry about the ZK variable names
#
ZK=1

for i in $(seq 1 "${TIMEOUT}"); do
    ZK_ALIVE="$(ps axufwwwwwwwwwwwwwwwwwwwwww | grep -v grep | grep "${DAEMON_STRING}")"

    if [[ "" == "${ZK_ALIVE}" ]]; then
        ZK=1
    else
        ZK=0
        continue
    fi

    sleep 2
done

exit "${ZK}"

""" % (daemon_string, timeout))

class Puppet(object):

    def __init__(self, configfile):
        pass

    @classmethod
    def apply(cls, module_name, args_vector, metadata):
        # construct the string out of the args vector
        # run the command on the box

        args_array = []
        for key in args_vector:
            args_array.append("%s => %s" % (key, args_vector[key]))

        args_string = ", ".join(args_array)

        if metadata.config['debug'] == True:
            debug_flag = '--debug'
        else:
            debug_flag = ''

        if metadata.config['verbose'] == True:
            verbose_flag = '--verbose'
        else:
            verbose_flag = ''

        if module_name == 'midonet::repository':
            pass
        else:
            xargs = {}

            if "OS_MIDOKURA_REPOSITORY_USER" in os.environ:
                xapt = 'http://%s:%s@apt.midokura.com' % (os.environ["OS_MIDOKURA_REPOSITORY_USER"], os.environ["OS_MIDOKURA_REPOSITORY_PASS"])
                xargs['midonet_stage'] = "'trusty'"
                xargs['openstack_release'] = "'juno'"
                xargs['midonet_repo'] = "'%s/midonet/v1.9/stable'" % xapt
                xargs['midonet_openstack_repo'] = "'%s/openstack/juno/stable'" % xapt
            else:
                xapt = 'http://repo.midonet.org'
                xargs['midonet_stage'] = "'stable'"
                xargs['openstack_release'] = "'juno'"
                xargs['midonet_repo'] = "'%s/midonet/v2014.11'" % xapt
                xargs['midonet_openstack_repo'] = "'%s/openstack'" % xapt
                xargs['midonet_thirdparty_repo'] = "'%s/misc'" % xapt
                xargs['midonet_key'] = "'50F18FCF'"
                xargs['midonet_key_url'] = "'%s/packages.midokura.key'" % xapt

            repo_args = []

            for key in xargs:
                repo_args.append("%s => %s" % (key, xargs[key]))

            run("""
DEBUG="%s"
VERBOSE="%s"

echo 'nameserver 8.8.8.8' > /etc/resolv.conf
yes | dpkg --configure -a

cat >/tmp/node.pp<<EOF
node $(hostname) {
    class { 'midonet::repository':
        %s
    }
    ->
    class { '%s':
        %s
    }
}
EOF

puppet apply ${DEBUG} ${VERBOSE} /tmp/node.pp 2>&1

""" % (debug_flag, verbose_flag, ",".join(repo_args), module_name, args_string))

