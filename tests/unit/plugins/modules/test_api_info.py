# Copyright (c) 2022, Felix Fontein (@felixfontein) <felix@fontein.de>
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from ansible_collections.community.internal_test_tools.tests.unit.compat.mock import patch, MagicMock
from ansible_collections.community.internal_test_tools.tests.unit.plugins.modules.utils import set_module_args, AnsibleExitJson, AnsibleFailJson, ModuleTestCase

from ansible_collections.community.routeros.tests.unit.plugins.modules.fake_api import (
    FAKE_ROS_VERSION, FakeLibRouterosError, Key, fake_ros_api,
)
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
        self.patch_get_api_version = patch(
            'ansible_collections.community.routeros.plugins.modules.api_info.get_api_version',
            MagicMock(return_value=FAKE_ROS_VERSION))
        self.patch_get_api_version.start()
        self.module.Key = MagicMock(new=Key)
        self.config_module_args = {
            'username': 'admin',
            'password': 'pаss',
            'hostname': '127.0.0.1',
        }

    def tearDown(self):
        self.patch_get_api_version.stop()
        self.patch_create_api.stop()

    def test_module_fail_when_required_args_missing(self):
        with self.assertRaises(AnsibleFailJson) as exc:
            with set_module_args({}):
                self.module.main()

        result = exc.exception.args[0]
        self.assertEqual(result['failed'], True)

    def test_invalid_path(self):
        with self.assertRaises(AnsibleFailJson) as exc:
            args = self.config_module_args.copy()
            args.update({
                'path': 'something invalid'
            })
            with set_module_args(args):
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
            with set_module_args(args):
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
            with set_module_args(args):
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
            with set_module_args(args):
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
            with set_module_args(args):
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
            with set_module_args(args):
                self.module.main()

        result = exc.exception.args[0]
        self.assertEqual(result['changed'], False)
        self.assertEqual(result['result'], [{
            'chain': 'input',
            'in-interface-list': 'LAN',
            '!action': None,
            '!address-list': None,
            '!address-list-timeout': None,
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
            '!hw-offload': None,
            '!icmp-options': None,
            '!in-bridge-port': None,
            '!in-bridge-port-list': None,
            '!in-interface': None,
            '!ingress-priority': None,
            '!ipsec-policy': None,
            '!ipv4-options': None,
            '!jump-target': None,
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
            '!realm': None,
            '!reject-with': None,
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
            with set_module_args(args):
                self.module.main()

        result = exc.exception.args[0]
        self.assertEqual(result['changed'], False)
        self.assertEqual(result['result'], [{
            'chain': 'input',
            'in-interface-list': 'LAN',
            'action': None,
            'address-list': None,
            'address-list-timeout': None,
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
            'hw-offload': None,
            'icmp-options': None,
            'in-bridge-port': None,
            'in-bridge-port-list': None,
            'in-interface': None,
            'ingress-priority': None,
            'ipsec-policy': None,
            'ipv4-options': None,
            'jump-target': None,
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
            'realm': None,
            'reject-with': None,
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
            with set_module_args(args):
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
            with set_module_args(args):
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
    def test_builtin_exclude(self, mock_compose_api_path):
        mock_compose_api_path.return_value = [
            {
                '.id': '*2000000',
                'name': 'all',
                'dynamic': False,
                'include': '',
                'exclude': '',
                'builtin': True,
                'comment': 'contains all interfaces',
            },
            {
                '.id': '*2000001',
                'name': 'none',
                'dynamic': False,
                'include': '',
                'exclude': '',
                'builtin': True,
                'comment': 'contains no interfaces',
            },
            {
                '.id': '*2000010',
                'name': 'WAN',
                'dynamic': False,
                'include': '',
                'exclude': '',
                'builtin': False,
                'comment': 'defconf',
            },
        ]
        with self.assertRaises(AnsibleExitJson) as exc:
            args = self.config_module_args.copy()
            args.update({
                'path': 'interface list',
                'handle_disabled': 'omit',
            })
            with set_module_args(args):
                self.module.main()

        result = exc.exception.args[0]
        self.assertEqual(result['changed'], False)
        self.assertEqual(result['result'], [
            {
                '.id': '*2000010',
                'name': 'WAN',
                'include': '',
                'exclude': '',
                'comment': 'defconf',
            },
        ])

    @patch('ansible_collections.community.routeros.plugins.modules.api_info.compose_api_path')
    def test_builtin_include(self, mock_compose_api_path):
        mock_compose_api_path.return_value = [
            {
                '.id': '*2000000',
                'name': 'all',
                'dynamic': False,
                'include': '',
                'exclude': '',
                'builtin': True,
                'comment': 'contains all interfaces',
            },
            {
                '.id': '*2000001',
                'name': 'none',
                'dynamic': False,
                'include': '',
                'exclude': '',
                'builtin': True,
                'comment': 'contains no interfaces',
            },
            {
                '.id': '*2000010',
                'name': 'WAN',
                'dynamic': False,
                'include': '',
                'exclude': '',
                'builtin': False,
                'comment': 'defconf',
            },
        ]
        with self.assertRaises(AnsibleExitJson) as exc:
            args = self.config_module_args.copy()
            args.update({
                'path': 'interface list',
                'handle_disabled': 'omit',
                'include_builtin': True,
            })
            with set_module_args(args):
                self.module.main()

        result = exc.exception.args[0]
        self.assertEqual(result['changed'], False)
        self.assertEqual(result['result'], [
            {
                '.id': '*2000000',
                'name': 'all',
                'include': '',
                'exclude': '',
                'builtin': True,
                'comment': 'contains all interfaces',
            },
            {
                '.id': '*2000001',
                'name': 'none',
                'include': '',
                'exclude': '',
                'builtin': True,
                'comment': 'contains no interfaces',
            },
            {
                '.id': '*2000010',
                'name': 'WAN',
                'include': '',
                'exclude': '',
                'builtin': False,
                'comment': 'defconf',
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
            with set_module_args(args):
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

    @patch('ansible_collections.community.routeros.plugins.modules.api_info.compose_api_path')
    def test_default_disable_1(self, mock_compose_api_path):
        mock_compose_api_path.return_value = [
            {
                '.id': '*10',
                'name': 'gre-tunnel3',
                'mtu': 'auto',
                'actual-mtu': 65496,
                'local-address': '0.0.0.0',
                'remote-address': '192.168.1.1',
                'dscp': 'inherit',
                'clamp-tcp-mss': True,
                'dont-fragment': False,
                'allow-fast-path': True,
                'running': True,
                'disabled': False,
            },
            {
                '.id': '*11',
                'name': 'gre-tunnel4',
                'mtu': 'auto',
                'actual-mtu': 65496,
                'local-address': '0.0.0.0',
                'remote-address': '192.168.1.2',
                'keepalive': '10s,10',
                'dscp': 'inherit',
                'clamp-tcp-mss': True,
                'dont-fragment': False,
                'allow-fast-path': True,
                'running': True,
                'disabled': False,
            },
            {
                '.id': '*12',
                'name': 'gre-tunnel5',
                'mtu': 'auto',
                'actual-mtu': 65496,
                'local-address': '192.168.0.1',
                'remote-address': '192.168.1.3',
                'keepalive': '20s,20',
                'dscp': 'inherit',
                'clamp-tcp-mss': True,
                'dont-fragment': False,
                'allow-fast-path': True,
                'running': True,
                'disabled': False,
                'comment': 'foo',
            },
        ]
        with self.assertRaises(AnsibleExitJson) as exc:
            args = self.config_module_args.copy()
            args.update({
                'path': 'interface gre',
            })
            with set_module_args(args):
                self.module.main()

        result = exc.exception.args[0]
        self.assertEqual(result['changed'], False)
        self.assertEqual(result['result'], [
            {
                '.id': '*10',
                'name': 'gre-tunnel3',
                'remote-address': '192.168.1.1',
                '!comment': None,
                '!ipsec-secret': None,
                '!keepalive': None,
            },
            {
                '.id': '*11',
                'name': 'gre-tunnel4',
                'remote-address': '192.168.1.2',
                '!comment': None,
                '!ipsec-secret': None,
            },
            {
                '.id': '*12',
                'name': 'gre-tunnel5',
                'local-address': '192.168.0.1',
                'remote-address': '192.168.1.3',
                'keepalive': '20s,20',
                'comment': 'foo',
                '!ipsec-secret': None,
            },
        ])

    @patch('ansible_collections.community.routeros.plugins.modules.api_info.compose_api_path')
    def test_default_disable_2(self, mock_compose_api_path):
        mock_compose_api_path.return_value = [
            {
                '.id': '*10',
                'name': 'gre-tunnel3',
                'mtu': 'auto',
                'actual-mtu': 65496,
                'local-address': '0.0.0.0',
                'remote-address': '192.168.1.1',
                'dscp': 'inherit',
                'clamp-tcp-mss': True,
                'dont-fragment': False,
                'allow-fast-path': True,
                'running': True,
                'disabled': False,
            },
            {
                '.id': '*11',
                'name': 'gre-tunnel4',
                'mtu': 'auto',
                'actual-mtu': 65496,
                'local-address': '0.0.0.0',
                'remote-address': '192.168.1.2',
                'keepalive': '10s,10',
                'dscp': 'inherit',
                'clamp-tcp-mss': True,
                'dont-fragment': False,
                'allow-fast-path': True,
                'running': True,
                'disabled': False,
            },
            {
                '.id': '*12',
                'name': 'gre-tunnel5',
                'mtu': 'auto',
                'actual-mtu': 65496,
                'local-address': '192.168.0.1',
                'remote-address': '192.168.1.3',
                'keepalive': '20s,20',
                'dscp': 'inherit',
                'clamp-tcp-mss': True,
                'dont-fragment': False,
                'allow-fast-path': True,
                'running': True,
                'disabled': False,
                'comment': 'foo',
            },
        ]
        with self.assertRaises(AnsibleExitJson) as exc:
            args = self.config_module_args.copy()
            args.update({
                'path': 'interface gre',
                'handle_disabled': 'omit',
                'hide_defaults': False,
            })
            with set_module_args(args):
                self.module.main()

        result = exc.exception.args[0]
        self.assertEqual(result['changed'], False)
        self.assertEqual(result['result'], [
            {
                '.id': '*10',
                'name': 'gre-tunnel3',
                'mtu': 'auto',
                'local-address': '0.0.0.0',
                'remote-address': '192.168.1.1',
                'dscp': 'inherit',
                'clamp-tcp-mss': True,
                'dont-fragment': False,
                'allow-fast-path': True,
                'disabled': False,
            },
            {
                '.id': '*11',
                'name': 'gre-tunnel4',
                'mtu': 'auto',
                'local-address': '0.0.0.0',
                'remote-address': '192.168.1.2',
                'keepalive': '10s,10',
                'dscp': 'inherit',
                'clamp-tcp-mss': True,
                'dont-fragment': False,
                'allow-fast-path': True,
                'disabled': False,
            },
            {
                '.id': '*12',
                'name': 'gre-tunnel5',
                'mtu': 'auto',
                'local-address': '192.168.0.1',
                'remote-address': '192.168.1.3',
                'keepalive': '20s,20',
                'dscp': 'inherit',
                'clamp-tcp-mss': True,
                'dont-fragment': False,
                'allow-fast-path': True,
                'disabled': False,
                'comment': 'foo',
            },
        ])

    @patch('ansible_collections.community.routeros.plugins.modules.api_info.compose_api_path')
    def test_restrict_1(self, mock_compose_api_path):
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
                'dynamic': False,
            },
        ]
        with self.assertRaises(AnsibleExitJson) as exc:
            args = self.config_module_args.copy()
            args.update({
                'path': 'ip firewall filter',
                'handle_disabled': 'omit',
                'restrict': [],
            })
            with set_module_args(args):
                self.module.main()

        result = exc.exception.args[0]
        self.assertEqual(result['changed'], False)
        self.assertEqual(result['result'], [
            {
                'chain': 'input',
                'in-interface-list': 'LAN',
                '.id': '*1',
            },
            {
                'chain': 'forward',
                'action': 'drop',
                'in-interface': 'sfp1',
                '.id': '*2',
            },
        ])

    @patch('ansible_collections.community.routeros.plugins.modules.api_info.compose_api_path')
    def test_restrict_2(self, mock_compose_api_path):
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
                'dynamic': False,
            },
            {
                'chain': 'input',
                'action': 'drop',
                'dynamic': False,
                '.id': '*3',
            },
        ]
        with self.assertRaises(AnsibleExitJson) as exc:
            args = self.config_module_args.copy()
            args.update({
                'path': 'ip firewall filter',
                'handle_disabled': 'omit',
                'restrict': [{
                    'field': 'chain',
                    'values': ['forward'],
                }],
            })
            with set_module_args(args):
                self.module.main()

        result = exc.exception.args[0]
        self.assertEqual(result['changed'], False)
        self.assertEqual(result['result'], [
            {
                'chain': 'forward',
                'action': 'drop',
                'in-interface': 'sfp1',
                '.id': '*2',
            },
        ])

    @patch('ansible_collections.community.routeros.plugins.modules.api_info.compose_api_path')
    def test_restrict_3(self, mock_compose_api_path):
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
                'dynamic': False,
            },
            {
                'chain': 'input',
                'action': 'drop',
                'dynamic': False,
                '.id': '*3',
            },
            {
                'chain': 'input',
                'action': 'drop',
                'comment': 'Foo',
                'dynamic': False,
                '.id': '*4',
            },
            {
                'chain': 'input',
                'action': 'drop',
                'comment': 'Bar',
                'dynamic': False,
                '.id': '*5',
            },
        ]
        with self.assertRaises(AnsibleExitJson) as exc:
            args = self.config_module_args.copy()
            args.update({
                'path': 'ip firewall filter',
                'handle_disabled': 'omit',
                'restrict': [
                    {
                        'field': 'chain',
                        'values': ['input', 'foobar'],
                    },
                    {
                        'field': 'action',
                        'values': ['drop', 42],
                    },
                    {
                        'field': 'comment',
                        'values': [None, 'Foo'],
                    },
                ],
            })
            with set_module_args(args):
                self.module.main()

        result = exc.exception.args[0]
        self.assertEqual(result['changed'], False)
        self.assertEqual(result['result'], [
            {
                'chain': 'input',
                'action': 'drop',
                '.id': '*3',
            },
            {
                'chain': 'input',
                'action': 'drop',
                'comment': 'Foo',
                '.id': '*4',
            },
        ])
