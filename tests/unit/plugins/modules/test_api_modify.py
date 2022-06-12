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
from ansible_collections.community.routeros.tests.unit.plugins.modules.fake_api import (
    FakeLibRouterosError, fake_ros_api, massage_expected_result_data, create_fake_path,
)
from ansible_collections.community.routeros.tests.unit.plugins.modules.utils import set_module_args, AnsibleExitJson, AnsibleFailJson, ModuleTestCase
from ansible_collections.community.routeros.plugins.module_utils._api_data import PATHS
from ansible_collections.community.routeros.plugins.modules import api_modify


START_IP_DNS_STATIC = [
    {
        '.id': '*1',
        'comment': 'defconf',
        'name': 'router',
        'address': '192.168.88.1',
        'dynamic': False,
    },
    {
        '.id': '*A',
        'name': 'router',
        'text': 'Router Text Entry',
        'dynamic': False,
    },
    {
        '.id': '*7',
        'comment': '',
        'name': 'foo',
        'address': '192.168.88.2',
        'dynamic': False,
    },
    {
        '.id': '*8',
        'comment': '',
        'name': 'dynfoo',
        'address': '192.168.88.15',
        'dynamic': True,
    },
]

START_IP_DNS_STATIC_OLD_DATA = massage_expected_result_data(START_IP_DNS_STATIC, ('ip', 'dns', 'static'), remove_dynamic=True)

START_IP_SETTINGS = [
    {
        'accept-redirects': True,
        'accept-source-route': False,
        'allow-fast-path': True,
        'arp-timeout': '30s',
        'icmp-rate-limit': 20,
        'icmp-rate-mask': '0x1818',
        'ip-forward': True,
        'max-neighbor-entries': 8192,
        'route-cache': True,
        'rp-filter': False,
        'secure-redirects': True,
        'send-redirects': True,
        'tcp-syncookies': False,
    },
]

START_IP_SETTINGS_OLD_DATA = massage_expected_result_data(START_IP_SETTINGS, ('ip', 'settings'))

START_IP_ADDRESS = [
    {
        '.id': '*1',
        'address': '192.168.88.0/24',
        'interface': 'bridge',
        'disabled': False,
    },
    {
        '.id': '*3',
        'address': '192.168.1.0/24',
        'interface': 'LAN',
        'disabled': False,
    },
    {
        '.id': '*F',
        'address': '10.0.0.0/16',
        'interface': 'WAN',
        'disabled': True,
    },
]

START_IP_ADDRESS_OLD_DATA = massage_expected_result_data(START_IP_ADDRESS, ('ip', 'address'))


