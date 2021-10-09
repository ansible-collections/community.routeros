# -*- coding: utf-8 -*-

# Copyright: (c) 2021, Felix Fontein (@felixfontein) <felix@fontein.de>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

import pytest

from ansible_collections.community.routeros.plugins.module_utils.quoting import (
    ParseError,
    split_routeros_command,
)


TEST_SPLIT_ROUTEROS_COMMAND = [
    ('', []),
    ('   ', []),
    (r'a b c', ['a', 'b', 'c']),
    (r'a=b c d=e', ['a=b', 'c', 'd=e']),
    (r'a="b f" c d=e', ['a=b f', 'c', 'd=e']),
    (r'a="b\"f" c\FF d=\"e', ['a=b"f', '\xff', 'c', 'd="e']),
]


@pytest.mark.parametrize("command, result", TEST_SPLIT_ROUTEROS_COMMAND)
def test_split_routeros_command(command, result):
    result_ = split_routeros_command(command)
    print(result_, result)
    assert result_ == result


TEST_SPLIT_ROUTEROS_COMMAND_ERRORS = [
    (r'a="b\"f" c\FF d="e', 'Unexpected end of string during escaped parameter'),
]


@pytest.mark.parametrize("command, message", TEST_SPLIT_ROUTEROS_COMMAND_ERRORS)
def test_split_routeros_command_errors(command, message):
    with pytest.raises(ParseError) as exc:
        split_routeros_command(command)
    print(exc.value.args[0], message)
    assert exc.value.args[0] == message
