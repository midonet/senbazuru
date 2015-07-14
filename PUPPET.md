how to use the puppet modules
=============================

to run the puppet modules we have to prepare the machine.

in the installer this will be done by fab.

we just document it here for our own peace of mind.

Install puppet and the midonet puppet modules from puppetforge with this command:
```
apt-get install puppet
puppet module install midonet-midonet
```

Do not attempt to git clone the puppet module directly, you should download it through puppetforge.

Next thing is creating the hiera configs for the modules to run.
Alternatively you can configure them in the class call.

We show the example with hiera here.

These files must exist and configured this way.

Configure hiera.yaml to use /var/lib/hiera.
```
root@senbazuru-3fa0c88a-aebf-40fa-a971-07b459a34ccd:/tmp# cat /etc/hiera.yaml
---
:backends:
  - yaml
  - module_data
:yaml:
  :datadirs:
  - /var/lib/hiera
:logger: console
```

Next configure the hiera file.
```
root@senbazuru-3fa0c88a-aebf-40fa-a971-07b459a34ccd:/tmp# cat /var/lib/hiera/midonet/common.yaml
midonet::repository::midonet_repo: 'http://x:x@apt.midokura.com/midonet/v1.8/stable'
midonet::repository::midonet_openstack_repo: 'http://x:x@apt.midokura.com/openstack/juno/stable'
midonet::repository::midonet_stage: 'trusty'
midonet::repository::midonet_key_url: 'http://x:x@apt.midokura.com/packages.midokura.key'
midonet::repository::openstack_release: 'juno'
midonet::midonet_api::zk_servers:
    - ip: '127.0.0.1'
      port: 2181
midonet::midonet_api::vtep: True
midonet::midonet_api::keystone_auth: true
midonet::midonet_api::api_ip: '127.0.0.2'
midonet::midonet_api::api_port: 8080
midonet::midonet_api::keystone_host: '127.0.0.3'
midonet::midonet_api::keystone_port: 5000
midonet::midonet_api::keystone_admin_token: 'x'
midonet::midonet_api::keystone_tenant_name: 'Admin'
```

This is the node.pp now:
```
root@senbazuru-3fa0c88a-aebf-40fa-a971-07b459a34ccd:/tmp# cat node.pp
node senbazuru-3fa0c88a-aebf-40fa-a971-07b459a34ccd {
    class { 'midonet::repository': } -> class {'midonet::midonet_api': }
}
```

Make sure the hostname is correct:
```
root@senbazuru-3fa0c88a-aebf-40fa-a971-07b459a34ccd:/tmp# hostname -f; hostname -i; hostname; cat /etc/hosts; ip a
senbazuru-3fa0c88a-aebf-40fa-a971-07b459a34ccd.senbazuru.midokura.de
192.168.77.25
senbazuru-3fa0c88a-aebf-40fa-a971-07b459a34ccd
127.0.0.1 localhost
192.168.77.25 senbazuru-3fa0c88a-aebf-40fa-a971-07b459a34ccd.senbazuru.midokura.de senbazuru-3fa0c88a-aebf-40fa-a971-07b459a34ccd

# The following lines are desirable for IPv6 capable hosts
::1 ip6-localhost ip6-loopback
fe00::0 ip6-localnet
ff00::0 ip6-mcastprefix
ff02::1 ip6-allnodes
ff02::2 ip6-allrouters
ff02::3 ip6-allhosts
1: lo: <LOOPBACK,UP,LOWER_UP> mtu 65536 qdisc noqueue state UNKNOWN group default 
    link/loopback 00:00:00:00:00:00 brd 00:00:00:00:00:00
    inet 127.0.0.1/8 scope host lo
       valid_lft forever preferred_lft forever
    inet6 ::1/128 scope host 
       valid_lft forever preferred_lft forever
2: eth0: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1450 qdisc pfifo_fast state UP group default qlen 1000
    link/ether fa:16:3e:61:c0:dc brd ff:ff:ff:ff:ff:ff
    inet 192.168.77.25/24 brd 192.168.77.255 scope global eth0
       valid_lft forever preferred_lft forever
    inet6 fe80::f816:3eff:fe61:c0dc/64 scope link 
       valid_lft forever preferred_lft forever
```

Finally, do the puppet run for testing the module:
```
root@senbazuru-3fa0c88a-aebf-40fa-a971-07b459a34ccd:/tmp# puppet apply --noop --debug --verbose /tmp/node.pp
```

All of this will be scripted in python-fabric so please use this only for reference here.

https://forge.puppetlabs.com/midonet/midonet

http://wiki.midonet.org/MidoNet-allinone

https://github.com/midonet/puppet-midonet/

https://docs.puppetlabs.com/references/3.3.1/man/apply.html

https://forge.puppetlabs.com/midonet

