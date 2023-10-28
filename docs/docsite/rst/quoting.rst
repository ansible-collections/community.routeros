..
  Copyright (c) Ansible Project
  GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
  SPDX-License-Identifier: GPL-3.0-or-later

.. _ansible_collections.community.routeros.docsite.quoting:

How to quote and unquote commands and arguments
===============================================

When using the :ansplugin:`community.routeros.command module <community.routeros.command#module>` or the :ansplugin:`community.routeros.api module <community.routeros.api#module>` modules, you need to pass text data in quoted form. While in some cases quoting is not needed (when passing IP addresses or names without spaces, for example), in other cases it is required, like when passing a comment which contains a space.

The community.routeros collection provides a set of Jinja2 filter plugins which helps you with these tasks:

- The :ansplugin:`community.routeros.quote_argument_value filter <community.routeros.quote_argument_value#filter>` quotes an argument value: ``'this is a "comment"' | community.routeros.quote_argument_value == '"this is a \\"comment\\""'``.
- The :ansplugin:`community.routeros.quote_argument filter <community.routeros.quote_argument#filter>` quotes an argument with or without a value: ``'comment=this is a "comment"' | community.routeros.quote_argument == 'comment="this is a \\"comment\\""'``.
- The :ansplugin:`community.routeros.join filter <community.routeros.join#filter>` quotes a list of arguments and joins them to one string: ``['foo=bar', 'comment=foo is bar'] | community.routeros.join == 'foo=bar comment="foo is bar"'``.
- The :ansplugin:`community.routeros.split filter <community.routeros.split#filter>` splits a command into a list of arguments (with or without values): ``'foo=bar comment="foo is bar"' | community.routeros.split == ['foo=bar', 'comment=foo is bar']``
- The :ansplugin:`community.routeros.list_to_dict filter <community.routeros.list_to_dict#filter>` splits a list of arguments with values into a dictionary: ``['foo=bar', 'comment=foo is bar'] | community.routeros.list_to_dict == {'foo': 'bar', 'comment': 'foo is bar'}``. It has two optional arguments: :ansopt:`community.routeros.list_to_dict#filter:require_assignment` (default value :ansval:`true`) allows to accept arguments without values when set to :ansval:`false`; and :ansopt:`community.routeros.list_to_dict#filter:skip_empty_values` (default value :ansval:`false`) allows to skip arguments whose value is empty.
