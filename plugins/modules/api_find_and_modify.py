#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (c) 2022, Felix Fontein <felix@fontein.de>
# GNU General Public License v3.0+ https://www.gnu.org/licenses/gpl-3.0.txt
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = '''
---
module: api_find_and_modify
author:
  - "Felix Fontein (@felixfontein)"
short_description: Find and modify information using the API
version_added: 2.1.0
description:
  - Allows to find entries for a path by conditions and modify the values of these entries.
  - Use the M(community.routeros.api_find_and_modify) module to set all entries of a path to specific values,
    or change multiple entries in different ways in one step.
notes:
  - "If you want to change values based on their old values (like change all comments 'foo' to 'bar') and make sure that
     there are at least N such values, you can use I(require_matches_min=N) together with I(allow_no_matches=true).
     This will make the module fail if there are less than N such entries, but not if there is no match. The latter case
     is needed for idempotency of the task: once the values have been changed, there should be no further match."
extends_documentation_fragment:
  - community.routeros.api
  - community.routeros.attributes
  - community.routeros.attributes.actiongroup_api
attributes:
  check_mode:
    support: full
  diff_mode:
    support: full
  platform:
    support: full
    platforms: RouterOS
options:
  path:
    description:
      - Path to query.
      - An example value is C(ip address). This is equivalent to running C(/ip address) in the RouterOS CLI.
    required: true
    type: str
  find:
    description:
      - Fields to search for.
      - The module will only consider entries in the given I(path) that match all fields provided here.
      - Use YAML C(~), or prepend keys with C(!), to specify an unset value.
      - Note that if the dictionary specified here is empty, every entry in the path will be matched.
    required: true
    type: dict
  values:
    description:
      - On all entries matching the conditions in I(find), set the keys of this option to the values specified here.
      - Use YAML C(~), or prepend keys with C(!), to specify to unset a value.
    required: true
    type: dict
  require_matches_min:
    description:
      - Make sure that there are no less matches than this number.
      - If there are less matches, fail instead of modifying anything.
    type: int
    default: 0
  require_matches_max:
    description:
      - Make sure that there are no more matches than this number.
      - If there are more matches, fail instead of modifying anything.
      - If not specified, there is no upper limit.
    type: int
  allow_no_matches:
    description:
      - Whether to allow that no match is found.
      - If not specified, this value is induced from whether I(require_matches_min) is 0 or larger.
    type: bool
seealso:
  - module: community.routeros.api
  - module: community.routeros.api_facts
  - module: community.routeros.api_modify
  - module: community.routeros.api_info
'''

EXAMPLES = '''
---
- name: Rename bridge from 'bridge' to 'my-bridge'
  community.routeros.api_find_and_modify:
    hostname: "{{ hostname }}"
    password: "{{ password }}"
    username: "{{ username }}"
    path: interface bridge
    find:
      name: bridge
    values:
      name: my-bridge

- name: Change IP address to 192.168.1.1 for interface bridge - assuming there is only one
  community.routeros.api_find_and_modify:
    hostname: "{{ hostname }}"
    password: "{{ password }}"
    username: "{{ username }}"
    path: ip address
    find:
      interface: bridge
    values:
      address: "192.168.1.1/24"
    # If there are zero entries, or more than one: fail! We expected that
    # exactly one is configured.
    require_matches_min: 1
    require_matches_max: 1
'''

