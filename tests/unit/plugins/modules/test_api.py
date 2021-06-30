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
from ansible_collections.community.routeros.tests.unit.plugins.modules.utils import set_module_args, AnsibleExitJson, AnsibleFailJson, ModuleTestCase
from ansible_collections.community.routeros.plugins.modules import api


class FakeLibRouterosError(Exception):
    def __init__(self, message):
        self.message = message
        super(FakeLibRouterosError, self).__init__(self.message)


class TrapError(FakeLibRouterosError):
    def __init__(self, message="failure: already have interface with such name"):
        super(TrapError, self).__init__(message)


# fixtures
class fake_ros_api(object):
    def __init__(self, api, path):
        pass

    def path(self, api, path):
        fake_bridge = [{".id": "*DC", "name": "b2", "mtu": "auto", "actual-mtu": 1500,
                        "l2mtu": 65535, "arp": "enabled", "arp-timeout": "auto",
                        "mac-address": "3A:C1:90:D6:E8:44", "protocol-mode": "rstp",
                        "fast-forward": "true", "igmp-snooping": "false",
                        "auto-mac": "true", "ageing-time": "5m", "priority":
                        "0x8000", "max-message-age": "20s", "forward-delay": "15s",
                        "transmit-hold-count": 6, "vlan-filtering": "false",
                        "dhcp-snooping": "false", "running": "true", "disabled": "false"}]
        return fake_bridge

    def arbitrary(self, api, path):
        def retr(self, *args, **kwargs):
            if 'name' not in kwargs.keys():
                raise TrapError(message="no such command")
            dummy_test_string = '/interface/bridge add name=unit_test_brige_arbitrary'
            result = "/%s/%s add name=%s" % (path[0], path[1], kwargs['name'])
            return [result]
        return retr

    def add(self, name):
        if name == "unit_test_brige_exist":
            raise TrapError
        return '*A1'

    def remove(self, id):
        if id != "*A1":
            raise TrapError(message="no such item (4)")
        return '*A1'

    def update(self, **kwargs):
        if kwargs['.id'] != "*A1" or 'name' not in kwargs.keys():
            raise TrapError(message="no such item (4)")
        return ["updated: {'.id': '%s' % kwargs['.id'], 'name': '%s' % kwargs['name']}"]

    def select(self, *args):
        dummy_bridge = [{".id": "*A1", "name": "dummy_bridge_A1"},
                        {".id": "*A2", "name": "dummy_bridge_A2"},
                        {".id": "*A3", "name": "dummy_bridge_A3"}]

        result = []
        for dummy in dummy_bridge:
            found = {}
            for search in args:
                if search in dummy.keys():
                    found[search] = dummy[search]
                else:
                    continue
            if len(found.keys()) == 2:
                result.append(found)

        if result:
            return result
        else:
            return ["no results for 'interface bridge 'query' %s" % ' '.join(args)]

    def select_where(self, api, path):
        api_path = Where()
        return api_path


class Where(object):
    def __init__(self):
        pass

    def select(self, *args):
        return self

    def where(self, *args):
        return ["*A1"]


class Key(object):
    def __init__(self, name):
        self.name = name
        self.str_return()

    def str_return(self):
        return str(self.name)


class TestRouterosApiModule(ModuleTestCase):

    def setUp(self):
        super(TestRouterosApiModule, self).setUp()
        librouteros = pytest.importorskip("librouteros")
        self.module = api
        self.module.LibRouterosError = FakeLibRouterosError
        self.module.connect = MagicMock(new=fake_ros_api)
        self.module.Key = MagicMock(new=Key)
        self.config_module_args = {"username": "admin",
                                   "password": "pаss",
                                   "hostname": "127.0.0.1",
                                   "path": "interface bridge"}

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

    @patch('ansible_collections.community.routeros.plugins.modules.api.ROS_api_module.api_add_path', new=fake_ros_api)
    def test_api_query_missing_key(self):
        with self.assertRaises(AnsibleExitJson) as exc:
            module_args = self.config_module_args.copy()
            module_args['query'] = ".id other"
            set_module_args(module_args)
            self.module.main()

        result = exc.exception.args[0]
        self.assertEqual(result['changed'], False)

    @patch('ansible_collections.community.routeros.plugins.modules.api.ROS_api_module.api_add_path', new=fake_ros_api.select_where)
    def test_api_query_and_WHERE(self):
        with self.assertRaises(AnsibleExitJson) as exc:
            module_args = self.config_module_args.copy()
            module_args['query'] = ".id name WHERE name == dummy_bridge_A2"
            set_module_args(module_args)
            self.module.main()

        result = exc.exception.args[0]
        self.assertEqual(result['changed'], False)

    @patch('ansible_collections.community.routeros.plugins.modules.api.ROS_api_module.api_add_path', new=fake_ros_api.select_where)
    def test_api_query_and_WHERE_no_cond(self):
        with self.assertRaises(AnsibleExitJson) as exc:
            module_args = self.config_module_args.copy()
            module_args['query'] = ".id name WHERE name != dummy_bridge_A2"
            set_module_args(module_args)
            self.module.main()

        result = exc.exception.args[0]
        self.assertEqual(result['changed'], False)
