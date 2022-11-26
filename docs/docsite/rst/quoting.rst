..
  Copyright (c) Ansible Project
  GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
  SPDX-License-Identifier: GPL-3.0-or-later

.. _ansible_collections.community.routeros.docsite.quoting:

How to quote and unquote commands and arguments
===============================================

When using the :ref:`community.routeros.command module <ansible_collections.community.routeros.command_module>` or the :ref:`community.routeros.api module <ansible_collections.community.routeros.api_module>` modules, you need to pass text data in quoted form. While in some cases quoting is not needed (when passing IP addresses or names without spaces, for example), in other cases it is required, like when passing a comment which contains a space.

The community.routeros collection provides a set of Jinja2 filter plugins which helps you with these tasks:

- The :ref:`community.routeros.quote_argument_value filter <ansible_collections.community.routeros.quote_argument_value_filter>` quotes an argument value: ``'this is a "comment"' | community.routeros.quote_argument_value == '"this is a \\"comment\\""'``.
- The :ref:`community.routeros.quote_argument filter <ansible_collections.community.routeros.quote_argument_filter>` quotes an argument with or without a value: ``'comment=this is a "comment"' | community.routeros.quote_argument == 'comment="this is a \\"comment\\""'``.
- The :ref:`community.routeros.join filter <ansible_collections.community.routeros.join_filter>` quotes a list of arguments and joins them to one string: ``['foo=bar', 'comment=foo is bar'] | community.routeros.join == 'foo=bar comment="foo is bar"'``.
- The :ref:`community.routeros.split filter <ansible_collections.community.routeros.split_filter>` splits a command into a list of arguments (with or without values): ``'foo=bar comment="foo is bar"' | community.routeros.split == ['foo=bar', 'comment=foo is bar']``
- The :ref:`community.routeros.list_to_dict filter <ansible_collections.community.routeros.list_to_dict_filter>` splits a list of arguments with values into a dictionary: ``['foo=bar', 'comment=foo is bar'] | community.routeros.list_to_dict == {'foo': 'bar', 'comment': 'foo is bar'}``. It has two optional arguments: ``require_assignment`` (default value ``true``) allows to accept arguments without values when set to ``false``; and ``skip_empty_values`` (default value ``false``) allows to skip arguments whose value is empty.
