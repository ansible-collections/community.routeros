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
from ansible_collections.community.routeros.tests.unit.plugins.modules.utils import set_module_args, basic, AnsibleExitJson, AnsibleFailJson, ModuleTestCase
from ansible_collections.community.routeros.plugins.modules import api


class AnsibleExitJson(Exception):
    """Exception class to be raised by module.exit_json and caught by the test case"""
    pass


class AnsibleFailJson(Exception):
    """Exception class to be raised by module.fail_json and caught by the test case"""
    pass


def exit_json(*args, **kwargs):
    """function to patch over exit_json; package return data into an exception"""
    if 'changed' not in kwargs:
        kwargs['changed'] = False
    raise AnsibleExitJson(kwargs)


def fail_json(*args, **kwargs):
    """function to patch over fail_json; package return data into an exception"""
    kwargs['failed'] = True
    raise AnsibleFailJson(kwargs)


# fixtures
class fake_ros_api:
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


class Where:
    def __init__(self):
        pass

    def select(self, *args):
        return self

    def where(self, *args):
        return ["*A1"]


class TrapError(Exception):
    def __init__(self, message="failure: already have interface with such name"):
        self.message = message
        super().__init__(self.message)


class Key:
    def __init__(self, name):
        self.name = name
        self.str_return()

    def str_return(self):
        return str(self.name)


class TestRouterosApiModule(ModuleTestCase):

    def setUp(self):
        librouteros = pytest.importorskip("librouteros")
        self.module = api
        self.module.connect = MagicMock(new=fake_ros_api)
        self.module.Key = MagicMock(new=Key)
        self.config_module_args = {"username": "admin",
                                   "password": "pаss",
                                   "hostname": "127.0.0.1",
                                   "path": "interface bridge"}

        self.mock_module_helper = patch.multiple(basic.AnsibleModule,
                                                 exit_json=exit_json,
                                                 fail_json=fail_json)
        self.mock_module_helper.start()
        self.addCleanup(self.mock_module_helper.stop)

    def test_module_fail_when_required_args_missing(self):
        with self.assertRaises(AnsibleFailJson):
            set_module_args({})
            self.module.main()

    @patch('ansible_collections.community.routeros.plugins.modules.api.ROS_api_module.api_add_path', new=fake_ros_api.path)
    def test_api_path(self):
        with self.assertRaises(AnsibleExitJson):
            set_module_args(self.config_module_args)
            self.module.main()

    @patch('ansible_collections.community.routeros.plugins.modules.api.ROS_api_module.api_add_path', new=fake_ros_api.arbitrary)
    def test_api_add(self):
        with self.assertRaises(AnsibleExitJson):
            module_args = self.config_module_args.copy()
            module_args['add'] = "name=unit_test_brige"
            set_module_args(module_args)
            self.module.main()

    @patch('ansible_collections.community.routeros.plugins.modules.api.ROS_api_module.api_add_path', new=fake_ros_api)
    def test_api_add_already_exist(self):
        with self.assertRaises(AnsibleExitJson):
            module_args = self.config_module_args.copy()
            module_args['add'] = "name=unit_test_brige_exist"
            set_module_args(module_args)
            self.module.main()

    @patch('ansible_collections.community.routeros.plugins.modules.api.ROS_api_module.api_add_path', new=fake_ros_api)
    def test_api_remove(self):
        with self.assertRaises(AnsibleExitJson):
            module_args = self.config_module_args.copy()
            module_args['remove'] = "*A1"
            set_module_args(module_args)
            self.module.main()

    @patch('ansible_collections.community.routeros.plugins.modules.api.ROS_api_module.api_add_path', new=fake_ros_api)
    def test_api_remove_no_id(self):
        with self.assertRaises(AnsibleExitJson):
            module_args = self.config_module_args.copy()
            module_args['remove'] = "*A2"
            set_module_args(module_args)
            self.module.main()

    @patch('ansible_collections.community.routeros.plugins.modules.api.ROS_api_module.api_add_path', new=fake_ros_api.arbitrary)
    def test_api_cmd(self):
        with self.assertRaises(AnsibleExitJson):
            module_args = self.config_module_args.copy()
            module_args['cmd'] = "add name=unit_test_brige_arbitrary"
            set_module_args(module_args)
            self.module.main()

    @patch('ansible_collections.community.routeros.plugins.modules.api.ROS_api_module.api_add_path', new=fake_ros_api.arbitrary)
    def test_api_cmd_none_existing_cmd(self):
        with self.assertRaises(AnsibleExitJson):
            module_args = self.config_module_args.copy()
            module_args['cmd'] = "add NONE_EXIST=unit_test_brige_arbitrary"
            set_module_args(module_args)
            self.module.main()

    @patch('ansible_collections.community.routeros.plugins.modules.api.ROS_api_module.api_add_path', new=fake_ros_api)
    def test_api_update(self):
        with self.assertRaises(AnsibleExitJson):
            module_args = self.config_module_args.copy()
            module_args['update'] = ".id=*A1 name=unit_test_brige"
            set_module_args(module_args)
            self.module.main()

    @patch('ansible_collections.community.routeros.plugins.modules.api.ROS_api_module.api_add_path', new=fake_ros_api)
    def test_api_update_none_existing_id(self):
        with self.assertRaises(AnsibleExitJson):
            module_args = self.config_module_args.copy()
            module_args['update'] = ".id=*A2 name=unit_test_brige"
            set_module_args(module_args)
            self.module.main()

    @patch('ansible_collections.community.routeros.plugins.modules.api.ROS_api_module.api_add_path', new=fake_ros_api)
    def test_api_query(self):
        with self.assertRaises(AnsibleExitJson):
            module_args = self.config_module_args.copy()
            module_args['query'] = ".id name"
            set_module_args(module_args)
            self.module.main()

    @patch('ansible_collections.community.routeros.plugins.modules.api.ROS_api_module.api_add_path', new=fake_ros_api)
    def test_api_query_missing_key(self):
        with self.assertRaises(AnsibleExitJson):
            module_args = self.config_module_args.copy()
            module_args['query'] = ".id other"
            set_module_args(module_args)
            self.module.main()

    @patch('ansible_collections.community.routeros.plugins.modules.api.ROS_api_module.api_add_path', new=fake_ros_api.select_where)
    def test_api_query_and_WHERE(self):
        with self.assertRaises(AnsibleExitJson):
            module_args = self.config_module_args.copy()
            module_args['query'] = ".id name WHERE name == dummy_bridge_A2"
            set_module_args(module_args)
            self.module.main()

    @patch('ansible_collections.community.routeros.plugins.modules.api.ROS_api_module.api_add_path', new=fake_ros_api.select_where)
    def test_api_query_and_WHERE_no_cond(self):
        with self.assertRaises(AnsibleExitJson):
            module_args = self.config_module_args.copy()
            module_args['query'] = ".id name WHERE name =! dummy_bridge_A2"
            set_module_args(module_args)
            self.module.main()
