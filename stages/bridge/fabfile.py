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
def bridge():
    puts(green("configuring midonet virtual switch (using cli on %s)" % env.host_string))

    run("""

midonet-cli -e 'bridge list' | grep 'name alexbridge' || midonet-cli -e 'bridge add name alexbridge'

""")

