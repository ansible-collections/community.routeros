# Copyright (c) Ansible Project
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

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
from ansible_collections.community.routeros.plugins.modules import api_find_and_modify


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
]

START_IP_DNS_STATIC_OLD_DATA = massage_expected_result_data(START_IP_DNS_STATIC, ('ip', 'dns', 'static'), keep_all=True)

START_IP_FIREWALL_FILTER = [
    {
        '.id': '*2',
        'action': 'accept',
        'chain': 'input',
        'comment': 'defconf',
        'protocol': 'icmp',
    },
    {
        '.id': '*3',
        'action': 'accept',
        'chain': 'input',
        'comment': 'defconf',
        'connection-state': 'established',
    },
    {
        '.id': '*4',
        'action': 'accept',
        'chain': 'input',
        'comment': 'defconf',
        'connection-state': 'related',
    },
    {
        '.id': '*7',
        'action': 'drop',
        'chain': 'input',
        'comment': 'defconf',
        'in-interface': 'wan',
    },
    {
        '.id': '*8',
        'action': 'accept',
        'chain': 'forward',
        'comment': 'defconf',
        'connection-state': 'established',
    },
    {
        '.id': '*9',
        'action': 'accept',
        'chain': 'forward',
        'comment': 'defconf',
        'connection-state': 'related',
    },
    {
        '.id': '*A',
        'action': 'drop',
        'chain': 'forward',
        'comment': 'defconf',
        'connection-status': 'invalid',
    },
]

START_IP_FIREWALL_FILTER_OLD_DATA = massage_expected_result_data(START_IP_FIREWALL_FILTER, ('ip', 'firewall', 'filter'), keep_all=True)


