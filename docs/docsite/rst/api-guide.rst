.. _ansible_collections.community.routeros.docsite.api-guide:

How to connect to RouterOS devices with the RouterOS API
========================================================

You can use the :ref:`community.routeros.api module <ansible_collections.community.routeros.api_module>` to connect to a RouterOS device with the RouterOS API.

No special setup is needed; the module needs to be run on a host that can connect to the device's API. The most common case is that the module is run on ``localhost``, either by using ``hosts: localhost`` in the playbook, or by using ``delegate_to: localhost`` for the task. The following example shows how to run the equivalent of ``/ip address print``:

.. code-block:: yaml+jinja

    ---
    - name: RouterOS test with API
      hosts: localhost
      gather_facts: no
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
      debug:
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

Check out the documenation of the :ref:`community.routeros.api module <ansible_collections.community.routeros.api_module>` for details on the options.

Setting up encryption
---------------------

It is recommended to always use ``tls: true`` when connecting with the API, even if you are only connecting to the device through a trusted network. The following options control how TLS/SSL is used:

:validate_certs: Setting to ``false`` disables any certificate validation. **This is discouraged to use in production**, but is needed when setting the device up. The default value is ``true``.
:validate_cert_hostname: Setting to ``false`` (default) disables hostname verification during certificate validation. This is needed if the hostnames specified in the certificate do not match the hostname used for connecting (usually the device's IP). It is recommended to set up the certificate correctly and set this to ``true``; the default ``false`` is chosen for backwards compatibility to an older version of the module.
:ca_path: If you are not using a commerically trusted CA certificate to sign your device's certificate, or have not included your CA certificate in Python's truststore, you need to point this option to the CA certificate.

We recommend to create a CA certificate that is used to sign the certificates for your RouterOS devices, and have the certificates include the correct hostname(s), including the IP of the device. That way, you can fully enable TLS and be sure that you always talk to the correct device.