class TestRouterosApiModifyModule(ModuleTestCase):

    def setUp(self):
        super(TestRouterosApiModifyModule, self).setUp()
        self.module = api_modify
        self.module.LibRouterosError = FakeLibRouterosError
        self.module.connect = MagicMock(new=fake_ros_api)
        self.module.check_has_library = MagicMock()
        self.patch_create_api = patch(
            'ansible_collections.community.routeros.plugins.modules.api_modify.create_api',
            MagicMock(new=fake_ros_api))
        self.patch_create_api.start()
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
                'path': 'something invalid',
                'data': [],
            })
            set_module_args(args)
            self.module.main()

        result = exc.exception.args[0]
        self.assertEqual(result['failed'], True)
        self.assertEqual(result['msg'].startswith('value of path must be one of: '), True)

    def test_invalid_option(self):
        with self.assertRaises(AnsibleFailJson) as exc:
            args = self.config_module_args.copy()
            args.update({
                'path': 'ip dns static',
                'data': [{
                    'name': 'baz',
                    'foo': 'bar',
                }],
            })
            set_module_args(args)
            self.module.main()

        result = exc.exception.args[0]
        self.assertEqual(result['failed'], True)
        self.assertEqual(result['msg'], 'Unknown key "foo" at index 1.')

    def test_invalid_disabled_and_enabled_option(self):
        with self.assertRaises(AnsibleFailJson) as exc:
            args = self.config_module_args.copy()
            args.update({
                'path': 'ip dns static',
                'data': [{
                    'name': 'baz',
                    'comment': 'foo',
                    '!comment': None,
                }],
            })
            set_module_args(args)
            self.module.main()

        result = exc.exception.args[0]
        self.assertEqual(result['failed'], True)
        self.assertEqual(result['msg'], 'Not both "comment" and "!comment" must appear at index 1.')

    def test_invalid_disabled_option(self):
        with self.assertRaises(AnsibleFailJson) as exc:
            args = self.config_module_args.copy()
            args.update({
                'path': 'ip dns static',
                'data': [{
                    'name': 'foo',
                    '!disabled': None,
                }],
            })
            set_module_args(args)
            self.module.main()

        result = exc.exception.args[0]
        self.assertEqual(result['failed'], True)
        self.assertEqual(result['msg'], 'Key "!disabled" must not be disabled (leading "!") at index 1.')

    def test_invalid_disabled_option_value(self):
        with self.assertRaises(AnsibleFailJson) as exc:
            args = self.config_module_args.copy()
            args.update({
                'path': 'ip dns static',
                'data': [{
                    'name': 'baz',
                    '!comment': 'foo',
                }],
            })
            set_module_args(args)
            self.module.main()

        result = exc.exception.args[0]
        self.assertEqual(result['failed'], True)
        self.assertEqual(result['msg'], 'Disabled key "!comment" must not have a value at index 1.')

    def test_invalid_non_disabled_option_value(self):
        with self.assertRaises(AnsibleFailJson) as exc:
            args = self.config_module_args.copy()
            args.update({
                'path': 'ip dns static',
                'data': [{
                    'name': None,
                }],
            })
            set_module_args(args)
            self.module.main()

        result = exc.exception.args[0]
        self.assertEqual(result['failed'], True)
        self.assertEqual(result['msg'], 'Key "name" must not be disabled (value null/~/None) at index 1.')

    def test_invalid_required_missing(self):
        with self.assertRaises(AnsibleFailJson) as exc:
            args = self.config_module_args.copy()
            args.update({
                'path': 'ip dns static',
                'data': [{
                    'address': '1.2.3.4',
                }],
            })
            set_module_args(args)
            self.module.main()

        result = exc.exception.args[0]
        self.assertEqual(result['failed'], True)
        self.assertEqual(result['msg'], 'Every element in data must contain "name". For example, the element at index #1 does not provide it.')

    @patch('ansible_collections.community.routeros.plugins.modules.api_modify.compose_api_path',
           new=create_fake_path(('ip', 'dns', 'static'), START_IP_DNS_STATIC, read_only=True))
    def test_sync_list_idempotent(self):
        with self.assertRaises(AnsibleExitJson) as exc:
            args = self.config_module_args.copy()
            args.update({
                'path': 'ip dns static',
                'data': [
                    {
                        '.id': 'bam',  # this should be ignored
                        'comment': 'defconf',
                        'name': 'router',
                        'address': '192.168.88.1',
                    },
                    {
                        'name': 'foo',
                        'address': '192.168.88.2',
                    },
                    {
                        'comment': None,
                        'name': 'router',
                        'text': 'Router Text Entry',
                    },
                ],
            })
            set_module_args(args)
            self.module.main()

        result = exc.exception.args[0]
        self.assertEqual(result['changed'], False)
        self.assertEqual(result['old_data'], START_IP_DNS_STATIC_OLD_DATA)
        self.assertEqual(result['new_data'], START_IP_DNS_STATIC_OLD_DATA)

    @patch('ansible_collections.community.routeros.plugins.modules.api_modify.compose_api_path',
           new=create_fake_path(('ip', 'dns', 'static'), START_IP_DNS_STATIC, read_only=True))
    def test_sync_list_idempotent_2(self):
        with self.assertRaises(AnsibleExitJson) as exc:
            args = self.config_module_args.copy()
            args.update({
                'path': 'ip dns static',
                'data': [
                    {
                        'comment': 'defconf',
                        'name': 'router',
                        'address': '192.168.88.1',
                    },
                    {
                        'name': 'foo',
                        'comment': '',
                        'address': '192.168.88.2',
                    },
                    {
                        'name': 'router',
                        '!comment': None,
                        'text': 'Router Text Entry',
                    },
                ],
                'handle_absent_entries': 'remove',
                'handle_entries_content': 'remove',
            })
            set_module_args(args)
            self.module.main()

        result = exc.exception.args[0]
        self.assertEqual(result['changed'], False)
        self.assertEqual(result['old_data'], START_IP_DNS_STATIC_OLD_DATA)
        self.assertEqual(result['new_data'], START_IP_DNS_STATIC_OLD_DATA)

    @patch('ansible_collections.community.routeros.plugins.modules.api_modify.compose_api_path',
           new=create_fake_path(('ip', 'dns', 'static'), START_IP_DNS_STATIC, read_only=True))
    def test_sync_list_idempotent_3(self):
        with self.assertRaises(AnsibleExitJson) as exc:
            args = self.config_module_args.copy()
            args.update({
                'path': 'ip dns static',
                'data': [
                    {
                        'comment': 'defconf',
                        'name': 'router',
                        'address': '192.168.88.1',
                    },
                ],
            })
            set_module_args(args)
            self.module.main()

        result = exc.exception.args[0]
        self.assertEqual(result['changed'], False)
        self.assertEqual(result['old_data'], START_IP_DNS_STATIC_OLD_DATA)
        self.assertEqual(result['new_data'], START_IP_DNS_STATIC_OLD_DATA)

    @patch('ansible_collections.community.routeros.plugins.modules.api_modify.compose_api_path',
           new=create_fake_path(('ip', 'dns', 'static'), START_IP_DNS_STATIC))
    def test_sync_list_add(self):
        with self.assertRaises(AnsibleExitJson) as exc:
            args = self.config_module_args.copy()
            args.update({
                'path': 'ip dns static',
                'data': [
                    {
                        'comment': 'defconf',
                        'name': 'router',
                        'address': '192.168.88.1',
                    },
                    {
                        'name': 'router',
                        'text': 'Router Text Entry',
                    },
                    {
                        'name': 'router',
                        'text': 'Router Text Entry 2',
                    },
                    {
                        'name': 'foo',
                        'address': '192.168.88.2',
                    },
                ],
            })
            set_module_args(args)
            self.module.main()

        result = exc.exception.args[0]
        self.assertEqual(result['changed'], True)
        self.assertEqual(result['old_data'], START_IP_DNS_STATIC_OLD_DATA)
        self.assertEqual(result['new_data'], [
            {
                '.id': '*1',
                'comment': 'defconf',
                'name': 'router',
                'address': '192.168.88.1',
                'ttl': '1d',
                'disabled': False,
            },
            {
                '.id': '*A',
                'name': 'router',
                'text': 'Router Text Entry',
                'ttl': '1d',
                'disabled': False,
            },
            {
                '.id': '*7',
                'name': 'foo',
                'address': '192.168.88.2',
                'ttl': '1d',
                'disabled': False,
            },
            {
                '.id': '*NEW1',
                'name': 'router',
                'text': 'Router Text Entry 2',
                'ttl': '1d',
                'disabled': False,
            },
        ])

    @patch('ansible_collections.community.routeros.plugins.modules.api_modify.compose_api_path',
           new=create_fake_path(('ip', 'dns', 'static'), START_IP_DNS_STATIC))
    def test_sync_list_modify_1(self):
        with self.assertRaises(AnsibleExitJson) as exc:
            args = self.config_module_args.copy()
            args.update({
                'path': 'ip dns static',
                'data': [
                    {
                        'comment': 'defconf',
                        'name': 'router',
                        'address': '192.168.88.1',
                    },
                    {
                        'name': 'router',
                        'text': 'Router Text Entry 2',
                    },
                    {
                        'name': 'foo',
                        'address': '192.168.88.2',
                    },
                ],
            })
            set_module_args(args)
            self.module.main()

        result = exc.exception.args[0]
        self.assertEqual(result['changed'], True)
        self.assertEqual(result['old_data'], START_IP_DNS_STATIC_OLD_DATA)
        self.assertEqual(result['new_data'], [
            {
                '.id': '*1',
                'comment': 'defconf',
                'name': 'router',
                'address': '192.168.88.1',
                'ttl': '1d',
                'disabled': False,
            },
            {
                '.id': '*A',
                'name': 'router',
                'text': 'Router Text Entry',
                'ttl': '1d',
                'disabled': False,
            },
            {
                '.id': '*7',
                'name': 'foo',
                'address': '192.168.88.2',
                'ttl': '1d',
                'disabled': False,
            },
            {
                '.id': '*NEW1',
                'name': 'router',
                'text': 'Router Text Entry 2',
                'ttl': '1d',
                'disabled': False,
            },
        ])

    @patch('ansible_collections.community.routeros.plugins.modules.api_modify.compose_api_path',
           new=create_fake_path(('ip', 'dns', 'static'), START_IP_DNS_STATIC, read_only=True))
    def test_sync_list_modify_1_check(self):
        with self.assertRaises(AnsibleExitJson) as exc:
            args = self.config_module_args.copy()
            args.update({
                'path': 'ip dns static',
                'data': [
                    {
                        'comment': 'defconf',
                        'name': 'router',
                        'address': '192.168.88.1',
                    },
                    {
                        'name': 'router',
                        'text': 'Router Text Entry 2',
                    },
                    {
                        'name': 'foo',
                        'address': '192.168.88.2',
                    },
                ],
                '_ansible_check_mode': True,
            })
            set_module_args(args)
            self.module.main()

        result = exc.exception.args[0]
        self.assertEqual(result['changed'], True)
        self.assertEqual(result['old_data'], START_IP_DNS_STATIC_OLD_DATA)
        self.assertEqual(result['new_data'], [
            {
                '.id': '*1',
                'comment': 'defconf',
                'name': 'router',
                'address': '192.168.88.1',
                'ttl': '1d',
                'disabled': False,
            },
            {
                '.id': '*A',
                'name': 'router',
                'text': 'Router Text Entry',
                'ttl': '1d',
                'disabled': False,
            },
            {
                '.id': '*7',
                'name': 'foo',
                'address': '192.168.88.2',
                'ttl': '1d',
                'disabled': False,
            },
            {
                'name': 'router',
                'text': 'Router Text Entry 2',
            },
        ])

    @patch('ansible_collections.community.routeros.plugins.modules.api_modify.compose_api_path',
           new=create_fake_path(('ip', 'dns', 'static'), START_IP_DNS_STATIC))
    def test_sync_list_modify_2(self):
        with self.assertRaises(AnsibleExitJson) as exc:
            args = self.config_module_args.copy()
            args.update({
                'path': 'ip dns static',
                'data': [
                    {
                        'comment': '',
                        'name': 'router',
                        'address': '192.168.88.1',
                    },
                    {
                        'name': 'router',
                        'text': 'Router Text Entry 2',
                    },
                    {
                        'name': 'foo',
                        'address': '192.168.88.2',
                    },
                ],
                'handle_absent_entries': 'remove',
                'handle_entries_content': 'remove',
            })
            set_module_args(args)
            self.module.main()

        result = exc.exception.args[0]
        self.assertEqual(result['changed'], True)
        self.assertEqual(result['old_data'], START_IP_DNS_STATIC_OLD_DATA)
        self.assertEqual(result['new_data'], [
            {
                '.id': '*1',
                'name': 'router',
                'address': '192.168.88.1',
                'ttl': '1d',
                'disabled': False,
            },
            {
                '.id': '*A',
                'name': 'router',
                'text': 'Router Text Entry 2',
                'ttl': '1d',
                'disabled': False,
            },
            {
                '.id': '*7',
                'name': 'foo',
                'address': '192.168.88.2',
                'ttl': '1d',
                'disabled': False,
            },
        ])

    @patch('ansible_collections.community.routeros.plugins.modules.api_modify.compose_api_path',
           new=create_fake_path(('ip', 'dns', 'static'), START_IP_DNS_STATIC, read_only=True))
    def test_sync_list_modify_2_check(self):
        with self.assertRaises(AnsibleExitJson) as exc:
            args = self.config_module_args.copy()
            args.update({
                'path': 'ip dns static',
                'data': [
                    {
                        'comment': '',
                        'name': 'router',
                        'address': '192.168.88.1',
                    },
                    {
                        'name': 'router',
                        'text': 'Router Text Entry 2',
                    },
                    {
                        'name': 'foo',
                        'address': '192.168.88.2',
                    },
                ],
                'handle_absent_entries': 'remove',
                'handle_entries_content': 'remove',
                '_ansible_check_mode': True,
            })
            set_module_args(args)
            self.module.main()

        result = exc.exception.args[0]
        self.assertEqual(result['changed'], True)
        self.assertEqual(result['old_data'], START_IP_DNS_STATIC_OLD_DATA)
        self.assertEqual(result['new_data'], [
            {
                '.id': '*1',
                'name': 'router',
                'address': '192.168.88.1',
                'ttl': '1d',
                'disabled': False,
            },
            {
                '.id': '*A',
                'name': 'router',
                'text': 'Router Text Entry 2',
                'ttl': '1d',
                'disabled': False,
            },
            {
                '.id': '*7',
                'name': 'foo',
                'address': '192.168.88.2',
                'ttl': '1d',
                'disabled': False,
            },
        ])

    @patch('ansible_collections.community.routeros.plugins.modules.api_modify.compose_api_path',
           new=create_fake_path(('ip', 'dns', 'static'), START_IP_DNS_STATIC))
    def test_sync_list_modify_3(self):
        with self.assertRaises(AnsibleExitJson) as exc:
            args = self.config_module_args.copy()
            args.update({
                'path': 'ip dns static',
                'data': [
                    {
                        '!comment': None,
                        'name': 'router',
                        'address': '192.168.88.1',
                    },
                    {
                        'name': 'router',
                        'cname': 'router.com.',
                    },
                    {
                        'name': 'foo',
                        'address': '192.168.88.2',
                        'ttl': '1d',
                    },
                ],
                'handle_absent_entries': 'remove',
                'handle_entries_content': 'remove',
            })
            set_module_args(args)
            self.module.main()

        result = exc.exception.args[0]
        self.assertEqual(result['changed'], True)
        self.assertEqual(result['old_data'], START_IP_DNS_STATIC_OLD_DATA)
        self.assertEqual(result['new_data'], [
            {
                '.id': '*1',
                'name': 'router',
                'address': '192.168.88.1',
                'ttl': '1d',
                'disabled': False,
            },
            {
                '.id': '*7',
                'name': 'foo',
                'address': '192.168.88.2',
                'ttl': '1d',
                'disabled': False,
            },
            {
                '.id': '*NEW1',
                'name': 'router',
                'cname': 'router.com.',
                'ttl': '1d',
                'disabled': False,
            },
        ])

    @patch('ansible_collections.community.routeros.plugins.modules.api_modify.compose_api_path',
           new=create_fake_path(('ip', 'dns', 'static'), START_IP_DNS_STATIC, read_only=True))
    def test_sync_list_modify_3_check(self):
        with self.assertRaises(AnsibleExitJson) as exc:
            args = self.config_module_args.copy()
            args.update({
                'path': 'ip dns static',
                'data': [
                    {
                        '!comment': None,
                        'name': 'router',
                        'address': '192.168.88.1',
                    },
                    {
                        'name': 'router',
                        'cname': 'router.com.',
                    },
                    {
                        'name': 'foo',
                        'address': '192.168.88.2',
                        'ttl': '1d',
                    },
                ],
                'handle_absent_entries': 'remove',
                'handle_entries_content': 'remove',
                '_ansible_check_mode': True,
            })
            set_module_args(args)
            self.module.main()

        result = exc.exception.args[0]
        self.assertEqual(result['changed'], True)
        self.assertEqual(result['old_data'], START_IP_DNS_STATIC_OLD_DATA)
        self.assertEqual(result['new_data'], [
            {
                '.id': '*1',
                'name': 'router',
                'address': '192.168.88.1',
                'ttl': '1d',
                'disabled': False,
            },
            {
                '.id': '*7',
                'name': 'foo',
                'address': '192.168.88.2',
                'ttl': '1d',
                'disabled': False,
            },
            {
                'name': 'router',
                'cname': 'router.com.',
            },
        ])

    @patch('ansible_collections.community.routeros.plugins.modules.api_modify.compose_api_path',
           new=create_fake_path(('ip', 'dns', 'static'), START_IP_DNS_STATIC))
    def test_sync_list_modify_4(self):
        with self.assertRaises(AnsibleExitJson) as exc:
            args = self.config_module_args.copy()
            args.update({
                'path': 'ip dns static',
                'data': [
                    {
                        'name': 'router',
                        'address': '192.168.88.1',
                    },
                    {
                        'name': 'router',
                        'comment': 'defconf',
                        'text': 'Router Text Entry 2',
                    },
                    {
                        'name': 'foo',
                        'address': '192.168.88.2',
                    },
                ],
                'handle_absent_entries': 'remove',
                'handle_entries_content': 'remove',
            })
            set_module_args(args)
            self.module.main()

        result = exc.exception.args[0]
        self.assertEqual(result['changed'], True)
        self.assertEqual(result['old_data'], START_IP_DNS_STATIC_OLD_DATA)
        self.assertEqual(result['new_data'], [
            {
                '.id': '*1',
                'name': 'router',
                'address': '192.168.88.1',
                'ttl': '1d',
                'disabled': False,
            },
            {
                '.id': '*A',
                'comment': 'defconf',
                'name': 'router',
                'text': 'Router Text Entry 2',
                'ttl': '1d',
                'disabled': False,
            },
            {
                '.id': '*7',
                'name': 'foo',
                'address': '192.168.88.2',
                'ttl': '1d',
                'disabled': False,
            },
        ])

    @patch('ansible_collections.community.routeros.plugins.modules.api_modify.compose_api_path',
           new=create_fake_path(('ip', 'dns', 'static'), START_IP_DNS_STATIC, read_only=True))
    def test_sync_list_modify_4_check(self):
        with self.assertRaises(AnsibleExitJson) as exc:
            args = self.config_module_args.copy()
            args.update({
                'path': 'ip dns static',
                'data': [
                    {
                        'name': 'router',
                        'address': '192.168.88.1',
                    },
                    {
                        'name': 'router',
                        'comment': 'defconf',
                        'text': 'Router Text Entry 2',
                    },
                    {
                        'name': 'foo',
                        'address': '192.168.88.2',
                    },
                ],
                'handle_absent_entries': 'remove',
                'handle_entries_content': 'remove',
                '_ansible_check_mode': True,
            })
            set_module_args(args)
            self.module.main()

        result = exc.exception.args[0]
        self.assertEqual(result['changed'], True)
        self.assertEqual(result['old_data'], START_IP_DNS_STATIC_OLD_DATA)
        self.assertEqual(result['new_data'], [
            {
                '.id': '*1',
                'name': 'router',
                'address': '192.168.88.1',
                'ttl': '1d',
                'disabled': False,
            },
            {
                '.id': '*A',
                'comment': 'defconf',
                'name': 'router',
                'text': 'Router Text Entry 2',
                'ttl': '1d',
                'disabled': False,
            },
            {
                '.id': '*7',
                'name': 'foo',
                'address': '192.168.88.2',
                'ttl': '1d',
                'disabled': False,
            },
        ])

    @patch('ansible_collections.community.routeros.plugins.modules.api_modify.compose_api_path',
           new=create_fake_path(('ip', 'dns', 'static'), START_IP_DNS_STATIC))
    def test_sync_list_delete(self):
        with self.assertRaises(AnsibleExitJson) as exc:
            args = self.config_module_args.copy()
            args.update({
                'path': 'ip dns static',
                'data': [
                    {
                        'comment': 'defconf',
                        'name': 'router',
                        'address': '192.168.88.1',
                    },
                ],
                'handle_absent_entries': 'remove',
                'handle_entries_content': 'remove',
            })
            set_module_args(args)
            self.module.main()

        result = exc.exception.args[0]
        self.assertEqual(result['changed'], True)
        self.assertEqual(result['old_data'], START_IP_DNS_STATIC_OLD_DATA)
        self.assertEqual(result['new_data'], [
            {
                '.id': '*1',
                'comment': 'defconf',
                'name': 'router',
                'address': '192.168.88.1',
                'ttl': '1d',
                'disabled': False,
            },
        ])

    @patch('ansible_collections.community.routeros.plugins.modules.api_modify.compose_api_path',
           new=create_fake_path(('ip', 'dns', 'static'), START_IP_DNS_STATIC, read_only=True))
    def test_sync_list_delete_check(self):
        with self.assertRaises(AnsibleExitJson) as exc:
            args = self.config_module_args.copy()
            args.update({
                'path': 'ip dns static',
                'data': [
                    {
                        'comment': 'defconf',
                        'name': 'router',
                        'address': '192.168.88.1',
                    },
                ],
                'handle_absent_entries': 'remove',
                'handle_entries_content': 'remove',
                '_ansible_check_mode': True,
            })
            set_module_args(args)
            self.module.main()

        result = exc.exception.args[0]
        self.assertEqual(result['changed'], True)
        self.assertEqual(result['old_data'], START_IP_DNS_STATIC_OLD_DATA)
        self.assertEqual(result['new_data'], [
            {
                '.id': '*1',
                'comment': 'defconf',
                'name': 'router',
                'address': '192.168.88.1',
                'ttl': '1d',
                'disabled': False,
            },
        ])

    @patch('ansible_collections.community.routeros.plugins.modules.api_modify.compose_api_path',
           new=create_fake_path(('ip', 'dns', 'static'), START_IP_DNS_STATIC))
    def test_sync_list_reorder(self):
        with self.assertRaises(AnsibleExitJson) as exc:
            args = self.config_module_args.copy()
            args.update({
                'path': 'ip dns static',
                'data': [
                    {
                        'name': 'foo',
                        'address': '192.168.88.2',
                    },
                    {
                        'name': 'foo',
                        'text': 'bar',
                    },
                    {
                        'name': 'router',
                        'text': 'Router Text Entry',
                    },
                    {
                        'comment': 'defconf',
                        'name': 'router',
                        'address': '192.168.88.1',
                    },
                ],
                'handle_absent_entries': 'remove',
                'handle_entries_content': 'remove',
                'ensure_order': True,
            })
            set_module_args(args)
            self.module.main()

        result = exc.exception.args[0]
        self.assertEqual(result['changed'], True)
        self.assertEqual(result['old_data'], START_IP_DNS_STATIC_OLD_DATA)
        self.assertEqual(result['new_data'], [
            {
                '.id': '*7',
                'name': 'foo',
                'address': '192.168.88.2',
                'ttl': '1d',
                'disabled': False,
            },
            {
                '.id': '*NEW1',
                'name': 'foo',
                'text': 'bar',
                'ttl': '1d',
                'disabled': False,
            },
            {
                '.id': '*A',
                'name': 'router',
                'text': 'Router Text Entry',
                'ttl': '1d',
                'disabled': False,
            },
            {
                '.id': '*1',
                'comment': 'defconf',
                'name': 'router',
                'address': '192.168.88.1',
                'ttl': '1d',
                'disabled': False,
            },
        ])

    @patch('ansible_collections.community.routeros.plugins.modules.api_modify.compose_api_path',
           new=create_fake_path(('ip', 'dns', 'static'), START_IP_DNS_STATIC, read_only=True))
    def test_sync_list_reorder_check(self):
        with self.assertRaises(AnsibleExitJson) as exc:
            args = self.config_module_args.copy()
            args.update({
                'path': 'ip dns static',
                'data': [
                    {
                        'name': 'foo',
                        'address': '192.168.88.2',
                    },
                    {
                        'name': 'foo',
                        'text': 'bar',
                    },
                    {
                        'name': 'router',
                        'text': 'Router Text Entry',
                    },
                    {
                        'comment': 'defconf',
                        'name': 'router',
                        'address': '192.168.88.1',
                    },
                ],
                'handle_absent_entries': 'remove',
                'handle_entries_content': 'remove',
                'ensure_order': True,
                '_ansible_check_mode': True,
            })
            set_module_args(args)
            self.module.main()

        result = exc.exception.args[0]
        self.assertEqual(result['changed'], True)
        self.assertEqual(result['old_data'], START_IP_DNS_STATIC_OLD_DATA)
        self.assertEqual(result['new_data'], [
            {
                '.id': '*7',
                'name': 'foo',
                'address': '192.168.88.2',
                'ttl': '1d',
                'disabled': False,
            },
            {
                'name': 'foo',
                'text': 'bar',
            },
            {
                '.id': '*A',
                'name': 'router',
                'text': 'Router Text Entry',
                'ttl': '1d',
                'disabled': False,
            },
            {
                '.id': '*1',
                'comment': 'defconf',
                'name': 'router',
                'address': '192.168.88.1',
                'ttl': '1d',
                'disabled': False,
            },
        ])

    @patch('ansible_collections.community.routeros.plugins.modules.api_modify.compose_api_path',
           new=create_fake_path(('ip', 'settings'), START_IP_SETTINGS, read_only=True))
    def test_sync_value_idempotent(self):
        with self.assertRaises(AnsibleExitJson) as exc:
            args = self.config_module_args.copy()
            args.update({
                'path': 'ip settings',
                'data': [
                    {
                        'arp-timeout': '30s',
                        'icmp-rate-limit': 20,
                        'icmp-rate-mask': '0x1818',
                        'ip-forward': True,
                        'max-neighbor-entries': 8192,
                    },
                ],
            })
            set_module_args(args)
            self.module.main()

        result = exc.exception.args[0]
        self.assertEqual(result['changed'], False)
        self.assertEqual(result['old_data'], START_IP_SETTINGS_OLD_DATA)
        self.assertEqual(result['new_data'], START_IP_SETTINGS_OLD_DATA)

    @patch('ansible_collections.community.routeros.plugins.modules.api_modify.compose_api_path',
           new=create_fake_path(('ip', 'settings'), START_IP_SETTINGS, read_only=True))
    def test_sync_value_idempotent_2(self):
        with self.assertRaises(AnsibleExitJson) as exc:
            args = self.config_module_args.copy()
            args.update({
                'path': 'ip settings',
                'data': [
                    {
                        'accept-redirects': True,
                        'icmp-rate-limit': 20,
                    },
                ],
                'handle_entries_content': 'remove',
            })
            set_module_args(args)
            self.module.main()

        result = exc.exception.args[0]
        self.assertEqual(result['changed'], False)
        self.assertEqual(result['old_data'], START_IP_SETTINGS_OLD_DATA)
        self.assertEqual(result['new_data'], START_IP_SETTINGS_OLD_DATA)

    @patch('ansible_collections.community.routeros.plugins.modules.api_modify.compose_api_path',
           new=create_fake_path(('ip', 'settings'), START_IP_SETTINGS))
    def test_sync_value_modify(self):
        with self.assertRaises(AnsibleExitJson) as exc:
            args = self.config_module_args.copy()
            args.update({
                'path': 'ip settings',
                'data': [
                    {
                        'accept-redirects': True,
                        'accept-source-route': True,
                        'max-neighbor-entries': 4096,
                    },
                ],
            })
            set_module_args(args)
            self.module.main()

        result = exc.exception.args[0]
        self.assertEqual(result['changed'], True)
        self.assertEqual(result['old_data'], START_IP_SETTINGS_OLD_DATA)
        self.assertEqual(result['new_data'], [
            {
                'accept-redirects': True,
                'accept-source-route': True,
                'allow-fast-path': True,
                'arp-timeout': '30s',
                'icmp-rate-limit': 20,
                'icmp-rate-mask': '0x1818',
                'ip-forward': True,
                'max-neighbor-entries': 4096,
                'route-cache': True,
                'rp-filter': False,
                'secure-redirects': True,
                'send-redirects': True,
                'tcp-syncookies': False,
            },
        ])

    @patch('ansible_collections.community.routeros.plugins.modules.api_modify.compose_api_path',
           new=create_fake_path(('ip', 'settings'), START_IP_SETTINGS, read_only=True))
    def test_sync_value_modify_check(self):
        with self.assertRaises(AnsibleExitJson) as exc:
            args = self.config_module_args.copy()
            args.update({
                'path': 'ip settings',
                'data': [
                    {
                        'accept-redirects': True,
                        'accept-source-route': True,
                        'max-neighbor-entries': 4096,
                    },
                ],
                '_ansible_check_mode': True,
            })
            set_module_args(args)
            self.module.main()

        result = exc.exception.args[0]
        self.assertEqual(result['changed'], True)
        self.assertEqual(result['old_data'], START_IP_SETTINGS_OLD_DATA)
        self.assertEqual(result['new_data'], [
            {
                'accept-redirects': True,
                'accept-source-route': True,
                'allow-fast-path': True,
                'arp-timeout': '30s',
                'icmp-rate-limit': 20,
                'icmp-rate-mask': '0x1818',
                'ip-forward': True,
                'max-neighbor-entries': 4096,
                'route-cache': True,
                'rp-filter': False,
                'secure-redirects': True,
                'send-redirects': True,
                'tcp-syncookies': False,
            },
        ])

    @patch('ansible_collections.community.routeros.plugins.modules.api_modify.compose_api_path',
           new=create_fake_path(('ip', 'settings'), START_IP_SETTINGS))
    def test_sync_value_modify_2(self):
        with self.assertRaises(AnsibleExitJson) as exc:
            args = self.config_module_args.copy()
            args.update({
                'path': 'ip settings',
                'data': [
                    {
                        'accept-redirects': True,
                        'accept-source-route': True,
                        'max-neighbor-entries': 4096,
                    },
                ],
                'handle_entries_content': 'remove',
            })
            set_module_args(args)
            self.module.main()

        result = exc.exception.args[0]
        self.assertEqual(result['changed'], True)
        self.assertEqual(result['old_data'], START_IP_SETTINGS_OLD_DATA)
        self.assertEqual(result['new_data'], [
            {
                'accept-redirects': True,
                'accept-source-route': True,
                'allow-fast-path': True,
                'arp-timeout': '30s',
                'icmp-rate-limit': 10,
                'icmp-rate-mask': '0x1818',
                'ip-forward': True,
                'max-neighbor-entries': 4096,
                'route-cache': True,
                'rp-filter': False,
                'secure-redirects': True,
                'send-redirects': True,
                'tcp-syncookies': False,
            },
        ])

    @patch('ansible_collections.community.routeros.plugins.modules.api_modify.compose_api_path',
           new=create_fake_path(('ip', 'settings'), START_IP_SETTINGS, read_only=True))
    def test_sync_value_modify_2_check(self):
        with self.assertRaises(AnsibleExitJson) as exc:
            args = self.config_module_args.copy()
            args.update({
                'path': 'ip settings',
                'data': [
                    {
                        'accept-redirects': True,
                        'accept-source-route': True,
                        'max-neighbor-entries': 4096,
                    },
                ],
                'handle_entries_content': 'remove',
                '_ansible_check_mode': True,
            })
            set_module_args(args)
            self.module.main()

        result = exc.exception.args[0]
        self.assertEqual(result['changed'], True)
        self.assertEqual(result['old_data'], START_IP_SETTINGS_OLD_DATA)
        self.assertEqual(result['new_data'], [
            {
                'accept-redirects': True,
                'accept-source-route': True,
                'allow-fast-path': True,
                'arp-timeout': '30s',
                'icmp-rate-limit': 10,
                'icmp-rate-mask': '0x1818',
                'ip-forward': True,
                'max-neighbor-entries': 4096,
                'route-cache': True,
                'rp-filter': False,
                'secure-redirects': True,
                'send-redirects': True,
                'tcp-syncookies': False,
            },
        ])

    @patch('ansible_collections.community.routeros.plugins.modules.api_modify.compose_api_path',
           new=create_fake_path(('ip', 'address'), START_IP_ADDRESS, read_only=True))
    def test_sync_primary_key_idempotent(self):
        with self.assertRaises(AnsibleExitJson) as exc:
            args = self.config_module_args.copy()
            args.update({
                'path': 'ip address',
                'data': [
                    {
                        'address': '192.168.1.0/24',
                        'interface': 'LAN',
                        'comment': '',
                    },
                    {
                        'address': '192.168.88.0/24',
                        'interface': 'bridge',
                        '!comment': None,
                    },
                ],
            })
            set_module_args(args)
            self.module.main()

        result = exc.exception.args[0]
        self.assertEqual(result['changed'], False)
        self.assertEqual(result['old_data'], START_IP_ADDRESS_OLD_DATA)
        self.assertEqual(result['new_data'], START_IP_ADDRESS_OLD_DATA)

    @patch('ansible_collections.community.routeros.plugins.modules.api_modify.compose_api_path',
           new=create_fake_path(('ip', 'address'), START_IP_ADDRESS, read_only=True))
    def test_sync_primary_key_idempotent_2(self):
        with self.assertRaises(AnsibleExitJson) as exc:
            args = self.config_module_args.copy()
            args.update({
                'path': 'ip address',
                'data': [
                    {
                        'address': '192.168.88.0/24',
                        'interface': 'bridge',
                    },
                    {
                        'address': '10.0.0.0/16',
                        'interface': 'WAN',
                        'disabled': True,
                        '!comment': '',
                    },
                    {
                        'address': '192.168.1.0/24',
                        'interface': 'LAN',
                        'disabled': False,
                        'comment': None,
                    },
                ],
                'handle_absent_entries': 'remove',
                'handle_entries_content': 'remove',
            })
            set_module_args(args)
            self.module.main()

        result = exc.exception.args[0]
        self.assertEqual(result['changed'], False)
        self.assertEqual(result['old_data'], START_IP_ADDRESS_OLD_DATA)
        self.assertEqual(result['new_data'], START_IP_ADDRESS_OLD_DATA)

    @patch('ansible_collections.community.routeros.plugins.modules.api_modify.compose_api_path',
           new=create_fake_path(('ip', 'address'), START_IP_ADDRESS))
    def test_sync_primary_key_cru(self):
        with self.assertRaises(AnsibleExitJson) as exc:
            args = self.config_module_args.copy()
            args.update({
                'path': 'ip address',
                'data': [
                    {
                        'address': '10.10.0.0/16',
                        'interface': 'WIFI',
                    },
                    {
                        'address': '192.168.1.0/24',
                        'interface': 'LAN',
                        'disabled': True,
                    },
                    {
                        'address': '192.168.88.0/24',
                        'interface': 'bridge',
                        'comment': 'foo',
                    },
                ],
                'handle_absent_entries': 'remove',
                'handle_entries_content': 'remove',
            })
            set_module_args(args)
            self.module.main()

        result = exc.exception.args[0]
        self.assertEqual(result['changed'], True)
        self.assertEqual(result['old_data'], START_IP_ADDRESS_OLD_DATA)
        self.assertEqual(result['new_data'], [
            {
                '.id': '*1',
                'comment': 'foo',
                'address': '192.168.88.0/24',
                'interface': 'bridge',
                'disabled': False,
            },
            {
                '.id': '*3',
                'address': '192.168.1.0/24',
                'interface': 'LAN',
                'disabled': True,
            },
            {
                '.id': '*NEW1',
                'address': '10.10.0.0/16',
                'interface': 'WIFI',
                'disabled': False,
            },
        ])

    @patch('ansible_collections.community.routeros.plugins.modules.api_modify.compose_api_path',
           new=create_fake_path(('ip', 'address'), START_IP_ADDRESS, read_only=True))
    def test_sync_primary_key_cru_check(self):
        with self.assertRaises(AnsibleExitJson) as exc:
            args = self.config_module_args.copy()
            args.update({
                'path': 'ip address',
                'data': [
                    {
                        'address': '10.10.0.0/16',
                        'interface': 'WIFI',
                    },
                    {
                        'address': '192.168.1.0/24',
                        'interface': 'LAN',
                        'disabled': True,
                    },
                    {
                        'address': '192.168.88.0/24',
                        'interface': 'bridge',
                        'comment': 'foo',
                    },
                ],
                'handle_absent_entries': 'remove',
                'handle_entries_content': 'remove',
                '_ansible_check_mode': True,
            })
            set_module_args(args)
            self.module.main()

        result = exc.exception.args[0]
        self.assertEqual(result['changed'], True)
        self.assertEqual(result['old_data'], START_IP_ADDRESS_OLD_DATA)
        self.assertEqual(result['new_data'], [
            {
                '.id': '*1',
                'comment': 'foo',
                'address': '192.168.88.0/24',
                'interface': 'bridge',
                'disabled': False,
            },
            {
                '.id': '*3',
                'address': '192.168.1.0/24',
                'interface': 'LAN',
                'disabled': True,
            },
            {
                'address': '10.10.0.0/16',
                'interface': 'WIFI',
            },
        ])

    @patch('ansible_collections.community.routeros.plugins.modules.api_modify.compose_api_path',
           new=create_fake_path(('ip', 'address'), START_IP_ADDRESS))
    def test_sync_primary_key_cru_reorder(self):
        with self.assertRaises(AnsibleExitJson) as exc:
            args = self.config_module_args.copy()
            args.update({
                'path': 'ip address',
                'data': [
                    {
                        'address': '10.10.0.0/16',
                        'interface': 'WIFI',
                    },
                    {
                        'address': '192.168.1.0/24',
                        'interface': 'LAN',
                        'disabled': True,
                    },
                    {
                        'address': '192.168.88.0/24',
                        'interface': 'bridge',
                        'comment': 'foo',
                    },
                ],
                'handle_absent_entries': 'remove',
                'handle_entries_content': 'remove',
                'ensure_order': True,
            })
            set_module_args(args)
            self.module.main()

        result = exc.exception.args[0]
        self.assertEqual(result['changed'], True)
        self.assertEqual(result['old_data'], START_IP_ADDRESS_OLD_DATA)
        self.assertEqual(result['new_data'], [
            {
                '.id': '*NEW1',
                'address': '10.10.0.0/16',
                'interface': 'WIFI',
                'disabled': False,
            },
            {
                '.id': '*3',
                'address': '192.168.1.0/24',
                'interface': 'LAN',
                'disabled': True,
            },
            {
                '.id': '*1',
                'comment': 'foo',
                'address': '192.168.88.0/24',
                'interface': 'bridge',
                'disabled': False,
            },
        ])

    @patch('ansible_collections.community.routeros.plugins.modules.api_modify.compose_api_path',
           new=create_fake_path(('ip', 'address'), START_IP_ADDRESS, read_only=True))
    def test_sync_primary_key_cru_reorder_check(self):
        with self.assertRaises(AnsibleExitJson) as exc:
            args = self.config_module_args.copy()
            args.update({
                'path': 'ip address',
                'data': [
                    {
                        'address': '10.10.0.0/16',
                        'interface': 'WIFI',
                    },
                    {
                        'address': '192.168.1.0/24',
                        'interface': 'LAN',
                        'disabled': True,
                    },
                    {
                        'address': '192.168.88.0/24',
                        'interface': 'bridge',
                        'comment': 'foo',
                    },
                ],
                'handle_absent_entries': 'remove',
                'handle_entries_content': 'remove',
                'ensure_order': True,
                '_ansible_check_mode': True,
            })
            set_module_args(args)
            self.module.main()

        result = exc.exception.args[0]
        self.assertEqual(result['changed'], True)
        self.assertEqual(result['old_data'], START_IP_ADDRESS_OLD_DATA)
        self.assertEqual(result['new_data'], [
            {
                'address': '10.10.0.0/16',
                'interface': 'WIFI',
            },
            {
                '.id': '*3',
                'address': '192.168.1.0/24',
                'interface': 'LAN',
                'disabled': True,
            },
            {
                '.id': '*1',
                'comment': 'foo',
                'address': '192.168.88.0/24',
                'interface': 'bridge',
                'disabled': False,
            },
        ])
