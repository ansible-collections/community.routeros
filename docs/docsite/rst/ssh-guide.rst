..
  Copyright (c) Ansible Project
  GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
  SPDX-License-Identifier: GPL-3.0-or-later

.. _ansible_collections.community.routeros.docsite.ssh-guide:

How to connect to RouterOS devices with SSH
===========================================

The collection offers two modules to connect to RouterOS devies with SSH:

- The :ansplugin:`community.routeros.facts module <community.routeros.facts#module>` gathers facts about a RouterOS device;
- The :ansplugin:`community.routeros.command module <community.routeros.command#module>` executes commands on a RouterOS device.

The modules need the :ansplugin:`ansible.netcommon.network_cli connection plugin <ansible.netcommon.network_cli#connection>` for this.

Important notes
---------------

1. The SSH-based modules do not support arbitrary symbols in the router's identity. If you are having trouble connecting to your device, please make sure that your MikroTik's identity contains only alphanumeric characters and dashes. Also make sure that the identity string is not longer than 19 characters (`see issue for details <https://github.com/ansible-collections/community.routeros/issues/31>`__). Similar problems can happen for unsupported characters in your username.

2. The :ansplugin:`community.routeros.command module <community.routeros.command#module>` does not support nesting commands and expects every command to start with a forward slash (``/``). Running the following command will produce an error:

   .. code-block:: yaml+jinja

       - community.routeros.command:
           commands:
             - /ip
             - print

3. When using the :ansplugin:`community.routeros.command module <community.routeros.command#module>` module, make sure to not specify too long commands. Alternatively, add something like ``+cet512w`` to the username (replace ``admin`` with ``admin+cet512w``) to tell RouterOS to not wrap before 512 characters in a line (`see issue for details <https://github.com/ansible-collections/community.routeros/issues/6>`__).

4. The :ansplugin:`ansible.netcommon.network_cli connection plugin <ansible.netcommon.network_cli#connection>` uses `paramiko <https://pypi.org/project/paramiko/>`_ by default to connect to devices with SSH. You can set its :ansopt:`ansible.netcommon.network_cli#connection:ssh_type` option to :ansval:`libssh` to use `ansible-pylibssh <https://pypi.org/project/ansible-pylibssh/>`_ instead, which offers Python bindings to libssh. See its documentation for details.

5. User is **not allowed** to login via SSH by password to modern Mikrotik if SSH key for the user is added!

Setting up an inventory
-----------------------

An example inventory ``hosts`` file for a RouterOS device is as follows:

.. code-block:: ini

    [routers]
    router ansible_host=192.168.2.1

    [routers:vars]
    ansible_connection=ansible.netcommon.network_cli
    ansible_network_os=community.routeros.routeros
    ansible_user=admin
    ansible_ssh_pass=test1234

This tells Ansible that you have a RouterOS device called ``router`` with IP ``192.168.2.1``. Ansible should use the :ansplugin:`ansible.netcommon.network_cli connection plugin <ansible.netcommon.network_cli#connection>` together with the the :ansplugin:`community.routeros.routeros cliconf plugin <community.routeros.routeros#cliconf>`. The credentials are stored as ``ansible_user`` and ``ansible_ssh_pass`` in the inventory.

Connecting to the device
------------------------

With the above inventory, you can use the following playbook to execute ``/system resource print`` on the device

.. code-block:: yaml+jinja

    ---
    - name: RouterOS test with network_cli connection
      hosts: routers
      gather_facts: false
      tasks:

        - name: Gather system resources
          community.routeros.command:
            commands:
              - /system resource print
          register: system_resource_print

        - name: Show system resources
          debug:
            var: system_resource_print.stdout_lines

        - name: Gather facts
          community.routeros.facts:

        - name: Show a fact
          debug:
            msg: "First IP address: {{ ansible_net_all_ipv4_addresses[0] }}"

This results in the following output:

.. code-block:: ansible-output

    PLAY [RouterOS test with network_cli connection] *****************************************************************

    TASK [Gather system resources] ***********************************************************************************
    ok: [router]

    TASK [Show system resources] *************************************************************************************
    ok: [router] => {
        "system_resource_print.stdout_lines": [
            [
                "uptime: 3d10h28m51s",
                "                  version: 6.48.3 (stable)",
                "               build-time: May/25/2021 06:09:45",
                "              free-memory: 31.2MiB",
                "             total-memory: 64.0MiB",
                "                      cpu: MIPS 24Kc V7.4",
                "                cpu-count: 1",
                "            cpu-frequency: 400MHz",
                "                 cpu-load: 1%",
                "           free-hdd-space: 54.2MiB",
                "          total-hdd-space: 128.0MiB",
                "  write-sect-since-reboot: 927",
                "         write-sect-total: 51572981",
                "               bad-blocks: 1%",
                "        architecture-name: mipsbe",
                "               board-name: RB750GL",
                "                 platform: MikroTik"
            ]
        ]
    }

    TASK [Gather facts] **********************************************************************************************
    ok: [router]

    TASK [Show a fact] ***********************************************************************************************
    ok: [router] => {
        "msg": "First IP address: 192.168.2.1"
    }

    PLAY RECAP *******************************************************************************************************
    router                     : ok=4    changed=0    unreachable=0    failed=0    skipped=0    rescued=0    ignored=0
