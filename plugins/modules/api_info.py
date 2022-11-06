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
  - Entries are normalized, and dynamic entries are not returned. Use the I(handle_disabled) and
    I(hide_defaults) options to control normalization, the I(include_dynamic) option to also return
    dynamic entries, and use I(unfiltered) to return all fields including counters.
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
      - An example value is C(ip address). This is equivalent to running C(/ip address print) in the RouterOS CLI.
    required: true
    type: str
    choices:
    # BEGIN PATH LIST
        - caps-man aaa
        - certificate settings
        - interface bridge port
        - interface bridge port-controller
        - interface bridge port-extender
        - interface bridge settings
        - interface detect-internet
        - interface ethernet
        - interface ethernet switch
        - interface ethernet switch port
        - interface l2tp-server server
        - interface ovpn-server server
        - interface pptp-server server
        - interface sstp-server server
        - interface wireless align
        - interface wireless cap
        - interface wireless sniffer
        - interface wireless snooper
        - ip accounting
        - ip accounting web-access
        - ip address
        - ip cloud
        - ip cloud advanced
        - ip dhcp-client
        - ip dhcp-client option
        - ip dhcp-server
        - ip dhcp-server config
        - ip dhcp-server lease
        - ip dhcp-server network
        - ip dns
        - ip dns static
        - ip firewall address-list
        - ip firewall connection tracking
        - ip firewall filter
        - ip firewall mangle
        - ip firewall nat
        - ip firewall service-port
        - ip hotspot service-port
        - ip ipsec settings
        - ip neighbor discovery-settings
        - ip pool
        - ip proxy
        - ip service
        - ip settings
        - ip smb
        - ip socks
        - ip ssh
        - ip tftp settings
        - ip traffic-flow
        - ip traffic-flow ipfix
        - ip upnp
        - ipv6 dhcp-client
        - ipv6 firewall address-list
        - ipv6 firewall filter
        - ipv6 nd prefix default
        - ipv6 settings
        - mpls
        - mpls ldp
        - port firmware
        - ppp aaa
        - queue interface
        - radius incoming
        - routing bgp instance
        - routing mme
        - routing rip
        - routing ripng
        - snmp
        - system clock
        - system clock manual
        - system identity
        - system leds settings
        - system note
        - system ntp client
        - system package update
        - system routerboard settings
        - system upgrade mirror
        - system watchdog
        - tool bandwidth-server
        - tool e-mail
        - tool graphing
        - tool mac-server
        - tool mac-server mac-winbox
        - tool mac-server ping
        - tool romon
        - tool sms
        - tool sniffer
        - tool traffic-generator
        - user aaa
        - user group
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
      - C(exclamation) prepends the keys with C(!) in the output with value C(null).
      - C(null-value) uses the regular key with value C(null).
      - C(omit) omits these values from the result.
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
      - If set to C(true), they are returned as well, and the C(dynamic) keys are returned as well.
    type: bool
    default: false
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
    )
    module_args.update(api_argument_spec())

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True,
    )

    check_has_library(module)
    api = create_api(module)

    path = split_path(module.params['path'])
    path_info = PATHS.get(tuple(path))
    if path_info is None:
        module.fail_json(msg='Path /{path} is not yet supported'.format(path='/'.join(path)))

    handle_disabled = module.params['handle_disabled']
    hide_defaults = module.params['hide_defaults']
    include_dynamic = module.params['include_dynamic']
    try:
        api_path = compose_api_path(api, path)

        result = []
        unfiltered = module.params['unfiltered']
        for entry in api_path:
            if not include_dynamic:
                if entry.get('dynamic', False):
                    continue
            if not unfiltered:
                for k in list(entry):
                    if k == '.id':
                        continue
                    if k == 'dynamic' and include_dynamic:
                        continue
                    if k not in path_info.fields:
                        entry.pop(k)
            if handle_disabled != 'omit':
                for k in path_info.fields:
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
            result.append(entry)

        module.exit_json(result=result)
    except (LibRouterosError, UnicodeEncodeError) as e:
        module.fail_json(msg=to_native(e))


if __name__ == '__main__':
    main()
