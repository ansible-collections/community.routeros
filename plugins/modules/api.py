#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2020, Nikolay Dachev <nikolay@dachev.info>
# GNU General Public License v3.0+ https://www.gnu.org/licenses/gpl-3.0.txt

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = '''
---
module: api
author: "Nikolay Dachev (@NikolayDachev)"
short_description: Ansible module for RouterOS API
description:
  - Ansible module for RouterOS API with python librouteros.
  - This module can add, remove, update, query and execute arbitrary command in routeros via API.
notes:
  - I(add), I(remove), I(update), I(cmd) and I(query) are mutually exclusive.
  - I(check_mode) is not supported.
requirements:
  - librouteros
  - Python >= 3.6 (for librouteros)
options:
  hostname:
    description:
      - RouterOS hostname API.
    required: true
    type: str
  username:
    description:
      - RouterOS login user.
    required: true
    type: str
  password:
    description:
      - RouterOS user password.
    required: true
    type: str
  tls:
    description:
      - If is set TLS will be used for RouterOS API connection.
    required: false
    type: bool
    default: false
    aliases:
      - ssl
  port:
    description:
      - RouterOS api port. If I(tls) is set, port will apply to TLS/SSL connection.
      - Defaults are C(8728) for the HTTP API, and C(8729) for the HTTPS API.
    type: int
  path:
    description:
      - Main path for all other arguments.
      - If other arguments are not set, api will return all items in selected path.
      - Example C(ip address). Equivalent of RouterOS CLI C(/ip address print).
    required: true
    type: str
  add:
    description:
      - Will add selected arguments in selected path to RouterOS config.
      - Example C(address=1.1.1.1/32 interface=ether1).
      - Equivalent in RouterOS CLI C(/ip address add address=1.1.1.1/32 interface=ether1).
    type: str
  remove:
    description:
      - Remove config/value from RouterOS by '.id'.
      - Example C(*03) will remove config/value with C(id=*03) in selected path.
      - Equivalent in RouterOS CLI C(/ip address remove numbers=1).
      - Note C(number) in RouterOS CLI is different from C(.id).
    type: str
  update:
    description:
      - Update config/value in RouterOS by '.id' in selected path.
      - Example C(.id=*03 address=1.1.1.3/32) and path C(ip address) will replace existing ip address with C(.id=*03).
      - Equivalent in RouterOS CLI C(/ip address set address=1.1.1.3/32 numbers=1).
      - Note C(number) in RouterOS CLI is different from C(.id).
    type: str
  query:
    description:
      - Query given path for selected query attributes from RouterOS aip and return '.id'.
      - WHERE is key word which extend query. WHERE format is key operator value - with spaces.
      - WHERE valid operators are C(==), C(!=), C(>), C(<).
      - Example path C(ip address) and query C(.id address) will return only C(.id) and C(address) for all items in C(ip address) path.
      - Example path C(ip address) and query C(.id address WHERE address == 1.1.1.3/32).
        will return only C(.id) and C(address) for items in C(ip address) path, where address is eq to 1.1.1.3/32.
      - Example path C(interface) and query C(mtu name WHERE mut > 1400) will
        return only interfaces C(mtu,name) where mtu is bigger than 1400.
      - Equivalent in RouterOS CLI C(/interface print where mtu > 1400).
    type: str
  cmd:
    description:
      - Execute any/arbitrary command in selected path, after the command we can add C(.id).
      - Example path C(system script) and cmd C(run .id=*03) is equivalent in RouterOS CLI C(/system script run number=0).
      - Example path C(ip address) and cmd C(print) is equivalent in RouterOS CLI C(/ip address print).
    type: str
  validate_certs:
    description:
      - Set to C(false) to skip validation of TLS certificates.
      - See also I(validate_cert_hostname). Only used when I(tls=true).
      - B(Note:) instead of simply deactivating certificate validations to "make things work",
        please consider creating your own CA certificate and using it to sign certificates used
        for your router. You can tell the module about your CA certificate with the I(ca_path)
        option.
    type: bool
    default: true
    version_added: 1.2.0
  validate_cert_hostname:
    description:
      - Set to C(true) to validate hostnames in certificates.
      - See also I(validate_certs). Only used when I(tls=true) and I(validate_certs=true).
    type: bool
    default: false
    version_added: 1.2.0
  ca_path:
    description:
      - PEM formatted file that contains a CA certificate to be used for certificate validation.
      - See also I(validate_cert_hostname). Only used when I(tls=true) and I(validate_certs=true).
    type: path
    version_added: 1.2.0
seealso:
  - ref: ansible_collections.community.routeros.docsite.api-guide
    description: How to connect to RouterOS devices with the RouterOS API
  - ref: ansible_collections.community.routeros.docsite.quoting
    description: How to quote and unquote commands and arguments
'''

