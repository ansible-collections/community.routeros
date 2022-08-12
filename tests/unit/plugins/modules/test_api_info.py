# Copyright (c) 2022, Felix Fontein (@felixfontein) <felix@fontein.de>
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
from ansible_collections.community.routeros.plugins.modules import api_info


class TestRouterosApiInfoModule(ModuleTestCase):

    def setUp(self):
        super(TestRouterosApiInfoModule, self).setUp()
        self.module = api_info
        self.module.LibRouterosError = FakeLibRouterosError
        self.module.connect = MagicMock(new=fake_ros_api)
        self.module.check_has_library = MagicMock()
        self.patch_create_api = patch('ansible_collections.community.routeros.plugins.modules.api_info.create_api', MagicMock(new=fake_ros_api))
        self.patch_create_api.start()
        self.module.Key = MagicMock(new=Key)
        self.config_module_args = {
            'username': 'admin',
            'password': 'pаss',
            'hostname': '127.0.0.1',
        }

    def tearDown(self):
        self.patch_create_api.stop()

    def test_module_fail_when_required_args_missing(self):
        with self.assertRaises(AnsibleFailJson) as exc:
            set_module_args({})
            self.module.main()

        result = exc.exception.args[0]
        self.assertEqual(result['failed'], True)

    def test_invalid_path(self):
        with self.assertRaises(AnsibleFailJson) as exc:
            args = self.config_module_args.copy()
            args.update({
                'path': 'something invalid'
            })
            set_module_args(args)
            self.module.main()

        result = exc.exception.args[0]
        self.assertEqual(result['failed'], True)
        self.assertEqual(result['msg'].startswith('value of path must be one of: '), True)

    @patch('ansible_collections.community.routeros.plugins.modules.api_info.compose_api_path')
    def test_empty_result(self, mock_compose_api_path):
        mock_compose_api_path.return_value = []
        with self.assertRaises(AnsibleExitJson) as exc:
            args = self.config_module_args.copy()
            args.update({
                'path': 'ip dns static'
            })
            set_module_args(args)
            self.module.main()

        result = exc.exception.args[0]
        self.assertEqual(result['changed'], False)
        self.assertEqual(result['result'], [])

    @patch('ansible_collections.community.routeros.plugins.modules.api_info.compose_api_path')
    def test_regular_result(self, mock_compose_api_path):
        mock_compose_api_path.return_value = [
            {
                'called-format': 'mac:ssid',
                'interim-update': 'enabled',
                'mac-caching': 'disabled',
                'mac-format': 'XX:XX:XX:XX:XX:XX',
                'mac-mode': 'as-username',
                'foo': 'bar',
                '.id': '*1',
            },
        ]
        with self.assertRaises(AnsibleExitJson) as exc:
            args = self.config_module_args.copy()
            args.update({
                'path': 'caps-man aaa',
            })
            set_module_args(args)
            self.module.main()

        result = exc.exception.args[0]
        self.assertEqual(result['changed'], False)
        self.assertEqual(result['result'], [{
            'interim-update': 'enabled',
            '.id': '*1',
        }])

    @patch('ansible_collections.community.routeros.plugins.modules.api_info.compose_api_path')
    def test_result_with_defaults(self, mock_compose_api_path):
        mock_compose_api_path.return_value = [
            {
                'called-format': 'mac:ssid',
                'interim-update': 'enabled',
                'mac-caching': 'disabled',
                'mac-format': 'XX:XX:XX:XX:XX:XX',
                'mac-mode': 'as-username',
                'foo': 'bar',
                '.id': '*1',
            },
        ]
        with self.assertRaises(AnsibleExitJson) as exc:
            args = self.config_module_args.copy()
            args.update({
                'path': 'caps-man aaa',
                'hide_defaults': False,
            })
            set_module_args(args)
            self.module.main()

        result = exc.exception.args[0]
        self.assertEqual(result['changed'], False)
        self.assertEqual(result['result'], [{
            'called-format': 'mac:ssid',
            'interim-update': 'enabled',
            'mac-caching': 'disabled',
            'mac-format': 'XX:XX:XX:XX:XX:XX',
            'mac-mode': 'as-username',
            '.id': '*1',
        }])

    @patch('ansible_collections.community.routeros.plugins.modules.api_info.compose_api_path')
    def test_full_result(self, mock_compose_api_path):
        mock_compose_api_path.return_value = [
            {
                'called-format': 'mac:ssid',
                'interim-update': 'enabled',
                'mac-caching': 'disabled',
                'mac-format': 'XX:XX:XX:XX:XX:XX',
                'mac-mode': 'as-username',
                'foo': 'bar',
                '.id': '*1',
            },
        ]
        with self.assertRaises(AnsibleExitJson) as exc:
            args = self.config_module_args.copy()
            args.update({
                'path': 'caps-man aaa',
                'unfiltered': True,
            })
            set_module_args(args)
            self.module.main()

        result = exc.exception.args[0]
        self.assertEqual(result['changed'], False)
        self.assertEqual(result['result'], [{
            'interim-update': 'enabled',
            'foo': 'bar',
            '.id': '*1',
        }])

    @patch('ansible_collections.community.routeros.plugins.modules.api_info.compose_api_path')
    def test_disabled_exclamation(self, mock_compose_api_path):
        mock_compose_api_path.return_value = [
            {
                'chain': 'input',
                'in-interface-list': 'LAN',
                '.id': '*1',
                'dynamic': False,
            },
            {
                'chain': 'forward',
                'action': 'drop',
                'in-interface': 'sfp1',
                '.id': '*2',
                'dynamic': True,
            },
        ]
        with self.assertRaises(AnsibleExitJson) as exc:
            args = self.config_module_args.copy()
            args.update({
                'path': 'ip firewall filter',
                'handle_disabled': 'exclamation',
            })
            set_module_args(args)
            self.module.main()

        result = exc.exception.args[0]
        self.assertEqual(result['changed'], False)
        self.assertEqual(result['result'], [{
            'chain': 'input',
            'in-interface-list': 'LAN',
            '!action': None,
            '!comment': None,
            '!connection-bytes': None,
            '!connection-limit': None,
            '!connection-mark': None,
            '!connection-nat-state': None,
            '!connection-rate': None,
            '!connection-state': None,
            '!connection-type': None,
            '!content': None,
            '!disabled': None,
            '!dscp': None,
            '!dst-address': None,
            '!dst-address-list': None,
            '!dst-address-type': None,
            '!dst-limit': None,
            '!dst-port': None,
            '!fragment': None,
            '!hotspot': None,
            '!icmp-options': None,
            '!in-bridge-port': None,
            '!in-bridge-port-list': None,
            '!in-interface': None,
            '!ingress-priority': None,
            '!ipsec-policy': None,
            '!ipv4-options': None,
            '!layer7-protocol': None,
            '!limit': None,
            '!log': None,
            '!log-prefix': None,
            '!nth': None,
            '!out-bridge-port': None,
            '!out-bridge-port-list': None,
            '!out-interface': None,
            '!out-interface-list': None,
            '!p2p': None,
            '!packet-mark': None,
            '!packet-size': None,
            '!per-connection-classifier': None,
            '!port': None,
            '!priority': None,
            '!protocol': None,
            '!psd': None,
            '!random': None,
            '!routing-mark': None,
            '!routing-table': None,
            '!src-address': None,
            '!src-address-list': None,
            '!src-address-type': None,
            '!src-mac-address': None,
            '!src-port': None,
            '!tcp-flags': None,
            '!tcp-mss': None,
            '!time': None,
            '!tls-host': None,
            '!ttl': None,
            '.id': '*1',
        }])

    @patch('ansible_collections.community.routeros.plugins.modules.api_info.compose_api_path')
    def test_disabled_null_value(self, mock_compose_api_path):
        mock_compose_api_path.return_value = [
            {
                'chain': 'input',
                'in-interface-list': 'LAN',
                '.id': '*1',
                'dynamic': False,
            },
        ]
        with self.assertRaises(AnsibleExitJson) as exc:
            args = self.config_module_args.copy()
            args.update({
                'path': 'ip firewall filter',
                'handle_disabled': 'null-value',
            })
            set_module_args(args)
            self.module.main()

        result = exc.exception.args[0]
        self.assertEqual(result['changed'], False)
        self.assertEqual(result['result'], [{
            'chain': 'input',
            'in-interface-list': 'LAN',
            'action': None,
            'comment': None,
            'connection-bytes': None,
            'connection-limit': None,
            'connection-mark': None,
            'connection-nat-state': None,
            'connection-rate': None,
            'connection-state': None,
            'connection-type': None,
            'content': None,
            'disabled': None,
            'dscp': None,
            'dst-address': None,
            'dst-address-list': None,
            'dst-address-type': None,
            'dst-limit': None,
            'dst-port': None,
            'fragment': None,
            'hotspot': None,
            'icmp-options': None,
            'in-bridge-port': None,
            'in-bridge-port-list': None,
            'in-interface': None,
            'ingress-priority': None,
            'ipsec-policy': None,
            'ipv4-options': None,
            'layer7-protocol': None,
            'limit': None,
            'log': None,
            'log-prefix': None,
            'nth': None,
            'out-bridge-port': None,
            'out-bridge-port-list': None,
            'out-interface': None,
            'out-interface-list': None,
            'p2p': None,
            'packet-mark': None,
            'packet-size': None,
            'per-connection-classifier': None,
            'port': None,
            'priority': None,
            'protocol': None,
            'psd': None,
            'random': None,
            'routing-mark': None,
            'routing-table': None,
            'src-address': None,
            'src-address-list': None,
            'src-address-type': None,
            'src-mac-address': None,
            'src-port': None,
            'tcp-flags': None,
            'tcp-mss': None,
            'time': None,
            'tls-host': None,
            'ttl': None,
            '.id': '*1',
        }])

    @patch('ansible_collections.community.routeros.plugins.modules.api_info.compose_api_path')
    def test_disabled_omit(self, mock_compose_api_path):
        mock_compose_api_path.return_value = [
            {
                'chain': 'input',
                'in-interface-list': 'LAN',
                '.id': '*1',
                'dynamic': False,
            },
        ]
        with self.assertRaises(AnsibleExitJson) as exc:
            args = self.config_module_args.copy()
            args.update({
                'path': 'ip firewall filter',
                'handle_disabled': 'omit',
            })
            set_module_args(args)
            self.module.main()

        result = exc.exception.args[0]
        self.assertEqual(result['changed'], False)
        self.assertEqual(result['result'], [{
            'chain': 'input',
            'in-interface-list': 'LAN',
            '.id': '*1',
        }])

    @patch('ansible_collections.community.routeros.plugins.modules.api_info.compose_api_path')
    def test_dynamic(self, mock_compose_api_path):
        mock_compose_api_path.return_value = [
            {
                'chain': 'input',
                'in-interface-list': 'LAN',
                'dynamic': False,
                '.id': '*1',
            },
            {
                'chain': 'forward',
                'action': 'drop',
                'in-interface': 'sfp1',
                '.id': '*2',
                'dynamic': True,
            },
        ]
        with self.assertRaises(AnsibleExitJson) as exc:
            args = self.config_module_args.copy()
            args.update({
                'path': 'ip firewall filter',
                'handle_disabled': 'omit',
                'include_dynamic': True,
            })
            set_module_args(args)
            self.module.main()

        result = exc.exception.args[0]
        self.assertEqual(result['changed'], False)
        self.assertEqual(result['result'], [
            {
                'chain': 'input',
                'in-interface-list': 'LAN',
                '.id': '*1',
                'dynamic': False,
            },
            {
                'chain': 'forward',
                'action': 'drop',
                'in-interface': 'sfp1',
                '.id': '*2',
                'dynamic': True,
            },
        ])

    @patch('ansible_collections.community.routeros.plugins.modules.api_info.compose_api_path')
    def test_absent(self, mock_compose_api_path):
        mock_compose_api_path.return_value = [
            {
                '.id': '*1',
                'address': '192.168.88.2',
                'mac-address': '11:22:33:44:55:66',
                'client-id': 'ff:1:2:3:4:5:6:7:8:9:a:b:c:d:e:f:0:1:2',
                'address-lists': '',
                'server': 'main',
                'dhcp-option': '',
                'status': 'waiting',
                'last-seen': 'never',
                'radius': False,
                'dynamic': False,
                'blocked': False,
                'disabled': False,
                'comment': 'foo',
            },
            {
                '.id': '*2',
                'address': '192.168.88.3',
                'mac-address': '11:22:33:44:55:77',
                'client-id': '1:2:3:4:5:6:7',
                'address-lists': '',
                'server': 'main',
                'dhcp-option': '',
                'status': 'bound',
                'expires-after': '3d7m8s',
                'last-seen': '1m52s',
                'active-address': '192.168.88.14',
                'active-mac-address': '11:22:33:44:55:76',
                'active-client-id': '1:2:3:4:5:6:7',
                'active-server': 'main',
                'host-name': 'bar',
                'radius': False,
                'dynamic': False,
                'blocked': False,
                'disabled': False,
            },
            {
                '.id': '*3',
                'address': '0.0.0.1',
                'mac-address': '00:00:00:00:00:01',
                'address-lists': '',
                'dhcp-option': '',
                'status': 'waiting',
                'last-seen': 'never',
                'radius': False,
                'dynamic': False,
                'blocked': False,
                'disabled': False,
            },
        ]
        with self.assertRaises(AnsibleExitJson) as exc:
            args = self.config_module_args.copy()
            args.update({
                'path': 'ip dhcp-server lease',
                'handle_disabled': 'omit',
            })
            set_module_args(args)
            self.module.main()

        result = exc.exception.args[0]
        self.assertEqual(result['changed'], False)
        self.assertEqual(result['result'], [
            {
                '.id': '*1',
                'address': '192.168.88.2',
                'mac-address': '11:22:33:44:55:66',
                'client-id': 'ff:1:2:3:4:5:6:7:8:9:a:b:c:d:e:f:0:1:2',
                'server': 'main',
                'comment': 'foo',
            },
            {
                '.id': '*2',
                'address': '192.168.88.3',
                'mac-address': '11:22:33:44:55:77',
                'client-id': '1:2:3:4:5:6:7',
                'server': 'main',
            },
            {
                '.id': '*3',
                'address': '0.0.0.1',
                'mac-address': '00:00:00:00:00:01',
                'server': 'all',
            },
        ])
