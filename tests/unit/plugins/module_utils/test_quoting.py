# -*- coding: utf-8 -*-

# Copyright (c) 2021, Felix Fontein (@felixfontein) <felix@fontein.de>
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import absolute_import, division, print_function
__metaclass__ = type

import pytest

from ansible.module_utils.common.text.converters import to_native

from ansible_collections.community.routeros.plugins.module_utils.quoting import (
    ParseError,
    convert_list_to_dictionary,
    join_routeros_command,
    parse_argument_value,
    quote_routeros_argument,
    quote_routeros_argument_value,
    split_routeros_command,
)


TEST_PARSE_ARGUMENT_VALUE = [
    ('a', {}, ('a', 1)),
    ('a   ', {'must_match_everything': False}, ('a', 1)),
    (r'"a b"', {}, ('a b', 5)),
    (r'"b\"f"', {}, ('b"f', 6)),
    (r'"\01"', {}, ('\x01', 5)),
    (r'"\1F"', {}, ('\x1f', 5)),
    (r'"\FF"', {}, (to_native(b'\xff'), 5)),
    (r'"\"e"', {}, ('"e', 5)),
    (r'"\""', {}, ('"', 4)),
    (r'"\\"', {}, ('\\', 4)),
    (r'"\?"', {}, ('?', 4)),
    (r'"\$"', {}, ('$', 4)),
    (r'"\_"', {}, (' ', 4)),
    (r'"\a"', {}, ('\a', 4)),
    (r'"\b"', {}, ('\b', 4)),
    (r'"\f"', {}, (to_native(b'\xff'), 4)),
    (r'"\n"', {}, ('\n', 4)),
    (r'"\r"', {}, ('\r', 4)),
    (r'"\t"', {}, ('\t', 4)),
    (r'"\v"', {}, ('\v', 4)),
    (r'"b=c"', {}, ('b=c', 5)),
    (r'""', {}, ('', 2)),
    (r'"" ', {'must_match_everything': False}, ('', 2)),
    ("'e", {'start_index': 1}, ('e', 2)),
]


@pytest.mark.parametrize("command, kwargs, result", TEST_PARSE_ARGUMENT_VALUE)
def test_parse_argument_value(command, kwargs, result):
    result_ = parse_argument_value(command, **kwargs)
    print(result_, result)
    assert result_ == result


TEST_PARSE_ARGUMENT_VALUE_ERRORS = [
    (r'"e', {}, 'Unexpected end of string during escaped parameter'),
    ("'e", {}, '"\'" can only be used inside double quotes'),
    (r'\FF', {}, 'Escape sequences can only be used inside double quotes'),
    (r'\"e', {}, 'Escape sequences can only be used inside double quotes'),
    ('e=f', {}, '"=" can only be used inside double quotes'),
    ('e$', {}, '"$" can only be used inside double quotes'),
    ('e(', {}, '"(" can only be used inside double quotes'),
    ('e)', {}, '")" can only be used inside double quotes'),
    ('e[', {}, '"[" can only be used inside double quotes'),
    ('e{', {}, '"{" can only be used inside double quotes'),
    ('e`', {}, '"`" can only be used inside double quotes'),
    ('?', {}, '"?" can only be used in escaped form'),
    (r'b"', {}, '\'"\' must not appear in an unquoted value'),
    (r'""a', {}, "Ending '\"' must be followed by space or end of string"),
    (r'"" ', {}, "Unexpected data at end of value"),
    ('"\\', {}, r"'\' must not be at the end of the line"),
    (r'"\A', {}, r'Hex escape sequence cut off at end of line'),
    (r'"\Z"', {}, r"Invalid escape sequence '\Z'"),
    (r'"\Aa"', {}, r"Invalid hex escape sequence '\Aa'"),
]


@pytest.mark.parametrize("command, kwargs, message", TEST_PARSE_ARGUMENT_VALUE_ERRORS)
def test_parse_argument_value_errors(command, kwargs, message):
    with pytest.raises(ParseError) as exc:
        parse_argument_value(command, **kwargs)
    print(exc.value.args[0], message)
    assert exc.value.args[0] == message


