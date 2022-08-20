================================
Community RouterOS Release Notes
================================

.. contents:: Topics


v2.2.1
======

Release Summary
---------------

Bugfix release.

Bugfixes
--------

- api_modify, api_info - make API path ``ip dhcp-server lease`` support ``server=all`` (https://github.com/ansible-collections/community.routeros/issues/104, https://github.com/ansible-collections/community.routeros/pull/107).
- api_modify, api_info - make API path ``ip dhcp-server network`` support missing options ``boot-file-name``, ``dhcp-option-set``, ``dns-none``, ``domain``, and ``next-server`` (https://github.com/ansible-collections/community.routeros/issues/104, https://github.com/ansible-collections/community.routeros/pull/106).

v2.2.0
======

Release Summary
---------------

New feature release.

Minor Changes
-------------

- All software licenses are now in the ``LICENSES/`` directory of the collection root. Moreover, ``SPDX-License-Identifier:`` is used to declare the applicable license for every file that is not automatically generated (https://github.com/ansible-collections/community.routeros/pull/101).

Bugfixes
--------

- Include ``LICENSES/BSD-2-Clause.txt`` file for the ``routeros`` module utils (https://github.com/ansible-collections/community.routeros/pull/101).

New Modules
-----------

- api_info - Retrieve information from API
- api_modify - Modify data at paths with API

v2.1.0
======

Release Summary
---------------

Feature and bugfix release with new modules.

Minor Changes
-------------

- Added a ``community.routeros.api`` module defaults group. Use with ``group/community.routeros.api`` to provide options for all API-based modules (https://github.com/ansible-collections/community.routeros/pull/89).
- Prepare collection for inclusion in an Execution Environment by declaring its dependencies (https://github.com/ansible-collections/community.routeros/pull/83).
- api - add new option ``extended query`` more complex queries against RouterOS API (https://github.com/ansible-collections/community.routeros/pull/63).
- api - update ``query`` to accept symbolic parameters (https://github.com/ansible-collections/community.routeros/pull/63).
- api* modules - allow to set an encoding other than the default ASCII for communicating with the API (https://github.com/ansible-collections/community.routeros/pull/95).

Bugfixes
--------

- query - fix query function check for ``.id`` vs. ``id`` arguments to not conflict with routeros arguments like ``identity`` (https://github.com/ansible-collections/community.routeros/pull/68, https://github.com/ansible-collections/community.routeros/issues/67).
- quoting and unquoting filter plugins, api module - handle the escape sequence ``\_`` correctly as escaping a space and not an underscore (https://github.com/ansible-collections/community.routeros/pull/89).

New Modules
-----------

- api_facts - Collect facts from remote devices running MikroTik RouterOS using the API
- api_find_and_modify - Find and modify information using the API

v2.0.0
======

Release Summary
---------------

A new major release with breaking changes in the behavior of ``community.routeros.api`` and ``community.routeros.command``.

Minor Changes
-------------

- api - make validation of ``WHERE`` for ``query`` more strict (https://github.com/ansible-collections/community.routeros/pull/53).
- command - the ``commands`` and ``wait_for`` options now convert the list elements to strings (https://github.com/ansible-collections/community.routeros/pull/55).
- facts - the ``gather_subset`` option now converts the list elements to strings (https://github.com/ansible-collections/community.routeros/pull/55).

Breaking Changes / Porting Guide
--------------------------------

- api - due to a programming error, the module never failed on errors. This has now been fixed. If you are relying on the module not failing in case of idempotent commands (resulting in errors like ``failure: already have such address``), you need to adjust your roles/playbooks. We suggest to use ``failed_when`` to accept failure in specific circumstances, for example ``failed_when: "'failure: already have ' in result.msg[0]"`` (https://github.com/ansible-collections/community.routeros/pull/39).
- api - splitting commands no longer uses a naive split by whitespace, but a more RouterOS CLI compatible splitting algorithm (https://github.com/ansible-collections/community.routeros/pull/45).
- command - the module now always indicates that a change happens. If this is not correct, please use ``changed_when`` to determine the correct changed status for a task (https://github.com/ansible-collections/community.routeros/pull/50).

Bugfixes
--------

- api - improve splitting of ``WHERE`` queries (https://github.com/ansible-collections/community.routeros/pull/47).
- api - when converting result lists to dictionaries, no longer removes second ``=`` and text following that if present (https://github.com/ansible-collections/community.routeros/pull/47).
- routeros cliconf plugin - adjust function signature that was modified in Ansible after creation of this plugin (https://github.com/ansible-collections/community.routeros/pull/43).

New Plugins
-----------

Filter
~~~~~~

- join - Join a list of arguments to a command
- list_to_dict - Convert a list of arguments to a list of dictionary
- quote_argument - Quote an argument
- quote_argument_value - Quote an argument value
- split - Split a command into arguments

v1.2.0
======

Release Summary
---------------

Bugfix and feature release.

Minor Changes
-------------

- Avoid internal ansible-core module_utils in favor of equivalent public API available since at least Ansible 2.9 (https://github.com/ansible-collections/community.routeros/pull/38).
- api - add options ``validate_certs`` (default value ``true``), ``validate_cert_hostname`` (default value ``false``), and ``ca_path`` to control certificate validation (https://github.com/ansible-collections/community.routeros/pull/37).
- api - rename option ``ssl`` to ``tls``, and keep the old name as an alias (https://github.com/ansible-collections/community.routeros/pull/37).
- fact - add fact ``ansible_net_config_nonverbose`` to get idempotent config (no date, no verbose) (https://github.com/ansible-collections/community.routeros/pull/23).

Bugfixes
--------

- api - when using TLS/SSL, remove explicit cipher configuration to insecure values, which also makes it impossible to connect to newer RouterOS versions (https://github.com/ansible-collections/community.routeros/pull/34).

v1.1.0
======

Release Summary
---------------

This release allow dashes in usernames for SSH-based modules.

Minor Changes
-------------

- command - added support for a dash (``-``) in username (https://github.com/ansible-collections/community.routeros/pull/18).
- facts - added support for a dash (``-``) in username (https://github.com/ansible-collections/community.routeros/pull/18).

v1.0.1
======

Release Summary
---------------

Maintenance release with a bugfix for ``api``.

Bugfixes
--------

- api - remove ``id to .id`` as default requirement which conflicts with RouterOS ``id`` configuration parameter (https://github.com/ansible-collections/community.routeros/pull/15).

v1.0.0
======

Release Summary
---------------

This is the first production (non-prerelease) release of ``community.routeros``.


Bugfixes
--------

- routeros terminal plugin - allow slashes in hostnames for terminal detection. Without this, slashes in hostnames will result in connection timeouts (https://github.com/ansible-collections/community.network/pull/138).

v0.1.1
======

Release Summary
---------------

Small improvements and bugfixes over the initial release.

Bugfixes
--------

- api - fix crash when the ``ssl`` parameter is used (https://github.com/ansible-collections/community.routeros/pull/3).

v0.1.0
======

Release Summary
---------------

The ``community.routeros`` continues the work on the Ansible RouterOS modules from their state in ``community.network`` 1.2.0. The changes listed here are thus relative to the modules ``community.network.routeros_*``.


Minor Changes
-------------

- facts - now also collecting data about BGP and OSPF (https://github.com/ansible-collections/community.network/pull/101).
- facts - set configuration export on to verbose, for full configuration export (https://github.com/ansible-collections/community.network/pull/104).
