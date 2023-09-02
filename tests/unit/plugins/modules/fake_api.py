# Copyright (c) Ansible Project
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from ansible_collections.community.routeros.plugins.module_utils._api_data import PATHS


FAKE_ROS_VERSION = '7.5.0'


class FakeLibRouterosError(Exception):
    def __init__(self, message):
        self.message = message
        super(FakeLibRouterosError, self).__init__(self.message)


class TrapError(FakeLibRouterosError):
    def __init__(self, message='failure: already have interface with such name'):
        super(TrapError, self).__init__(message)


# fixtures
class fake_ros_api(object):
    def __init__(self, api, path):
        pass

    @classmethod
    def path(cls, api, path):
        fake_bridge = [{".id": "*DC", "name": "b2", "mtu": "auto", "actual-mtu": 1500,
                        "l2mtu": 65535, "arp": "enabled", "arp-timeout": "auto",
                        "mac-address": "3A:C1:90:D6:E8:44", "protocol-mode": "rstp",
                        "fast-forward": "true", "igmp-snooping": "false",
                        "auto-mac": "true", "ageing-time": "5m", "priority":
                        "0x8000", "max-message-age": "20s", "forward-delay": "15s",
                        "transmit-hold-count": 6, "vlan-filtering": "false",
                        "dhcp-snooping": "false", "running": "true", "disabled": "false"}]
        return fake_bridge

    @classmethod
    def arbitrary(cls, api, path):
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
            return []

    @classmethod
    def select_where(cls, api, path):
        api_path = Where()
        return api_path


class Where(object):
    def __init__(self):
        pass

    def select(self, *args):
        return self

    def where(self, *args):
        return [{".id": "*A1", "name": "dummy_bridge_A1"}]


class Key(object):
    def __init__(self, name):
        self.name = name
        self.str_return()

    def str_return(self):
        return str(self.name)


class Or(object):
    def __init__(self, *args):
        self.args = args
        self.str_return()

    def str_return(self):
        return repr(self.args)


def _normalize_entry(entry, path_info, on_create=False):
    for key, data in path_info.fields.items():
        if key not in entry and data.default is not None and (not data.can_disable or on_create):
            entry[key] = data.default
        if data.can_disable:
            if key in entry and entry[key] in (None, data.remove_value):
                del entry[key]
            if ('!%s' % key) in entry:
                entry.pop(key, None)
                del entry['!%s' % key]
        if data.absent_value is not None and key in entry and entry[key] == data.absent_value:
            del entry[key]


def massage_expected_result_data(values, path, keep_all=False, remove_dynamic=False, remove_builtin=False):
    versioned_path_info = PATHS[path]
    versioned_path_info.provide_version(FAKE_ROS_VERSION)
    path_info = versioned_path_info.get_data()
    if remove_dynamic:
        values = [entry for entry in values if not entry.get('dynamic', False)]
    if remove_builtin:
        values = [entry for entry in values if not entry.get('builtin', False)]
    values = [entry.copy() for entry in values]
    for entry in values:
        _normalize_entry(entry, path_info)
        if not keep_all:
            for key in list(entry):
                if key == '.id' or key in path_info.fields:
                    continue
                del entry[key]
        for key, data in path_info.fields.items():
            if data.absent_value is not None and key not in entry:
                entry[key] = data.absent_value
    return values


