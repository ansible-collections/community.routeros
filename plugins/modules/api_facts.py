#!/usr/bin/python

# Copyright: (c) 2022, Felix Fontein <felix@fontein.de>
# Copyright: (c) 2020, Nikolay Dachev <nikolay@dachev.info>
# Copyright: (c) 2018, Egor Zaitsev (@heuels)
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = '''
---
module: facts
author:
    - "Egor Zaitsev (@heuels)"
    - "Nikolay Dachev (@NikolayDachev)"
    - "Felix Fontein (@felixfontein)"
version_added: 2.1.0
short_description: Collect facts from remote devices running MikroTik RouterOS using the API
description:
  - Collects a base set of device facts from a remote device that
    is running RouterOS.  This module prepends all of the
    base network fact keys with C(ansible_net_<fact>).  The facts
    module will always collect a base set of facts from the device
    and can enable or disable collection of additional facts.
  - As opposed to the M(community.routeros.facts) module, it uses the
    RouterOS API, similar to the M(community.routeros.api) module.
extends_documentation_fragment:
  - community.routeros.api
options:
  gather_subset:
    description:
      - When supplied, this argument will restrict the facts collected
        to a given subset.  Possible values for this argument include
        C(all), C(hardware), C(interfaces), and C(routing).
      - Can specify a list of values to include a larger subset.
        Values can also be used with an initial C(!) to specify that a
        specific subset should not be collected.
    required: false
    default: '!config'
    type: list
    elements: str
seealso:
  - module: community.routeros.facts
  - module: community.routeros.api
'''

EXAMPLES = """
- name: Collect all facts from the device
  community.routeros.api_facts:
    hostname: 192.168.88.1
    username: admin
    password: password
    gather_subset: all

- name: Collect only the config and default facts
  community.routeros.api_facts:
    hostname: myrouter
    username: admin
    password: password
    gather_subset:
      - config

- name: Do not collect hardware facts
  community.routeros.api_facts:
    hostname: 192.168.88.1
    username: admin
    password: password
    gather_subset:
      - "!hardware"
"""

RETURN = """
ansible_facts:
  description: "Dictionary of IP geolocation facts for a host's IP address."
  returned: always
  type: dict
  contains:
    ansible_net_gather_subset:
      description: The list of fact subsets collected from the device.
      returned: always
      type: list

    # default
    ansible_net_model:
      description: The model name returned from the device.
      returned: I(gather_subset) contains C(default)
      type: str
    ansible_net_serialnum:
      description: The serial number of the remote device.
      returned: I(gather_subset) contains C(default)
      type: str
    ansible_net_version:
      description: The operating system version running on the remote device.
      returned: I(gather_subset) contains C(default)
      type: str
    ansible_net_hostname:
      description: The configured hostname of the device.
      returned: I(gather_subset) contains C(default)
      type: str
    ansible_net_arch:
      description: The CPU architecture of the device.
      returned: I(gather_subset) contains C(default)
      type: str
    ansible_net_uptime:
      description: The uptime of the device.
      returned: I(gather_subset) contains C(default)
      type: str
    ansible_net_cpu_load:
      description: Current CPU load.
      returned: I(gather_subset) contains C(default)
      type: str

    # hardware
    ansible_net_spacefree_mb:
      description: The available disk space on the remote device in MiB.
      returned: I(gather_subset) contains C(hardware)
      type: dict
    ansible_net_spacetotal_mb:
      description: The total disk space on the remote device in MiB.
      returned: I(gather_subset) contains C(hardware)
      type: dict
    ansible_net_memfree_mb:
      description: The available free memory on the remote device in MiB.
      returned: I(gather_subset) contains C(hardware)
      type: int
    ansible_net_memtotal_mb:
      description: The total memory on the remote device in MiB.
      returned: I(gather_subset) contains C(hardware)
      type: int

    # config
    ansible_net_config:
      description: The current active config from the device.
      returned: I(gather_subset) contains C(config)
      type: str

    ansible_net_config_nonverbose:
      description:
        - The current active config from the device in minimal form.
        - This value is idempotent in the sense that if the facts module is run twice and the device's config
          was not changed between the runs, the value is identical. This is achieved by running C(/export)
          and stripping the timestamp from the comment in the first line.
      returned: I(gather_subset) contains C(config)
      type: str
      version_added: 1.2.0

    # interfaces
    ansible_net_all_ipv4_addresses:
      description: All IPv4 addresses configured on the device.
      returned: I(gather_subset) contains C(interfaces)
      type: list
    ansible_net_all_ipv6_addresses:
      description: All IPv6 addresses configured on the device.
      returned: I(gather_subset) contains C(interfaces)
      type: list
    ansible_net_interfaces:
      description: A hash of all interfaces running on the system.
      returned: I(gather_subset) contains C(interfaces)
      type: dict
    ansible_net_neighbors:
      description: The list of neighbors from the remote device.
      returned: I(gather_subset) contains C(interfaces)
      type: dict

    # routing
    ansible_net_bgp_peer:
      description: A dictionary with BGP peer information.
      returned: I(gather_subset) contains C(routing)
      type: dict
    ansible_net_bgp_vpnv4_route:
      description: A dictionary with BGP vpnv4 route information.
      returned: I(gather_subset) contains C(routing)
      type: dict
    ansible_net_bgp_instance:
      description: A dictionary with BGP instance information.
      returned: I(gather_subset) contains C(routing)
      type: dict
    ansible_net_route:
      description: A dictionary for routes in all routing tables.
      returned: I(gather_subset) contains C(routing)
      type: dict
    ansible_net_ospf_instance:
      description: A dictionary with OSPF instances.
      returned: I(gather_subset) contains C(routing)
      type: dict
    ansible_net_ospf_neighbor:
      description: A dictionary with OSPF neighbors.
      returned: I(gather_subset) contains C(routing)
      type: dict
"""
import re

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.six import iteritems
from ansible.module_utils.common.text.converters import to_native