RETURN = '''
---
old_data:
    description:
      - A list of all elements for the current path before a change was made.
    sample:
      - '.id': '*1'
        actual-interface: bridge
        address: "192.168.88.1/24"
        comment: defconf
        disabled: false
        dynamic: false
        interface: bridge
        invalid: false
        network: 192.168.88.0
    type: list
    elements: dict
    returned: success
new_data:
    description:
      - A list of all elements for the current path after a change was made.
    sample:
      - '.id': '*1'
        actual-interface: bridge
        address: "192.168.1.1/24"
        comment: awesome
        disabled: false
        dynamic: false
        interface: bridge
        invalid: false
        network: 192.168.1.0
    type: list
    elements: dict
    returned: success
match_count:
    description:
      - The number of entries that matched the criteria in I(find).
    sample: 1
    type: int
    returned: success
modify__count:
    description:
      - The number of entries that were modified.
    sample: 1
    type: int
    returned: success
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.common.text.converters import to_native

from ansible_collections.community.routeros.plugins.module_utils.api import (
    api_argument_spec,
    check_has_library,
    create_api,
)

from ansible_collections.community.routeros.plugins.module_utils._api_data import (
    split_path,
)

try:
    from librouteros.exceptions import LibRouterosError
except Exception:
    # Handled in api module_utils
    pass


def compose_api_path(api, path):
    api_path = api.path()
    for p in path:
        api_path = api_path.join(p)
    return api_path


DISABLED_MEANS_EMPTY_STRING = ('comment', )


def main():
    module_args = dict(
        path=dict(type='str', required=True),
        find=dict(type='dict', required=True),
        values=dict(type='dict', required=True),
        require_matches_min=dict(type='int', default=0),
        require_matches_max=dict(type='int'),
        allow_no_matches=dict(type='bool'),
    )
    module_args.update(api_argument_spec())

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True,
    )
    if module.params['allow_no_matches'] is None:
        module.params['allow_no_matches'] = module.params['require_matches_min'] <= 0

    find = module.params['find']
    for key, value in sorted(find.items()):
        if key.startswith('!'):
            key = key[1:]
            if value not in (None, ''):
                module.fail_json(msg='The value for "!{key}" in `find` must not be non-trivial!'.format(key=key))
            if key in find:
                module.fail_json(msg='`find` must not contain both "{key}" and "!{key}"!'.format(key=key))
    values = module.params['values']
    for key, value in sorted(values.items()):
        if key.startswith('!'):
            key = key[1:]
            if value not in (None, ''):
                module.fail_json(msg='The value for "!{key}" in `values` must not be non-trivial!'.format(key=key))
            if key in values:
                module.fail_json(msg='`values` must not contain both "{key}" and "!{key}"!'.format(key=key))

    check_has_library(module)
    api = create_api(module)

    path = split_path(module.params['path'])

    api_path = compose_api_path(api, path)

    old_data = list(api_path)
    new_data = [entry.copy() for entry in old_data]

    # Find matching entries
    matching_entries = []
    for index, entry in enumerate(new_data):
        matches = True
        for key, value in find.items():
            if key.startswith('!'):
                # Allow to specify keys that should not be present by prepending '!'
                key = key[1:]
                value = None
            current_value = entry.get(key)
            if key in DISABLED_MEANS_EMPTY_STRING and value == '' and current_value is None:
                current_value = value
            if current_value != value:
                matches = False
                break
        if matches:
            matching_entries.append((index, entry))

    # Check whether the correct amount of entries was found
    if matching_entries:
        if len(matching_entries) < module.params['require_matches_min']:
            module.fail_json(msg='Found %d entries, but expected at least %d' % (len(matching_entries), module.params['require_matches_min']))
        if module.params['require_matches_max'] is not None and len(matching_entries) > module.params['require_matches_max']:
            module.fail_json(msg='Found %d entries, but expected at most %d' % (len(matching_entries), module.params['require_matches_max']))
    elif not module.params['allow_no_matches']:
        module.fail_json(msg='Found no entries, but allow_no_matches=false')

    # Identify entries to update
    modifications = []
    for index, entry in matching_entries:
        modification = {}
        for key, value in values.items():
            if key.startswith('!'):
                # Allow to specify keys to remove by prepending '!'
                key = key[1:]
                value = None
            current_value = entry.get(key)
            if key in DISABLED_MEANS_EMPTY_STRING and value == '' and current_value is None:
                current_value = value
            if current_value != value:
                if value is None:
                    disable_key = '!%s' % key
                    if key in DISABLED_MEANS_EMPTY_STRING:
                        disable_key = key
                    modification[disable_key] = ''
                    entry.pop(key, None)
                else:
                    modification[key] = value
                    entry[key] = value
        if modification:
            if '.id' in entry:
                modification['.id'] = entry['.id']
            modifications.append(modification)

    # Apply changes
    if not module.check_mode and modifications:
        for modification in modifications:
            try:
                api_path.update(**modification)
            except (LibRouterosError, UnicodeEncodeError) as e:
                module.fail_json(
                    msg='Error while modifying for .id={id}: {error}'.format(
                        id=modification['.id'],
                        error=to_native(e),
                    )
                )
        new_data = list(api_path)

    # Produce return value
    more = {}
    if module._diff:
        # Only include the matching values
        more['diff'] = {
            'before': {
                'values': [old_data[index] for index, entry in matching_entries],
            },
            'after': {
                'values': [entry for index, entry in matching_entries],
            },
        }
    module.exit_json(
        changed=bool(modifications),
        old_data=old_data,
        new_data=new_data,
        match_count=len(matching_entries),
        modify_count=len(modifications),
        **more
    )


if __name__ == '__main__':
    main()
