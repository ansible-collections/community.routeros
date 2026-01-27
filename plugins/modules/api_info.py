#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (c) 2022, Felix Fontein (@felixfontein) <felix@fontein.de>
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = r"""
module: api_info
author:
  - "Felix Fontein (@felixfontein)"
short_description: Retrieve information from API
version_added: 2.2.0
description:
  - Allows to retrieve information for a path using the API.
  - This can be used to backup a path to restore it with the M(community.routeros.api_modify) module.
  - Entries are normalized, dynamic and builtin entries are not returned. Use the O(handle_disabled) and O(hide_defaults)
    options to control normalization, the O(include_dynamic) and O(include_builtin) options to also return dynamic resp. builtin
    entries, and use O(unfiltered) to return all fields including counters.
  - B(Note) that this module is still heavily in development, and only supports B(some) paths. If you want to support new
    paths, or think you found problems with existing paths, please first L(create an issue in the community.routeros Issue
    Tracker,https://github.com/ansible-collections/community.routeros/issues/).
extends_documentation_fragment:
  - community.routeros.api
  - community.routeros.api.restrict
  - community.routeros.attributes
  - community.routeros.attributes.actiongroup_api
  - community.routeros.attributes.idempotent_not_modify_state
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
      - app
      - app settings
      - caps-man aaa
      - caps-man access-list
      - caps-man actual-interface-configuration
      - caps-man channel
      - caps-man configuration
      - caps-man datapath
      - caps-man interface
      - caps-man manager
      - caps-man manager interface
      - caps-man provisioning
      - caps-man rates
      - caps-man security
      - certificate
      - certificate crl
      - certificate scep-server
      - certificate scep-server ra
      - certificate settings
      - console settings
      - container
      - container config
      - container envs
      - container mounts
      - disk
      - disk btrfs filesystem
      - disk btrfs subvolume
      - disk btrfs transfer
      - disk settings
      - dude
      - dude agent
      - dude device
      - dude device-type
      - dude notification
      - dude probe
      - dude ros address
      - dude ros arp
      - dude ros health
      - dude ros interface
      - dude ros lease
      - dude ros neighbor
      - dude ros queue
      - dude ros resource
      - dude ros route
      - dude ros routerboard
      - dude service
      - file
      - file rsync-daemon
      - file sync
      - interface
      - interface 6to4
      - interface amt
      - interface bonding
      - interface bridge
      - interface bridge calea
      - interface bridge filter
      - interface bridge host
      - interface bridge mdb
      - interface bridge mlag
      - interface bridge msti
      - interface bridge nat
      - interface bridge port
      - interface bridge port mst-override
      - interface bridge port-controller
      - interface bridge port-controller device
      - interface bridge port-controller port
      - interface bridge port-extender
      - interface bridge settings
      - interface bridge vlan
      - interface detect-internet
      - interface dot1x client
      - interface dot1x server
      - interface eoip
      - interface eoipv6
      - interface ethernet
      - interface ethernet poe
      - interface ethernet switch
      - interface ethernet switch host
      - interface ethernet switch l3hw-settings
      - interface ethernet switch l3hw-settings advanced
      - interface ethernet switch port
      - interface ethernet switch port-isolation
      - interface ethernet switch qos map
      - interface ethernet switch qos map ip
      - interface ethernet switch qos map vlan
      - interface ethernet switch qos port
      - interface ethernet switch qos priority-flow-control
      - interface ethernet switch qos profile
      - interface ethernet switch qos settings
      - interface ethernet switch qos tx-manager
      - interface ethernet switch qos tx-manager queue
      - interface ethernet switch rule
      - interface ethernet switch vlan
      - interface gre
      - interface gre6
      - interface ipip
      - interface ipipv6
      - interface l2tp-client
      - interface l2tp-ether
      - interface l2tp-server
      - interface l2tp-server server
      - interface list
      - interface list member
      - interface lte
      - interface lte apn
      - interface lte settings
      - interface macsec
      - interface macsec profile
      - interface macvlan
      - interface mesh
      - interface mesh port
      - interface ovpn-client
      - interface ovpn-server
      - interface ovpn-server server
      - interface ppp-client
      - interface ppp-server
      - interface pppoe-client
      - interface pppoe-server
      - interface pppoe-server server
      - interface pptp-client
      - interface pptp-server
      - interface pptp-server server
      - interface sstp-client
      - interface sstp-server
      - interface sstp-server server
      - interface veth
      - interface vlan
      - interface vpls
      - interface vrrp
      - interface vxlan
      - interface vxlan vteps
      - interface wifi
      - interface wifi aaa
      - interface wifi access-list
      - interface wifi cap
      - interface wifi capsman
      - interface wifi channel
      - interface wifi configuration
      - interface wifi datapath
      - interface wifi interworking
      - interface wifi provisioning
      - interface wifi radio settings
      - interface wifi security
      - interface wifi security multi-passphrase
      - interface wifi steering
      - interface wifi steering neighbor-group
      - interface wifiwave2
      - interface wifiwave2 aaa
      - interface wifiwave2 access-list
      - interface wifiwave2 cap
      - interface wifiwave2 capsman
      - interface wifiwave2 channel
      - interface wifiwave2 configuration
      - interface wifiwave2 datapath
      - interface wifiwave2 interworking
      - interface wifiwave2 provisioning
      - interface wifiwave2 security
      - interface wifiwave2 steering
      - interface wireguard
      - interface wireguard peers
      - interface wireless
      - interface wireless access-list
      - interface wireless align
      - interface wireless cap
      - interface wireless channels
      - interface wireless connect-list
      - interface wireless interworking-profiles
      - interface wireless manual-tx-power-table
      - interface wireless nstreme
      - interface wireless nstreme-dual
      - interface wireless security-profiles
      - interface wireless sniffer
      - interface wireless snooper
      - interface wireless wds
      - iot bluetooth
      - iot bluetooth advertisers
      - iot bluetooth advertisers ad-structures
      - iot bluetooth peripheral-devices
      - iot bluetooth scanners
      - iot bluetooth whitelist
      - iot lora
      - iot lora channels
      - iot lora joineui
      - iot lora netid
      - iot lora radios
      - iot lora servers
      - iot lora traffic options
      - iot modbus
      - iot modbus security-rules
      - iot mqtt brokers
      - iot mqtt subscriptions
      - ip accounting
      - ip accounting web-access
      - ip address
      - ip arp
      - ip cloud
      - ip cloud advanced
      - ip cloud back-to-home-file
      - ip cloud back-to-home-file settings
      - ip cloud back-to-home-user
      - ip cloud back-to-home-users
      - ip dhcp-client
      - ip dhcp-client option
      - ip dhcp-relay
      - ip dhcp-server
      - ip dhcp-server alert
      - ip dhcp-server config
      - ip dhcp-server lease
      - ip dhcp-server matcher
      - ip dhcp-server network
      - ip dhcp-server option
      - ip dhcp-server option sets
      - ip dns
      - ip dns adlist
      - ip dns forwarders
      - ip dns static
      - ip firewall address-list
      - ip firewall calea
      - ip firewall connection tracking
      - ip firewall filter
      - ip firewall layer7-protocol
      - ip firewall mangle
      - ip firewall nat
      - ip firewall raw
      - ip firewall service-port
      - ip hotspot
      - ip hotspot ip-binding
      - ip hotspot profile
      - ip hotspot service-port
      - ip hotspot user
      - ip hotspot user profile
      - ip hotspot walled-garden
      - ip hotspot walled-garden ip
      - ip ipsec identity
      - ip ipsec key
      - ip ipsec key psk
      - ip ipsec key qkd
      - ip ipsec key rsa
      - ip ipsec mode-config
      - ip ipsec peer
      - ip ipsec policy
      - ip ipsec policy group
      - ip ipsec profile
      - ip ipsec proposal
      - ip ipsec settings
      - ip kid-control
      - ip kid-control device
      - ip media
      - ip media settings
      - ip nat-pmp
      - ip nat-pmp interfaces
      - ip neighbor discovery-settings
      - ip packing
      - ip pool
      - ip pool used
      - ip proxy
      - ip proxy access
      - ip proxy cache
      - ip proxy cache-contents
      - ip proxy connections
      - ip proxy direct
      - ip route
      - ip route rule
      - ip route vrf
      - ip service
      - ip service webserver
      - ip settings
      - ip smb
      - ip smb shares
      - ip smb users
      - ip socks
      - ip socks access
      - ip socks connections
      - ip socks users
      - ip socksify
      - ip ssh
      - ip tftp
      - ip tftp settings
      - ip traffic-flow
      - ip traffic-flow ipfix
      - ip traffic-flow target
      - ip upnp
      - ip upnp interfaces
      - ip vrf
      - ipv6 address
      - ipv6 dhcp-client
      - ipv6 dhcp-client option
      - ipv6 dhcp-relay
      - ipv6 dhcp-relay option
      - ipv6 dhcp-server
      - ipv6 dhcp-server binding
      - ipv6 dhcp-server option
      - ipv6 dhcp-server option sets
      - ipv6 firewall address-list
      - ipv6 firewall filter
      - ipv6 firewall mangle
      - ipv6 firewall nat
      - ipv6 firewall raw
      - ipv6 nd
      - ipv6 nd prefix
      - ipv6 nd prefix default
      - ipv6 nd proxy
      - ipv6 neighbor
      - ipv6 pool
      - ipv6 route
      - ipv6 settings
      - lcd
      - lcd interface
      - lcd interface pages
      - lcd pin
      - lcd screen
      - lora
      - lora channels
      - lora joineui
      - lora netid
      - lora radios
      - lora servers
      - lora traffic options
      - mpls
      - mpls interface
      - mpls ldp
      - mpls ldp accept-filter
      - mpls ldp advertise-filter
      - mpls ldp interface
      - mpls ldp local-mapping
      - mpls ldp neighbor
      - mpls ldp remote-mapping
      - mpls mangle
      - mpls settings
      - mpls traffic-eng interface
      - mpls traffic-eng path
      - mpls traffic-eng tunnel
      - openflow
      - openflow port
      - partitions
      - port
      - port firmware
      - port remote-access
      - ppp aaa
      - ppp l2tp-secret
      - ppp profile
      - ppp secret
      - queue interface
      - queue simple
      - queue tree
      - queue type
      - radius
      - radius incoming
      - routing bfd configuration
      - routing bgp aggregate
      - routing bgp connection
      - routing bgp evpn
      - routing bgp instance
      - routing bgp network
      - routing bgp peer
      - routing bgp template
      - routing bgp vpls
      - routing bgp vpn
      - routing fantasy
      - routing filter
      - routing filter community-ext-list
      - routing filter community-large-list
      - routing filter community-list
      - routing filter num-list
      - routing filter rule
      - routing filter select-rule
      - routing gmp
      - routing id
      - routing igmp-proxy
      - routing igmp-proxy interface
      - routing igmp-proxy mfc
      - routing isis instance
      - routing isis interface
      - routing isis interface-template
      - routing isis lsp
      - routing isis neighbor
      - routing mme
      - routing ospf area
      - routing ospf area range
      - routing ospf instance
      - routing ospf interface-template
      - routing ospf neighbor
      - routing ospf static-neighbor
      - routing pimsm bsr candidate
      - routing pimsm bsr rp-candidate
      - routing pimsm igmp-interface-template
      - routing pimsm instance
      - routing pimsm interface-template
      - routing pimsm static-rp
      - routing rip
      - routing rip instance
      - routing rip interface-template
      - routing rip keys
      - routing rip static-neighbor
      - routing ripng
      - routing route
      - routing route rule
      - routing rpki
      - routing rule
      - routing settings
      - routing table
      - rsync-daemon
      - snmp
      - snmp community
      - special-login
      - system clock
      - system clock manual
      - system console
      - system console screen
      - system gps
      - system hardware
      - system health
      - system health settings
      - system identity
      - system leds
      - system leds settings
      - system logging
      - system logging action
      - system note
      - system ntp client
      - system ntp client servers
      - system ntp key
      - system ntp server
      - system package local-update
      - system package local-update mirror
      - system package local-update update-package-source
      - system package update
      - system resource hardware usb-settings
      - system resource irq
      - system resource irq rps
      - system resource usb
      - system resource usb settings
      - system routerboard mode-button
      - system routerboard reset-button
      - system routerboard settings
      - system routerboard usb
      - system routerboard wps-button
      - system scheduler
      - system script
      - system script environment
      - system script job
      - system swos
      - system upgrade
      - system upgrade mirror
      - system upgrade upgrade-package-source
      - system ups
      - system watchdog
      - task
      - tool bandwidth-server
      - tool calea
      - tool e-mail
      - tool graphing
      - tool graphing interface
      - tool graphing queue
      - tool graphing resource
      - tool mac-server
      - tool mac-server mac-winbox
      - tool mac-server ping
      - tool mac-server sessions
      - tool netwatch
      - tool romon
      - tool romon port
      - tool sms
      - tool sniffer
      - tool traffic-generator
      - tool traffic-generator packet-template
      - tool traffic-generator port
      - tool traffic-generator raw-packet-template
      - tool traffic-generator stream
      - tool traffic-monitor
      - tr069-client
      - user
      - user aaa
      - user group
      - user settings
      - user ssh-keys
      - user-manager
      - user-manager advanced
      - user-manager attribute
      - user-manager database
      - user-manager limitation
      - user-manager payment
      - user-manager profile
      - user-manager profile-limitation
      - user-manager router
      - user-manager session
      - user-manager user
      - user-manager user group
      - user-manager user-profile
      - zerotier
      - zerotier controller
      - zerotier controller member
      - zerotier interface
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
  restrict:
    description:
      - Restrict output to entries matching the following criteria.
    version_added: 2.18.0
seealso:
  - module: community.routeros.api
  - module: community.routeros.api_facts
  - module: community.routeros.api_find_and_modify
  - module: community.routeros.api_modify
"""

EXAMPLES = r"""
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
"""

RETURN = r"""
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
"""

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

from ansible_collections.community.routeros.plugins.module_utils._api_helper import (
    restrict_argument_spec,
    restrict_entry_accepted,
    validate_and_prepare_restrict,
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
    module_args.update(restrict_argument_spec())

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
        supported, not_supported_msg = versioned_path_info.provide_version(api_version)
        if not supported:
            msg = 'Path /{path} is not supported for API version {api_version}'.format(path='/'.join(path), api_version=api_version)
            if not_supported_msg:
                msg = '{0}: {1}'.format(msg, not_supported_msg)
            module.fail_json(msg=msg)
    path_info = versioned_path_info.get_data()

    handle_disabled = module.params['handle_disabled']
    hide_defaults = module.params['hide_defaults']
    include_dynamic = module.params['include_dynamic']
    include_builtin = module.params['include_builtin']
    include_read_only = module.params['include_read_only']
    restrict_data = validate_and_prepare_restrict(module, path_info)
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
            if not restrict_entry_accepted(entry, path_info, restrict_data):
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
