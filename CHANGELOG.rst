================================
Community RouterOS Release Notes
================================

.. contents:: Topics


v2.0.0-a1
=========

Release Summary
---------------

First prerelease for a new major release with a breaking change in the behavior of ``community.routeros.api``.

Breaking Changes / Porting Guide
--------------------------------

- api - due to a programming error, the module never failed on errors. This has now been fixed. If you are relying on the module not failing in case of idempotent commands (resulting in errors like ``failure: already have such address``), you need to adjust your roles/playbooks. We suggest to use ``failed_when`` to accept failure in specific circumstances, for example ``failed_when: "'failure: already have ' in result.msg[0]"`` (https://github.com/ansible-collections/community.routeros/pull/39).

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