from ansible_collections.community.routeros.plugins.module_utils.api import (
    api_argument_spec,
    check_has_library,
    create_api,
)

try:
    from librouteros.exceptions import LibRouterosError
except Exception:
    # Handled in api module_utils
    pass



class FactsBase(object):

    COMMANDS = []

    def __init__(self, module, api):
        self.module = module
        self.api = api
        self.facts = {}
        self.responses = None

    def populate(self):
        self.responses = []
        for path in self.COMMANDS:
            api_path = self.api.path()
            for part in path:
                api_path = api_path.join(part)
            try:
                result = list(api_path)
            except LibRouterosError as e:
                result = []
                self.module.warn('Error while querying path {path}: {error}'.format(
                    path=' '.join(path),
                    error=to_native(e),
                ))
            self.responses.append(result)

    def run(self, cmd):
        return run_commands(self.module, commands=cmd, check_rc=False)


class Default(FactsBase):

    COMMANDS = [
        ['system', 'identity'],
        ['system', 'resource'],
        ['system', 'routerboard'],
    ]

    def populate(self):
        super(Default, self).populate()
        data = self.responses[0]
        if data:
            self.facts['hostname'] = self.parse_hostname(data[0])
        data = self.responses[1]
        if data:
            self.facts['version'] = self.parse_version(data[0])
            self.facts['arch'] = self.parse_arch(data[0])
            self.facts['uptime'] = self.parse_uptime(data[0])
            self.facts['cpu_load'] = self.parse_cpu_load(data[0])
        data = self.responses[2]
        if data:
            self.facts['model'] = self.parse_model(data[0])
            self.facts['serialnum'] = self.parse_serialnum(data[0])

    def parse_hostname(self, data):
        return data.get('name')

    def parse_version(self, data):
        return data.get('version')

    def parse_model(self, data):
        return data.get('model')

    def parse_arch(self, data):
        return data.get('architecture-name')

    def parse_uptime(self, data):
        return data.get('uptime')

    def parse_cpu_load(self, data):
        return data.get('cpu-load')

    def parse_serialnum(self, data):
        return data.get('serial-number')