EXAMPLES = '''
---
- name: Use RouterOS API
  hosts: localhost
  gather_facts: no
  vars:
    hostname: "ros_api_hostname/ip"
    username: "admin"
    password: "secret_password"

    path: "ip address"

    nic: "ether2"
    ip1: "1.1.1.1/32"
    ip2: "2.2.2.2/32"
    ip3: "3.3.3.3/32"

  tasks:
    - name: Get "{{ path }} print"
      community.routeros.api:
        hostname: "{{ hostname }}"
        password: "{{ password }}"
        username: "{{ username }}"
        path: "{{ path }}"
      register: print_path

    - name: Dump "{{ path }} print" output
      ansible.builtin.debug:
        msg: '{{ print_path }}'

    - name: Add ip address "{{ ip1 }}" and "{{ ip2 }}"
      community.routeros.api:
        hostname: "{{ hostname }}"
        password: "{{ password }}"
        username: "{{ username }}"
        path: "{{ path }}"
        add: "{{ item }}"
      loop:
        - "address={{ ip1 }} interface={{ nic }}"
        - "address={{ ip2 }} interface={{ nic }}"
      register: addout

    - name: Dump "Add ip address" output - ".id" for new added items
      ansible.builtin.debug:
        msg: '{{ addout }}'

    - name: Query for ".id" in "{{ path }} WHERE address == {{ ip2 }}"
      community.routeros.api:
        hostname: "{{ hostname }}"
        password: "{{ password }}"
        username: "{{ username }}"
        path: "{{ path }}"
        query: ".id address WHERE address == {{ ip2 }}"
      register: queryout

    - name: Dump "Query for" output and set fact with ".id" for "{{ ip2 }}"
      ansible.builtin.debug:
        msg: '{{ queryout }}'

    - name: Store query_id for later usage
      ansible.builtin.set_fact:
        query_id: "{{ queryout['msg'][0]['.id'] }}"

    - name: Update ".id = {{ query_id }}" taken with custom fact "fquery_id"
      community.routeros.api:
        hostname: "{{ hostname }}"
        password: "{{ password }}"
        username: "{{ username }}"
        path: "{{ path }}"
        update: >-
            .id={{ query_id }}
            address={{ ip3 }}
            comment={{ 'A comment with spaces' | community.routeros.quote_argument_value }}
      register: updateout

    - name: Dump "Update" output
      ansible.builtin.debug:
        msg: '{{ updateout }}'

    - name: Remove ips - stage 1 - query ".id" for "{{ ip2 }}" and "{{ ip3 }}"
      community.routeros.api:
        hostname: "{{ hostname }}"
        password: "{{ password }}"
        username: "{{ username }}"
        path: "{{ path }}"
        query: ".id address WHERE address == {{ item }}"
      register: id_to_remove
      loop:
        - "{{ ip2 }}"
        - "{{ ip3 }}"

    - name: Set fact for ".id" from "Remove ips - stage 1 - query"
      ansible.builtin.set_fact:
        to_be_remove: "{{ to_be_remove |default([]) + [item['msg'][0]['.id']] }}"
      loop: "{{ id_to_remove.results }}"

    - name: Dump "Remove ips - stage 1 - query" output
      ansible.builtin.debug:
        msg: '{{ to_be_remove }}'

    # Remove "{{ rmips }}" with ".id" by "to_be_remove" from query
    - name: Remove ips - stage 2 - remove "{{ ip2 }}" and "{{ ip3 }}" by '.id'
      community.routeros.api:
        hostname: "{{ hostname }}"
        password: "{{ password }}"
        username: "{{ username }}"
        path: "{{ path }}"
        remove: "{{ item }}"
      register: remove
      loop: "{{ to_be_remove }}"

    - name: Dump "Remove ips - stage 2 - remove" output
      ansible.builtin.debug:
        msg: '{{ remove }}'

    - name: Arbitrary command example "/system identity print"
      community.routeros.api:
        hostname: "{{ hostname }}"
        password: "{{ password }}"
        username: "{{ username }}"
        path: "system identity"
        cmd: "print"
      register: cmdout

    - name: Dump "Arbitrary command example" output
      ansible.builtin.debug:
        msg: "{{ cmdout }}"
'''

