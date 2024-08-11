# -*- coding: utf-8 -*-
# Copyright (c) 2022, Felix Fontein (@felixfontein) <felix@fontein.de>
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

# The data inside here is private to this collection. If you use this from outside the collection,
# you are on your own. There can be random changes to its format even in bugfix releases!

from __future__ import absolute_import, division, print_function
__metaclass__ = type


def validate_restrict(module, path_info):
    restrict = module.params['restrict']
    if restrict is None:
        return
    for entry in restrict:
        field = entry['field']
        if field.startswith('!'):
            module.fail_json(msg='restrict: the field name "{0}" must not start with "!"'.format(field))
        f = path_info.fields.get(field)
        if f is None:
            module.fail_json(msg='restrict: the field "{0}" does not exist for this path'.format(field))


def entry_accepted(entry, path_info, module):
    restrict = module.params['restrict']
    if restrict is None:
        return True
    for rule in restrict:
        field = rule['field']
        field_info = path_info.fields[field]
        value = entry.get(field)
        if value is None:
            value = field_info.default
        if field not in entry and field_info.absent_value:
            value = field_info.absent_value
        if value not in rule['values']:
            return False
    return True
