# -*- coding: utf-8 -*-
# Copyright (c) 2022, Felix Fontein (@felixfontein) <felix@fontein.de>
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

# The data inside here is private to this collection. If you use this from outside the collection,
# you are on your own. There can be random changes to its format even in bugfix releases!

from __future__ import absolute_import, division, print_function
__metaclass__ = type

import re

from ansible.module_utils.common.text.converters import to_text


def validate_and_prepare_restrict(module, path_info):
    restrict = module.params['restrict']
    if restrict is None:
        return None
    restrict_data = []
    for rule in restrict:
        field = rule['field']
        if field.startswith('!'):
            module.fail_json(msg='restrict: the field name "{0}" must not start with "!"'.format(field))
        f = path_info.fields.get(field)
        if f is None:
            module.fail_json(msg='restrict: the field "{0}" does not exist for this path'.format(field))

        new_rule = dict(field=field)
        if rule['values'] is not None:
            new_rule['values'] = rule['values']
        elif rule['regex'] is not None:
            regex = rule['regex']
            try:
                new_rule['regex'] = re.compile(regex)
                new_rule['regex_source'] = regex
            except Exception as exc:
                module.fail_json(msg='restrict: invalid regular expression "{0}": {1}'.format(regex, exc))
        restrict_data.append(new_rule)
    return restrict_data


def restrict_entry_accepted(entry, path_info, restrict_data):
    if restrict_data is None:
        return True
    for rule in restrict_data:
        # Obtain field and value
        field = rule['field']
        field_info = path_info.fields[field]
        value = entry.get(field)
        if value is None:
            value = field_info.default
        if field not in entry and field_info.absent_value:
            value = field_info.absent_value

        # Actual test
        if 'values' in rule and value not in rule['values']:
            return False
        if 'regex' in rule:
            if value is None:
                # regex cannot match None
                return False
            value_str = to_text(value)
            if isinstance(value, bool):
                value_str = value_str.lower()
            if rule['regex'].match(value_str):
                return False
    return True


def restrict_argument_spec():
    return dict(
        restrict=dict(
            type='list',
            elements='dict',
            options=dict(
                field=dict(type='str', required=True),
                values=dict(type='list', elements='raw'),
                regex=dict(type='str'),
            ),
            mutually_exclusive=[
                ('values', 'regex'),
            ],
            required_one_of=[
                ('values', 'regex'),
            ],
        ),
    )
