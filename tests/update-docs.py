#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Copyright (c) 2022, Felix Fontein (@felixfontein) <felix@fontein.de>
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

'''
Updates DOCUMENTATION of modules using module_utils._api_data with the correct list of supported paths.
'''

import sys

from ansible_collections.community.routeros.plugins.module_utils._api_data import (
    PATHS,
    join_path,
)


MODULES = [
    'plugins/modules/api_info.py',
    'plugins/modules/api_modify.py',
]


def update_file(file: str, begin_line: str, end_line: str, choice_line: str, path_choices: list[str]) -> bool:
    with open(file, 'r', encoding='utf-8') as f:
        lines = f.read().splitlines()
    begin_index = lines.index(begin_line)
    end_index = lines.index(end_line, begin_index + 1)
    new_lines = lines[:begin_index + 1] + [choice_line.format(choice=choice) for choice in path_choices] + lines[end_index:]
    if lines == new_lines:
        return False
    print(f'{file} has been updated')
    with open(file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(new_lines) + '\n')
    return True


def main(args: list[str]) -> int:
    path_choices = sorted([join_path(path) for path, path_info in PATHS.items() if path_info.fully_understood])

    changes = False
    for file in MODULES:
        changes |= update_file(file, '    # BEGIN PATH LIST', '    # END PATH LIST', '      - {choice}', path_choices)

    lint = "--lint" in args
    if not lint or not changes:
        return 0

    print("Run 'nox -Re update-docs'!")
    return 1


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
