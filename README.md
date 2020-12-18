# Community RouterOS Collection
[![CI](https://github.com/ansible-collections/community.routeros/workflows/CI/badge.svg?event=push)](https://github.com/ansible-collections/community.routeros/actions) [![Codecov](https://img.shields.io/codecov/c/github/ansible-collections/community.routeros)](https://codecov.io/gh/ansible-collections/community.routeros)

Provides modules for [Ansible](https://www.ansible.com/community) to manage [MikroTik RouterOS](http://www.mikrotik-routeros.net/routeros.aspx) instances.

You can find [documentation for the modules and plugins in this collection here](https://ansible.fontein.de/collections/community/routeros/).

## Tested with Ansible

Tested with both the current Ansible 2.9 and 2.10 releases and the current development version of Ansible. Ansible versions before 2.9.10 are not supported.

## External requirements

The exact requirements for every module are listed in the module documentation. 

### Supported connections

The collection supports the `network_cli` connection.

## Included content

- `community.routeros.api`
- `community.routeros.command`
- `community.routeros.facts`

You can find [documentation for the modules and plugins in this collection here](https://ansible.fontein.de/collections/community/routeros/).

## Using this collection

See [Ansible Using collections](https://docs.ansible.com/ansible/latest/user_guide/collections_using.html) for general detail on using collections.

There are two approaches for using this collection. The `command` and `facts` modules use the `network_cli` connection and connect with SSH. The `api` module connects with the HTTP/HTTPS API.

### Prerequisites

The terminal-based modules in this collection (`community.routeros.command` and `community.routeros.facts`) do not support arbitrary symbols in router's identity. If you are having trouble connecting to your device, please make sure that your MikroTik's identity contains only alphanumeric characters and dashes. Also, the `community.routeros.command` module does not support nesting commands and expects every command to start with a forward slash (`/`). Running the following command will produce an error.

```yaml
- community.routeros.command:
    commands:
      - /ip
      - print
```

### Connecting with `network_cli`

Example inventory `hosts` file:

```.ini
[routers]
router ansible_host=192.168.1.1

[routers:vars]
ansible_connection=ansible.netcommon.network_cli
ansible_network_os=community.routeros.routeros
ansible_user=admin
ansible_ssh_pass=test1234
```

Example playbook:

```.yaml
---
- name: RouterOS test with network_cli connection
  hosts: routers
  gather_facts: false
  tasks:

  # Run a command and print its output
  - community.routeros.command:
      commands:
        - /system resource print
    register: system_resource_print
  - debug:
      var: system_resource_print.stdout_lines

  # Retrieve facts
  - community.routeros.facts:
  - debug:
      msg: "First IP address: {{ ansible_net_all_ipv4_addresses[0] }}"
```

### Connecting with HTTP/HTTPS API

Example playbook:

```.yaml
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
```

## Contributing to this collection

We're following the general Ansible contributor guidelines; see [Ansible Community Guide](https://docs.ansible.com/ansible/latest/community/index.html).

If you want to clone this repositority (or a fork of it) to improve it, you can proceed as follows:
1. Create a directory `ansible_collections/community`;
2. In there, checkout this repository (or a fork) as `routeros`;
3. Add the directory containing `ansible_collections` to your [ANSIBLE_COLLECTIONS_PATH](https://docs.ansible.com/ansible/latest/reference_appendices/config.html#collections-paths).

See [Ansible's dev guide](https://docs.ansible.com/ansible/devel/dev_guide/developing_collections.html#contributing-to-collections) for more information.

## Release notes

See the [changelog](https://github.com/ansible-collections/community.routeros/blob/main/CHANGELOG.rst).

## Roadmap

We plan to regularly release minor and patch versions, whenever new features are added or bugs fixed. Our collection follows [semantic versioning](https://semver.org/), so breaking changes will only happen in major releases.

## More information

- [Ansible Collection overview](https://github.com/ansible-collections/overview)
- [Ansible User guide](https://docs.ansible.com/ansible/latest/user_guide/index.html)
- [Ansible Developer guide](https://docs.ansible.com/ansible/latest/dev_guide/index.html)
- [Ansible Collections Checklist](https://github.com/ansible-collections/overview/blob/master/collection_requirements.rst)
- [Ansible Community code of conduct](https://docs.ansible.com/ansible/latest/community/code_of_conduct.html)
- [The Bullhorn (the Ansible Contributor newsletter)](https://us19.campaign-archive.com/home/?u=56d874e027110e35dea0e03c1&id=d6635f5420)
- [Changes impacting Contributors](https://github.com/ansible-collections/overview/issues/45)

## Licensing

GNU General Public License v3.0 or later.

See [COPYING](https://www.gnu.org/licenses/gpl-3.0.txt) to see the full text.