TEST_SPLIT_ROUTEROS_COMMAND = [
    ('', []),
    ('   ', []),
    (r'a b c', ['a', 'b', 'c']),
    (r'a=b c d=e', ['a=b', 'c', 'd=e']),
    (r'a="b f" c d=e', ['a=b f', 'c', 'd=e']),
    (r'a="b\"f" c="\FF" d="\"e"', ['a=b"f', to_native(b'c=\xff'), 'd="e']),
    (r'a="b=c"', ['a=b=c']),
    (r'a=b ', ['a=b']),
]


@pytest.mark.parametrize("command, result", TEST_SPLIT_ROUTEROS_COMMAND)
def test_split_routeros_command(command, result):
    result_ = split_routeros_command(command)
    print(result_, result)
    assert result_ == result


TEST_SPLIT_ROUTEROS_COMMAND_ERRORS = [
    (r'a=', 'Expected value, but found end of string'),
    (r'a="b\"f" d="e', 'Unexpected end of string during escaped parameter'),
    ('d=\'e', '"\'" can only be used inside double quotes'),
    (r'c\FF', r'Found unexpected "\"'),
    (r'd=\"e', 'Escape sequences can only be used inside double quotes'),
    ('d=e=f', '"=" can only be used inside double quotes'),
    ('d=e$', '"$" can only be used inside double quotes'),
    ('d=e(', '"(" can only be used inside double quotes'),
    ('d=e)', '")" can only be used inside double quotes'),
    ('d=e[', '"[" can only be used inside double quotes'),
    ('d=e{', '"{" can only be used inside double quotes'),
    ('d=e`', '"`" can only be used inside double quotes'),
    ('d=?', '"?" can only be used in escaped form'),
    (r'a=b"', '\'"\' must not appear in an unquoted value'),
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
    (['a=b', 'c=d=e', 'e=', 'f', 'g=h i j', 'h="h"'], r'a=b c="d=e" e="" f g="h\_i\_j" h="\"h\""'),
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
    (r'a=b c', r'a="b\_c"'),
    (r'a="b c"', r'a="\"b\_c\""'),
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
    (r" ", r'"\_"'),
    (r"=", r'"="'),
    (r'a', r'a'),
    (r'a=b', r'"a=b"'),
    (r'b c', r'"b\_c"'),
    (r'"b c"', r'"\"b\_c\""'),
    ("'b", "\"'b\""),
    ("b'", "\"b'\""),
    ('"', r'"\""'),
    ('\\', r'"\\"'),
    ('?', r'"\?"'),
    ('$', r'"\$"'),
    ('_', r'_'),
    (' ', r'"\_"'),
    ('\a', r'"\a"'),
    ('\b', r'"\b"'),
    # (to_native(b'\xff'), r'"\f"'),
    ('\n', r'"\n"'),
    ('\r', r'"\r"'),
    ('\t', r'"\t"'),
    ('\v', r'"\v"'),
    ('\x01', r'"\01"'),
    ('\x1f', r'"\1F"'),
]


@pytest.mark.parametrize("argument, expected", TEST_QUOTE_ROUTEROS_ARGUMENT_VALUE)
def test_quote_routeros_argument_value(argument, expected):
    result = quote_routeros_argument_value(argument)
    print(result, expected)
    assert result == expected


TEST_ROUNDTRIP = [
    {'a': 'b', 'c': 'd'},
    {'script': ''':local host value=[/system identity get name];
:local date value=[/system clock get date];
:local day [ :pick $date 4 6 ];
:local month [ :pick $date 0 3 ];
:local year [ :pick $date 7 11 ];
:local name value=($host."-".$day."-".$month."-".$year);
/system backup save name=$name;
/export file=$name;
/tool fetch address="192.168.1.1" user=ros password="PASSWORD" mode=ftp dst-path=("/mikrotik/rsc/".$name.".rsc") src-path=($name.".rsc") upload=yes;
/tool fetch address="192.168.1.1" user=ros password="PASSWORD" mode=ftp dst-path=("/mikrotik/backup/".$name.".backup") src-path=($name.".backup") upload=yes;
'''},
]


@pytest.mark.parametrize("dictionary", TEST_ROUNDTRIP)
def test_roundtrip(dictionary):
    argument_list = ['%s=%s' % (k, v) for k, v in dictionary.items()]
    command = join_routeros_command(argument_list)
    resplit_list = split_routeros_command(command)
    print(resplit_list, argument_list)
    assert resplit_list == argument_list
    re_dictionary = convert_list_to_dictionary(resplit_list)
    print(re_dictionary, dictionary)
    assert re_dictionary == dictionary