class Hardware(FactsBase):

    COMMANDS = [
        ['system', 'resource'],
    ]

    def populate(self):
        super(Hardware, self).populate()
        data = self.responses[0]
        if data:
            self.parse_filesystem_info(data[0])
            self.parse_memory_info(data[0])

    def parse_filesystem_info(self, data):
        self.facts['spacefree_mb'] = self.to_megabytes(data.get('free-hdd-space'))
        self.facts['spacetotal_mb'] = self.to_megabytes(data.get('total-hdd-space'))

    def parse_memory_info(self, data):
        self.facts['memfree_mb'] = self.to_megabytes(data.get('free-memory'))
        self.facts['memtotal_mb'] = self.to_megabytes(data.get('total-memory'))

    def to_megabytes(self, value):
        if value is None:
            return None
        return float(value) / 1024 / 1024


class Interfaces(FactsBase):

    COMMANDS = [
        ['interface'],
        ['ip', 'address'],
        ['ipv6', 'address'],
        ['ip', 'neighbor'],
    ]

    def populate(self):
        super(Interfaces, self).populate()

        self.facts['interfaces'] = {}
        self.facts['all_ipv4_addresses'] = []
        self.facts['all_ipv6_addresses'] = []
        self.facts['neighbors'] = []

        data = self.responses[0]
        if data:
            interfaces = self.parse_interfaces(data)
            self.populate_interfaces(interfaces)

        data = self.responses[1]
        if data:
            data = self.parse_detail(data)
            self.populate_addresses(data, 'ipv4')

        data = self.responses[2]
        if data:
            data = self.parse_detail(data)
            self.populate_addresses(data, 'ipv6')

        data = self.responses[3]
        if data:
            self.facts['neighbors'] = list(self.parse_detail(data))

    def populate_interfaces(self, data):
        for key, value in iteritems(data):
            self.facts['interfaces'][key] = value

    def populate_addresses(self, data, family):
        for value in data:
            key = value['interface']
            if family not in self.facts['interfaces'][key]:
                self.facts['interfaces'][key][family] = []
            addr, subnet = value['address'].split('/')
            subnet = subnet.strip()
            # Try to convert subnet to an integer
            try:
                subnet = int(subnet)
            except Exception:
                pass
            ip = dict(address=addr.strip(), subnet=subnet)
            self.add_ip_address(addr.strip(), family)
            self.facts['interfaces'][key][family].append(ip)

    def add_ip_address(self, address, family):
        if family == 'ipv4':
            self.facts['all_ipv4_addresses'].append(address)
        else:
            self.facts['all_ipv6_addresses'].append(address)

    def parse_interfaces(self, data):
        facts = {}
        for entry in data:
            if 'name' not in entry:
                continue
            entry.pop('.id', None)
            facts[entry['name']] = entry
        return facts

    def parse_detail(self, data):
        for entry in data:
            if 'interface' not in entry:
                continue
            entry.pop('.id', None)
            yield entry


