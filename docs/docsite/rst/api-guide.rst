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
            ssl: true
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
