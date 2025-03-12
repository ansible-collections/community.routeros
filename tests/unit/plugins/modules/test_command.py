# Copyright (c) 2016 Red Hat Inc.
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import json

from ansible_collections.community.internal_test_tools.tests.unit.compat.mock import patch
from ansible_collections.community.internal_test_tools.tests.unit.plugins.modules.utils import set_module_args

from ansible_collections.community.routeros.plugins.modules import command
from .routeros_module import TestRouterosModule, load_fixture


class TestRouterosCommandModule(TestRouterosModule):

    module = command

    def setUp(self):
        super(TestRouterosCommandModule, self).setUp()

        self.mock_run_commands = patch('ansible_collections.community.routeros.plugins.modules.command.run_commands')
        self.run_commands = self.mock_run_commands.start()

    def tearDown(self):
        super(TestRouterosCommandModule, self).tearDown()
        self.mock_run_commands.stop()

    def load_fixtures(self, commands=None):

        def load_from_file(*args, **kwargs):
            module, commands = args
            output = list()

            for item in commands:
                try:
                    obj = json.loads(item)
                    command = obj
                except ValueError:
                    command = item
                filename = str(command).replace(' ', '_').replace('/', '')
                output.append(load_fixture(filename))
            return output

        self.run_commands.side_effect = load_from_file

    def test_command_simple(self):
        with set_module_args(dict(commands=['/system resource print'])):
            result = self.execute_module(changed=True)
        self.assertEqual(len(result['stdout']), 1)
        self.assertTrue('platform: "MikroTik"' in result['stdout'][0])

    def test_command_multiple(self):
        with set_module_args(dict(commands=['/system resource print', '/system resource print'])):
            result = self.execute_module(changed=True)
        self.assertEqual(len(result['stdout']), 2)
        self.assertTrue('platform: "MikroTik"' in result['stdout'][0])

    def test_command_wait_for(self):
        wait_for = 'result[0] contains "MikroTik"'
        with set_module_args(dict(commands=['/system resource print'], wait_for=wait_for)):
            self.execute_module(changed=True)

    def test_command_wait_for_fails(self):
        wait_for = 'result[0] contains "test string"'
        with set_module_args(dict(commands=['/system resource print'], wait_for=wait_for)):
            self.execute_module(failed=True)
        self.assertEqual(self.run_commands.call_count, 10)

    def test_command_retries(self):
        wait_for = 'result[0] contains "test string"'
        with set_module_args(dict(commands=['/system resource print'], wait_for=wait_for, retries=2)):
            self.execute_module(failed=True)
        self.assertEqual(self.run_commands.call_count, 2)

    def test_command_match_any(self):
        wait_for = ['result[0] contains "MikroTik"',
                    'result[0] contains "test string"']
        with set_module_args(dict(commands=['/system resource print'], wait_for=wait_for, match='any')):
            self.execute_module(changed=True)

    def test_command_match_all(self):
        wait_for = ['result[0] contains "MikroTik"',
                    'result[0] contains "RB1100"']
        with set_module_args(dict(commands=['/system resource print'], wait_for=wait_for, match='all')):
            self.execute_module(changed=True)

    def test_command_match_all_failure(self):
        wait_for = ['result[0] contains "MikroTik"',
                    'result[0] contains "test string"']
        commands = ['/system resource print', '/system resource print']
        with set_module_args(dict(commands=commands, wait_for=wait_for, match='all')):
            self.execute_module(failed=True)

    def test_command_wait_for_2(self):
        wait_for = 'result[0] contains "wireless"'
        with set_module_args(dict(commands=['/system package print'], wait_for=wait_for)):
            self.execute_module(changed=True)