class Routing(FactsBase):

    COMMANDS = [
        ['routing', 'bgp', 'peer'],
        ['routing', 'bgp', 'vpnv4-route'],
        ['routing', 'bgp', 'instance'],
        ['ip', 'route'],
        ['routing', 'ospf', 'instance'],
        ['routing', 'ospf', 'neighbor'],
    ]

    def populate(self):
        super(Routing, self).populate()
        self.facts['bgp_peer'] = {}
        self.facts['bgp_vpnv4_route'] = {}
        self.facts['bgp_instance'] = {}
        self.facts['route'] = {}
        self.facts['ospf_instance'] = {}
        self.facts['ospf_neighbor'] = {}
        data = self.responses[0]
        if data:
            peer = self.parse_bgp_peer(data)
            self.populate_bgp_peer(peer)
        data = self.responses[1]
        if data:
            vpnv4 = self.parse_vpnv4_route(data)
            self.populate_vpnv4_route(vpnv4)
        data = self.responses[2]
        if data:
            instance = self.parse_instance(data)
            self.populate_bgp_instance(instance)
        data = self.responses[3]
        if data:
            route = self.parse_route(data)
            self.populate_route(route)
        data = self.responses[4]
        if data:
            instance = self.parse_instance(data)
            self.populate_ospf_instance(instance)
        data = self.responses[5]
        if data:
            instance = self.parse_ospf_neighbor(data)
            self.populate_ospf_neighbor(instance)

    def parse_name(self, data):
        return data.get('name')

    def parse_interface(self, data):
        return data.get('interface')

    def parse_instance_name(self, data):
        return data.get('instance')

    def parse_routing_mark(self, data):
        return data.get('routing-mark') or 'main'

    def parse_bgp_peer(self, data):
        facts = {}
        for line in data:
            name = self.parse_name(line)
            line.pop('.id', None)
            facts[name] = line
        return facts

    def parse_instance(self, data):
        facts = {}
        for line in data:
            name = self.parse_name(line)
            line.pop('.id', None)
            facts[name] = line
        return facts

    def parse_vpnv4_route(self, data):
        facts = {}
        for line in data:
            name = self.parse_interface(line)
            line.pop('.id', None)
            facts[name] = line
        return facts

    def parse_route(self, data):
        facts = {}
        for line in data:
            name = self.parse_routing_mark(line)
            line.pop('.id', None)
            facts[name] = line
        return facts

    def parse_ospf_instance(self, data):
        facts = {}
        for line in data:
            name = self.parse_name(line)
            line.pop('.id', None)
            facts[name] = line
        return facts

    def parse_ospf_neighbor(self, data):
        facts = {}
        for line in data:
            name = self.parse_instance_name(line)
            line.pop('.id', None)
            facts[name] = line
        return facts

    def populate_bgp_peer(self, data):
        for key, value in iteritems(data):
            self.facts['bgp_peer'][key] = value

    def populate_vpnv4_route(self, data):
        for key, value in iteritems(data):
            self.facts['bgp_vpnv4_route'][key] = value

    def populate_bgp_instance(self, data):
        for key, value in iteritems(data):
            self.facts['bgp_instance'][key] = value

    def populate_route(self, data):
        for key, value in iteritems(data):
            self.facts['route'][key] = value

    def populate_ospf_instance(self, data):
        for key, value in iteritems(data):
            self.facts['ospf_instance'][key] = value

    def populate_ospf_neighbor(self, data):
        for key, value in iteritems(data):
            self.facts['ospf_neighbor'][key] = value


FACT_SUBSETS = dict(
    default=Default,
    hardware=Hardware,
    interfaces=Interfaces,
    routing=Routing,
)

VALID_SUBSETS = frozenset(FACT_SUBSETS.keys())

warnings = []


def main():
    argument_spec = dict(
        gather_subset=dict(
            default=['!config'],
            type='list',
            elements='str',
        )
    )
    argument_spec.update(api_argument_spec())

    module = AnsibleModule(argument_spec=argument_spec, supports_check_mode=True)
    check_has_library(module)
    api = create_api(module)

    gather_subset = module.params['gather_subset']

    runable_subsets = set()
    exclude_subsets = set()

    for subset in gather_subset:
        if subset == 'all':
            runable_subsets.update(VALID_SUBSETS)
            continue

        if subset.startswith('!'):
            subset = subset[1:]
            if subset == 'all':
                exclude_subsets.update(VALID_SUBSETS)
                continue
            exclude = True
        else:
            exclude = False

        if subset not in VALID_SUBSETS:
            module.fail_json(msg='Bad subset: %s' % subset)

        if exclude:
            exclude_subsets.add(subset)
        else:
            runable_subsets.add(subset)

    if not runable_subsets:
        runable_subsets.update(VALID_SUBSETS)

    runable_subsets.difference_update(exclude_subsets)
    runable_subsets.add('default')

    facts = {}
    facts['gather_subset'] = list(runable_subsets)

    instances = []
    for key in runable_subsets:
        instances.append(FACT_SUBSETS[key](module, api))

    for inst in instances:
        inst.populate()
        facts.update(inst.facts)

    ansible_facts = {}
    for key, value in iteritems(facts):
        key = 'ansible_net_%s' % key
        ansible_facts[key] = value

    module.exit_json(ansible_facts=ansible_facts, warnings=warnings)


if __name__ == '__main__':
    main()
