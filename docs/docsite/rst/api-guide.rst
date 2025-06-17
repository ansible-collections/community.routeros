..
  Copyright (c) Ansible Project
  GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
  SPDX-License-Identifier: GPL-3.0-or-later

.. _ansible_collections.community.routeros.docsite.api-guide:

How to connect to RouterOS devices with the RouterOS API
========================================================

You can use the :ansplugin:`community.routeros.api module <community.routeros.api#module>` to connect to a RouterOS device with the RouterOS API. More specific module to modify certain entries are the :ansplugin:`community.routeros.api_modify <community.routeros.api_modify#module>` and :ansplugin:`community.routeros.api_find_and_modify <community.routeros.api_find_and_modify#module>` modules. The :ansplugin:`community.routeros.api_info module <community.routeros.api_info#module>` allows to retrieve information on specific predefined paths that can be used as input for the :ansplugin:`community.routeros.api_modify <community.routeros.api_modify#module>` module, and the :ansplugin:`community.routeros.api_facts module <community.routeros.api_facts#module>` allows to retrieve Ansible facts using the RouterOS API.

No special setup is needed; the module needs to be run on a host that can connect to the device's API. The most common case is that the module is run on ``localhost``, either by using ``hosts: localhost`` in the playbook, or by using ``delegate_to: localhost`` for the task. The following example shows how to run the equivalent of ``/ip address print``:

.. code-block:: yaml+jinja

    ---
    - name: RouterOS test with API
      hosts: localhost
      gather_facts: false
      vars:
        hostname: 192.168.1.1
        username: admin
        password: test1234
      tasks:
        - name: Get "ip address print"
          community.routeros.api:
            hostname: "{{ hostname }}"
            password: "{{ password }}"
            username: "{{ username }}"
            path: "ip address"
            # The following options configure TLS/SSL.
            # Depending on your setup, these options need different values:
            tls: true
            validate_certs: true
            validate_cert_hostname: true
            # If you are using your own PKI, specify the path to your CA certificate here:
            # ca_path: /path/to/ca-certificate.pem
          register: print_path

        - name: Show IP address of first interface
          ansible.builtin.debug:
            msg: "{{ print_path.msg[0].address }}"

This results in the following output:

.. code-block:: ansible-output

    PLAY [RouterOS test] *********************************************************************************************

    TASK [Get "ip address print"] ************************************************************************************
    ok: [localhost]

    TASK [Show IP address of first interface] ************************************************************************
    ok: [localhost] => {
        "msg": "192.168.2.1/24"
    }

    PLAY RECAP *******************************************************************************************************
    localhost                  : ok=2    changed=0    unreachable=0    failed=0    skipped=0    rescued=0    ignored=0

Check out the documentation of the :ansplugin:`community.routeros.api module <community.routeros.api#module>` for details on the options.

Using the ``community.routeros.api`` module defaults group
----------------------------------------------------------

To avoid having to specify common parameters for all the API based modules in every task, you can use the ``community.routeros.api`` :ref:`module defaults group <module_defaults_groups>`:

.. code-block:: yaml+jinja

    ---
    - name: RouterOS test with API
      hosts: localhost
      gather_facts: false
      module_defaults:
        group/community.routeros.api:
          hostname: 192.168.1.1
          password: admin
          username: test1234
          # The following options configure TLS/SSL.
          # Depending on your setup, these options need different values:
          tls: true
          validate_certs: true
          validate_cert_hostname: true
          # If you are using your own PKI, specify the path to your CA certificate here:
          # ca_path: /path/to/ca-certificate.pem
      tasks:
        - name: Gather facts
          community.routeros.api_facts:

        - name: Get "ip address print"
          community.routeros.api:
            path: "ip address"

        - name: Change IP address to 192.168.1.1 for interface bridge
          community.routeros.api_find_and_modify:
            path: ip address
            find:
              interface: bridge
            values:
              address: "192.168.1.1/24"

Here all three tasks will use the options set for the module defaults group.

Setting up encryption
---------------------

It is recommended to always use :ansopt:`tls=true` when connecting with the API, even if you are only connecting to the device through a trusted network. The following options control how TLS/SSL is used:

