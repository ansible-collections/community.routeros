# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.

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