RETURN = '''
---
message:
    description: All outputs are in list with dictionary elements returned from RouterOS api.
    sample: C([{...},{...}])
    type: list
    returned: always
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.basic import missing_required_lib
from ansible.module_utils.common.text.converters import to_native

from ansible_collections.community.routeros.plugins.module_utils.quoting import (
    ParseError,
    convert_list_to_dictionary,
    parse_argument_value,
    split_routeros_command,
)

import re
import ssl
import traceback

LIB_IMP_ERR = None
try:
    from librouteros import connect
    from librouteros.exceptions import LibRouterosError
    from librouteros.query import Key
    HAS_LIB = True
except Exception as e:
    HAS_LIB = False
    LIB_IMP_ERR = traceback.format_exc()


class ROS_api_module:
    def __init__(self):
        module_args = dict(
            username=dict(type='str', required=True),
            password=dict(type='str', required=True, no_log=True),
            hostname=dict(type='str', required=True),
            port=dict(type='int'),
            tls=dict(type='bool', default=False, aliases=['ssl']),
            path=dict(type='str', required=True),
            add=dict(type='str'),
            remove=dict(type='str'),
            update=dict(type='str'),
            cmd=dict(type='str'),
            query=dict(type='str'),
            validate_certs=dict(type='bool', default=True),
            validate_cert_hostname=dict(type='bool', default=False),
            ca_path=dict(type='path'),
        )

        self.module = AnsibleModule(argument_spec=module_args,
                                    supports_check_mode=False,
                                    mutually_exclusive=(('add', 'remove', 'update',
                                                         'cmd', 'query'),),)

        if not HAS_LIB:
            self.module.fail_json(msg=missing_required_lib("librouteros"),
                                  exception=LIB_IMP_ERR)

        self.api = self.ros_api_connect(self.module.params['username'],
                                        self.module.params['password'],
                                        self.module.params['hostname'],
                                        self.module.params['port'],
                                        self.module.params['tls'],
                                        self.module.params['validate_certs'],
                                        self.module.params['validate_cert_hostname'],
                                        self.module.params['ca_path'],
                                        )

        self.path = self.module.params['path'].split()
        self.add = self.module.params['add']
        self.remove = self.module.params['remove']
        self.update = self.module.params['update']
        self.arbitrary = self.module.params['cmd']

        self.where = None
        self.query = self.module.params['query']
        if self.query:
            where_index = self.query.find(' WHERE ')
            if where_index < 0:
                self.query = self.split_params(self.query)
            else:
                where = self.query[where_index + len(' WHERE '):]
                self.query = self.split_params(self.query[:where_index])
                # where must be of the format '<attribute> <operator> <value>'
                m = re.match(r'^\s*([^ ]+)\s+([^ ]+)\s+(.*)$', where)
                if not m:
                    self.errors("invalid syntax for 'WHERE %s'" % where)
                try:
                    self.where = [
                        m.group(1),  # attribute
                        m.group(2),  # operator
                        parse_argument_value(m.group(3).rstrip())[0],  # value
                    ]
                except ParseError as exc:
                    self.errors("invalid syntax for 'WHERE %s': %s" % (where, exc))
            try:
                idx = self.query.index('WHERE')
                self.where = self.query[idx + 1:]
                self.query = self.query[:idx]
            except ValueError:
                # Raised when WHERE has not been found
                pass

        self.result = dict(
            message=[])

        # create api base path
        self.api_path = self.api_add_path(self.api, self.path)

        # api call's
        if self.add:
            self.api_add()
        elif self.remove:
            self.api_remove()
        elif self.update:
            self.api_update()
        elif self.query:
            self.api_query()
        elif self.arbitrary:
            self.api_arbitrary()
        else:
            self.api_get_all()

    def list_to_dic(self, ldict):
        return convert_list_to_dictionary(ldict, skip_empty_values=True, require_assignment=True)

    def split_params(self, params):
        if not isinstance(params, str):
            raise AssertionError('Parameters can only be a string, received %s' % type(params))
        try:
            return split_routeros_command(params)
        except ParseError as e:
            self.module.fail_json(msg=to_native(e))

    def api_add_path(self, api, path):
        api_path = api.path()
        for p in path:
            api_path = api_path.join(p)
        return api_path

    def api_get_all(self):
        try:
            for i in self.api_path:
                self.result['message'].append(i)
            self.return_result(False, True)
        except LibRouterosError as e:
            self.errors(e)

    def api_add(self):
        param = self.list_to_dic(self.split_params(self.add))
        try:
            self.result['message'].append("added: .id= %s"
                                          % self.api_path.add(**param))
            self.return_result(True)
        except LibRouterosError as e:
            self.errors(e)

    def api_remove(self):
        try:
            self.api_path.remove(self.remove)
            self.result['message'].append("removed: .id= %s" % self.remove)
            self.return_result(True)
        except LibRouterosError as e:
            self.errors(e)

    def api_update(self):
        param = self.list_to_dic(self.split_params(self.update))
        if '.id' not in param.keys():
            self.errors("missing '.id' for %s" % param)
        try:
            self.api_path.update(**param)
            self.result['message'].append("updated: %s" % param)
            self.return_result(True)
        except LibRouterosError as e:
            self.errors(e)

    def api_query(self):
        keys = {}
        for k in self.query:
            if 'id' in k and k != ".id":
                self.errors("'%s' must be '.id'" % k)
            keys[k] = Key(k)
        try:
            if self.where:
                if self.where[1] == '==':
                    select = self.api_path.select(*keys).where(keys[self.where[0]] == self.where[2])
                elif self.where[1] == '!=':
                    select = self.api_path.select(*keys).where(keys[self.where[0]] != self.where[2])
                elif self.where[1] == '>':
                    select = self.api_path.select(*keys).where(keys[self.where[0]] > self.where[2])
                elif self.where[1] == '<':
                    select = self.api_path.select(*keys).where(keys[self.where[0]] < self.where[2])
                else:
                    self.errors("'%s' is not operator for 'where'"
                                % self.where[1])
            else:
                select = self.api_path.select(*keys)
            for row in select:
                self.result['message'].append(row)
            if len(self.result['message']) < 1:
                msg = "no results for '%s 'query' %s" % (' '.join(self.path),
                                                         ' '.join(self.query))
                if self.where:
                    msg = msg + ' WHERE %s' % ' '.join(self.where)
                self.result['message'].append(msg)
            self.return_result(False)
        except LibRouterosError as e:
            self.errors(e)

    def api_arbitrary(self):
        param = {}
        self.arbitrary = self.split_params(self.arbitrary)
        arb_cmd = self.arbitrary[0]
        if len(self.arbitrary) > 1:
            param = self.list_to_dic(self.arbitrary[1:])
        try:
            arbitrary_result = self.api_path(arb_cmd, **param)
            for i in arbitrary_result:
                self.result['message'].append(i)
            self.return_result(False)
        except LibRouterosError as e:
            self.errors(e)

    def return_result(self, ch_status=False, status=True):
        if not status:
            self.module.fail_json(msg=self.result['message'])
        else:
            self.module.exit_json(changed=ch_status,
                                  msg=self.result['message'])

    def errors(self, e):
        if e.__class__.__name__ == 'TrapError':
            self.result['message'].append("%s" % e)
            self.return_result(False, False)
        self.result['message'].append("%s" % e)
        self.return_result(False, False)

    def ros_api_connect(self, username, password, host, port, use_tls, validate_certs, validate_cert_hostname, ca_path):
        # connect to routeros api
        conn_status = {"connection": {"username": username,
                                      "hostname": host,
                                      "port": port,
                                      "ssl": use_tls,
                                      "status": "Connected"}}
        try:
            if use_tls:
                if not port:
                    port = 8729
                    conn_status["connection"]["port"] = port
                ctx = ssl.create_default_context(cafile=ca_path)
                wrap_context = ctx.wrap_socket
                if not validate_certs:
                    ctx.check_hostname = False
                    ctx.verify_mode = ssl.CERT_NONE
                elif not validate_cert_hostname:
                    ctx.check_hostname = False
                else:
                    # Since librouteros doesn't pass server_hostname,
                    # we have to do this ourselves:
                    def wrap_context(*args, **kwargs):
                        kwargs.pop('server_hostname', None)
                        return ctx.wrap_socket(*args, server_hostname=host, **kwargs)
                api = connect(username=username,
                              password=password,
                              host=host,
                              ssl_wrapper=wrap_context,
                              port=port)
            else:
                if not port:
                    port = 8728
                    conn_status["connection"]["port"] = port
                api = connect(username=username,
                              password=password,
                              host=host,
                              port=port)
        except Exception as e:
            conn_status["connection"]["status"] = "error: %s" % e
            self.module.fail_json(msg=to_native([conn_status]))
        return api


def main():

    ROS_api_module()


if __name__ == '__main__':
    main()
