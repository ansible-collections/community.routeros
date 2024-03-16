================================
Community RouterOS Release Notes
================================

.. contents:: Topics

v1.2.2
======

Release Summary
---------------

End of Life release.

The 1.x.y release train of the community.routeros collection is now End of Life.
There will be no more 1.x.y releases. Please upgrade to community.routeros 2.x.y.
Thanks to all contributors to the 1.x.y releases!

v1.2.1
======

Release Summary
---------------

Bugfix maintenance release.

Bugfixes
--------

- query - fix query function check for ``.id`` vs. ``id`` arguments to not conflict with routeros arguments like ``identity`` (https://github.com/ansible-collections/community.routeros/pull/68, https://github.com/ansible-collections/community.routeros/issues/67).
- routeros cliconf plugin - adjust function signature that was modified in Ansible after creation of this plugin (https://github.com/ansible-collections/community.routeros/pull/43).

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
