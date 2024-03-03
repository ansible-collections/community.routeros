# -*- coding: utf-8 -*-

# Copyright (c) 2021, Felix Fontein (@felixfontein) <felix@fontein.de>
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import absolute_import, division, print_function
__metaclass__ = type

import pytest

from ansible_collections.community.routeros.plugins.module_utils._api_data import (
    VersionedAPIData,
    KeyInfo,
    split_path,
    join_path,
)


def test_api_data_errors():
    with pytest.raises(ValueError) as exc:
        VersionedAPIData()
    assert exc.value.args[0] == 'fields must be provided'

    values = [
        ('primary_keys', []),
        ('stratify_keys', []),
        ('has_identifier', True),
        ('single_value', True),
        ('unknown_mechanism', True),
    ]

    for index, (param, param_value) in enumerate(values):
        for param2, param2_value in values[index + 1:]:
            with pytest.raises(ValueError) as exc:
                VersionedAPIData(**{param: param_value, param2: param2_value})
            assert exc.value.args[0] == 'primary_keys, stratify_keys, has_identifier, single_value, and unknown_mechanism are mutually exclusive'

    with pytest.raises(ValueError) as exc:
        VersionedAPIData(unknown_mechanism=True, fully_understood=True)
    assert exc.value.args[0] == 'unknown_mechanism and fully_understood cannot be combined'

    with pytest.raises(ValueError) as exc:
        VersionedAPIData(unknown_mechanism=True, fixed_entries=True)
    assert exc.value.args[0] == 'fixed_entries can only be used with primary_keys'

    with pytest.raises(ValueError) as exc:
        VersionedAPIData(primary_keys=['foo'], fields={})
    assert exc.value.args[0] == 'Primary key foo must be in fields!'

    with pytest.raises(ValueError) as exc:
        VersionedAPIData(stratify_keys=['foo'], fields={})
    assert exc.value.args[0] == 'Stratify key foo must be in fields!'

    with pytest.raises(ValueError) as exc:
        VersionedAPIData(required_one_of=['foo'], fields={})
    assert exc.value.args[0] == 'Require one of element at index #1 must be a list!'

    with pytest.raises(ValueError) as exc:
        VersionedAPIData(required_one_of=[['foo']], fields={})
    assert exc.value.args[0] == 'Require one of key foo must be in fields!'

    with pytest.raises(ValueError) as exc:
        VersionedAPIData(mutually_exclusive=['foo'], fields={})
    assert exc.value.args[0] == 'Mutually exclusive element at index #1 must be a list!'

    with pytest.raises(ValueError) as exc:
        VersionedAPIData(mutually_exclusive=[['foo']], fields={})
    assert exc.value.args[0] == 'Mutually exclusive key foo must be in fields!'


def test_key_info_errors():
    values = [
        ('required', True),
        ('default', ''),
        ('automatically_computed_from', ()),
        ('can_disable', True),
    ]

    params_allowed_together = [
        'default',
        'can_disable',
    ]

    emsg = 'required, default, automatically_computed_from, and can_disable are mutually exclusive besides default and can_disable which can be set together'
    for index, (param, param_value) in enumerate(values):
        for param2, param2_value in values[index + 1:]:
            if param in params_allowed_together and param2 in params_allowed_together:
                continue
            with pytest.raises(ValueError) as exc:
                KeyInfo(**{param: param_value, param2: param2_value})
            assert exc.value.args[0] == emsg

    with pytest.raises(ValueError) as exc:
        KeyInfo('foo')
    assert exc.value.args[0] == 'KeyInfo() does not have positional arguments'

    with pytest.raises(ValueError) as exc:
        KeyInfo(remove_value='')
    assert exc.value.args[0] == 'remove_value can only be specified if can_disable=True'

    with pytest.raises(ValueError) as exc:
        KeyInfo(read_only=True, write_only=True)
    assert exc.value.args[0] == 'read_only and write_only cannot be used at the same time'

    with pytest.raises(ValueError) as exc:
        KeyInfo(read_only=True, default=0)
    assert exc.value.args[0] == 'read_only can not be combined with can_disable, remove_value, absent_value, default, or required'


SPLIT_PATHS = [
    ('', [], ''),
    ('  ip  ', ['ip'], 'ip'),
    ('ip', ['ip'], 'ip'),
    ('  ip \t\n\raddress  ', ['ip', 'address'], 'ip address'),
]


@pytest.mark.parametrize("joined_input, split, joined_output", SPLIT_PATHS)
def test_join_split_path(joined_input, split, joined_output):
    assert split_path(joined_input) == split
    assert join_path(split) == joined_output
