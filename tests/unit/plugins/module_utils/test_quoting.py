# -*- coding: utf-8 -*-

# Copyright: (c) 2021, Felix Fontein (@felixfontein) <felix@fontein.de>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

import pytest

from ansible_collections.community.routeros.plugins.module_utils.quoting import (
    ParseError,
    convert_list_to_dictionary,
    join_routeros_command,
    quote_routeros_argument,
    quote_routeros_argument_value,
    split_routeros_command,
)


TEST_SPLIT_ROUTEROS_COMMAND = [
    ('', []),
    ('   ', []),
    (r'a b c', ['a', 'b', 'c']),
    (r'a=b c d=e', ['a=b', 'c', 'd=e']),
    (r'a="b f" c d=e', ['a=b f', 'c', 'd=e']),
    (r'a="b\"f" c\FF d=\"e', ['a=b"f', '\xff', 'c', 'd="e']),
    (r'a=b ', ['a=b']),
    (r'a=', ['a=']),
]


@pytest.mark.parametrize("command, result", TEST_SPLIT_ROUTEROS_COMMAND)
def test_split_routeros_command(command, result):
    result_ = split_routeros_command(command)
    print(result_, result)
    assert result_ == result


TEST_SPLIT_ROUTEROS_COMMAND_ERRORS = [
    (r'a="b\"f" c\FF d="e', 'Unexpected end of string during escaped parameter'),
    (r'a=b"', '\'"\' must follow \'=\''),
    (r'a=""a', "Ending '\"' must be followed by space or end of string"),
    ('a="\\', r"'\' must not be at the end of the line"),
    (r'a="\Z', r"Invalid escape sequence '\Z'"),
    (r'a="\Aa', r"Invalid hex escape sequence '\Aa'"),
]


@pytest.mark.parametrize("command, message", TEST_SPLIT_ROUTEROS_COMMAND_ERRORS)
def test_split_routeros_command_errors(command, message):
    with pytest.raises(ParseError) as exc:
        split_routeros_command(command)
    print(exc.value.args[0], message)
    assert exc.value.args[0] == message


TEST_CONVERT_LIST_TO_DICTIONARY = [
    (['a=b', 'c=d=e', 'e='], {}, {'a': 'b', 'c': 'd=e', 'e': ''}),
    (['a=b', 'c=d=e', 'e='], {'skip_empty_values': False}, {'a': 'b', 'c': 'd=e', 'e': ''}),
    (['a=b', 'c=d=e', 'e='], {'skip_empty_values': True}, {'a': 'b', 'c': 'd=e'}),
    (['a=b', 'c=d=e', 'e=', 'f'], {'require_assignment': False}, {'a': 'b', 'c': 'd=e', 'e': '', 'f': None}),
]


@pytest.mark.parametrize("list, kwargs, expected_dict", TEST_CONVERT_LIST_TO_DICTIONARY)
def test_convert_list_to_dictionary(list, kwargs, expected_dict):
    result = convert_list_to_dictionary(list, **kwargs)
    print(result, expected_dict)
    assert result == expected_dict


TEST_CONVERT_LIST_TO_DICTIONARY_ERRORS = [
    (['a=b', 'c=d=e', 'e=', 'f'], {}, "missing '=' after 'f'"),
]


@pytest.mark.parametrize("list, kwargs, message", TEST_CONVERT_LIST_TO_DICTIONARY_ERRORS)
def test_convert_list_to_dictionary_errors(list, kwargs, message):
    with pytest.raises(ParseError) as exc:
        result = convert_list_to_dictionary(list, **kwargs)
    print(exc.value.args[0], message)
    assert exc.value.args[0] == message


TEST_JOIN_ROUTEROS_COMMAND = [
    (['a=b', 'c=d=e', 'e=', 'f', 'g=h i j', 'h="h"'], r'a=b c="d=e" e="" f g="h i j" h="\"h\""'),
]


@pytest.mark.parametrize("list, expected", TEST_JOIN_ROUTEROS_COMMAND)
def test_join_routeros_command(list, expected):
    result = join_routeros_command(list)
    print(result, expected)
    assert result == expected


TEST_QUOTE_ROUTEROS_ARGUMENT = [
    (r'', r''),
    (r'a', r'a'),
    (r'a=b', r'a=b'),
    (r'a=b c', r'a="b c"'),
    (r'a="b c"', r'a="\"b c\""'),
    (r"a='b", "a=\"'b\""),
    (r"a=b'", "a=\"b'\""),
    (r'a=""', r'a="\"\""'),
]


@pytest.mark.parametrize("argument, expected", TEST_QUOTE_ROUTEROS_ARGUMENT)
def test_quote_routeros_argument(argument, expected):
    result = quote_routeros_argument(argument)
    print(result, expected)
    assert result == expected


TEST_QUOTE_ROUTEROS_ARGUMENT_ERRORS = [
    ('a b', 'Attribute names must not contain spaces'),
    ('a b=c', 'Attribute names must not contain spaces'),
]


@pytest.mark.parametrize("argument, message", TEST_QUOTE_ROUTEROS_ARGUMENT_ERRORS)
def test_quote_routeros_argument_errors(argument, message):
    with pytest.raises(ParseError) as exc:
        result = quote_routeros_argument(argument)
    print(exc.value.args[0], message)
    assert exc.value.args[0] == message


TEST_QUOTE_ROUTEROS_ARGUMENT_VALUE = [
    (r'', r'""'),
    (r";", r'";"'),
    (r" ", r'" "'),
    (r"=", r'"="'),
    (r'a', r'a'),
    (r'a=b', r'"a=b"'),
    (r'b c', r'"b c"'),
    (r'"b c"', r'"\"b c\""'),
    ("'b", "\"'b\""),
    ("b'", "\"b'\""),
]


@pytest.mark.parametrize("argument, expected", TEST_QUOTE_ROUTEROS_ARGUMENT_VALUE)
def test_quote_routeros_argument_value(argument, expected):
    result = quote_routeros_argument_value(argument)
    print(result, expected)
    assert result == expected
