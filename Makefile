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

#  __  __ _     _                  _
# |  \/  (_) __| | ___  _ __   ___| |_
# | |\/| | |/ _` |/ _ \| '_ \ / _ \ __|
# | |  | | | (_| | (_) | | | |  __/ |_
# |_|  |_|_|\__,_|\___/|_| |_|\___|\__|
#

#
# run a stand-alone MidoNet cluster with a lot of veth pairs per server.
#
# how much is 'a lot'? That depends on the upper bound of memory you have. if the box has 16 GB then 2000 veth pairs may work.
#
# the limiting factor is not the veth pair or the ip namespace but the iperf -s daemon that comes at 30-90 megabyte RAM usage for each vport
#
# one end of the veth pair is wired to a vport on a bridge, the other end goes to a device with an ip and an iperf -s -p 80.
#
# this way you can test and benchmark your routing through the midonet BGP gateways and your distributed L4 load balancing.
#
# examples will be provided how to run the iperf -c sessions and on how to set up the routing through the gateways.
#

#
# set this if you want to see debugging info from the install stage
#
# DEBUG = xoxo

PREREQUISITES = preflight sshconfig

ALLTARGETS = $(PREREQUISITES) install zookeeper cassandra midonet_agents midonet_api midonet_manager midonet_cli tunnelzone bridge router midonet_gateways vethpairs l4lb

all: $(ALLTARGETS)

include include/senbazuru.mk

#
# prepare the machines and install the puppet modules
#
install:          $(PREREQUISITES)
	$(RUNSTAGE)

#
# install zookeeper, the topology database
#
zookeeper:        $(PREREQUISITES)
	$(RUNSTAGE)

#
# install cassandra
#
cassandra:        $(PREREQUISITES)
	$(RUNSTAGE)

#
# install and configure midonet agents on all gateways and veth pair hosts
#
midonet_agents:   $(PREREQUISITES) zookeeper cassandra
	$(RUNSTAGE)

#
# install and configure midonet api
#
midonet_api:      $(PREREQUISITES) zookeeper cassandra midonet_agents
	$(RUNSTAGE)

#
# install and configure midonet manager
#
midonet_manager:  $(PREREQUISITES) midonet_api
	$(RUNSTAGE)

#
# install and configure midonet_cli on all machines
#
midonet_cli:      $(PREREQUISITES) midonet_api
	$(RUNSTAGE)

#
# add hosts to tunnel-zone
#
tunnelzone:       $(PREREQUISITES) midonet_cli
	$(RUNSTAGE)

#
# create a virtual bridge
#
bridge:           $(PREREQUISITES) midonet_cli tunnelzone
	$(RUNSTAGE)

#
# create a virtual router, attaches it to the bridge
#
router:           $(PREREQUISITES) midonet_cli bridge
	$(RUNSTAGE)

#
# configure the router uplinks on the gateways with veth pairs and classic SNAT
#
midonet_gateways: $(PREREQUISITES) midonet_cli tunnelzone router
	$(RUNSTAGE)

#
# this creates the actual veth pairs and hooks them up to the virtual bridge
#
# it also starts the iperf -s -p 80 daemons on each server
#
vethpairs:        $(PREREQUISITES) midonet_cli bridge
	$(RUNSTAGE)

#
# ping into the overlay from the gateway uplinks
#
test:
	$(RUNSTAGE)

#
# run a lot of iperf -c from the gws
#
iperf:
	$(RUNSTAGE)

#
# http://docs.midonet.org/docs/operation-guide/2015.06/content/l4lb_configuration.html
#
l4lb:             $(PREREQUISITES) midonet_cli bridge
	$(RUNSTAGE)

#
# this creates a local tmp/.ssh/config file for fabric to use
# if you modify this target you should understand how fabric works
# to understand the implications of modifications to this target
#
sshconfig: preflight
	mkdir -pv $(shell dirname $(SSHCONFIG));
	touch $(SSHCONFIG);
	SSHCONFIG=$(SSHCONFIG) $(RUNSTAGE)

clean:
	rm -rf ./$(shell basename $(TMPDIR))

prune: sshconfig
	$(RUNSTAGE)

reboot:
	which parallel-ssh && parallel-ssh -h $(TMPDIR)/servers.txt -lroot -o $(TMPDIR)/o -- 'reboot' || echo 'please install parallel-ssh'

poweroff:
	which parallel-ssh && parallel-ssh -h $(TMPDIR)/servers.txt -lroot -o $(TMPDIR)/o -- 'poweroff' || echo 'please install parallel-ssh'

ipa:
	which parallel-ssh && parallel-ssh -h $(TMPDIR)/servers.txt -lubuntu -o $(TMPDIR)/o -- 'ip a; ip netns show' || echo 'please install parallel-ssh'

sourceslist:
	which parallel-ssh && parallel-ssh -h $(TMPDIR)/servers.txt -lubuntu -o $(TMPDIR)/o -- "cat /etc/apt/sources*/*list"; grep '' $(TMPDIR)/o/*

todo:
	grep -B2 -A2 -ri TODO .