class TestRouterosApiFindAndModifyModule(ModuleTestCase):

    def setUp(self):
        super(TestRouterosApiFindAndModifyModule, self).setUp()
        self.module = api_find_and_modify
        self.module.LibRouterosError = FakeLibRouterosError
        self.module.connect = MagicMock(new=fake_ros_api)
        self.module.check_has_library = MagicMock()
        self.patch_create_api = patch(
            'ansible_collections.community.routeros.plugins.modules.api_find_and_modify.create_api',
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

    def test_invalid_disabled_and_enabled_option_in_find(self):
        with self.assertRaises(AnsibleFailJson) as exc:
            args = self.config_module_args.copy()
            args.update({
                'path': 'ip dns static',
                'find': {
                    'comment': 'foo',
                    '!comment': None,
                },
                'values': {
                    'comment': 'bar',
                },
            })
            set_module_args(args)
            self.module.main()

        result = exc.exception.args[0]
        self.assertEqual(result['failed'], True)
        self.assertEqual(result['msg'], '`find` must not contain both "comment" and "!comment"!')

    def test_invalid_disabled_option_invalid_value_in_find(self):
        with self.assertRaises(AnsibleFailJson) as exc:
            args = self.config_module_args.copy()
            args.update({
                'path': 'ip dns static',
                'find': {
                    '!comment': 'gone',
                },
                'values': {
                    'comment': 'bar',
                },
            })
            set_module_args(args)
            self.module.main()

        result = exc.exception.args[0]
        self.assertEqual(result['failed'], True)
        self.assertEqual(result['msg'], 'The value for "!comment" in `find` must not be non-trivial!')

    def test_invalid_disabled_and_enabled_option_in_values(self):
        with self.assertRaises(AnsibleFailJson) as exc:
            args = self.config_module_args.copy()
            args.update({
                'path': 'ip dns static',
                'find': {},
                'values': {
                    'comment': 'foo',
                    '!comment': None,
                },
            })
            set_module_args(args)
            self.module.main()

        result = exc.exception.args[0]
        self.assertEqual(result['failed'], True)
        self.assertEqual(result['msg'], '`values` must not contain both "comment" and "!comment"!')

    def test_invalid_disabled_option_invalid_value_in_values(self):
        with self.assertRaises(AnsibleFailJson) as exc:
            args = self.config_module_args.copy()
            args.update({
                'path': 'ip dns static',
                'find': {},
                'values': {
                    '!comment': 'gone',
                },
            })
            set_module_args(args)
            self.module.main()

        result = exc.exception.args[0]
        self.assertEqual(result['failed'], True)
        self.assertEqual(result['msg'], 'The value for "!comment" in `values` must not be non-trivial!')

    @patch('ansible_collections.community.routeros.plugins.modules.api_find_and_modify.compose_api_path',
           new=create_fake_path(('ip', 'dns', 'static'), START_IP_DNS_STATIC, read_only=True))
    def test_change_invalid_zero(self):
        with self.assertRaises(AnsibleFailJson) as exc:
            args = self.config_module_args.copy()
            args.update({
                'path': 'ip dns static',
                'find': {
                    'name': 'bam',
                },
                'values': {
                    'name': 'baz',
                },
                'require_matches_min': 10,
            })
            set_module_args(args)
            self.module.main()

        result = exc.exception.args[0]
        self.assertEqual(result['failed'], True)
        self.assertEqual(result['msg'], 'Found no entries, but allow_no_matches=false')

    @patch('ansible_collections.community.routeros.plugins.modules.api_find_and_modify.compose_api_path',
           new=create_fake_path(('ip', 'dns', 'static'), START_IP_DNS_STATIC, read_only=True))
    def test_change_invalid_too_few(self):
        with self.assertRaises(AnsibleFailJson) as exc:
            args = self.config_module_args.copy()
            args.update({
                'path': 'ip dns static',
                'find': {
                    'name': 'router',
                },
                'values': {
                    'name': 'foobar',
                },
                'require_matches_min': 10,
            })
            set_module_args(args)
            self.module.main()

        result = exc.exception.args[0]
        self.assertEqual(result['failed'], True)
        self.assertEqual(result['msg'], 'Found 2 entries, but expected at least 10')

    @patch('ansible_collections.community.routeros.plugins.modules.api_find_and_modify.compose_api_path',
           new=create_fake_path(('ip', 'dns', 'static'), START_IP_DNS_STATIC, read_only=True))
    def test_change_invalid_too_many(self):
        with self.assertRaises(AnsibleFailJson) as exc:
            args = self.config_module_args.copy()
            args.update({
                'path': 'ip dns static',
                'find': {
                    'name': 'router',
                },
                'values': {
                    'name': 'foobar',
                },
                'require_matches_max': 1,
            })
            set_module_args(args)
            self.module.main()

        result = exc.exception.args[0]
        self.assertEqual(result['failed'], True)
        self.assertEqual(result['msg'], 'Found 2 entries, but expected at most 1')

    @patch('ansible_collections.community.routeros.plugins.modules.api_find_and_modify.compose_api_path',
           new=create_fake_path(('ip', 'dns', 'static'), START_IP_DNS_STATIC, read_only=True))
    def test_change_idempotent_zero_matches_1(self):
        with self.assertRaises(AnsibleExitJson) as exc:
            args = self.config_module_args.copy()
            args.update({
                'path': 'ip dns static',
                'find': {
                    'name': 'baz',
                },
                'values': {
                    'name': 'bam',
                },
            })
            set_module_args(args)
            self.module.main()

        result = exc.exception.args[0]
        self.assertEqual(result['changed'], False)
        self.assertEqual(result['old_data'], START_IP_DNS_STATIC_OLD_DATA)
        self.assertEqual(result['new_data'], START_IP_DNS_STATIC_OLD_DATA)
        self.assertEqual(result['match_count'], 0)
        self.assertEqual(result['modify_count'], 0)

    @patch('ansible_collections.community.routeros.plugins.modules.api_find_and_modify.compose_api_path',
           new=create_fake_path(('ip', 'dns', 'static'), START_IP_DNS_STATIC, read_only=True))
    def test_change_idempotent_zero_matches_2(self):
        with self.assertRaises(AnsibleExitJson) as exc:
            args = self.config_module_args.copy()
            args.update({
                'path': 'ip dns static',
                'find': {
                    'name': 'baz',
                },
                'values': {
                    'name': 'bam',
                },
                'require_matches_min': 2,
                'allow_no_matches': True,
            })
            set_module_args(args)
            self.module.main()

        result = exc.exception.args[0]
        self.assertEqual(result['changed'], False)
        self.assertEqual(result['old_data'], START_IP_DNS_STATIC_OLD_DATA)
        self.assertEqual(result['new_data'], START_IP_DNS_STATIC_OLD_DATA)
        self.assertEqual(result['match_count'], 0)
        self.assertEqual(result['modify_count'], 0)

    @patch('ansible_collections.community.routeros.plugins.modules.api_find_and_modify.compose_api_path',
           new=create_fake_path(('ip', 'dns', 'static'), START_IP_DNS_STATIC, read_only=True))
    def test_idempotent_1(self):
        with self.assertRaises(AnsibleExitJson) as exc:
            args = self.config_module_args.copy()
            args.update({
                'path': 'ip dns static',
                'find': {
                },
                'values': {
                },
            })
            set_module_args(args)
            self.module.main()

        result = exc.exception.args[0]
        self.assertEqual(result['changed'], False)
        self.assertEqual(result['old_data'], START_IP_DNS_STATIC_OLD_DATA)
        self.assertEqual(result['new_data'], START_IP_DNS_STATIC_OLD_DATA)
        self.assertEqual(result['match_count'], 3)
        self.assertEqual(result['modify_count'], 0)

    @patch('ansible_collections.community.routeros.plugins.modules.api_find_and_modify.compose_api_path',
           new=create_fake_path(('ip', 'dns', 'static'), START_IP_DNS_STATIC, read_only=True))
    def test_idempotent_2(self):
        with self.assertRaises(AnsibleExitJson) as exc:
            args = self.config_module_args.copy()
            args.update({
                'path': 'ip dns static',
                'find': {
                    'name': 'foo',
                },
                'values': {
                    'comment': None,
                },
            })
            set_module_args(args)
            self.module.main()

        result = exc.exception.args[0]
        self.assertEqual(result['changed'], False)
        self.assertEqual(result['old_data'], START_IP_DNS_STATIC_OLD_DATA)
        self.assertEqual(result['new_data'], START_IP_DNS_STATIC_OLD_DATA)
        self.assertEqual(result['match_count'], 1)
        self.assertEqual(result['modify_count'], 0)

    @patch('ansible_collections.community.routeros.plugins.modules.api_find_and_modify.compose_api_path',
           new=create_fake_path(('ip', 'dns', 'static'), START_IP_DNS_STATIC))
    def test_change(self):
        with self.assertRaises(AnsibleExitJson) as exc:
            args = self.config_module_args.copy()
            args.update({
                'path': 'ip dns static',
                'find': {
                    'name': 'foo',
                },
                'values': {
                    'comment': 'bar',
                },
                '_ansible_diff': True,
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
                'dynamic': False,
            },
            {
                '.id': '*A',
                'name': 'router',
                'text': 'Router Text Entry',
                'ttl': '1d',
                'disabled': False,
                'dynamic': False,
            },
            {
                '.id': '*7',
                'comment': 'bar',
                'name': 'foo',
                'address': '192.168.88.2',
                'ttl': '1d',
                'disabled': False,
                'dynamic': False,
            },
        ])
        self.assertEqual(result['diff']['before']['values'], [
            {
                '.id': '*7',
                'name': 'foo',
                'address': '192.168.88.2',
                'ttl': '1d',
                'disabled': False,
                'dynamic': False,
            },
        ])
        self.assertEqual(result['diff']['after']['values'], [
            {
                '.id': '*7',
                'comment': 'bar',
                'name': 'foo',
                'address': '192.168.88.2',
                'ttl': '1d',
                'disabled': False,
                'dynamic': False,
            },
        ])
        self.assertEqual(result['match_count'], 1)
        self.assertEqual(result['modify_count'], 1)

    @patch('ansible_collections.community.routeros.plugins.modules.api_find_and_modify.compose_api_path',
           new=create_fake_path(('ip', 'dns', 'static'), START_IP_DNS_STATIC))
    def test_change_remove_comment_1(self):
        with self.assertRaises(AnsibleExitJson) as exc:
            args = self.config_module_args.copy()
            args.update({
                'path': 'ip dns static',
                'find': {
                },
                'values': {
                    'comment': None,
                },
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
                'dynamic': False,
            },
            {
                '.id': '*A',
                'name': 'router',
                'text': 'Router Text Entry',
                'ttl': '1d',
                'disabled': False,
                'dynamic': False,
            },
            {
                '.id': '*7',
                'name': 'foo',
                'address': '192.168.88.2',
                'ttl': '1d',
                'disabled': False,
                'dynamic': False,
            },
        ])
        self.assertEqual('diff' in result, False)
        self.assertEqual(result['match_count'], 3)
        self.assertEqual(result['modify_count'], 1)

    @patch('ansible_collections.community.routeros.plugins.modules.api_find_and_modify.compose_api_path',
           new=create_fake_path(('ip', 'dns', 'static'), START_IP_DNS_STATIC))
    def test_change_remove_comment_2(self):
        with self.assertRaises(AnsibleExitJson) as exc:
            args = self.config_module_args.copy()
            args.update({
                'path': 'ip dns static',
                'find': {
                },
                'values': {
                    'comment': '',
                },
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
                'dynamic': False,
            },
            {
                '.id': '*A',
                'name': 'router',
                'text': 'Router Text Entry',
                'ttl': '1d',
                'disabled': False,
                'dynamic': False,
            },
            {
                '.id': '*7',
                'name': 'foo',
                'address': '192.168.88.2',
                'ttl': '1d',
                'disabled': False,
                'dynamic': False,
            },
        ])
        self.assertEqual(result['match_count'], 3)
        self.assertEqual(result['modify_count'], 1)

    @patch('ansible_collections.community.routeros.plugins.modules.api_find_and_modify.compose_api_path',
           new=create_fake_path(('ip', 'dns', 'static'), START_IP_DNS_STATIC))
    def test_change_remove_comment_3(self):
        with self.assertRaises(AnsibleExitJson) as exc:
            args = self.config_module_args.copy()
            args.update({
                'path': 'ip dns static',
                'find': {
                },
                'values': {
                    '!comment': None,
                },
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
                'dynamic': False,
            },
            {
                '.id': '*A',
                'name': 'router',
                'text': 'Router Text Entry',
                'ttl': '1d',
                'disabled': False,
                'dynamic': False,
            },
            {
                '.id': '*7',
                'name': 'foo',
                'address': '192.168.88.2',
                'ttl': '1d',
                'disabled': False,
                'dynamic': False,
            },
        ])
        self.assertEqual(result['match_count'], 3)
        self.assertEqual(result['modify_count'], 1)

    @patch('ansible_collections.community.routeros.plugins.modules.api_find_and_modify.compose_api_path',
           new=create_fake_path(('ip', 'firewall', 'filter'), START_IP_FIREWALL_FILTER))
    def test_change_remove_generic(self):
        with self.assertRaises(AnsibleExitJson) as exc:
            args = self.config_module_args.copy()
            args.update({
                'path': 'ip firewall filter',
                'find': {
                    'chain': 'input',
                    '!protocol': '',
                },
                'values': {
                    '!connection-state': None,
                },
            })
            set_module_args(args)
            self.module.main()

        result = exc.exception.args[0]
        self.assertEqual(result['changed'], True)
        self.assertEqual(result['old_data'], START_IP_FIREWALL_FILTER_OLD_DATA)
        self.assertEqual(result['new_data'], [
            {
                '.id': '*2',
                'action': 'accept',
                'chain': 'input',
                'comment': 'defconf',
                'protocol': 'icmp',
            },
            {
                '.id': '*3',
                'action': 'accept',
                'chain': 'input',
                'comment': 'defconf',
            },
            {
                '.id': '*4',
                'action': 'accept',
                'chain': 'input',
                'comment': 'defconf',
            },
            {
                '.id': '*7',
                'action': 'drop',
                'chain': 'input',
                'comment': 'defconf',
                'in-interface': 'wan',
            },
            {
                '.id': '*8',
                'action': 'accept',
                'chain': 'forward',
                'comment': 'defconf',
                'connection-state': 'established',
            },
            {
                '.id': '*9',
                'action': 'accept',
                'chain': 'forward',
                'comment': 'defconf',
                'connection-state': 'related',
            },
            {
                '.id': '*A',
                'action': 'drop',
                'chain': 'forward',
                'comment': 'defconf',
                'connection-status': 'invalid',
            },
        ])
        self.assertEqual(result['match_count'], 3)
        self.assertEqual(result['modify_count'], 2)
