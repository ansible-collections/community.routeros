# -*- coding: utf-8 -*-

# Copyright (c) 2021, Felix Fontein (@felixfontein) <felix@fontein.de>
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import absolute_import, division, print_function
__metaclass__ = type

import pytest

from ansible.module_utils.common.text.converters import to_native

from ansible_collections.community.routeros.plugins.module_utils._api_data import (
    APIData,
    KeyInfo,
    split_path,
    join_path,
)


def test_api_data_errors():
    with pytest.raises(ValueError) as exc:
        APIData()
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
                APIData(**{param: param_value, param2: param2_value})
            assert exc.value.args[0] == 'primary_keys, stratify_keys, has_identifier, single_value, and unknown_mechanism are mutually exclusive'

    with pytest.raises(ValueError) as exc:
        APIData(unknown_mechanism=True, fully_understood=True)
    assert exc.value.args[0] == 'unknown_mechanism and fully_understood cannot be combined'

    with pytest.raises(ValueError) as exc:
        APIData(unknown_mechanism=True, fixed_entries=True)
    assert exc.value.args[0] == 'fixed_entries can only be used with primary_keys'

    with pytest.raises(ValueError) as exc:
        APIData(primary_keys=['foo'], fields={})
    assert exc.value.args[0] == 'Primary key foo must be in fields!'

    with pytest.raises(ValueError) as exc:
        APIData(stratify_keys=['foo'], fields={})
    assert exc.value.args[0] == 'Stratify key foo must be in fields!'


def test_key_info_errors():
    values = [
        ('required', True),
        ('default', ''),
        ('automatically_computed_from', ()),
        ('can_disable', True),
    ]

    for index, (param, param_value) in enumerate(values):
        for param2, param2_value in values[index + 1:]:
            with pytest.raises(ValueError) as exc:
                KeyInfo(**{param: param_value, param2: param2_value})
            assert exc.value.args[0] == 'required, default, automatically_computed_from, and can_disable are mutually exclusive'

    with pytest.raises(ValueError) as exc:
        KeyInfo('foo')
    assert exc.value.args[0] == 'KeyInfo() does not have positional arguments'

    with pytest.raises(ValueError) as exc:
        KeyInfo(remove_value='')
    assert exc.value.args[0] == 'remove_value can only be specified if can_disable=True'


SPLITTED_PATHS = [
    ('', [], ''),
    ('  ip  ', ['ip'], 'ip'),
    ('ip', ['ip'], 'ip'),
    ('  ip \t\n\raddress  ', ['ip', 'address'], 'ip address'),
]


@pytest.mark.parametrize("joined_input, splitted, joined_output", SPLITTED_PATHS)
def test_join_split_path(joined_input, splitted, joined_output):
    assert split_path(joined_input) == splitted
    assert join_path(splitted) == joined_output
