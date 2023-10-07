#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (c) 2022, Felix Fontein (@felixfontein) <felix@fontein.de>
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = '''
---
module: api_info
author:
  - "Felix Fontein (@felixfontein)"
short_description: Retrieve information from API
version_added: 2.2.0
description:
  - Allows to retrieve information for a path using the API.
  - This can be used to backup a path to restore it with the M(community.routeros.api_modify) module.
  - Entries are normalized, dynamic and builtin entries are not returned. Use the O(handle_disabled) and
    O(hide_defaults) options to control normalization, the O(include_dynamic) and O(include_builtin) options to also return
    dynamic resp. builtin entries, and use O(unfiltered) to return all fields including counters.
  - B(Note) that this module is still heavily in development, and only supports B(some) paths.
    If you want to support new paths, or think you found problems with existing paths, please first
    L(create an issue in the community.routeros Issue Tracker,https://github.com/ansible-collections/community.routeros/issues/).
extends_documentation_fragment:
  - community.routeros.api
  - community.routeros.attributes
  - community.routeros.attributes.actiongroup_api
  - community.routeros.attributes.info_module
attributes:
  platform:
    support: full
    platforms: RouterOS
options:
  path:
    description:
      - Path to query.
      - An example value is V(ip address). This is equivalent to running C(/ip address print) in the RouterOS CLI.
    required: true
    type: str
    choices:
    # BEGIN PATH LIST
        - caps-man aaa
        - caps-man access-list
        - caps-man channel
        - caps-man configuration
        - caps-man datapath
        - caps-man manager
        - caps-man manager interface
        - caps-man provisioning
        - caps-man security
        - certificate settings
        - interface bonding
        - interface bridge
        - interface bridge mlag
        - interface bridge port
        - interface bridge port-controller
        - interface bridge port-extender
        - interface bridge settings
        - interface bridge vlan
        - interface detect-internet
        - interface eoip
        - interface ethernet
        - interface ethernet poe
        - interface ethernet switch
        - interface ethernet switch port
        - interface gre
        - interface gre6
        - interface l2tp-server server
        - interface list
        - interface list member
        - interface ovpn-server server
        - interface ppp-client
        - interface pppoe-client
        - interface pptp-server server
        - interface sstp-server server
        - interface vlan
        - interface vrrp
        - interface wireguard
        - interface wireguard peers
        - interface wireless
        - interface wireless align
        - interface wireless cap
        - interface wireless security-profiles
        - interface wireless sniffer
        - interface wireless snooper
        - iot modbus
        - ip accounting
        - ip accounting web-access
        - ip address
        - ip arp
        - ip cloud
        - ip cloud advanced
        - ip dhcp-client
        - ip dhcp-client option
        - ip dhcp-server
        - ip dhcp-server config
        - ip dhcp-server lease
        - ip dhcp-server network
        - ip dhcp-server option
        - ip dhcp-server option sets
        - ip dns
        - ip dns static
        - ip firewall address-list
        - ip firewall connection tracking
        - ip firewall filter
        - ip firewall layer7-protocol
        - ip firewall mangle
        - ip firewall nat
        - ip firewall raw
        - ip firewall service-port
        - ip hotspot service-port
        - ip ipsec identity
        - ip ipsec peer
        - ip ipsec policy
        - ip ipsec profile
        - ip ipsec proposal
        - ip ipsec settings
        - ip neighbor discovery-settings
        - ip pool
        - ip proxy
        - ip route
        - ip route vrf
        - ip service
        - ip settings
        - ip smb
        - ip socks
        - ip ssh
        - ip tftp settings
        - ip traffic-flow
        - ip traffic-flow ipfix
        - ip traffic-flow target
        - ip upnp
        - ip upnp interfaces
        - ipv6 address
        - ipv6 dhcp-client
        - ipv6 dhcp-server
        - ipv6 dhcp-server option
        - ipv6 firewall address-list
        - ipv6 firewall filter
        - ipv6 firewall mangle
        - ipv6 firewall nat
        - ipv6 firewall raw
        - ipv6 nd
        - ipv6 nd prefix default
        - ipv6 route
        - ipv6 settings
        - mpls
        - mpls ldp
        - port firmware
        - port remote-access
        - ppp aaa
        - ppp profile
        - queue interface
        - queue tree
        - radius incoming
        - routing bgp connection
        - routing bgp instance
        - routing filter rule
        - routing filter select-rule
        - routing id
        - routing mme
        - routing ospf area
        - routing ospf area range
        - routing ospf instance
        - routing ospf interface-template
        - routing pimsm instance
        - routing pimsm interface-template
        - routing rip
        - routing ripng
        - routing table
        - snmp
        - snmp community
        - system clock
        - system clock manual
        - system identity
        - system leds settings
        - system logging
        - system logging action
        - system note
        - system ntp client
        - system ntp client servers
        - system ntp server
        - system package update
        - system routerboard settings
        - system scheduler
        - system script
        - system upgrade mirror
        - system ups
        - system watchdog
        - tool bandwidth-server
        - tool e-mail
        - tool graphing
        - tool graphing interface
        - tool graphing resource
        - tool mac-server
        - tool mac-server mac-winbox
        - tool mac-server ping
        - tool netwatch
        - tool romon
        - tool sms
        - tool sniffer
        - tool traffic-generator
        - user
        - user aaa
        - user group
        - user settings
    # END PATH LIST
  unfiltered:
    description:
      - Whether to output all fields, and not just the ones supported as input for M(community.routeros.api_modify).
      - Unfiltered output can contain counters and other state information.
    type: bool
    default: false
  handle_disabled:
    description:
      - How to handle unset values.
      - V(exclamation) prepends the keys with V(!) in the output with value V(null).
      - V(null-value) uses the regular key with value V(null).
      - V(omit) omits these values from the result.
    type: str
    choices:
      - exclamation
      - null-value
      - omit
    default: exclamation
  hide_defaults:
    description:
      - Whether to hide default values.
    type: bool
    default: true
  include_dynamic:
    description:
      - Whether to include dynamic values.
      - By default, they are not returned, and the C(dynamic) keys are omitted.
      - If set to V(true), they are returned as well, and the C(dynamic) keys are returned as well.
    type: bool
    default: false
  include_builtin:
    description:
      - Whether to include builtin values.
      - By default, they are not returned, and the C(builtin) keys are omitted.
      - If set to V(true), they are returned as well, and the C(builtin) keys are returned as well.
    type: bool
    default: false
    version_added: 2.4.0
  include_read_only:
    description:
      - Whether to include read-only fields.
      - By default, they are not returned.
    type: bool
    default: false
    version_added: 2.10.0
seealso:
  - module: community.routeros.api
  - module: community.routeros.api_facts
  - module: community.routeros.api_find_and_modify
  - module: community.routeros.api_modify
'''