class Path(object):
    def __init__(self, path, initial_values, read_only=False):
        self._path = path
        versioned_path_info = PATHS[path]
        versioned_path_info.provide_version(FAKE_ROS_VERSION)
        self._path_info = versioned_path_info.get_data()
        self._values = [entry.copy() for entry in initial_values]
        for entry in self._values:
            _normalize_entry(entry, self._path_info)
        self._new_id_counter = 0
        self._read_only = read_only

    def _sanitize(self, entry):
        entry = entry.copy()
        for field, field_info in self._path_info.fields.items():
            if field in entry:
                if field_info.write_only:
                    del entry[field]
        return entry

    def __iter__(self):
        return [self._sanitize(entry) for entry in self._values].__iter__()

    def _find_id(self, id, required=False):
        for index, entry in enumerate(self._values):
            if entry['.id'] == id:
                return index
        if required:
            raise FakeLibRouterosError('Cannot find key "%s"' % id)
        return None

    def add(self, **kwargs):
        if self._path_info.fixed_entries or self._path_info.single_value:
            raise Exception('Cannot add entries')
        if self._read_only:
            raise Exception('Modifying read-only path: add %s' % repr(kwargs))
        if '.id' in kwargs:
            raise Exception('Trying to create new entry with ".id" field: %s' % repr(kwargs))
        if 'dynamic' in kwargs or 'builtin' in kwargs:
            raise Exception('Trying to add a dynamic or builtin entry')
        self._new_id_counter += 1
        id = '*NEW%d' % self._new_id_counter
        entry = {
            '.id': id,
        }
        for field, value in kwargs.items():
            if field.startswith('!'):
                field = field[1:]
            if field not in self._path_info.fields:
                raise ValueError('Trying to set unknown field "{field}"'.format(field=field))
            field_info = self._path_info.fields[field]
            if field_info.read_only:
                raise ValueError('Trying to set read-only field "{field}"'.format(field=field))
            entry[field] = value
        _normalize_entry(entry, self._path_info, on_create=True)
        self._values.append(entry)
        return id

    def remove(self, *args):
        if self._path_info.fixed_entries or self._path_info.single_value:
            raise Exception('Cannot remove entries')
        if self._read_only:
            raise Exception('Modifying read-only path: remove %s' % repr(args))
        for id in args:
            index = self._find_id(id, required=True)
            entry = self._values[index]
            if entry.get('dynamic', False) or entry.get('builtin', False):
                raise Exception('Trying to remove a dynamic or builtin entry')
            del self._values[index]

    def update(self, **kwargs):
        if self._read_only:
            raise Exception('Modifying read-only path: update %s' % repr(kwargs))
        if 'dynamic' in kwargs or 'builtin' in kwargs:
            raise Exception('Trying to update dynamic builtin fields')
        if self._path_info.single_value:
            index = 0
        else:
            index = self._find_id(kwargs['.id'], required=True)
        entry = self._values[index]
        if entry.get('dynamic', False) or entry.get('builtin', False):
            raise Exception('Trying to update a dynamic or builtin entry')
        for field in kwargs:
            if field == '.id':
                continue
            if field.startswith('!'):
                field = field[1:]
            if field not in self._path_info.fields:
                raise ValueError('Trying to update unknown field "{field}"'.format(field=field))
            field_info = self._path_info.fields[field]
            if field_info.read_only:
                raise ValueError('Trying to update read-only field "{field}"'.format(field=field))
        entry.update(kwargs)
        _normalize_entry(entry, self._path_info)

    def __call__(self, command, *args, **kwargs):
        if self._read_only:
            raise Exception('Modifying read-only path: "%s" %s %s' % (command, repr(args), repr(kwargs)))
        if command != 'move':
            raise FakeLibRouterosError('Unsupported command "%s"' % command)
        if self._path_info.fixed_entries or self._path_info.single_value:
            raise Exception('Cannot move entries')
        yield None  # make sure that nothing happens if the result isn't consumed
        source_index = self._find_id(kwargs.pop('numbers'), required=True)
        entry = self._values.pop(source_index)
        dest_index = self._find_id(kwargs.pop('destination'), required=True)
        self._values.insert(dest_index, entry)


def create_fake_path(path, initial_values, read_only=False):
    def create(api, called_path):
        called_path = tuple(called_path)
        if path != called_path:
            raise AssertionError('Expected {path}, got {called_path}'.format(path=path, called_path=called_path))
        return Path(path, initial_values, read_only=read_only)

    return create
