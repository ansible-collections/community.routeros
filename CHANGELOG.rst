================================
Community RouterOS Release Notes
================================

.. contents:: Topics


v0.1.0
======

Release Summary
---------------

The ``community.routeros`` continues the work on the Ansible RouterOS modules from their state in ``community.network`` 1.2.0. The changes listed here are thus relative to the modules ``community.network.routeros_*``.


Minor Changes
-------------

- facts - now also collecting data about BGP and OSPF (https://github.com/ansible-collections/community.network/pull/101).
- facts - set configuration export on to verbose, for full configuration export (https://github.com/ansible-collections/community.network/pull/104).
