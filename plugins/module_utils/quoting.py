# -*- coding: utf-8 -*-

# Copyright: (c) 2021, Felix Fontein (@felixfontein) <felix@fontein.de>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


from ansible.module_utils.common.text.converters import to_native, to_bytes


class ParseError(Exception):
    pass


ESCAPE_SEQUENCES = {
    b'"': b'"',
    b'\\': b'\\',
    b'?': b'?',
    b'$': b'$',
    b'_': b'_',
    b'a': b'\a',
    b'b': b'\b',
    b'f': b'\xFF',
    b'n': b'\n',
    b'r': b'\r',
    b't': b'\t',
    b'v': b'\v',
}

ESCAPE_DIGITS = b'0123456789ABCDEF'


def split_routeros_command(line):
    line = to_bytes(line)
    result = []
    current = []
    index = 0
    length = len(line)
    # States:
    #   0 = outside param
    #   1 = param before '='
    #   2 = param after '=' without quote
    #   3 = param after '=' with quote
    state = 0
    while index < length:
        ch = line[index:index + 1]
        index += 1
        if state == 0 and ch == b' ':
            pass
        elif state in (1, 2) and ch == b' ':
            state = 0
            result.append(b''.join(current))
            current = []
        elif ch == b'=' and state == 1:
            state = 2
            current.append(ch)
            if index + 1 < length and line[index:index + 1] == b'"':
                state = 3
                index += 1
        elif ch == b'"':
            if state == 3:
                state = 0
                result.append(b''.join(current))
                current = []
                if index + 1 < length and line[index:index + 1] != b' ':
                    raise ParseError('Ending \'"\' must be followed by space or end of string')
            else:
                raise ParseError('\'"\' must follow \'=\'')
        elif ch == b'\\':
            if index + 1 == length:
                raise ParseError('\'\\\' must not be at the end of the line')
            ch = line[index:index + 1]
            index += 1
            if ch in ESCAPE_SEQUENCES:
                current.append(ch)
            else:
                d1 = ESCAPE_DIGITS.find(ch)
                if d1 < 0:
                    raise ParseError('Invalid escape sequence \'\\{0}\''.format(ch))
                if index + 1 == length:
                    raise ParseError('Hex escape sequence cut off at end of line')
                ch2 = line[index:index + 1]
                d2 = ESCAPE_DIGITS.find(ch2)
                index += 1
                if d2 < 0:
                    raise ParseError('Invalid hex escape sequence \'\\{0}{1}\''.format(ch, ch2))
                result.append(chr(d1 * 16 + d2))
        else:
            current.append(ch)
            if state == 0:
                state = 1
    if state in (1, 2):
        if current:
            result.append(b''.join(current))
    elif state == 3:
        raise ParseError('Unexpected end of string during escaped parameter')
    return [to_native(part) for part in result]


def convert_list_to_dictionary(string_list, require_assignment=True, skip_empty_values=False):
    dictionary = {}
    for p in string_list:
        if '=' not in p:
            if require_assignment:
                raise ParseError("missing '=' after '%s'" % p)
            dictionary[p] = None
            continue
        p = p.split('=', 1)
        if not skip_empty_values or p[1]:
            dictionary[p[0]] = p[1]
    return dictionary