:force_no_cert: Setting to :ansval:`true` connects to the device without a certificate. **This is discouraged to use in production and is susceptible to Man-in-the-Middle attacks**, but might be useful when setting the device up. The default value is :ansval:`false`.
:validate_certs: Setting to :ansval:`false` disables any certificate validation. **This is discouraged to use in production**, but is needed when setting the device up. The default value is :ansval:`true`.
:validate_cert_hostname: Setting to :ansval:`false` (default) disables hostname verification during certificate validation. This is needed if the hostnames specified in the certificate do not match the hostname used for connecting (usually the device's IP). It is recommended to set up the certificate correctly and set this to :ansval:`true`; the default :ansval:`false` is chosen for backwards compatibility to an older version of the module.
:ca_path: If you are not using a commercially trusted CA certificate to sign your device's certificate, or have not included your CA certificate in Python's truststore, you need to point this option to the CA certificate.

We recommend to create a CA certificate that is used to sign the certificates for your RouterOS devices, and have the certificates include the correct hostname(s), including the IP of the device. That way, you can fully enable TLS and be sure that you always talk to the correct device.

Setting up a PKI
^^^^^^^^^^^^^^^^

Please follow the instructions in the ``community.crypto`` :ref:`ansible_collections.community.crypto.docsite.guide_ownca` guide to set up a CA certificate and sign a certificate for your router. You should add a Subject Alternative Name for the IP address (for example ``IP:192.168.1.1``) and - if available - for the DNS name (for example ``DNS:router.local``) to the certificate.

Installing a certificate on a MikroTik router
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Installing the certificate is best done with the SSH connection. (See the :ref:`ansible_collections.community.routeros.docsite.ssh-guide` guide for more information.) Once the certificate has been installed, and the HTTPS API enabled, it's easier to work with the API, since it has a quite a few less problems, and returns data as JSON objects instead of text you first have to parse.

First you have to convert the certificate and its private key to a `PKCS #12 bundle <https://en.wikipedia.org/wiki/PKCS_12>`_. This can be done with the :ansplugin:`community.crypto.openssl_pkcs12 <community.crypto.openssl_pkcs12#module>`. The following playbook assumes that the certificate is available as ``keys/{{ inventory_hostname }}.pem``, and its private key is available as ``keys/{{ inventory_hostname }}.key``. It generates a random passphrase to protect the PKCS#12 file.

.. code-block:: yaml+jinja

    ---
    - name: Install certificates on devices
      hosts: routers
      gather_facts: false
      tasks:
        - block:
            - set_fact:
                random_password: "{{ lookup('community.general.random_string', length=32, override_all='0123456789abcdefghijklmnopqrstuvwxyz') }}"

            - name: Create PKCS#12 bundle
              openssl_pkcs12:
                path: keys/{{ inventory_hostname }}.p12
                certificate_path: keys/{{ inventory_hostname }}.pem
                privatekey_path: keys/{{ inventory_hostname }}.key
                friendly_name: '{{ inventory_hostname }}'
                passphrase: "{{ random_password }}"
                mode: "0600"
              changed_when: false
              delegate_to: localhost

            - name: Copy router certificate onto router
              ansible.netcommon.net_put:
                src: 'keys/{{ inventory_hostname }}.p12'
                dest: '{{ inventory_hostname }}.p12'

            - name: Install router certificate and clean up
              community.routeros.command:
                commands:
                  # Import certificate:
                  - /certificate import name={{ inventory_hostname }} file-name={{ inventory_hostname }}.p12 passphrase="{{ random_password }}"
                  # Remove PKCS12 bundle:
                  - /file remove {{ inventory_hostname }}.p12
                  # Show certificates
                  - /certificate print
              register: output

            - name: Show result of certificate import
              debug:
                var: output.stdout_lines[0]

            - name: Show certificates
              debug:
                var: output.stdout_lines[2]

          always:
            - name: Wipe PKCS12 bundle
              command: wipe keys/{{ inventory_hostname }}.p12
              changed_when: false
              delegate_to: localhost

        - name: Use certificate
          community.routeros.command:
            commands:
              - /ip service set www-ssl address={{ admin_network }} certificate={{ inventory_hostname }} disabled=no tls-version=only-1.2
              - /ip service set api-ssl address={{ admin_network }} certificate={{ inventory_hostname }} tls-version=only-1.2

The playbook also assumes that ``admin_network`` describes the network from which the HTTPS and API interface can be accessed. This can be for example ``192.168.1.0/24``.

When this playbook completed successfully, you should be able to use the HTTPS admin interface (reachable in a browser from ``https://192.168.1.1/``, with the correct IP inserted), as well as the :ansplugin:`community.routeros.api module <community.routeros.api#module>` module with TLS and certificate validation enabled:

.. code-block:: yaml+jinja

    - community.routeros.api:
        # ...
        tls: true
        validate_certs: true
        validate_cert_hostname: true
        ca_path: /path/to/ca-certificate.pem
