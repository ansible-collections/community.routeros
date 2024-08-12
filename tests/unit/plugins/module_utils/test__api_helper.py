# -*- coding: utf-8 -*-

# Copyright (c) 2021, Felix Fontein (@felixfontein) <felix@fontein.de>
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import absolute_import, division, print_function
__metaclass__ = type

import re
import sys

import pytest

from ansible_collections.community.routeros.plugins.module_utils._api_data import (
    PATHS,
)

from ansible_collections.community.routeros.plugins.module_utils._api_helper import (
    _value_to_str,
    _test_rule_except_invert,
    validate_and_prepare_restrict,
    restrict_entry_accepted,
)


VALUE_TO_STR = [
    (None, None),
    ('', u''),
    ('foo', u'foo'),
    (True, u'true'),
    (False, u'false'),
    ([], u'[]'),
    ({}, u'{}'),
    (1, u'1'),
    (-42, u'-42'),
    (1.5, u'1.5'),
    (1.0, u'1.0'),
]


@pytest.mark.parametrize("value, expected", VALUE_TO_STR)
def test_value_to_str(value, expected):
    result = _value_to_str(value)
    print(repr(result))
    assert result == expected


TEST_RULE_EXCEPT_INVERT = [
    (
        None,
        {
            'field': u'foo',
            'match_disabled': False,
            'invert': False,
        },
        False,
    ),
    (
        None,
        {
            'field': u'foo',
            'match_disabled': True,
            'invert': False,
        },
        True,
    ),
    (
        1,
        {
            'field': u'foo',
            'match_disabled': False,
            'invert': False,
            'values': [1],
        },
        True,
    ),
    (
        1,
        {
            'field': u'foo',
            'match_disabled': False,
            'invert': False,
            'values': ['1'],
        },
        False,
    ),
    (
        1,
        {
            'field': u'foo',
            'match_disabled': False,
            'invert': False,
            'regex': re.compile(u'^1$'),
            'regex_source': u'^1$',
        },
        True,
    ),
    (
        1.10,
        {
            'field': u'foo',
            'match_disabled': False,
            'invert': False,
            'regex': re.compile(u'^1\\.1$'),
            'regex_source': u'^1\\.1$',
        },
        True,
    ),
    (
        10,
        {
            'field': u'foo',
            'match_disabled': False,
            'invert': False,
            'regex': re.compile(u'^1$'),
            'regex_source': u'^1$',
        },
        False,
    ),
]


@pytest.mark.parametrize("value, rule, expected", TEST_RULE_EXCEPT_INVERT)
def test_rule_except_invert(value, rule, expected):
    result = _test_rule_except_invert(value, rule)
    print(repr(result))
    assert result == expected


_test_path = PATHS[('ip', 'firewall', 'filter')]
_test_path.provide_version('7.0')
TEST_PATH = _test_path.get_data()


class FailJsonExc(Exception):
    def __init__(self, msg, kwargs):
        self.msg = msg
        self.kwargs = kwargs


class FakeModule(object):
    def __init__(self, restrict_value):
        self.params = {
            'restrict': restrict_value,
        }

    def fail_json(self, msg, **kwargs):
        raise FailJsonExc(msg, kwargs)


TEST_VALIDATE_AND_PREPARE_RESTRICT = [
    (
        [{
            'field': u'chain',
            'match_disabled': False,
            'values': None,
            'regex': None,
            'invert': False,
        }],
        [{
            'field': u'chain',
            'match_disabled': False,
            'invert': False,
        }],
    ),
    (
        [{
            'field': u'comment',
            'match_disabled': True,
            'values': None,
            'regex': None,
            'invert': False,
        }],
        [{
            'field': u'comment',
            'match_disabled': True,
            'invert': False,
        }],
    ),
    (
        [{
            'field': u'comment',
            'match_disabled': False,
            'values': None,
            'regex': None,
            'invert': True,
        }],
        [{
            'field': u'comment',
            'match_disabled': False,
            'invert': True,
        }],
    ),
]

