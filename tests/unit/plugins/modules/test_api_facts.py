# Copyright (c) Ansible Project
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import json
import pytest

from ansible_collections.community.routeros.tests.unit.compat.mock import patch, MagicMock
from ansible_collections.community.routeros.tests.unit.plugins.modules.fake_api import FakeLibRouterosError, Key, fake_ros_api
from ansible_collections.community.routeros.tests.unit.plugins.modules.utils import set_module_args, AnsibleExitJson, AnsibleFailJson, ModuleTestCase
from ansible_collections.community.routeros.plugins.modules import api_facts


API_RESPONSES = {
    ('interface', ): [
        {
            '.id': '*1',
            'name': 'first-ether',
            'default-name': 'ether1',
            'type': 'ether',
            'mtu': 1500,
            'actual-mtu': 1500,
            'l2mtu': 1598,
            'max-l2mtu': 4074,
            'mac-address': '00:11:22:33:44:55',
            'last-link-up-time': 'apr/22/2022 07:54:55',
            'link-downs': 0,
            'rx-byte': 1234,
            'tx-byte': 1234,
            'rx-packet': 1234,
            'tx-packet': 1234,
            'rx-drop': 1234,
            'tx-drop': 1234,
            'tx-queue-drop': 1234,
            'rx-error': 1234,
            'tx-error': 1234,
            'fp-rx-byte': 1234,
            'fp-tx-byte': 1234,
            'fp-rx-packet': 1234,
            'fp-tx-packet': 1234,
            'running': True,
            'disabled': False,
        },
        {
            '.id': '*2',
            'name': 'second-ether',
            'default-name': 'ether2',
            'type': 'ether',
            'mtu': 1500,
            'actual-mtu': 1500,
            'l2mtu': 1598,
            'max-l2mtu': 4074,
            'mac-address': '00:11:22:33:44:66',
            'last-link-up-time': 'apr/22/2022 07:54:55',
            'link-downs': 0,
            'rx-byte': 1234,
            'tx-byte': 1234,
            'rx-packet': 1234,
            'tx-packet': 1234,
            'rx-drop': 1234,
            'tx-drop': 1234,
            'tx-queue-drop': 1234,
            'rx-error': 1234,
            'tx-error': 1234,
            'fp-rx-byte': 1234,
            'fp-tx-byte': 1234,
            'fp-rx-packet': 1234,
            'fp-tx-packet': 1234,
            'running': True,
            'slave': True,
            'disabled': False,
        },
        {
            '.id': '*3',
            'name': 'third-ether',
            'default-name': 'ether3',
            'type': 'ether',
            'mtu': 1500,
            'actual-mtu': 1500,
            'l2mtu': 1598,
            'max-l2mtu': 4074,
            'mac-address': '00:11:22:33:44:77',
            'last-link-up-time': 'apr/22/2022 07:54:55',
            'link-downs': 0,
            'rx-byte': 1234,
            'tx-byte': 1234,
            'rx-packet': 1234,
            'tx-packet': 1234,
            'rx-drop': 1234,
            'tx-drop': 1234,
            'tx-queue-drop': 1234,
            'rx-error': 1234,
            'tx-error': 1234,
            'fp-rx-byte': 1234,
            'fp-tx-byte': 1234,
            'fp-rx-packet': 1234,
            'fp-tx-packet': 1234,
            'running': True,
            'slave': True,
            'disabled': False,
        },
        {
            '.id': '*4',
            'name': 'fourth-ether',
            'default-name': 'ether4',
            'type': 'ether',
            'mtu': 1500,
            'actual-mtu': 1500,
            'l2mtu': 1598,
            'max-l2mtu': 4074,
            'mac-address': '00:11:22:33:44:88',
            'last-link-down-time': 'apr/23/2022 08:22:50',
            'last-link-up-time': 'apr/23/2022 08:22:52',
            'link-downs': 2,
            'rx-byte': 1234,
            'tx-byte': 1234,
            'rx-packet': 1234,
            'tx-packet': 1234,
            'rx-drop': 1234,
            'tx-drop': 1234,
            'tx-queue-drop': 1234,
            'rx-error': 1234,
            'tx-error': 1234,
            'fp-rx-byte': 1234,
            'fp-tx-byte': 1234,
            'fp-rx-packet': 1234,
            'fp-tx-packet': 1234,
            'running': True,
            'disabled': False,
        },
        {
            '.id': '*5',
            'name': 'fifth-ether',
            'default-name': 'ether5',
            'type': 'ether',
            'mtu': 1500,
            'actual-mtu': 1500,
            'l2mtu': 1598,
            'max-l2mtu': 4074,
            'mac-address': '00:11:22:33:44:99',
            'last-link-down-time': 'may/02/2022 18:12:32',
            'last-link-up-time': 'may/02/2022 18:08:01',
            'link-downs': 14,
            'rx-byte': 1234,
            'tx-byte': 1234,
            'rx-packet': 1234,
            'tx-packet': 1234,
            'rx-drop': 1234,
            'tx-drop': 1234,
            'tx-queue-drop': 1234,
            'rx-error': 1234,
            'tx-error': 1234,
            'fp-rx-byte': 1234,
            'fp-tx-byte': 1234,
            'fp-rx-packet': 1234,
            'fp-tx-packet': 1234,
            'running': False,
            'slave': True,
            'disabled': False,
        },
        {
            '.id': '*7',
            'name': 'my-bridge',
            'type': 'bridge',
            'mtu': 'auto',
            'actual-mtu': 1500,
            'l2mtu': 1598,
            'mac-address': '00:11:22:33:44:66',
            'last-link-up-time': 'apr/22/2022 07:54:48',
            'link-downs': 0,
            'rx-byte': 1234,
            'tx-byte': 1234,
            'rx-packet': 1234,
            'tx-packet': 1234,
            'rx-drop': 1234,
            'tx-drop': 1234,
            'tx-queue-drop': 1234,
            'rx-error': 1234,
            'tx-error': 1234,
            'fp-rx-byte': 1234,
            'fp-tx-byte': 1234,
            'fp-rx-packet': 1234,
            'fp-tx-packet': 1234,
            'running': True,
            'disabled': False,
        },
    ],
    ('ip', 'address', ): [
        {
            '.id': '*1',
            'address': '192.168.1.1/24',
            'network': '192.168.1.0',
            'interface': 'my-bridge',
            'actual-interface': 'my-bridge',
            'invalid': False,
            'dynamic': False,
            'disabled': False,
            'comment': 'Wohnung',
        },
        {
            '.id': '*5',
            'address': '192.168.2.1/24',
            'network': '192.168.2.0',
            'interface': 'fourth-ether',
            'actual-interface': 'fourth-ether',
            'invalid': False,
            'dynamic': False,
            'disabled': False,
            'comment': 'VoIP',
        },
        {
            '.id': '*6',
            'address': '1.2.3.4/21',
            'network': '84.73.216.0',
            'interface': 'first-ether',
            'actual-interface': 'first-ether',
            'invalid': False,
            'dynamic': True,
            'disabled': False,
        },
    ],
    ('ipv6', 'address', ): [
        {
            '.id': '*1',
            'address': 'fe80::1:2:3/64',
            'from-pool': '',
            'interface': 'my-bridge',
            'actual-interface': 'my-bridge',
            'eui-64': False,
            'advertise': False,
            'no-dad': False,
            'invalid': False,
            'dynamic': True,
            'link-local': True,
            'disabled': False,
        },
        {
            '.id': '*2',
            'address': 'fe80::1:2:4/64',
            'from-pool': '',
            'interface': 'fourth-ether',
            'actual-interface': 'fourth-ether',
            'eui-64': False,
            'advertise': False,
            'no-dad': False,
            'invalid': False,
            'dynamic': True,
            'link-local': True,
            'disabled': False,
        },
        {
            '.id': '*3',
            'address': 'fe80::1:2:5/64',
            'from-pool': '',
            'interface': 'first-ether',
            'actual-interface': 'first-ether',
            'eui-64': False,
            'advertise': False,
            'no-dad': False,
            'invalid': False,
            'dynamic': True,
            'link-local': True,
            'disabled': False,
        },
    ],
    ('ip', 'neighbor', ): [],
    ('system', 'identity', ): [
        {
            'name': 'MikroTik',
        },
    ],
    ('system', 'resource', ): [
        {
            'uptime': '2w3d4h5m6s',
            'version': '6.49.6 (stable)',
            'build-time': 'Apr/07/2022 17:53:31',
            'free-memory': 12345678,
            'total-memory': 23456789,
            'cpu': 'MIPS 24Kc V7.4',
            'cpu-count': 1,
            'cpu-frequency': 400,
            'cpu-load': 48,
            'free-hdd-space': 123456789,
            'total-hdd-space': 234567890,
            'write-sect-since-reboot': 1234,
            'write-sect-total': 12345,
            'bad-blocks': 0,
            'architecture-name': 'mipsbe',
            'board-name': 'RB750GL',
            'platform': 'MikroTik',
        },
    ],
    ('system', 'routerboard', ): [
        {
            'routerboard': True,
            'model': '750GL',
            'serial-number': '0123456789AB',
            'firmware-type': 'ar7240',
            'factory-firmware': '3.09',
            'current-firmware': '6.49.6',
            'upgrade-firmware': '6.49.6',
        },
    ],
    ('routing', 'bgp', 'peer', ): [],
    ('routing', 'bgp', 'vpnv4-route', ): [],
    ('routing', 'bgp', 'instance', ): [
        {
            '.id': '*0',
            'name': 'default',
            'as': 65530,
            'router-id': '0.0.0.0',
            'redistribute-connected': False,
            'redistribute-static': False,
            'redistribute-rip': False,
            'redistribute-ospf': False,
            'redistribute-other-bgp': False,
            'out-filter': '',
            'client-to-client-reflection': True,
            'ignore-as-path-len': False,
            'routing-table': '',
            'default': True,
            'disabled': False,
        },
    ],
    ('ip', 'route', ): [
        {
            '.id': '*30000001',
            'dst-address': '0.0.0.0/0',
            'gateway': '1.2.3.0',
            'gateway-status': '1.2.3.0 reachable via  first-ether',
            'distance': 1,
            'scope': 30,
            'target-scope': 10,
            'vrf-interface': 'first-ether',
            'active': True,
            'dynamic': True,
            'static': True,
            'disabled': False,
        },
        {
            '.id': '*40162F13',
            'dst-address': '84.73.216.0/21',
            'pref-src': '1.2.3.4',
            'gateway': 'first-ether',
            'gateway-status': 'first-ether reachable',
            'distance': 0,
            'scope': 10,
            'active': True,
            'dynamic': True,
            'connect': True,
            'disabled': False,
        },
        {
            '.id': '*4016AA23',
            'dst-address': '192.168.2.0/24',
            'pref-src': '192.168.2.1',
            'gateway': 'fourth-ether',
            'gateway-status': 'fourth-ether reachable',
            'distance': 0,
            'scope': 10,
            'active': True,
            'dynamic': True,
            'connect': True,
            'disabled': False,
        },
        {
            '.id': '*40168E05',
            'dst-address': '192.168.1.0/24',
            'pref-src': '192.168.1.1',
            'gateway': 'my-bridge',
            'gateway-status': 'my-bridge reachable',
            'distance': 0,
            'scope': 10,
            'active': True,
            'dynamic': True,
            'connect': True,
            'disabled': False,
        },
    ],
    ('routing', 'ospf', 'instance', ): [
        {
            '.id': '*0',
            'name': 'default',
            'router-id': '0.0.0.0',
            'distribute-default': 'never',
            'redistribute-connected': False,
            'redistribute-static': False,
            'redistribute-rip': False,
            'redistribute-bgp': False,
            'redistribute-other-ospf': False,
            'metric-default': 1,
            'metric-connected': 20,
            'metric-static': 20,
            'metric-rip': 20,
            'metric-bgp': 'auto',
            'metric-other-ospf': 'auto',
            'in-filter': 'ospf-in',
            'out-filter': 'ospf-out',
            'state': 'down',
            'default': True,
            'disabled': False,
        },
    ],
    ('routing', 'ospf', 'neighbor', ): [],
}