EXAMPLES = '''
---
- name: Get IP addresses
  community.routeros.api_info:
    hostname: "{{ hostname }}"
    password: "{{ password }}"
    username: "{{ username }}"
    path: ip address
  register: ip_addresses

- name: Print data for IP addresses
  ansible.builtin.debug:
    var: ip_addresses.result
'''

RETURN = '''
---
result:
    description: A list of all elements for the current path.
    sample:
      - '.id': '*1'
        actual-interface: bridge
        address: "192.168.88.1/24"
        comment: defconf
        disabled: false
        dynamic: false
        interface: bridge
        invalid: false
        network: 192.168.88.0
    type: list
    elements: dict
    returned: always
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.common.text.converters import to_native

from ansible_collections.community.routeros.plugins.module_utils.api import (
    api_argument_spec,
    check_has_library,
    create_api,
    get_api_version,
)

from ansible_collections.community.routeros.plugins.module_utils._api_data import (
    PATHS,
    join_path,
    split_path,
)

try:
    from librouteros.exceptions import LibRouterosError
except Exception:
    # Handled in api module_utils
    pass


def compose_api_path(api, path):
    api_path = api.path()
    for p in path:
        api_path = api_path.join(p)
    return api_path


def main():
    module_args = dict(
        path=dict(type='str', required=True, choices=sorted([join_path(path) for path in PATHS if PATHS[path].fully_understood])),
        unfiltered=dict(type='bool', default=False),
        handle_disabled=dict(type='str', choices=['exclamation', 'null-value', 'omit'], default='exclamation'),
        hide_defaults=dict(type='bool', default=True),
        include_dynamic=dict(type='bool', default=False),
        include_builtin=dict(type='bool', default=False),
        include_read_only=dict(type='bool', default=False),
    )
    module_args.update(api_argument_spec())

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True,
    )

    check_has_library(module)
    api = create_api(module)

    path = split_path(module.params['path'])
    versioned_path_info = PATHS.get(tuple(path))
    if versioned_path_info is None:
        module.fail_json(msg='Path /{path} is not yet supported'.format(path='/'.join(path)))
    if versioned_path_info.needs_version:
        api_version = get_api_version(api)
        if not versioned_path_info.provide_version(api_version):
            module.fail_json(msg='Path /{path} is not supported for API version {api_version}'.format(path='/'.join(path), api_version=api_version))
    path_info = versioned_path_info.get_data()

    handle_disabled = module.params['handle_disabled']
    hide_defaults = module.params['hide_defaults']
    include_dynamic = module.params['include_dynamic']
    include_builtin = module.params['include_builtin']
    include_read_only = module.params['include_read_only']
    try:
        api_path = compose_api_path(api, path)

        result = []
        unfiltered = module.params['unfiltered']
        for entry in api_path:
            if not include_dynamic:
                if entry.get('dynamic', False):
                    continue
            if not include_builtin:
                if entry.get('builtin', False):
                    continue
            if not unfiltered:
                for k in list(entry):
                    if k == '.id':
                        continue
                    if k == 'dynamic' and include_dynamic:
                        continue
                    if k == 'builtin' and include_builtin:
                        continue
                    if k not in path_info.fields:
                        entry.pop(k)
            if handle_disabled != 'omit':
                for k, field_info in path_info.fields.items():
                    if field_info.write_only:
                        entry.pop(k, None)
                        continue
                    if k not in entry:
                        if handle_disabled == 'exclamation':
                            k = '!%s' % k
                        entry[k] = None
            for k, field_info in path_info.fields.items():
                if hide_defaults:
                    if field_info.default is not None and entry.get(k) == field_info.default:
                        entry.pop(k)
                if field_info.absent_value and k not in entry:
                    entry[k] = field_info.absent_value
                if not include_read_only and k in entry and field_info.read_only:
                    entry.pop(k)
            result.append(entry)

        module.exit_json(result=result)
    except (LibRouterosError, UnicodeEncodeError) as e:
        module.fail_json(msg=to_native(e))


if __name__ == '__main__':
    main()
