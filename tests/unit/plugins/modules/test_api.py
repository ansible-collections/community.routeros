# Copyright (c) Ansible Project
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import json
import pytest

from ansible_collections.community.routeros.tests.unit.compat.mock import patch, MagicMock
from ansible_collections.community.routeros.tests.unit.plugins.modules.fake_api import FakeLibRouterosError, Key, Or, fake_ros_api
from ansible_collections.community.routeros.tests.unit.plugins.modules.utils import set_module_args, AnsibleExitJson, AnsibleFailJson, ModuleTestCase
from ansible_collections.community.routeros.plugins.modules import api


class TestRouterosApiModule(ModuleTestCase):

    def setUp(self):
        super(TestRouterosApiModule, self).setUp()
        self.module = api
        self.module.LibRouterosError = FakeLibRouterosError
        self.module.connect = MagicMock(new=fake_ros_api)
        self.module.check_has_library = MagicMock()
        self.patch_create_api = patch('ansible_collections.community.routeros.plugins.modules.api.create_api', MagicMock(new=fake_ros_api))
        self.patch_create_api.start()
        self.module.Key = MagicMock(new=Key)
        self.module.Or = MagicMock(new=Or)
        self.config_module_args = {"username": "admin",
                                   "password": "pаss",
                                   "hostname": "127.0.0.1",
                                   "path": "interface bridge"}

    def tearDown(self):
        self.patch_create_api.stop()

    def test_module_fail_when_required_args_missing(self):
        with self.assertRaises(AnsibleFailJson) as exc:
            set_module_args({})
            self.module.main()

        result = exc.exception.args[0]
        self.assertEqual(result['failed'], True)

    @patch('ansible_collections.community.routeros.plugins.modules.api.ROS_api_module.api_add_path', new=fake_ros_api.path)
    def test_api_path(self):
        with self.assertRaises(AnsibleExitJson) as exc:
            set_module_args(self.config_module_args.copy())
            self.module.main()

        result = exc.exception.args[0]
        self.assertEqual(result['changed'], False)

    @patch('ansible_collections.community.routeros.plugins.modules.api.ROS_api_module.api_add_path', new=fake_ros_api)
    def test_api_add(self):
        with self.assertRaises(AnsibleExitJson) as exc:
            module_args = self.config_module_args.copy()
            module_args['add'] = "name=unit_test_brige"
            set_module_args(module_args)
            self.module.main()

        result = exc.exception.args[0]
        self.assertEqual(result['changed'], True)

    @patch('ansible_collections.community.routeros.plugins.modules.api.ROS_api_module.api_add_path', new=fake_ros_api)
    def test_api_add_already_exist(self):
        with self.assertRaises(AnsibleFailJson) as exc:
            module_args = self.config_module_args.copy()
            module_args['add'] = "name=unit_test_brige_exist"
            set_module_args(module_args)
            self.module.main()

        result = exc.exception.args[0]
        self.assertEqual(result['failed'], True)
        self.assertEqual(result['msg'][0], 'failure: already have interface with such name')

    @patch('ansible_collections.community.routeros.plugins.modules.api.ROS_api_module.api_add_path', new=fake_ros_api)
    def test_api_remove(self):
        with self.assertRaises(AnsibleExitJson) as exc:
            module_args = self.config_module_args.copy()
            module_args['remove'] = "*A1"
            set_module_args(module_args)
            self.module.main()

        result = exc.exception.args[0]
        self.assertEqual(result['changed'], True)

    @patch('ansible_collections.community.routeros.plugins.modules.api.ROS_api_module.api_add_path', new=fake_ros_api)
    def test_api_remove_no_id(self):
        with self.assertRaises(AnsibleFailJson) as exc:
            module_args = self.config_module_args.copy()
            module_args['remove'] = "*A2"
            set_module_args(module_args)
            self.module.main()

        result = exc.exception.args[0]
        self.assertEqual(result['failed'], True)
        self.assertEqual(result['msg'][0], 'no such item (4)')

    @patch('ansible_collections.community.routeros.plugins.modules.api.ROS_api_module.api_add_path', new=fake_ros_api.arbitrary)
    def test_api_cmd(self):
        with self.assertRaises(AnsibleExitJson) as exc:
            module_args = self.config_module_args.copy()
            module_args['cmd'] = "add name=unit_test_brige_arbitrary"
            set_module_args(module_args)
            self.module.main()

        result = exc.exception.args[0]
        self.assertEqual(result['changed'], False)

    @patch('ansible_collections.community.routeros.plugins.modules.api.ROS_api_module.api_add_path', new=fake_ros_api.arbitrary)
    def test_api_cmd_none_existing_cmd(self):
        with self.assertRaises(AnsibleFailJson) as exc:
            module_args = self.config_module_args.copy()
            module_args['cmd'] = "add NONE_EXIST=unit_test_brige_arbitrary"
            set_module_args(module_args)
            self.module.main()

        result = exc.exception.args[0]
        self.assertEqual(result['failed'], True)
        self.assertEqual(result['msg'][0], 'no such command')

    @patch('ansible_collections.community.routeros.plugins.modules.api.ROS_api_module.api_add_path', new=fake_ros_api)
    def test_api_update(self):
        with self.assertRaises(AnsibleExitJson) as exc:
            module_args = self.config_module_args.copy()
            module_args['update'] = ".id=*A1 name=unit_test_brige"
            set_module_args(module_args)
            self.module.main()

        result = exc.exception.args[0]
        self.assertEqual(result['changed'], True)

    @patch('ansible_collections.community.routeros.plugins.modules.api.ROS_api_module.api_add_path', new=fake_ros_api)
    def test_api_update_none_existing_id(self):
        with self.assertRaises(AnsibleFailJson) as exc:
            module_args = self.config_module_args.copy()
            module_args['update'] = ".id=*A2 name=unit_test_brige"
            set_module_args(module_args)
            self.module.main()

        result = exc.exception.args[0]
        self.assertEqual(result['failed'], True)
        self.assertEqual(result['msg'][0], 'no such item (4)')

    @patch('ansible_collections.community.routeros.plugins.modules.api.ROS_api_module.api_add_path', new=fake_ros_api)
    def test_api_query(self):
        with self.assertRaises(AnsibleExitJson) as exc:
            module_args = self.config_module_args.copy()
            module_args['query'] = ".id name"
            set_module_args(module_args)
            self.module.main()

        result = exc.exception.args[0]
        self.assertEqual(result['changed'], False)
        self.assertEqual(result['msg'], [
            {'.id': '*A1', 'name': 'dummy_bridge_A1'},
            {'.id': '*A2', 'name': 'dummy_bridge_A2'},
            {'.id': '*A3', 'name': 'dummy_bridge_A3'},
        ])

    @patch('ansible_collections.community.routeros.plugins.modules.api.ROS_api_module.api_add_path', new=fake_ros_api)
    def test_api_query_missing_key(self):
        with self.assertRaises(AnsibleExitJson) as exc:
            module_args = self.config_module_args.copy()
            module_args['query'] = ".id other"
            set_module_args(module_args)
            self.module.main()

        result = exc.exception.args[0]
        self.assertEqual(result['changed'], False)
        self.assertEqual(result['msg'], ["no results for 'interface bridge 'query' .id other"])

    @patch('ansible_collections.community.routeros.plugins.modules.api.ROS_api_module.api_add_path', new=fake_ros_api.select_where)
    def test_api_query_and_WHERE(self):
        with self.assertRaises(AnsibleExitJson) as exc:
            module_args = self.config_module_args.copy()
            module_args['query'] = ".id name WHERE name == dummy_bridge_A2"
            set_module_args(module_args)
            self.module.main()

        result = exc.exception.args[0]
        self.assertEqual(result['changed'], False)
        self.assertEqual(result['msg'], [
            {'.id': '*A1', 'name': 'dummy_bridge_A1'},
        ])

    @patch('ansible_collections.community.routeros.plugins.modules.api.ROS_api_module.api_add_path', new=fake_ros_api.select_where)
    def test_api_query_and_WHERE_no_cond(self):
        with self.assertRaises(AnsibleExitJson) as exc:
            module_args = self.config_module_args.copy()
            module_args['query'] = ".id name WHERE name != dummy_bridge_A2"
            set_module_args(module_args)
            self.module.main()

        result = exc.exception.args[0]
        self.assertEqual(result['changed'], False)
        self.assertEqual(result['msg'], [
            {'.id': '*A1', 'name': 'dummy_bridge_A1'},
        ])

    @patch('ansible_collections.community.routeros.plugins.modules.api.ROS_api_module.api_add_path', new=fake_ros_api)
    def test_api_extended_query(self):
        with self.assertRaises(AnsibleExitJson) as exc:
            module_args = self.config_module_args.copy()
            module_args['extended_query'] = {
                'attributes': ['.id', 'name'],
            }
            set_module_args(module_args)
            self.module.main()

        result = exc.exception.args[0]
        self.assertEqual(result['changed'], False)
        self.assertEqual(result['msg'], [
            {'.id': '*A1', 'name': 'dummy_bridge_A1'},
            {'.id': '*A2', 'name': 'dummy_bridge_A2'},
            {'.id': '*A3', 'name': 'dummy_bridge_A3'},
        ])

    @patch('ansible_collections.community.routeros.plugins.modules.api.ROS_api_module.api_add_path', new=fake_ros_api)
    def test_api_extended_query_missing_key(self):
        with self.assertRaises(AnsibleExitJson) as exc:
            module_args = self.config_module_args.copy()
            module_args['extended_query'] = {
                'attributes': ['.id', 'other'],
            }
            set_module_args(module_args)
            self.module.main()

        result = exc.exception.args[0]
        self.assertEqual(result['changed'], False)
        self.assertEqual(result['msg'], [])

    @patch('ansible_collections.community.routeros.plugins.modules.api.ROS_api_module.api_add_path', new=fake_ros_api.select_where)
    def test_api_extended_query_and_WHERE(self):
        with self.assertRaises(AnsibleExitJson) as exc:
            module_args = self.config_module_args.copy()
            module_args['extended_query'] = {
                'attributes': ['.id', 'name'],
                'where': [
                    {
                        'attribute': 'name',
                        'is': '==',
                        'value': 'dummy_bridge_A2',
                    },
                ],
            }
            set_module_args(module_args)
            self.module.main()

        result = exc.exception.args[0]
        self.assertEqual(result['changed'], False)
        self.assertEqual(result['msg'], [
            {'.id': '*A1', 'name': 'dummy_bridge_A1'},
        ])

    @patch('ansible_collections.community.routeros.plugins.modules.api.ROS_api_module.api_add_path', new=fake_ros_api.select_where)
    def test_api_extended_query_and_WHERE_no_cond(self):
        with self.assertRaises(AnsibleExitJson) as exc:
            module_args = self.config_module_args.copy()
            module_args['extended_query'] = {
                'attributes': ['.id', 'name'],
                'where': [
                    {
                        'attribute': 'name',
                        'is': 'not',
                        'value': 'dummy_bridge_A2',
                    },
                ],
            }
            set_module_args(module_args)
            self.module.main()

        result = exc.exception.args[0]
        self.assertEqual(result['changed'], False)
        self.assertEqual(result['msg'], [
            {'.id': '*A1', 'name': 'dummy_bridge_A1'},
        ])

    @patch('ansible_collections.community.routeros.plugins.modules.api.ROS_api_module.api_add_path', new=fake_ros_api.select_where)
    def test_api_extended_query_and_WHERE_or(self):
        with self.assertRaises(AnsibleExitJson) as exc:
            module_args = self.config_module_args.copy()
            module_args['extended_query'] = {
                'attributes': ['.id', 'name'],
                'where': [
                    {
                        'or': [
                            {
                                'attribute': 'name',
                                'is': 'in',
                                'value': [1, 2],
                            },
                            {
                                'attribute': 'name',
                                'is': '!=',
                                'value': 5,
                            },
                        ],
                    },
                ],
            }
            set_module_args(module_args)
            self.module.main()

        result = exc.exception.args[0]
        self.assertEqual(result['changed'], False)
        self.assertEqual(result['msg'], [
            {'.id': '*A1', 'name': 'dummy_bridge_A1'},
        ])