class TestRouterosApiFactsModule(ModuleTestCase):

    def setUp(self):
        super(TestRouterosApiFactsModule, self).setUp()
        self.module = api_facts
        self.module.LibRouterosError = FakeLibRouterosError
        self.module.connect = MagicMock(new=fake_ros_api)
        self.module.check_has_library = MagicMock()
        self.patch_create_api = patch('ansible_collections.community.routeros.plugins.modules.api_facts.create_api', MagicMock(new=fake_ros_api))
        self.patch_create_api.start()
        self.patch_query_path = patch('ansible_collections.community.routeros.plugins.modules.api_facts.FactsBase.query_path', self.query_path)
        self.patch_query_path.start()
        self.module.Key = MagicMock(new=Key)
        self.config_module_args = {
            'username': 'admin',
            'password': 'pаss',
            'hostname': '127.0.0.1',
        }

    def tearDown(self):
        self.patch_query_path.stop()
        self.patch_create_api.stop()

    def query_path(self, path):
        response = API_RESPONSES.get(tuple(path))
        if response is None:
            raise Exception('Unexpected command: %s' % repr(path))
        return response

    def test_module_fail_when_required_args_missing(self):
        with self.assertRaises(AnsibleFailJson) as exc:
            set_module_args({})
            self.module.main()

        result = exc.exception.args[0]
        self.assertEqual(result['failed'], True)

    def test_module_fail_when_invalid_gather_subset(self):
        with self.assertRaises(AnsibleFailJson) as exc:
            module_args = self.config_module_args.copy()
            module_args['gather_subset'] = ['!foobar']
            set_module_args(module_args)
            self.module.main()

        result = exc.exception.args[0]
        self.assertEqual(result['failed'], True)
        self.assertEqual(result['msg'], 'Bad subset: foobar')

    def test_full_run(self):
        with self.assertRaises(AnsibleExitJson) as exc:
            set_module_args(self.config_module_args.copy())
            self.module.main()

        result = exc.exception.args[0]
        self.assertEqual(result['changed'], False)
        self.assertEqual(result['ansible_facts']['ansible_net_all_ipv4_addresses'], [
            '192.168.1.1',
            '192.168.2.1',
            '1.2.3.4',
        ])
        self.assertEqual(result['ansible_facts']['ansible_net_all_ipv6_addresses'], [
            'fe80::1:2:3',
            'fe80::1:2:4',
            'fe80::1:2:5',
        ])
        self.assertEqual(result['ansible_facts']['ansible_net_arch'], 'mipsbe')
        self.assertEqual(result['ansible_facts']['ansible_net_bgp_instance'], {
            'default': {
                'as': 65530,
                'client-to-client-reflection': True,
                'default': True,
                'disabled': False,
                'ignore-as-path-len': False,
                'name': 'default',
                'out-filter': '',
                'redistribute-connected': False,
                'redistribute-ospf': False,
                'redistribute-other-bgp': False,
                'redistribute-rip': False,
                'redistribute-static': False,
                'router-id': '0.0.0.0',
                'routing-table': ''
            },
        })
        self.assertEqual(result['ansible_facts']['ansible_net_bgp_peer'], {})
        self.assertEqual(result['ansible_facts']['ansible_net_bgp_vpnv4_route'], {})
        self.assertEqual(result['ansible_facts']['ansible_net_cpu_load'], 48)
        self.assertEqual(result['ansible_facts']['ansible_net_gather_subset'], [
            'default',
            'hardware',
            'interfaces',
            'routing',
        ])
        self.assertEqual(result['ansible_facts']['ansible_net_hostname'], 'MikroTik')
        self.assertEqual(result['ansible_facts']['ansible_net_interfaces'], {
            'my-bridge': {
                'actual-mtu': 1500,
                'disabled': False,
                'fp-rx-byte': 1234,
                'fp-rx-packet': 1234,
                'fp-tx-byte': 1234,
                'fp-tx-packet': 1234,
                'ipv4': [
                    {
                        'address': '192.168.1.1',
                        'subnet': 24
                    }
                ],
                'ipv6': [
                    {
                        'address': 'fe80::1:2:3',
                        'subnet': 64
                    }
                ],
                'l2mtu': 1598,
                'last-link-up-time': 'apr/22/2022 07:54:48',
                'link-downs': 0,
                'mac-address': '00:11:22:33:44:66',
                'mtu': 'auto',
                'name': 'my-bridge',
                'running': True,
                'rx-byte': 1234,
                'rx-drop': 1234,
                'rx-error': 1234,
                'rx-packet': 1234,
                'tx-byte': 1234,
                'tx-drop': 1234,
                'tx-error': 1234,
                'tx-packet': 1234,
                'tx-queue-drop': 1234,
                'type': 'bridge'
            },
            'first-ether': {
                'actual-mtu': 1500,
                'default-name': 'ether1',
                'disabled': False,
                'fp-rx-byte': 1234,
                'fp-rx-packet': 1234,
                'fp-tx-byte': 1234,
                'fp-tx-packet': 1234,
                'ipv4': [
                    {
                        'address': '1.2.3.4',
                        'subnet': 21
                    }
                ],
                'ipv6': [
                    {
                        'address': 'fe80::1:2:5',
                        'subnet': 64
                    }
                ],
                'l2mtu': 1598,
                'last-link-up-time': 'apr/22/2022 07:54:55',
                'link-downs': 0,
                'mac-address': '00:11:22:33:44:55',
                'max-l2mtu': 4074,
                'mtu': 1500,
                'name': 'first-ether',
                'running': True,
                'rx-byte': 1234,
                'rx-drop': 1234,
                'rx-error': 1234,
                'rx-packet': 1234,
                'tx-byte': 1234,
                'tx-drop': 1234,
                'tx-error': 1234,
                'tx-packet': 1234,
                'tx-queue-drop': 1234,
                'type': 'ether'
            },
            'second-ether': {
                'actual-mtu': 1500,
                'default-name': 'ether2',
                'disabled': False,
                'fp-rx-byte': 1234,
                'fp-rx-packet': 1234,
                'fp-tx-byte': 1234,
                'fp-tx-packet': 1234,
                'l2mtu': 1598,
                'last-link-up-time': 'apr/22/2022 07:54:55',
                'link-downs': 0,
                'mac-address': '00:11:22:33:44:66',
                'max-l2mtu': 4074,
                'mtu': 1500,
                'name': 'second-ether',
                'running': True,
                'rx-byte': 1234,
                'rx-drop': 1234,
                'rx-error': 1234,
                'rx-packet': 1234,
                'slave': True,
                'tx-byte': 1234,
                'tx-drop': 1234,
                'tx-error': 1234,
                'tx-packet': 1234,
                'tx-queue-drop': 1234,
                'type': 'ether'
            },
            'third-ether': {
                'actual-mtu': 1500,
                'default-name': 'ether3',
                'disabled': False,
                'fp-rx-byte': 1234,
                'fp-rx-packet': 1234,
                'fp-tx-byte': 1234,
                'fp-tx-packet': 1234,
                'l2mtu': 1598,
                'last-link-up-time': 'apr/22/2022 07:54:55',
                'link-downs': 0,
                'mac-address': '00:11:22:33:44:77',
                'max-l2mtu': 4074,
                'mtu': 1500,
                'name': 'third-ether',
                'running': True,
                'rx-byte': 1234,
                'rx-drop': 1234,
                'rx-error': 1234,
                'rx-packet': 1234,
                'slave': True,
                'tx-byte': 1234,
                'tx-drop': 1234,
                'tx-error': 1234,
                'tx-packet': 1234,
                'tx-queue-drop': 1234,
                'type': 'ether'
            },
            'fourth-ether': {
                'actual-mtu': 1500,
                'default-name': 'ether4',
                'disabled': False,
                'fp-rx-byte': 1234,
                'fp-rx-packet': 1234,
                'fp-tx-byte': 1234,
                'fp-tx-packet': 1234,
                'ipv4': [
                    {
                        'address': '192.168.2.1',
                        'subnet': 24
                    }
                ],
                'ipv6': [
                    {
                        'address': 'fe80::1:2:4',
                        'subnet': 64
                    }
                ],
                'l2mtu': 1598,
                'last-link-down-time': 'apr/23/2022 08:22:50',
                'last-link-up-time': 'apr/23/2022 08:22:52',
                'link-downs': 2,
                'mac-address': '00:11:22:33:44:88',
                'max-l2mtu': 4074,
                'mtu': 1500,
                'name': 'fourth-ether',
                'running': True,
                'rx-byte': 1234,
                'rx-drop': 1234,
                'rx-error': 1234,
                'rx-packet': 1234,
                'tx-byte': 1234,
                'tx-drop': 1234,
                'tx-error': 1234,
                'tx-packet': 1234,
                'tx-queue-drop': 1234,
                'type': 'ether'
            },
            'fifth-ether': {
                'actual-mtu': 1500,
                'default-name': 'ether5',
                'disabled': False,
                'fp-rx-byte': 1234,
                'fp-rx-packet': 1234,
                'fp-tx-byte': 1234,
                'fp-tx-packet': 1234,
                'l2mtu': 1598,
                'last-link-down-time': 'may/02/2022 18:12:32',
                'last-link-up-time': 'may/02/2022 18:08:01',
                'link-downs': 14,
                'mac-address': '00:11:22:33:44:99',
                'max-l2mtu': 4074,
                'mtu': 1500,
                'name': 'fifth-ether',
                'running': False,
                'rx-byte': 1234,
                'rx-drop': 1234,
                'rx-error': 1234,
                'rx-packet': 1234,
                'slave': True,
                'tx-byte': 1234,
                'tx-drop': 1234,
                'tx-error': 1234,
                'tx-packet': 1234,
                'tx-queue-drop': 1234,
                'type': 'ether'
            }
        })
        self.assertEqual(result['ansible_facts']['ansible_net_memfree_mb'], 12345678 / 1048576.0)
        self.assertEqual(result['ansible_facts']['ansible_net_memtotal_mb'], 23456789 / 1048576.0)
        self.assertEqual(result['ansible_facts']['ansible_net_model'], '750GL')
        self.assertEqual(result['ansible_facts']['ansible_net_neighbors'], [])
        self.assertEqual(result['ansible_facts']['ansible_net_ospf_instance'], {
            'default': {
                'default': True,
                'disabled': False,
                'distribute-default': 'never',
                'in-filter': 'ospf-in',
                'metric-bgp': 'auto',
                'metric-connected': 20,
                'metric-default': 1,
                'metric-other-ospf': 'auto',
                'metric-rip': 20,
                'metric-static': 20,
                'name': 'default',
                'out-filter': 'ospf-out',
                'redistribute-bgp': False,
                'redistribute-connected': False,
                'redistribute-other-ospf': False,
                'redistribute-rip': False,
                'redistribute-static': False,
                'router-id': '0.0.0.0',
                'state': 'down'
            }
        })
        self.assertEqual(result['ansible_facts']['ansible_net_ospf_neighbor'], {})
        self.assertEqual(result['ansible_facts']['ansible_net_route'], {
            'main': {
                'active': True,
                'connect': True,
                'disabled': False,
                'distance': 0,
                'dst-address': '192.168.1.0/24',
                'dynamic': True,
                'gateway': 'my-bridge',
                'gateway-status': 'my-bridge reachable',
                'pref-src': '192.168.1.1',
                'scope': 10
            }
        })
        self.assertEqual(result['ansible_facts']['ansible_net_serialnum'], '0123456789AB')
        self.assertEqual(result['ansible_facts']['ansible_net_spacefree_mb'], 123456789 / 1048576.0)
        self.assertEqual(result['ansible_facts']['ansible_net_spacetotal_mb'], 234567890 / 1048576.0)
        self.assertEqual(result['ansible_facts']['ansible_net_uptime'], '2w3d4h5m6s')
        self.assertEqual(result['ansible_facts']['ansible_net_version'], '6.49.6 (stable)')