if sys.version_info >= (2, 7, 17):
    # Somewhere between Python 2.7.15 (used by Ansible 3.9) and 2.7.17 (used by ansible-base 2.10)
    # something changed with ``==`` for ``re.Pattern``, at least for some patterns
    # (my guess is: for ``re.compile(u'')``)
    TEST_VALIDATE_AND_PREPARE_RESTRICT.extend([
        (
            [
                {
                    'field': u'comment',
                    'match_disabled': False,
                    'values': [],
                    'regex': None,
                    'invert': False,
                },
                {
                    'field': u'comment',
                    'match_disabled': False,
                    'values': [None, 1, 42.0, True, u'foo', [], {}],
                    'regex': None,
                    'invert': False,
                },
                {
                    'field': u'chain',
                    'match_disabled': False,
                    'values': None,
                    'regex': u'',
                    'invert': True,
                },
                {
                    'field': u'chain',
                    'match_disabled': False,
                    'values': None,
                    'regex': u'foo',
                    'invert': False,
                },
            ],
            [
                {
                    'field': u'comment',
                    'match_disabled': False,
                    'invert': False,
                    'values': [],
                },
                {
                    'field': u'comment',
                    'match_disabled': False,
                    'invert': False,
                    'values': [None, 1, 42.0, True, u'foo', [], {}],
                },
                {
                    'field': u'chain',
                    'match_disabled': False,
                    'invert': True,
                    'regex': re.compile(u''),
                    'regex_source': u'',
                },
                {
                    'field': u'chain',
                    'match_disabled': False,
                    'invert': False,
                    'regex': re.compile(u'foo'),
                    'regex_source': u'foo',
                },
            ],
        ),
    ])


@pytest.mark.parametrize("restrict_value, expected", TEST_VALIDATE_AND_PREPARE_RESTRICT)
def test_validate_and_prepare_restrict(restrict_value, expected):
    fake_module = FakeModule(restrict_value)
    result = validate_and_prepare_restrict(fake_module, TEST_PATH)
    print(repr(result))
    assert result == expected


TEST_VALIDATE_AND_PREPARE_RESTRICT_FAIL = [
    (
        [{
            'field': u'!foo',
            'match_disabled': False,
            'values': None,
            'regex': None,
            'invert': False,
        }],
        ['restrict: the field name "!foo" must not start with "!"'],
    ),
    (
        [{
            'field': u'foo',
            'match_disabled': False,
            'values': None,
            'regex': None,
            'invert': False,
        }],
        ['restrict: the field "foo" does not exist for this path'],
    ),
    (
        [{
            'field': u'chain',
            'match_disabled': False,
            'values': None,
            'regex': u'(',
            'invert': False,
        }],
        [
            'restrict: invalid regular expression "(": missing ), unterminated subpattern at position 0',
            'restrict: invalid regular expression "(": unbalanced parenthesis',
        ]
    ),
]


@pytest.mark.parametrize("restrict_value, expected", TEST_VALIDATE_AND_PREPARE_RESTRICT_FAIL)
def test_validate_and_prepare_restrict_fail(restrict_value, expected):
    fake_module = FakeModule(restrict_value)
    with pytest.raises(FailJsonExc) as exc:
        validate_and_prepare_restrict(fake_module, TEST_PATH)
    print(repr(exc.value.msg))
    assert exc.value.msg in expected


TEST_RESTRICT_ENTRY_ACCEPTED = [
    (
        {
            'chain': 'input',
        },
        [
            {
                'field': u'chain',
                'match_disabled': False,
                'invert': False,
            },
        ],
        False,
    ),
    (
        {
            'chain': 'input',
        },
        [
            {
                'field': u'chain',
                'match_disabled': False,
                'invert': True,
            },
        ],
        True,
    ),
    (
        {
            'comment': 'foo',
        },
        [
            {
                'field': u'comment',
                'match_disabled': True,
                'invert': False,
            },
        ],
        False,
    ),
    (
        {},
        [
            {
                'field': u'comment',
                'match_disabled': True,
                'invert': False,
            },
        ],
        True,
    ),
]


@pytest.mark.parametrize("entry, restrict_data, expected", TEST_RESTRICT_ENTRY_ACCEPTED)
def test_restrict_entry_accepted(entry, restrict_data, expected):
    result = restrict_entry_accepted(entry, TEST_PATH, restrict_data)
    print(repr(result))
    assert result == expected
