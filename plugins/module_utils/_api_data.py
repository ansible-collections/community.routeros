# -*- coding: utf-8 -*-
# Copyright (c) 2022, Felix Fontein (@felixfontein) <felix@fontein.de>
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

# The data inside here is private to this collection. If you use this from outside the collection,
# you are on your own. There can be random changes to its format even in bugfix releases!

from __future__ import absolute_import, division, print_function
__metaclass__ = type

from ansible_collections.community.routeros.plugins.module_utils.version import LooseVersion


def _compare(a, b, comparator):
    if comparator == '==':
        return a == b
    if comparator == '!=':
        return a != b
    if comparator == '<':
        return a < b
    if comparator == '<=':
        return a <= b
    if comparator == '>':
        return a > b
    if comparator == '>=':
        return a >= b
    raise ValueError('Unknown comparator "{comparator}"'.format(comparator=comparator))


class APIData(object):
    def __init__(self,
                 unversioned=None,
                 versioned=None):
        if (unversioned is None) == (versioned is None):
            raise ValueError('either unversioned or versioned must be provided')
        self.unversioned = unversioned
        self.versioned = versioned
        if self.unversioned is not None:
            self.needs_version = self.unversioned.needs_version
            self.fully_understood = self.unversioned.fully_understood
            self.has_identifier = self.unversioned.has_identifier
        else:
            self.needs_version = self.versioned is not None
            # Mark as 'fully understood' if it is for at least one version
            self.fully_understood = False
            for dummy, dummy, unversioned in self.versioned:
                if unversioned and not isinstance(unversioned, str) and unversioned.fully_understood:
                    self.fully_understood = True
                    break
            # Mark as 'has_identifier' if it is for at least one version
            self.has_identifier = False
            for dummy, dummy, unversioned in self.versioned:
                if unversioned and not isinstance(unversioned, str) and unversioned.has_identifier:
                    self.has_identifier = True
                    break
        self._current = None if self.needs_version else self.unversioned

    def _select(self, data, api_version):
        if data is None:
            self._current = None
            return False, None
        if isinstance(data, str):
            self._current = None
            return False, data
        self._current = data.specialize_for_version(api_version)
        return self._current.fully_understood, None

    def provide_version(self, version):
        if not self.needs_version:
            return self.unversioned.fully_understood, None
        api_version = LooseVersion(version)
        if self.unversioned is not None:
            self._current = self.unversioned.specialize_for_version(api_version)
            return self._current.fully_understood, None
        for other_version, comparator, data in self.versioned:
            if other_version == '*' and comparator == '*':
                return self._select(data, api_version)
            other_api_version = LooseVersion(other_version)
            if _compare(api_version, other_api_version, comparator):
                return self._select(data, api_version)
        self._current = None
        return False, None

    def get_data(self):
        if self._current is None:
            raise ValueError('either provide_version() was not called or it returned False')
        return self._current


class VersionedAPIData(object):
    def __init__(self,
                 primary_keys=None,
                 stratify_keys=None,
                 required_one_of=None,
                 mutually_exclusive=None,
                 has_identifier=False,
                 single_value=False,
                 unknown_mechanism=False,
                 fully_understood=False,
                 fixed_entries=False,
                 fields=None,
                 versioned_fields=None):
        if sum([primary_keys is not None, stratify_keys is not None, has_identifier, single_value, unknown_mechanism]) > 1:
            raise ValueError('primary_keys, stratify_keys, has_identifier, single_value, and unknown_mechanism are mutually exclusive')
        if unknown_mechanism and fully_understood:
            raise ValueError('unknown_mechanism and fully_understood cannot be combined')
        self.primary_keys = primary_keys
        self.stratify_keys = stratify_keys
        self.required_one_of = required_one_of or []
        self.mutually_exclusive = mutually_exclusive or []
        self.has_identifier = has_identifier
        self.single_value = single_value
        self.unknown_mechanism = unknown_mechanism
        self.fully_understood = fully_understood
        if single_value:
            fixed_entries = False
        self.fixed_entries = fixed_entries
        if fixed_entries and primary_keys is None:
            raise ValueError('fixed_entries can only be used with primary_keys')
        if fields is None:
            raise ValueError('fields must be provided')
        self.fields = fields
        if versioned_fields is not None:
            if not isinstance(versioned_fields, list):
                raise ValueError('unversioned_fields must be a list')
            for conditions, name, field in versioned_fields:
                if not isinstance(conditions, (tuple, list)):
                    raise ValueError('conditions must be a list or tuple')
                if not isinstance(field, KeyInfo):
                    raise ValueError('field must be a KeyInfo object')
                if name in fields:
                    raise ValueError('"{name}" appears both in fields and versioned_fields'.format(name=name))
        self.versioned_fields = versioned_fields or []
        if primary_keys:
            for pk in primary_keys:
                if pk not in fields:
                    raise ValueError('Primary key {pk} must be in fields!'.format(pk=pk))
        if stratify_keys:
            for sk in stratify_keys:
                if sk not in fields:
                    raise ValueError('Stratify key {sk} must be in fields!'.format(sk=sk))
        if required_one_of:
            for index, require_list in enumerate(required_one_of):
                if not isinstance(require_list, list):
                    raise ValueError('Require one of element at index #{index} must be a list!'.format(index=index + 1))
                for rk in require_list:
                    if rk not in fields:
                        raise ValueError('Require one of key {rk} must be in fields!'.format(rk=rk))
        if mutually_exclusive:
            for index, exclusive_list in enumerate(mutually_exclusive):
                if not isinstance(exclusive_list, list):
                    raise ValueError('Mutually exclusive element at index #{index} must be a list!'.format(index=index + 1))
                for ek in exclusive_list:
                    if ek not in fields:
                        raise ValueError('Mutually exclusive key {ek} must be in fields!'.format(ek=ek))
        self.needs_version = len(self.versioned_fields) > 0

    def specialize_for_version(self, api_version):
        fields = self.fields.copy()
        for conditions, name, field in self.versioned_fields:
            matching = True
            for other_version, comparator in conditions:
                other_api_version = LooseVersion(other_version)
                if not _compare(api_version, other_api_version, comparator):
                    matching = False
                    break
            if matching:
                if name in fields:
                    raise ValueError(
                        'Internal error: field "{field}" already exists for {version}'.format(field=name, version=api_version)
                    )
                fields[name] = field
        return VersionedAPIData(
            primary_keys=self.primary_keys,
            stratify_keys=self.stratify_keys,
            required_one_of=self.required_one_of,
            mutually_exclusive=self.mutually_exclusive,
            has_identifier=self.has_identifier,
            single_value=self.single_value,
            unknown_mechanism=self.unknown_mechanism,
            fully_understood=self.fully_understood,
            fixed_entries=self.fixed_entries,
            fields=fields,
        )


class KeyInfo(object):
    def __init__(self,
                 _dummy=None,
                 can_disable=False,
                 remove_value=None,
                 absent_value=None,
                 default=None,
                 required=False,
                 automatically_computed_from=None,
                 read_only=False,
                 write_only=False):
        if _dummy is not None:
            raise ValueError('KeyInfo() does not have positional arguments')
        if sum([required, default is not None or can_disable, automatically_computed_from is not None]) > 1:
            raise ValueError(
                'required, default, automatically_computed_from, and can_disable are mutually exclusive '
                'besides default and can_disable which can be set together')
        if not can_disable and remove_value is not None:
            raise ValueError('remove_value can only be specified if can_disable=True')
        if absent_value is not None and any([default is not None, automatically_computed_from is not None, can_disable]):
            raise ValueError('absent_value can not be combined with default, automatically_computed_from, can_disable=True, or absent_value')
        if read_only and write_only:
            raise ValueError('read_only and write_only cannot be used at the same time')
        if read_only and any([can_disable, remove_value is not None, absent_value is not None, default is not None, required]):
            raise ValueError('read_only can not be combined with can_disable, remove_value, absent_value, default, or required')
        self.can_disable = can_disable
        self.remove_value = remove_value
        self.automatically_computed_from = automatically_computed_from
        self.default = default
        self.required = required
        self.absent_value = absent_value
        self.read_only = read_only
        self.write_only = write_only


def split_path(path):
    return path.split()


def join_path(path):
    return ' '.join(path)


# How to obtain this information:
# 1. Run `/export verbose` in the CLI;
# 2. All attributes listed there go into the `fields` list;
#    attributes which can have a `!` ahead should have `canDisable=True`
# 3. All bold attributes go into the `primary_keys` list -- this is not always true!

PATHS = {
    ('app',): APIData(
        versioned=[
            ('7.21', '>=', VersionedAPIData(
                fully_understood=True,
                has_identifier=True,
                # fixed_entries=True,
                # primary_keys=('numbers',),
                fields={
                    'auto-update': KeyInfo(),
                    'disabled': KeyInfo(),
                    'environment': KeyInfo(),
                    'extra-mounts': KeyInfo(),
                    'firewall-redirects': KeyInfo(),
                    'hw-device-access': KeyInfo(),
                    'network': KeyInfo(),
                    'numbers': KeyInfo(),
                    'required-mounts': KeyInfo(),
                },
            )),
        ],
    ),

    ('app', 'settings'): APIData(
        versioned=[
            ('7.21', '>=', VersionedAPIData(
                fixed_entries=True,
                single_value=True,
                fully_understood=True,
                fields={
                    'auto-update': KeyInfo(),
                    'disk': KeyInfo(),
                    'download-path': KeyInfo(),
                    'lan-bridge': KeyInfo(),
                    'media-path': KeyInfo(),
                    'registry-mirrors': KeyInfo(),
                    'router-ip': KeyInfo(),
                    'show-in-webfig': KeyInfo(),
                },
            )),
        ],
    ),

    ('caps-man', 'aaa'): APIData(
        unversioned=VersionedAPIData(
            fixed_entries=True,
            single_value=True,
            fully_understood=True,
            fields={
                'called-format': KeyInfo(default='mac:ssid'),
                'interim-update': KeyInfo(default='disabled'),
                'mac-caching': KeyInfo(default='disabled'),
                'mac-format': KeyInfo(default='XX:XX:XX:XX:XX:XX'),
                'mac-mode': KeyInfo(default='as-username'),
            },
        ),
    ),

    ('caps-man', 'access-list'): APIData(
        unversioned=VersionedAPIData(
            fully_understood=True,
            # versioned_fields=[
            #     ([('7.15', '>=')], 'copy-from', KeyInfo(write_only=True)),
            #     ([('7.15', '>=')], 'place-before', KeyInfo(write_only=True)),
            # ],
            fields={
                'action': KeyInfo(can_disable=True),
                'allow-signal-out-of-range': KeyInfo(can_disable=True),
                'ap-tx-limit': KeyInfo(can_disable=True),
                'client-to-client-forwarding': KeyInfo(can_disable=True),
                'client-tx-limit': KeyInfo(can_disable=True),
                'comment': KeyInfo(can_disable=True, remove_value=''),
                'disabled': KeyInfo(default=False),
                'interface': KeyInfo(can_disable=True),
                'mac-address': KeyInfo(can_disable=True),
                'mac-address-mask': KeyInfo(can_disable=True),
                'private-passphrase': KeyInfo(can_disable=True),
                'radius-accounting': KeyInfo(can_disable=True),
                'signal-range': KeyInfo(can_disable=True),
                'ssid-regexp': KeyInfo(),
                'time': KeyInfo(can_disable=True),
                'vlan-id': KeyInfo(can_disable=True),
                'vlan-mode': KeyInfo(can_disable=True),
            },
        ),
    ),

    ('caps-man', 'actual-interface-configuration'): APIData(
        versioned=[
            ('7.15', '>=', VersionedAPIData(
                fully_understood=True,
                has_identifier=True,
                # fixed_entries=True,
                # primary_keys=('numbers',),
                fields={
                    'arp': KeyInfo(),
                    'arp-timeout': KeyInfo(),
                    'channel.band': KeyInfo(),
                    'channel.control-channel-width': KeyInfo(),
                    'channel.extension-channel': KeyInfo(),
                    'channel.frequency': KeyInfo(),
                    'channel.reselect-interval': KeyInfo(),
                    'channel.save-selected': KeyInfo(),
                    'channel.secondary-frequency': KeyInfo(),
                    'channel.skip-dfs-channels': KeyInfo(),
                    'channel.tx-power': KeyInfo(),
                    'comment': KeyInfo(),
                    'configuration.country': KeyInfo(),
                    'configuration.disconnect-timeout': KeyInfo(),
                    'configuration.distance': KeyInfo(),
                    'configuration.frame-lifetime': KeyInfo(),
                    'configuration.guard-interval': KeyInfo(),
                    'configuration.hide-ssid': KeyInfo(),
                    'configuration.hw-protection-mode': KeyInfo(),
                    'configuration.hw-retries': KeyInfo(),
                    'configuration.installation': KeyInfo(),
                    'configuration.keepalive-frames': KeyInfo(),
                    'configuration.load-balancing-group': KeyInfo(),
                    'configuration.max-sta-count': KeyInfo(),
                    'configuration.mode': KeyInfo(),
                    'configuration.multicast-helper': KeyInfo(),
                    'configuration.rx-chains': KeyInfo(),
                    'configuration.ssid': KeyInfo(),
                    'configuration.tx-chains': KeyInfo(),
                    'datapath.bridge': KeyInfo(),
                    'datapath.bridge-cost': KeyInfo(),
                    'datapath.bridge-horizon': KeyInfo(),
                    'datapath.client-to-client-forwarding': KeyInfo(),
                    'datapath.interface-list': KeyInfo(),
                    'datapath.local-forwarding': KeyInfo(),
                    'datapath.openflow-switch': KeyInfo(),
                    'datapath.vlan-id': KeyInfo(),
                    'datapath.vlan-mode': KeyInfo(),
                    'disable-running-check': KeyInfo(),
                    'disabled': KeyInfo(),
                    'l2mtu': KeyInfo(),
                    'mac-address': KeyInfo(),
                    'master-interface': KeyInfo(),
                    'mtu': KeyInfo(),
                    'name': KeyInfo(),
                    'numbers': KeyInfo(),
                    'radio-mac': KeyInfo(),
                    'security.authentication-types': KeyInfo(),
                    'security.disable-pmkid': KeyInfo(),
                    'security.eap-methods': KeyInfo(),
                    'security.eap-radius-accounting': KeyInfo(),
                    'security.encryption': KeyInfo(),
                    'security.group-encryption': KeyInfo(),
                    'security.group-key-update': KeyInfo(),
                    'security.passphrase': KeyInfo(),
                    'security.tls-certificate': KeyInfo(),
                    'security.tls-mode': KeyInfo(),
                },
            )),
        ],
    ),

    ('caps-man', 'channel'): APIData(
        unversioned=VersionedAPIData(
            primary_keys=('name',),
            fully_understood=True,
            # versioned_fields=[
            #     ([('7.15', '>=')], 'copy-from', KeyInfo(write_only=True)),
            # ],
            fields={
                'band': KeyInfo(can_disable=True),
                'comment': KeyInfo(can_disable=True, remove_value=''),
                'control-channel-width': KeyInfo(can_disable=True),
                'extension-channel': KeyInfo(can_disable=True),
                'frequency': KeyInfo(can_disable=True),
                'name': KeyInfo(),
                'reselect-interval': KeyInfo(can_disable=True),
                'save-selected': KeyInfo(can_disable=True),
                'secondary-frequency': KeyInfo(can_disable=True),
                'skip-dfs-channels': KeyInfo(can_disable=True),
                'tx-power': KeyInfo(can_disable=True),
            },
        ),
    ),

    ('caps-man', 'configuration'): APIData(
        unversioned=VersionedAPIData(
            primary_keys=('name',),
            fully_understood=True,
            # versioned_fields=[
            #     ([('7.15', '>=')], 'copy-from', KeyInfo(write_only=True)),
            # ],
            fields={
                'channel': KeyInfo(can_disable=True),
                'channel.band': KeyInfo(can_disable=True),
                'channel.control-channel-width': KeyInfo(can_disable=True),
                'channel.extension-channel': KeyInfo(can_disable=True),
                'channel.frequency': KeyInfo(can_disable=True),
                'channel.reselect-interval': KeyInfo(can_disable=True),
                'channel.save-selected': KeyInfo(can_disable=True),
                'channel.secondary-frequency': KeyInfo(can_disable=True),
                'channel.skip-dfs-channels': KeyInfo(can_disable=True),
                'channel.tx-power': KeyInfo(can_disable=True),
                'comment': KeyInfo(can_disable=True, remove_value=''),
                'country': KeyInfo(can_disable=True),
                'datapath': KeyInfo(can_disable=True),
                'datapath.arp': KeyInfo(),
                'datapath.bridge': KeyInfo(can_disable=True),
                'datapath.bridge-cost': KeyInfo(can_disable=True),
                'datapath.bridge-horizon': KeyInfo(can_disable=True),
                'datapath.client-to-client-forwarding': KeyInfo(can_disable=True),
                'datapath.interface-list': KeyInfo(can_disable=True),
                'datapath.l2mtu': KeyInfo(),
                'datapath.local-forwarding': KeyInfo(can_disable=True),
                'datapath.mtu': KeyInfo(),
                'datapath.openflow-switch': KeyInfo(can_disable=True),
                'datapath.vlan-id': KeyInfo(can_disable=True),
                'datapath.vlan-mode': KeyInfo(can_disable=True),
                'disconnect-timeout': KeyInfo(can_disable=True),
                'distance': KeyInfo(can_disable=True),
                'frame-lifetime': KeyInfo(can_disable=True),
                'guard-interval': KeyInfo(can_disable=True),
                'hide-ssid': KeyInfo(can_disable=True),
                'hw-protection-mode': KeyInfo(can_disable=True),
                'hw-retries': KeyInfo(can_disable=True),
                'installation': KeyInfo(can_disable=True),
                'keepalive-frames': KeyInfo(can_disable=True),
                'load-balancing-group': KeyInfo(can_disable=True),
                'max-sta-count': KeyInfo(can_disable=True),
                'mode': KeyInfo(can_disable=True),
                'multicast-helper': KeyInfo(can_disable=True),
                'name': KeyInfo(),
                'rates': KeyInfo(can_disable=True),
                'rates.basic': KeyInfo(can_disable=True),
                'rates.ht-basic-mcs': KeyInfo(can_disable=True),
                'rates.ht-supported-mcs': KeyInfo(can_disable=True),
                'rates.supported': KeyInfo(can_disable=True),
                'rates.vht-basic-mcs': KeyInfo(can_disable=True),
                'rates.vht-supported-mcs': KeyInfo(can_disable=True),
                'rx-chains': KeyInfo(can_disable=True),
                'security': KeyInfo(can_disable=True),
                'security.authentication-types': KeyInfo(can_disable=True),
                'security.disable-pmkid': KeyInfo(can_disable=True),
                'security.eap-methods': KeyInfo(can_disable=True),
                'security.eap-radius-accounting': KeyInfo(can_disable=True),
                'security.encryption': KeyInfo(can_disable=True),
                'security.group-encryption': KeyInfo(can_disable=True),
                'security.group-key-update': KeyInfo(),
                'security.passphrase': KeyInfo(can_disable=True),
                'security.tls-certificate': KeyInfo(),
                'security.tls-mode': KeyInfo(),
                'ssid': KeyInfo(can_disable=True),
                'tx-chains': KeyInfo(can_disable=True),
            },
        ),
    ),

    ('caps-man', 'datapath'): APIData(
        unversioned=VersionedAPIData(
            primary_keys=('name',),
            fully_understood=True,
            # versioned_fields=[
            #     ([('7.15', '>=')], 'copy-from', KeyInfo(write_only=True)),
            # ],
            fields={
                'arp': KeyInfo(),
                'bridge': KeyInfo(can_disable=True),
                'bridge-cost': KeyInfo(can_disable=True),
                'bridge-horizon': KeyInfo(can_disable=True),
                'client-to-client-forwarding': KeyInfo(can_disable=True),
                'comment': KeyInfo(can_disable=True, remove_value=''),
                'interface-list': KeyInfo(can_disable=True),
                'l2mtu': KeyInfo(),
                'local-forwarding': KeyInfo(can_disable=True),
                'mtu': KeyInfo(),
                'name': KeyInfo(),
                'openflow-switch': KeyInfo(can_disable=True),
                'vlan-id': KeyInfo(can_disable=True),
                'vlan-mode': KeyInfo(can_disable=True),
            },
        ),
    ),

    ('caps-man', 'interface'): APIData(
        versioned=[
            ('7.15', '>=', VersionedAPIData(
                fully_understood=True,
                fields={
                    'arp': KeyInfo(),
                    'arp-timeout': KeyInfo(),
                    'channel': KeyInfo(can_disable=True),
                    'channel.band': KeyInfo(can_disable=True),
                    'channel.control-channel-width': KeyInfo(can_disable=True),
                    'channel.extension-channel': KeyInfo(can_disable=True),
                    'channel.frequency': KeyInfo(can_disable=True),
                    'channel.reselect-interval': KeyInfo(can_disable=True),
                    'channel.save-selected': KeyInfo(can_disable=True),
                    'channel.secondary-frequency': KeyInfo(can_disable=True),
                    'channel.skip-dfs-channels': KeyInfo(can_disable=True),
                    'channel.tx-power': KeyInfo(can_disable=True),
                    'comment': KeyInfo(),
                    'configuration': KeyInfo(can_disable=True),
                    'configuration.country': KeyInfo(can_disable=True),
                    'configuration.disconnect-timeout': KeyInfo(can_disable=True),
                    'configuration.distance': KeyInfo(can_disable=True),
                    'configuration.frame-lifetime': KeyInfo(can_disable=True),
                    'configuration.guard-interval': KeyInfo(can_disable=True),
                    'configuration.hide-ssid': KeyInfo(can_disable=True),
                    'configuration.hw-protection-mode': KeyInfo(can_disable=True),
                    'configuration.hw-retries': KeyInfo(can_disable=True),
                    'configuration.installation': KeyInfo(can_disable=True),
                    'configuration.keepalive-frames': KeyInfo(can_disable=True),
                    'configuration.load-balancing-group': KeyInfo(can_disable=True),
                    'configuration.max-sta-count': KeyInfo(can_disable=True),
                    'configuration.mode': KeyInfo(can_disable=True),
                    'configuration.multicast-helper': KeyInfo(can_disable=True),
                    'configuration.rx-chains': KeyInfo(can_disable=True),
                    'configuration.ssid': KeyInfo(can_disable=True),
                    'configuration.tx-chains': KeyInfo(can_disable=True),
                    # 'copy-from': KeyInfo(write_only=True),
                    'datapath': KeyInfo(can_disable=True),
                    'datapath.bridge': KeyInfo(can_disable=True),
                    'datapath.bridge-cost': KeyInfo(can_disable=True),
                    'datapath.bridge-horizon': KeyInfo(can_disable=True),
                    'datapath.client-to-client-forwarding': KeyInfo(can_disable=True),
                    'datapath.interface-list': KeyInfo(can_disable=True),
                    'datapath.local-forwarding': KeyInfo(can_disable=True),
                    'datapath.openflow-switch': KeyInfo(can_disable=True),
                    'datapath.vlan-id': KeyInfo(can_disable=True),
                    'datapath.vlan-mode': KeyInfo(can_disable=True),
                    'disable-running-check': KeyInfo(),
                    'disabled': KeyInfo(),
                    'l2mtu': KeyInfo(),
                    'mac-address': KeyInfo(),
                    'master-interface': KeyInfo(),
                    'mtu': KeyInfo(),
                    'name': KeyInfo(),
                    'radio-mac': KeyInfo(),
                    'radio-name': KeyInfo(),
                    'rates': KeyInfo(can_disable=True),
                    'rates.basic': KeyInfo(can_disable=True),
                    'rates.ht-basic-mcs': KeyInfo(can_disable=True),
                    'rates.ht-supported-mcs': KeyInfo(can_disable=True),
                    'rates.supported': KeyInfo(can_disable=True),
                    'rates.vht-basic-mcs': KeyInfo(can_disable=True),
                    'rates.vht-supported-mcs': KeyInfo(can_disable=True),
                    'security': KeyInfo(can_disable=True),
                    'security.authentication-types': KeyInfo(can_disable=True),
                    'security.disable-pmkid': KeyInfo(can_disable=True),
                    'security.eap-methods': KeyInfo(can_disable=True),
                    'security.eap-radius-accounting': KeyInfo(can_disable=True),
                    'security.encryption': KeyInfo(can_disable=True),
                    'security.group-encryption': KeyInfo(can_disable=True),
                    'security.group-key-update': KeyInfo(),
                    'security.passphrase': KeyInfo(can_disable=True),
                    'security.tls-certificate': KeyInfo(),
                    'security.tls-mode': KeyInfo(),
                },
            )),
        ],
    ),

    ('caps-man', 'manager'): APIData(
        unversioned=VersionedAPIData(
            fixed_entries=True,
            single_value=True,
            fully_understood=True,
            fields={
                'ca-certificate': KeyInfo(default='none'),
                'certificate': KeyInfo(default='none'),
                'enabled': KeyInfo(default=False),
                'package-path': KeyInfo(default=''),
                'require-peer-certificate': KeyInfo(default=False),
                'upgrade-policy': KeyInfo(default='none'),
            },
        ),
    ),

    ('caps-man', 'manager', 'interface'): APIData(
        unversioned=VersionedAPIData(
            primary_keys=('interface',),
            fully_understood=True,
            versioned_fields=[
                # ([('7.15', '>=')], 'copy-from', KeyInfo(write_only=True)),
                ([('7.15', '<')], 'default', KeyInfo()),
            ],
            fields={
                'comment': KeyInfo(can_disable=True, remove_value=''),
                'disabled': KeyInfo(default=False),
                'forbid': KeyInfo(default=False),
                'interface': KeyInfo(),
            },
        ),
    ),

    ('caps-man', 'provisioning'): APIData(
        unversioned=VersionedAPIData(
            fully_understood=True,
            # versioned_fields=[
            #     ([('7.15', '>=')], 'copy-from', KeyInfo(write_only=True)),
            #     ([('7.15', '>=')], 'place-before', KeyInfo(write_only=True)),
            # ],
            fields={
                'action': KeyInfo(default='none'),
                'comment': KeyInfo(can_disable=True, remove_value=''),
                'common-name-regexp': KeyInfo(default=''),
                'disabled': KeyInfo(default=False),
                'hw-supported-modes': KeyInfo(default=''),
                'identity-regexp': KeyInfo(default=''),
                'ip-address-ranges': KeyInfo(default=''),
                'master-configuration': KeyInfo(default='*FFFFFFFF'),
                'name-format': KeyInfo(default='cap'),
                'name-prefix': KeyInfo(default=''),
                'radio-mac': KeyInfo(default='00:00:00:00:00:00'),
                'slave-configurations': KeyInfo(default=''),
            },
        ),
    ),

    ('caps-man', 'rates'): APIData(
        versioned=[
            ('7.15', '>=', VersionedAPIData(
                fully_understood=True,
                fields={
                    'basic': KeyInfo(can_disable=True),
                    'comment': KeyInfo(),
                    # 'copy-from': KeyInfo(write_only=True),
                    'ht-basic-mcs': KeyInfo(can_disable=True),
                    'ht-supported-mcs': KeyInfo(can_disable=True),
                    'name': KeyInfo(),
                    'supported': KeyInfo(can_disable=True),
                    'vht-basic-mcs': KeyInfo(can_disable=True),
                    'vht-supported-mcs': KeyInfo(can_disable=True),
                },
            )),
        ],
    ),

    ('caps-man', 'security'): APIData(
        unversioned=VersionedAPIData(
            primary_keys=('name',),
            fully_understood=True,
            # versioned_fields=[
            #     ([('7.15', '>=')], 'copy-from', KeyInfo(write_only=True)),
            # ],
            fields={
                'authentication-types': KeyInfo(can_disable=True),
                'comment': KeyInfo(can_disable=True, remove_value=''),
                'disable-pmkid': KeyInfo(can_disable=True),
                'eap-methods': KeyInfo(can_disable=True),
                'eap-radius-accounting': KeyInfo(can_disable=True),
                'encryption': KeyInfo(can_disable=True),
                'group-encryption': KeyInfo(can_disable=True),
                'group-key-update': KeyInfo(),
                'name': KeyInfo(),
                'passphrase': KeyInfo(can_disable=True),
                'tls-certificate': KeyInfo(),
                'tls-mode': KeyInfo(),
            },
        ),
    ),

    ('certificate',): APIData(
        versioned=[
            ('7.15', '>=', VersionedAPIData(
                fully_understood=True,
                versioned_fields=[
                    ([('7.21', '>=')], 'trust-store', KeyInfo()),
                ],
                fields={
                    'common-name': KeyInfo(),
                    # 'copy-from': KeyInfo(write_only=True),
                    'country': KeyInfo(),
                    'days-valid': KeyInfo(default=365),
                    'digest-algorithm': KeyInfo(default='sha256'),
                    'key-size': KeyInfo(default='2048'),
                    'key-usage': KeyInfo(default='digital-signature,key-encipherment,data-encipherment,key-cert-sign,crl-sign,tls-server,tls-client'),
                    'locality': KeyInfo(),
                    'name': KeyInfo(),
                    'organization': KeyInfo(),
                    'state': KeyInfo(),
                    'subject-alt-name': KeyInfo(),
                    'trusted': KeyInfo(),
                    'unit': KeyInfo(),
                },
            )),
        ],
    ),

    ('certificate', 'crl'): APIData(
        versioned=[
            ('7.15', '>=', VersionedAPIData(
                fully_understood=True,
                fields={
                    # 'copy-from': KeyInfo(write_only=True),
                    'url': KeyInfo(),
                },
            )),
        ],
    ),

    ('certificate', 'scep-server'): APIData(
        versioned=[
            ('7.15', '>=', VersionedAPIData(
                fully_understood=True,
                fields={
                    'ca-cert': KeyInfo(),
                    # 'copy-from': KeyInfo(write_only=True),
                    'days-valid': KeyInfo(),
                    'disabled': KeyInfo(),
                    'next-ca-cert': KeyInfo(),
                    'path': KeyInfo(),
                    'request-lifetime': KeyInfo(),
                },
            )),
        ],
    ),

    ('certificate', 'scep-server', 'ra'): APIData(
        versioned=[
            ('7.15', '>=', VersionedAPIData(
                fully_understood=True,
                fields={
                    'ca-identity': KeyInfo(),
                    'challenge-password': KeyInfo(),
                    # 'copy-from': KeyInfo(write_only=True),
                    'disabled': KeyInfo(),
                    'fingerprint-algorithm': KeyInfo(),
                    'name': KeyInfo(),
                    'on-smart-card': KeyInfo(),
                    'ra-path': KeyInfo(),
                    'ra-transaction-lifetime': KeyInfo(),
                    'server-url': KeyInfo(),
                    'template': KeyInfo(),
                },
            )),
        ],
    ),

    ('certificate', 'settings'): APIData(
        unversioned=VersionedAPIData(
            fixed_entries=True,
            single_value=True,
            fully_understood=True,
            versioned_fields=[
                ([('7.19', '>=')], 'builtin-trust-anchors', KeyInfo()),
                ([('7.21', '>=')], 'builtin-trust-store', KeyInfo()),
            ],
            fields={
                'crl-download': KeyInfo(default=False),
                'crl-store': KeyInfo(default='ram'),
                'crl-use': KeyInfo(default=False),
            },
        ),
    ),

    ('console', 'settings'): APIData(
        versioned=[
            ('7.15', '>=', VersionedAPIData(
                fixed_entries=True,
                single_value=True,
                fully_understood=True,
                versioned_fields=[
                    ([('7.18', '>=')], 'log-script-errors', KeyInfo()),
                    ([('7.20', '>=')], 'tab-width', KeyInfo()),
                ],
                fields={
                    'sanitize-names': KeyInfo(),
                },
            )),
        ],
    ),

    ('container',): APIData(
        versioned=[
            ('7.15', '>=', VersionedAPIData(
                fully_understood=True,
                versioned_fields=[
                    ([('7.20', '>=')], 'auto-restart-interval', KeyInfo()),
                    ([('7.20', '>=')], 'check-certificate', KeyInfo()),
                    ([('7.21', '>=')], 'cpu-list', KeyInfo()),
                    ([('7.20', '>=')], 'devices', KeyInfo()),
                    ([('7.21', '>=')], 'env', KeyInfo()),
                    ([('7.20', '>=')], 'envlists', KeyInfo()),
                    ([('7.21', '>=')], 'hosts', KeyInfo()),
                    ([('7.21', '>=')], 'layer-dir', KeyInfo()),
                    ([('7.20', '>=')], 'memory-high', KeyInfo()),
                    ([('7.21', '>=')], 'mount', KeyInfo()),
                    ([('7.21', '>=')], 'mountlists', KeyInfo()),
                    ([('7.19', '>=')], 'name', KeyInfo()),
                    ([('7.21.2', '>=')], 'shm-size', KeyInfo()),
                    ([('7.21', '>=')], 'stop-time', KeyInfo()),
                    ([('7.21.2', '>=')], 'tmpfs', KeyInfo()),
                ],
                fields={
                    'cmd': KeyInfo(),
                    'comment': KeyInfo(),
                    # 'copy-from': KeyInfo(write_only=True),
                    'dns': KeyInfo(),
                    'domain-name': KeyInfo(),
                    'entrypoint': KeyInfo(),
                    'envlist': KeyInfo(),
                    'file': KeyInfo(),
                    'hostname': KeyInfo(),
                    'interface': KeyInfo(),
                    'logging': KeyInfo(),
                    'mounts': KeyInfo(),
                    'remote-image': KeyInfo(),
                    'root-dir': KeyInfo(),
                    'start-on-boot': KeyInfo(),
                    'stop-signal': KeyInfo(),
                    'user': KeyInfo(),
                    'workdir': KeyInfo(),
                },
            )),
        ],
    ),

    ('container', 'config'): APIData(
        versioned=[
            ('7.15', '>=', VersionedAPIData(
                fixed_entries=True,
                single_value=True,
                fully_understood=True,
                versioned_fields=[
                    ([('7.20', '>=')], 'memory-high', KeyInfo()),
                ],
                fields={
                    'layer-dir': KeyInfo(),
                    'password': KeyInfo(),
                    'ram-high': KeyInfo(),
                    'registry-url': KeyInfo(),
                    'tmpdir': KeyInfo(),
                    'username': KeyInfo(),
                },
            )),
        ],
    ),

    ('container', 'envs'): APIData(
        versioned=[
            ('7.15', '>=', VersionedAPIData(
                fully_understood=True,
                versioned_fields=[
                    ([('7.21', '>=')], 'disabled', KeyInfo()),
                    ([('7.20', '>=')], 'list', KeyInfo()),
                ],
                fields={
                    'comment': KeyInfo(),
                    # 'copy-from': KeyInfo(write_only=True),
                    'key': KeyInfo(),
                    'name': KeyInfo(),
                    'value': KeyInfo(),
                },
            )),
        ],
    ),

    ('container', 'mounts'): APIData(
        versioned=[
            ('7.15', '>=', VersionedAPIData(
                fully_understood=True,
                versioned_fields=[
                    ([('7.21', '>=')], 'disabled', KeyInfo()),
                    ([('7.21', '>=')], 'list', KeyInfo()),
                    ([('7.20', '>=')], 'read-only', KeyInfo()),
                ],
                fields={
                    'comment': KeyInfo(),
                    # 'copy-from': KeyInfo(write_only=True),
                    'dst': KeyInfo(),
                    'name': KeyInfo(),
                    'src': KeyInfo(),
                },
            )),
        ],
    ),

    ('disk',): APIData(
        versioned=[
            ('7.15', '>=', VersionedAPIData(
                fully_understood=True,
                versioned_fields=[
                    ([('7.18', '>=')], 'compress', KeyInfo()),
                    ([('7.17', '>=')], 'file-offset', KeyInfo()),
                    ([('7.17', '>=')], 'file-path', KeyInfo()),
                    ([('7.17', '>=')], 'file-size', KeyInfo()),
                    ([('7.21', '>=')], 'iscsi-server-iqn', KeyInfo()),
                    ([('7.21', '>=')], 'iscsi-server-port', KeyInfo()),
                    ([('7.17', '>=')], 'mount-filesystem', KeyInfo()),
                    ([('7.17', '>=')], 'mount-point-template', KeyInfo()),
                    ([('7.17', '>=')], 'mount-read-only', KeyInfo()),
                    ([('7.21', '>=')], 'nvme-tcp-nqn', KeyInfo()),
                    ([('7.21', '>=')], 'nvme-tcp-server-nqn', KeyInfo()),
                    ([('7.21', '>=')], 'smb-server-encryption', KeyInfo()),
                    ([('7.21', '>=')], 'smb-server-password', KeyInfo()),
                    ([('7.21', '>=')], 'smb-server-user', KeyInfo()),
                    ([('7.17', '>=')], 'sshfs-address', KeyInfo()),
                    ([('7.17', '>=')], 'sshfs-password', KeyInfo()),
                    ([('7.17', '>=')], 'sshfs-path', KeyInfo()),
                    ([('7.17', '>=')], 'sshfs-port', KeyInfo()),
                    ([('7.17', '>=')], 'sshfs-user', KeyInfo()),
                    ([('7.17', '>=')], 'swap', KeyInfo()),
                ],
                fields={
                    'comment': KeyInfo(),
                    # 'copy-from': KeyInfo(write_only=True),
                    'crypted-backend': KeyInfo(),
                    'disabled': KeyInfo(),
                    'encryption-key': KeyInfo(),
                    'iscsi-address': KeyInfo(),
                    'iscsi-export': KeyInfo(),
                    'iscsi-iqn': KeyInfo(),
                    'iscsi-port': KeyInfo(),
                    'media-interface': KeyInfo(),
                    'media-sharing': KeyInfo(),
                    'nfs-address': KeyInfo(),
                    'nfs-share': KeyInfo(),
                    'nfs-sharing': KeyInfo(),
                    'nvme-tcp-address': KeyInfo(),
                    'nvme-tcp-export': KeyInfo(),
                    'nvme-tcp-host-name': KeyInfo(),
                    'nvme-tcp-name': KeyInfo(),
                    'nvme-tcp-password': KeyInfo(),
                    'nvme-tcp-port': KeyInfo(),
                    'nvme-tcp-server-allow-host-name': KeyInfo(),
                    'nvme-tcp-server-password': KeyInfo(),
                    'nvme-tcp-server-port': KeyInfo(),
                    'parent': KeyInfo(),
                    'partition-number': KeyInfo(),
                    'partition-offset': KeyInfo(),
                    'partition-size': KeyInfo(),
                    'raid-chunk-size': KeyInfo(),
                    'raid-device-count': KeyInfo(),
                    'raid-master': KeyInfo(),
                    'raid-max-component-size': KeyInfo(),
                    'raid-member-failed': KeyInfo(),
                    'raid-role': KeyInfo(),
                    'raid-type': KeyInfo(),
                    'ramdisk-size': KeyInfo(),
                    'self-encryption-password': KeyInfo(),
                    'slot': KeyInfo(),
                    'smb-address': KeyInfo(),
                    'smb-encryption': KeyInfo(),
                    'smb-password': KeyInfo(),
                    'smb-share': KeyInfo(),
                    'smb-sharing': KeyInfo(),
                    'smb-user': KeyInfo(),
                    'tmpfs-max-size': KeyInfo(),
                    'type': KeyInfo(),
                },
            )),
        ],
    ),

    ('disk', 'btrfs', 'filesystem'): APIData(
        versioned=[
            ('7.18', '>=', VersionedAPIData(
                fully_understood=True,
                has_identifier=True,
                # fixed_entries=True,
                # primary_keys=('numbers',),
                fields={
                    'default-subvolume': KeyInfo(),
                    'label': KeyInfo(),
                    'numbers': KeyInfo(),
                },
            )),
        ],
    ),

    ('disk', 'btrfs', 'subvolume'): APIData(
        versioned=[
            ('7.18', '>=', VersionedAPIData(
                fully_understood=True,
                fields={
                    # 'copy-from': KeyInfo(write_only=True),
                    'fs': KeyInfo(),
                    'mount': KeyInfo(),
                    'mountpoint': KeyInfo(),
                    'name': KeyInfo(),
                    'parent': KeyInfo(),
                    'read-only': KeyInfo(),
                },
            )),
        ],
    ),

    ('disk', 'btrfs', 'transfer'): APIData(
        versioned=[
            ('7.18', '>=', VersionedAPIData(
                fully_understood=True,
                fields={
                    # 'copy-from': KeyInfo(write_only=True),
                    'file': KeyInfo(),
                    'fs': KeyInfo(),
                    'send-parent': KeyInfo(),
                    'send-subvolumes': KeyInfo(),
                    'ssh-address': KeyInfo(),
                    'ssh-port': KeyInfo(),
                    'ssh-receive-mount': KeyInfo(),
                    'ssh-user': KeyInfo(),
                    'type': KeyInfo(),
                },
            )),
        ],
    ),

    ('disk', 'settings'): APIData(
        unversioned=VersionedAPIData(
            fixed_entries=True,
            single_value=True,
            fully_understood=True,
            versioned_fields=[
                ([('7.15', '<')], 'default-mount-point-template', KeyInfo(default='[slot]')),
            ],
            fields={
                'auto-media-interface': KeyInfo(default='bridge'),
                'auto-media-sharing': KeyInfo(default=True),
                'auto-smb-sharing': KeyInfo(default=True),
                'auto-smb-user': KeyInfo(default='guest'),
            },
        ),
    ),

    ('dude',): APIData(
        versioned=[
            ('7.15', '>=', VersionedAPIData(
                fixed_entries=True,
                single_value=True,
                fully_understood=True,
                fields={
                    'data-directory': KeyInfo(),
                    'enabled': KeyInfo(),
                },
            )),
        ],
    ),

    ('dude', 'agent'): APIData(
        versioned=[
            ('7.15', '>=', VersionedAPIData(
                fully_understood=True,
                fields={
                    'comment': KeyInfo(),
                    # 'copy-from': KeyInfo(write_only=True),
                    'name': KeyInfo(),
                },
            )),
        ],
    ),

    ('dude', 'device'): APIData(
        versioned=[
            ('7.15', '>=', VersionedAPIData(
                fully_understood=True,
                fields={
                    'comment': KeyInfo(),
                    # 'copy-from': KeyInfo(write_only=True),
                    'name': KeyInfo(),
                },
            )),
        ],
    ),

    ('dude', 'device-type'): APIData(
        versioned=[
            ('7.15', '>=', VersionedAPIData(
                fully_understood=True,
                fields={
                    'comment': KeyInfo(),
                    # 'copy-from': KeyInfo(write_only=True),
                    'name': KeyInfo(),
                },
            )),
        ],
    ),

    ('dude', 'notification'): APIData(
        versioned=[
            ('7.15', '>=', VersionedAPIData(
                fully_understood=True,
                fields={
                    'comment': KeyInfo(),
                    # 'copy-from': KeyInfo(write_only=True),
                    'name': KeyInfo(),
                },
            )),
        ],
    ),

    ('dude', 'probe'): APIData(
        versioned=[
            ('7.15', '>=', VersionedAPIData(
                fully_understood=True,
                fields={
                    'comment': KeyInfo(),
                    # 'copy-from': KeyInfo(write_only=True),
                    'name': KeyInfo(),
                },
            )),
        ],
    ),

    ('dude', 'ros', 'address'): APIData(
        versioned=[
            ('7.15', '>=', VersionedAPIData(
                fully_understood=True,
                fields={
                    'address': KeyInfo(),
                    'broadcast': KeyInfo(),
                    'comment': KeyInfo(),
                    # 'copy-from': KeyInfo(write_only=True),
                    'device': KeyInfo(),
                    'disabled': KeyInfo(),
                    'interface': KeyInfo(),
                    'netmask': KeyInfo(),
                    'network': KeyInfo(),
                },
            )),
        ],
    ),

    ('dude', 'ros', 'arp'): APIData(
        versioned=[
            ('7.15', '>=', VersionedAPIData(
                fully_understood=True,
                fields={
                    'address': KeyInfo(),
                    'comment': KeyInfo(),
                    # 'copy-from': KeyInfo(write_only=True),
                    'device': KeyInfo(),
                    'disabled': KeyInfo(),
                    'interface': KeyInfo(),
                    'mac-address': KeyInfo(),
                    'published': KeyInfo(),
                },
            )),
        ],
    ),

    ('dude', 'ros', 'health'): APIData(
        versioned=[
            ('7.15', '>=', VersionedAPIData(
                fully_understood=True,
                has_identifier=True,
                # fixed_entries=True,
                # primary_keys=('numbers',),
                fields={
                    'cpu-overtemp-check': KeyInfo(),
                    'cpu-overtemp-startup-delay': KeyInfo(),
                    'cpu-overtemp-threshold': KeyInfo(),
                    'device': KeyInfo(),
                    'fan-mode': KeyInfo(),
                    'fan-on-threshold': KeyInfo(),
                    'fan-switch': KeyInfo(),
                    'numbers': KeyInfo(),
                    'psu1-state': KeyInfo(),
                    'psu2-state': KeyInfo(),
                    'use-fan': KeyInfo(),
                    'use-fan2': KeyInfo(),
                },
            )),
        ],
    ),

    ('dude', 'ros', 'interface'): APIData(
        versioned=[
            ('7.15', '>=', VersionedAPIData(
                fully_understood=True,
                has_identifier=True,
                # fixed_entries=True,
                # primary_keys=('numbers',),
                fields={
                    'comment': KeyInfo(),
                    'device': KeyInfo(),
                    'disabled': KeyInfo(),
                    'l2mtu': KeyInfo(),
                    'mtu': KeyInfo(),
                    'name': KeyInfo(),
                    'numbers': KeyInfo(),
                },
            )),
        ],
    ),

    ('dude', 'ros', 'lease'): APIData(
        versioned=[
            ('7.15', '>=', VersionedAPIData(
                fully_understood=True,
                fields={
                    'address': KeyInfo(),
                    'address-lists': KeyInfo(),
                    'always-broadcast': KeyInfo(),
                    'block-access': KeyInfo(),
                    'client-id': KeyInfo(),
                    'comment': KeyInfo(),
                    # 'copy-from': KeyInfo(write_only=True),
                    'device': KeyInfo(),
                    'dhcp-option': KeyInfo(),
                    'dhcp-option-set': KeyInfo(),
                    'disabled': KeyInfo(),
                    'insert-queue-before': KeyInfo(),
                    'lease-time': KeyInfo(),
                    'mac-address': KeyInfo(),
                    'rate-limit': KeyInfo(),
                    'server': KeyInfo(),
                    'use-src-mac': KeyInfo(),
                },
            )),
        ],
    ),

    ('dude', 'ros', 'neighbor'): APIData(
        versioned=[
            ('7.15', '>=', VersionedAPIData(
                fully_understood=True,
                has_identifier=True,
                # fixed_entries=True,
                # primary_keys=('numbers',),
                fields={
                    'device': KeyInfo(),
                    'numbers': KeyInfo(),
                },
            )),
        ],
    ),

    ('dude', 'ros', 'queue'): APIData(
        versioned=[
            ('7.15', '>=', VersionedAPIData(
                fully_understood=True,
                fields={
                    'bucket-size': KeyInfo(),
                    'burst-limit': KeyInfo(),
                    'burst-threshold': KeyInfo(),
                    'burst-time': KeyInfo(),
                    'comment': KeyInfo(),
                    # 'copy-from': KeyInfo(write_only=True),
                    'device': KeyInfo(),
                    'disabled': KeyInfo(),
                    'dst': KeyInfo(),
                    'limit-at': KeyInfo(),
                    'max-limit': KeyInfo(),
                    'name': KeyInfo(),
                    'packet-marks': KeyInfo(),
                    'parent': KeyInfo(),
                    'priority': KeyInfo(),
                    'queue': KeyInfo(),
                    'target': KeyInfo(),
                    'time': KeyInfo(),
                    'total-bucket-size': KeyInfo(),
                    'total-burst-limit': KeyInfo(),
                    'total-burst-threshold': KeyInfo(),
                    'total-burst-time': KeyInfo(),
                    'total-limit-at': KeyInfo(),
                    'total-max-limit': KeyInfo(),
                    'total-priority': KeyInfo(),
                    'total-queue': KeyInfo(),
                },
            )),
        ],
    ),

    ('dude', 'ros', 'resource'): APIData(
        versioned=[
            ('7.15', '>=', VersionedAPIData(
                fully_understood=True,
                has_identifier=True,
                # fixed_entries=True,
                # primary_keys=('numbers',),
                fields={
                    'device': KeyInfo(),
                    'numbers': KeyInfo(),
                },
            )),
        ],
    ),

    ('dude', 'ros', 'route'): APIData(
        versioned=[
            ('7.15', '>=', VersionedAPIData(
                fully_understood=True,
                fields={
                    'bgp-as-path': KeyInfo(),
                    'bgp-atomic-aggregate': KeyInfo(),
                    'bgp-communities': KeyInfo(),
                    'bgp-local-pref': KeyInfo(),
                    'bgp-med': KeyInfo(),
                    'bgp-origin': KeyInfo(),
                    'bgp-prepend': KeyInfo(),
                    'check-gateway': KeyInfo(),
                    'comment': KeyInfo(),
                    # 'copy-from': KeyInfo(write_only=True),
                    'device': KeyInfo(),
                    'disabled': KeyInfo(),
                    'distance': KeyInfo(),
                    'dst-address': KeyInfo(),
                    'gateway': KeyInfo(),
                    'pref-src': KeyInfo(),
                    'route-tag': KeyInfo(),
                    'routing-mark': KeyInfo(),
                    'scope': KeyInfo(),
                    'target-scope': KeyInfo(),
                    'type': KeyInfo(),
                    'vrf-interface': KeyInfo(),
                },
            )),
        ],
    ),

    ('dude', 'ros', 'routerboard'): APIData(
        versioned=[
            ('7.15', '>=', VersionedAPIData(
                fully_understood=True,
                has_identifier=True,
                # fixed_entries=True,
                # primary_keys=('numbers',),
                fields={
                    'device': KeyInfo(),
                    'numbers': KeyInfo(),
                },
            )),
        ],
    ),

    ('dude', 'service'): APIData(
        versioned=[
            ('7.15', '>=', VersionedAPIData(
                fully_understood=True,
                fields={
                    'comment': KeyInfo(),
                    # 'copy-from': KeyInfo(write_only=True),
                    'name': KeyInfo(),
                },
            )),
        ],
    ),

    ('file',): APIData(
        versioned=[
            ('7.15', '>=', VersionedAPIData(
                fully_understood=True,
                # versioned_fields=[
                #     ([('7.15', '>='), ('7.21.2', '<')], 'copy-from': KeyInfo(write_only=True)),
                # ],
                fields={
                    'contents': KeyInfo(),
                    'name': KeyInfo(),
                    'type': KeyInfo(default='file'),
                },
            )),
        ],
    ),

    ('file', 'rsync-daemon'): APIData(
        versioned=[
            ('7.16', '>=', VersionedAPIData(
                fixed_entries=True,
                single_value=True,
                fully_understood=True,
                fields={
                    'enabled': KeyInfo(),
                },
            )),
        ],
    ),

    ('file', 'sync'): APIData(
        versioned=[
            ('7.15', '>=', VersionedAPIData(
                fully_understood=True,
                versioned_fields=[
                    ([('7.16', '>=')], 'remote-address', KeyInfo()),
                ],
                fields={
                    'comment': KeyInfo(),
                    # 'copy-from': KeyInfo(write_only=True),
                    'disabled': KeyInfo(),
                    'local-path': KeyInfo(),
                    'mode': KeyInfo(),
                    'password': KeyInfo(),
                    'remote-addrs': KeyInfo(),
                    'remote-path': KeyInfo(),
                    'status': KeyInfo(),
                    'user': KeyInfo(),
                },
            )),
        ],
    ),

    ('interface',): APIData(
        versioned=[
            ('7.15', '>=', VersionedAPIData(
                fully_understood=True,
                has_identifier=True,
                # fixed_entries=True,
                # primary_keys=('numbers',),
                fields={
                    'comment': KeyInfo(),
                    'disabled': KeyInfo(),
                    'l2mtu': KeyInfo(),
                    'mtu': KeyInfo(),
                    'name': KeyInfo(),
                    'numbers': KeyInfo(),
                },
            )),
        ],
    ),

    ('interface', '6to4'): APIData(
        unversioned=VersionedAPIData(
            primary_keys=('name',),
            fully_understood=True,
            # versioned_fields=[
            #     ([('7.15', '>=')], 'copy-from', KeyInfo(write_only=True)),
            # ],
            fields={
                'clamp-tcp-mss': KeyInfo(default=True),
                'comment': KeyInfo(can_disable=True, remove_value=''),
                'disabled': KeyInfo(default=False),
                'dont-fragment': KeyInfo(default=False),
                'dscp': KeyInfo(default='inherit'),
                'ipsec-secret': KeyInfo(can_disable=True),
                'keepalive': KeyInfo(can_disable=True, default='10s,10'),
                'local-address': KeyInfo(default='0.0.0.0'),
                'mtu': KeyInfo(default='auto'),
                'name': KeyInfo(),
                'remote-address': KeyInfo(required=True),
            },
        ),
    ),

    ('interface', 'amt'): APIData(
        versioned=[
            ('7.18', '>=', VersionedAPIData(
                fully_understood=True,
                fields={
                    'comment': KeyInfo(),
                    # 'copy-from': KeyInfo(write_only=True),
                    'disabled': KeyInfo(),
                    'discovery-ip': KeyInfo(),
                    'dont-fragment': KeyInfo(),
                    'gateway-port': KeyInfo(),
                    'interface': KeyInfo(),
                    'local-ip': KeyInfo(),
                    'mac-address': KeyInfo(),
                    'max-tunnels': KeyInfo(),
                    'mode': KeyInfo(),
                    'name': KeyInfo(),
                    'relay-port': KeyInfo(),
                },
            )),
            ('7.19', '>=', 'Not supported anymore in version 7.19'),
        ],
    ),

    ('interface', 'bonding'): APIData(
        unversioned=VersionedAPIData(
            primary_keys=('name',),
            fully_understood=True,
            versioned_fields=[
                # ([('7.15', '>=')], 'copy-from', KeyInfo(write_only=True)),
                ([('7.19', '>=')], 'lacp-mode', KeyInfo()),
                ([('7.21', '>=')], 'lacp-system-id', KeyInfo()),
                ([('7.21', '>=')], 'lacp-system-priority', KeyInfo()),
            ],
            fields={
                'arp': KeyInfo(default='enabled'),
                'arp-interval': KeyInfo(default='100ms'),
                'arp-ip-targets': KeyInfo(default=''),
                'arp-timeout': KeyInfo(default='auto'),
                'comment': KeyInfo(can_disable=True, remove_value=''),
                'disabled': KeyInfo(default=False),
                'down-delay': KeyInfo(default='0ms'),
                'forced-mac-address': KeyInfo(can_disable=True),
                'lacp-rate': KeyInfo(default='30secs'),
                'lacp-user-key': KeyInfo(can_disable=True, remove_value=0),
                'link-monitoring': KeyInfo(default='mii'),
                'mii-interval': KeyInfo(default='100ms'),
                'min-links': KeyInfo(default=0),
                'mlag-id': KeyInfo(can_disable=True, remove_value=0),
                'mode': KeyInfo(default='balance-rr'),
                'mtu': KeyInfo(default=1500),
                'name': KeyInfo(),
                'primary': KeyInfo(default='none'),
                'slaves': KeyInfo(required=True),
                'transmit-hash-policy': KeyInfo(default='layer-2'),
                'up-delay': KeyInfo(default='0ms'),
            },
        ),
    ),

    ('interface', 'bridge'): APIData(
        unversioned=VersionedAPIData(
            primary_keys=('name',),
            fully_understood=True,
            versioned_fields=[
                ([('7.20', '>=')], 'add-dhcp-option82', KeyInfo(default=False)),
                # ([('7.15', '>=')], 'copy-from', KeyInfo(write_only=True)),
                ([('7.16', '>=')], 'forward-reserved-addresses', KeyInfo(default=False)),
                ([('7.20', '>=')], 'igmp-version', KeyInfo(default=2)),
                ([('7.0', '<')], 'ingress-filtering', KeyInfo(default=False)),
                ([('7.0', '>=')], 'ingress-filtering', KeyInfo(default=True)),
                ([('7.20', '>=')], 'last-member-interval', KeyInfo(default='1s')),
                ([('7.20', '>=')], 'last-member-query-count', KeyInfo(default=2)),
                ([('7.20', '>=')], 'max-hops', KeyInfo(default=20)),
                ([('7.16', '>=')], 'max-learned-entries', KeyInfo(default='auto')),
                ([('7.20', '>=')], 'membership-interval', KeyInfo(default='4m20s')),
                ([('7.20', '>=')], 'multicast-router', KeyInfo(default='temporary-query')),
                ([('7.20', '>=')], 'mvrp', KeyInfo(default=False)),
                ([('7.13', '>=')], 'port-cost-mode', KeyInfo(default='long')),
                ([('7.20', '>=')], 'querier-interval', KeyInfo(default='4m15s')),
                ([('7.20', '>=')], 'query-interval', KeyInfo(default='2m5s')),
                ([('7.20', '>=')], 'query-response-interval', KeyInfo(default='10s')),
                ([('7.20', '>=')], 'region-name', KeyInfo(default='')),
                ([('7.20', '>=')], 'region-revision', KeyInfo(default=0)),
                ([('7.20', '>=')], 'startup-query-count', KeyInfo(default=2)),
                ([('7.20', '>=')], 'startup-query-interval', KeyInfo(default='31s250ms')),
            ],
            fields={
                'admin-mac': KeyInfo(default=''),
                'ageing-time': KeyInfo(default='5m'),
                'arp': KeyInfo(default='enabled'),
                'arp-timeout': KeyInfo(default='auto'),
                'auto-mac': KeyInfo(default=True),
                'comment': KeyInfo(can_disable=True, remove_value=''),
                'dhcp-snooping': KeyInfo(default=False),
                'disabled': KeyInfo(default=False),
                'ether-type': KeyInfo(default='0x8100'),
                'fast-forward': KeyInfo(default=True),
                'forward-delay': KeyInfo(default='15s'),
                'frame-types': KeyInfo(default='admit-all'),
                'igmp-snooping': KeyInfo(default=False),
                'max-message-age': KeyInfo(default='20s'),
                'mld-version': KeyInfo(default=1),
                'mtu': KeyInfo(default='auto'),
                'multicast-querier': KeyInfo(default=False),
                'name': KeyInfo(),
                'priority': KeyInfo(default='0x8000'),
                'protocol-mode': KeyInfo(default='rstp'),
                'pvid': KeyInfo(default=1),
                'transmit-hold-count': KeyInfo(default=6),
                'vlan-filtering': KeyInfo(default=False),
            },
        ),
    ),

    ('interface', 'bridge', 'calea'): APIData(
        versioned=[
            ('7.15', '>=', VersionedAPIData(
                fully_understood=True,
                fields={
                    '802.3-sap': KeyInfo(can_disable=True),
                    '802.3-type': KeyInfo(can_disable=True),
                    'action': KeyInfo(),
                    'arp-dst-address': KeyInfo(can_disable=True),
                    'arp-dst-mac-address': KeyInfo(can_disable=True),
                    'arp-gratuitous': KeyInfo(can_disable=True),
                    'arp-hardware-type': KeyInfo(can_disable=True),
                    'arp-opcode': KeyInfo(can_disable=True),
                    'arp-packet-type': KeyInfo(can_disable=True),
                    'arp-src-address': KeyInfo(can_disable=True),
                    'arp-src-mac-address': KeyInfo(can_disable=True),
                    'chain': KeyInfo(),
                    'comment': KeyInfo(),
                    # 'copy-from': KeyInfo(write_only=True),
                    'disabled': KeyInfo(),
                    'dst-address': KeyInfo(can_disable=True),
                    'dst-address6': KeyInfo(can_disable=True),
                    'dst-mac-address': KeyInfo(can_disable=True),
                    'dst-port': KeyInfo(can_disable=True),
                    'in-bridge': KeyInfo(can_disable=True),
                    'in-bridge-list': KeyInfo(can_disable=True),
                    'in-interface': KeyInfo(can_disable=True),
                    'in-interface-list': KeyInfo(can_disable=True),
                    'ingress-priority': KeyInfo(can_disable=True),
                    'ip-protocol': KeyInfo(can_disable=True),
                    'limit': KeyInfo(can_disable=True),
                    'log': KeyInfo(),
                    'log-prefix': KeyInfo(),
                    'mac-protocol': KeyInfo(can_disable=True),
                    'out-bridge': KeyInfo(can_disable=True),
                    'out-bridge-list': KeyInfo(can_disable=True),
                    'out-interface': KeyInfo(can_disable=True),
                    'out-interface-list': KeyInfo(can_disable=True),
                    'packet-mark': KeyInfo(can_disable=True),
                    'packet-type': KeyInfo(can_disable=True),
                    # 'place-before': KeyInfo(write_only=True),
                    'sniff-id': KeyInfo(),
                    'sniff-target': KeyInfo(),
                    'sniff-target-port': KeyInfo(),
                    'src-address': KeyInfo(can_disable=True),
                    'src-address6': KeyInfo(can_disable=True),
                    'src-mac-address': KeyInfo(can_disable=True),
                    'src-port': KeyInfo(can_disable=True),
                    'stp-flags': KeyInfo(can_disable=True),
                    'stp-forward-delay': KeyInfo(can_disable=True),
                    'stp-hello-time': KeyInfo(can_disable=True),
                    'stp-max-age': KeyInfo(can_disable=True),
                    'stp-msg-age': KeyInfo(can_disable=True),
                    'stp-port': KeyInfo(can_disable=True),
                    'stp-root-address': KeyInfo(can_disable=True),
                    'stp-root-cost': KeyInfo(can_disable=True),
                    'stp-root-priority': KeyInfo(can_disable=True),
                    'stp-sender-address': KeyInfo(can_disable=True),
                    'stp-sender-priority': KeyInfo(can_disable=True),
                    'stp-type': KeyInfo(can_disable=True),
                    'tls-host': KeyInfo(can_disable=True),
                    'vlan-encap': KeyInfo(can_disable=True),
                    'vlan-id': KeyInfo(can_disable=True),
                    'vlan-priority': KeyInfo(can_disable=True),
                },
            )),
        ],
    ),

    ('interface', 'bridge', 'filter'): APIData(
        versioned=[
            ('7.15', '>=', VersionedAPIData(
                fully_understood=True,
                fields={
                    '802.3-sap': KeyInfo(can_disable=True),
                    '802.3-type': KeyInfo(can_disable=True),
                    'action': KeyInfo(),
                    'arp-dst-address': KeyInfo(can_disable=True),
                    'arp-dst-mac-address': KeyInfo(can_disable=True),
                    'arp-gratuitous': KeyInfo(can_disable=True),
                    'arp-hardware-type': KeyInfo(can_disable=True),
                    'arp-opcode': KeyInfo(can_disable=True),
                    'arp-packet-type': KeyInfo(can_disable=True),
                    'arp-src-address': KeyInfo(can_disable=True),
                    'arp-src-mac-address': KeyInfo(can_disable=True),
                    'chain': KeyInfo(),
                    'comment': KeyInfo(),
                    # 'copy-from': KeyInfo(write_only=True),
                    'disabled': KeyInfo(),
                    'dst-address': KeyInfo(can_disable=True),
                    'dst-address6': KeyInfo(can_disable=True),
                    'dst-mac-address': KeyInfo(can_disable=True),
                    'dst-port': KeyInfo(can_disable=True),
                    'in-bridge': KeyInfo(can_disable=True),
                    'in-bridge-list': KeyInfo(can_disable=True),
                    'in-interface': KeyInfo(can_disable=True),
                    'in-interface-list': KeyInfo(can_disable=True),
                    'ingress-priority': KeyInfo(can_disable=True),
                    'ip-protocol': KeyInfo(can_disable=True),
                    'jump-target': KeyInfo(),
                    'limit': KeyInfo(can_disable=True),
                    'log': KeyInfo(),
                    'log-prefix': KeyInfo(),
                    'mac-protocol': KeyInfo(can_disable=True),
                    'new-packet-mark': KeyInfo(),
                    'new-priority': KeyInfo(),
                    'out-bridge': KeyInfo(can_disable=True),
                    'out-bridge-list': KeyInfo(can_disable=True),
                    'out-interface': KeyInfo(can_disable=True),
                    'out-interface-list': KeyInfo(can_disable=True),
                    'packet-mark': KeyInfo(can_disable=True),
                    'packet-type': KeyInfo(can_disable=True),
                    'passthrough': KeyInfo(),
                    # 'place-before': KeyInfo(write_only=True),
                    'src-address': KeyInfo(can_disable=True),
                    'src-address6': KeyInfo(can_disable=True),
                    'src-mac-address': KeyInfo(can_disable=True),
                    'src-port': KeyInfo(can_disable=True),
                    'stp-flags': KeyInfo(can_disable=True),
                    'stp-forward-delay': KeyInfo(can_disable=True),
                    'stp-hello-time': KeyInfo(can_disable=True),
                    'stp-max-age': KeyInfo(can_disable=True),
                    'stp-msg-age': KeyInfo(can_disable=True),
                    'stp-port': KeyInfo(can_disable=True),
                    'stp-root-address': KeyInfo(can_disable=True),
                    'stp-root-cost': KeyInfo(can_disable=True),
                    'stp-root-priority': KeyInfo(can_disable=True),
                    'stp-sender-address': KeyInfo(can_disable=True),
                    'stp-sender-priority': KeyInfo(can_disable=True),
                    'stp-type': KeyInfo(can_disable=True),
                    'tls-host': KeyInfo(can_disable=True),
                    'vlan-encap': KeyInfo(can_disable=True),
                    'vlan-id': KeyInfo(can_disable=True),
                    'vlan-priority': KeyInfo(can_disable=True),
                },
            )),
        ],
    ),

    ('interface', 'bridge', 'host'): APIData(
        versioned=[
            ('7.15', '>=', VersionedAPIData(
                fully_understood=True,
                fields={
                    'bridge': KeyInfo(),
                    'comment': KeyInfo(),
                    # 'copy-from': KeyInfo(write_only=True),
                    'disabled': KeyInfo(),
                    'interface': KeyInfo(),
                    'mac-address': KeyInfo(),
                    'vid': KeyInfo(can_disable=True),
                },
            )),
        ],
    ),

    ('interface', 'bridge', 'mdb'): APIData(
        versioned=[
            ('7.15', '>=', VersionedAPIData(
                fully_understood=True,
                versioned_fields=[
                    ([('7.19', '>=')], 'interface', KeyInfo()),
                ],
                fields={
                    'bridge': KeyInfo(),
                    'comment': KeyInfo(),
                    # 'copy-from': KeyInfo(write_only=True),
                    'disabled': KeyInfo(),
                    'group': KeyInfo(),
                    'ports': KeyInfo(),
                    'vid': KeyInfo(can_disable=True),
                },
            )),
        ],
    ),

    ('interface', 'bridge', 'mlag'): APIData(
        unversioned=VersionedAPIData(
            fixed_entries=True,
            single_value=True,
            fully_understood=True,
            versioned_fields=[
                ([('7.18', '>=')], 'heartbeat', KeyInfo()),
                ([('7.17', '>=')], 'priority', KeyInfo()),
            ],
            fields={
                'bridge': KeyInfo(default='none'),
                'peer-port': KeyInfo(default='none'),
            },
        ),
    ),

    ('interface', 'bridge', 'msti'): APIData(
        versioned=[
            ('7.15', '>=', VersionedAPIData(
                fully_understood=True,
                fields={
                    'bridge': KeyInfo(),
                    'comment': KeyInfo(),
                    # 'copy-from': KeyInfo(write_only=True),
                    'disabled': KeyInfo(),
                    'identifier': KeyInfo(),
                    'priority': KeyInfo(),
                    'vlan-mapping': KeyInfo(),
                },
            )),
        ],
    ),

    ('interface', 'bridge', 'nat'): APIData(
        versioned=[
            ('7.15', '>=', VersionedAPIData(
                fully_understood=True,
                fields={
                    '802.3-sap': KeyInfo(can_disable=True),
                    '802.3-type': KeyInfo(can_disable=True),
                    'action': KeyInfo(),
                    'arp-dst-address': KeyInfo(can_disable=True),
                    'arp-dst-mac-address': KeyInfo(can_disable=True),
                    'arp-gratuitous': KeyInfo(can_disable=True),
                    'arp-hardware-type': KeyInfo(can_disable=True),
                    'arp-opcode': KeyInfo(can_disable=True),
                    'arp-packet-type': KeyInfo(can_disable=True),
                    'arp-src-address': KeyInfo(can_disable=True),
                    'arp-src-mac-address': KeyInfo(can_disable=True),
                    'chain': KeyInfo(),
                    'comment': KeyInfo(),
                    # 'copy-from': KeyInfo(write_only=True),
                    'disabled': KeyInfo(),
                    'dst-address': KeyInfo(can_disable=True),
                    'dst-address6': KeyInfo(can_disable=True),
                    'dst-mac-address': KeyInfo(can_disable=True),
                    'dst-port': KeyInfo(can_disable=True),
                    'in-bridge': KeyInfo(can_disable=True),
                    'in-bridge-list': KeyInfo(can_disable=True),
                    'in-interface': KeyInfo(can_disable=True),
                    'in-interface-list': KeyInfo(can_disable=True),
                    'ingress-priority': KeyInfo(can_disable=True),
                    'ip-protocol': KeyInfo(can_disable=True),
                    'jump-target': KeyInfo(),
                    'limit': KeyInfo(can_disable=True),
                    'log': KeyInfo(),
                    'log-prefix': KeyInfo(),
                    'mac-protocol': KeyInfo(can_disable=True),
                    'new-packet-mark': KeyInfo(),
                    'new-priority': KeyInfo(),
                    'out-bridge': KeyInfo(can_disable=True),
                    'out-bridge-list': KeyInfo(can_disable=True),
                    'out-interface': KeyInfo(can_disable=True),
                    'out-interface-list': KeyInfo(can_disable=True),
                    'packet-mark': KeyInfo(can_disable=True),
                    'packet-type': KeyInfo(can_disable=True),
                    'passthrough': KeyInfo(),
                    # 'place-before': KeyInfo(write_only=True),
                    'src-address': KeyInfo(can_disable=True),
                    'src-address6': KeyInfo(can_disable=True),
                    'src-mac-address': KeyInfo(can_disable=True),
                    'src-port': KeyInfo(can_disable=True),
                    'stp-flags': KeyInfo(can_disable=True),
                    'stp-forward-delay': KeyInfo(can_disable=True),
                    'stp-hello-time': KeyInfo(can_disable=True),
                    'stp-max-age': KeyInfo(can_disable=True),
                    'stp-msg-age': KeyInfo(can_disable=True),
                    'stp-port': KeyInfo(can_disable=True),
                    'stp-root-address': KeyInfo(can_disable=True),
                    'stp-root-cost': KeyInfo(can_disable=True),
                    'stp-root-priority': KeyInfo(can_disable=True),
                    'stp-sender-address': KeyInfo(can_disable=True),
                    'stp-sender-priority': KeyInfo(can_disable=True),
                    'stp-type': KeyInfo(can_disable=True),
                    'tls-host': KeyInfo(can_disable=True),
                    'to-arp-reply-mac-address': KeyInfo(),
                    'to-dst-mac-address': KeyInfo(),
                    'to-src-mac-address': KeyInfo(),
                    'vlan-encap': KeyInfo(can_disable=True),
                    'vlan-id': KeyInfo(can_disable=True),
                    'vlan-priority': KeyInfo(can_disable=True),
                },
            )),
        ],
    ),

    ('interface', 'bridge', 'port'): APIData(
        unversioned=VersionedAPIData(
            primary_keys=('interface',),
            fully_understood=True,
            versioned_fields=[
                # ([('7.15', '>=')], 'copy-from', KeyInfo(write_only=True)),
                ([('7.0', '<')], 'ingress-filtering', KeyInfo(default=False)),
                ([('7.0', '>=')], 'ingress-filtering', KeyInfo(default=True)),
                ([('7.13', '<')], 'internal-path-cost', KeyInfo(default=10)),
                ([('7.13', '>=')], 'internal-path-cost', KeyInfo(can_disable=True)),
                ([('7.20', '>=')], 'mvrp-applicant-state', KeyInfo(default='normal-participant')),
                ([('7.20', '>=')], 'mvrp-registrar-state', KeyInfo(default='normal')),
                ([('7.13', '<')], 'path-cost', KeyInfo(default=10)),
                ([('7.13', '>=')], 'path-cost', KeyInfo(can_disable=True)),
                # ([('7.15', '>=')], 'place-before', KeyInfo(write_only=True)),
            ],
            fields={
                'auto-isolate': KeyInfo(default=False),
                'bpdu-guard': KeyInfo(default=False),
                'bridge': KeyInfo(required=True),
                'broadcast-flood': KeyInfo(default=True),
                'comment': KeyInfo(can_disable=True, remove_value=''),
                'disabled': KeyInfo(default=False),
                'edge': KeyInfo(default='auto'),
                'fast-leave': KeyInfo(default=False),
                'frame-types': KeyInfo(default='admit-all'),
                'horizon': KeyInfo(default='none'),
                'hw': KeyInfo(default=True),
                'interface': KeyInfo(),
                'learn': KeyInfo(default='auto'),
                'multicast-router': KeyInfo(default='temporary-query'),
                'point-to-point': KeyInfo(default='auto'),
                'priority': KeyInfo(default='0x80'),
                'pvid': KeyInfo(default=1),
                'restricted-role': KeyInfo(default=False),
                'restricted-tcn': KeyInfo(default=False),
                'tag-stacking': KeyInfo(default=False),
                'trusted': KeyInfo(default=False),
                'unknown-multicast-flood': KeyInfo(default=True),
                'unknown-unicast-flood': KeyInfo(default=True),
            },
        ),
    ),

    ('interface', 'bridge', 'port', 'mst-override'): APIData(
        versioned=[
            ('7.15', '>=', VersionedAPIData(
                fully_understood=True,
                fields={
                    'comment': KeyInfo(),
                    # 'copy-from': KeyInfo(write_only=True),
                    'disabled': KeyInfo(),
                    'identifier': KeyInfo(),
                    'interface': KeyInfo(),
                    'internal-path-cost': KeyInfo(can_disable=True),
                    'priority': KeyInfo(),
                },
            )),
        ],
    ),

    ('interface', 'bridge', 'port-controller'): APIData(
        versioned=[
            ('7.18', '<', VersionedAPIData(
                fixed_entries=True,
                single_value=True,
                fully_understood=True,
                fields={
                    'bridge': KeyInfo(default='none'),
                    'cascade-ports': KeyInfo(default=''),
                    'switch': KeyInfo(default='none'),
                },
            )),
            ('7.18', '>=', 'Not supported anymore in version 7.18'),
        ],
    ),

    ('interface', 'bridge', 'port-controller', 'device'): APIData(
        versioned=[
            ('7.15', '>=', VersionedAPIData(
                fully_understood=True,
                fields={
                    # 'copy-from': KeyInfo(write_only=True),
                    'name': KeyInfo(),
                },
            )),
            ('7.18', '>=', 'Not supported anymore in version 7.18'),
        ],
    ),

    ('interface', 'bridge', 'port-controller', 'port'): APIData(
        versioned=[
            ('7.15', '>=', VersionedAPIData(
                fully_understood=True,
                has_identifier=True,
                # fixed_entries=True,
                # primary_keys=('numbers',),
                fields={
                    'disabled': KeyInfo(),
                    'name': KeyInfo(),
                    'numbers': KeyInfo(),
                },
            )),
            ('7.18', '>=', 'Not supported anymore in version 7.18'),
        ],
    ),

    ('interface', 'bridge', 'port-extender'): APIData(
        versioned=[
            ('7.18', '<', VersionedAPIData(
                fixed_entries=True,
                single_value=True,
                fully_understood=True,
                fields={
                    'control-ports': KeyInfo(default=''),
                    'excluded-ports': KeyInfo(default=''),
                    'switch': KeyInfo(default='none'),
                },
            )),
            ('7.18', '>=', 'Not supported anymore in version 7.18'),
        ],
    ),

    ('interface', 'bridge', 'settings'): APIData(
        unversioned=VersionedAPIData(
            fixed_entries=True,
            single_value=True,
            fully_understood=True,
            fields={
                'allow-fast-path': KeyInfo(default=True),
                'use-ip-firewall': KeyInfo(default=False),
                'use-ip-firewall-for-pppoe': KeyInfo(default=False),
                'use-ip-firewall-for-vlan': KeyInfo(default=False),
            },
        ),
    ),

    ('interface', 'bridge', 'vlan'): APIData(
        unversioned=VersionedAPIData(
            primary_keys=('bridge', 'vlan-ids'),
            fully_understood=True,
            versioned_fields=[
                # ([('7.15', '>=')], 'copy-from', KeyInfo(write_only=True)),
                ([('7.15', '>=')], 'mvrp-forbidden', KeyInfo()),
            ],
            fields={
                'bridge': KeyInfo(),
                'comment': KeyInfo(can_disable=True, remove_value=''),
                'disabled': KeyInfo(default=False),
                'tagged': KeyInfo(default=''),
                'untagged': KeyInfo(default=''),
                'vlan-ids': KeyInfo(),
            },
        ),
    ),

    ('interface', 'detect-internet'): APIData(
        unversioned=VersionedAPIData(
            fixed_entries=True,
            single_value=True,
            fully_understood=True,
            fields={
                'detect-interface-list': KeyInfo(default='none'),
                'internet-interface-list': KeyInfo(default='none'),
                'lan-interface-list': KeyInfo(default='none'),
                'wan-interface-list': KeyInfo(default='none'),
            },
        ),
    ),

    ('interface', 'dot1x', 'client'): APIData(
        unversioned=VersionedAPIData(
            primary_keys=('eap-methods', 'identity', 'interface'),
            fully_understood=True,
            versioned_fields=[
                # ([('7.15', '>=')], 'copy-from', KeyInfo(write_only=True)),
                ([('7.15', '>=')], 'password', KeyInfo()),
            ],
            fields={
                'anon-identity': KeyInfo(default=''),
                'certificate': KeyInfo(default='none'),
                'comment': KeyInfo(can_disable=True, remove_value=''),
                'disabled': KeyInfo(default=False),
                'eap-methods': KeyInfo(),
                'identity': KeyInfo(),
                'interface': KeyInfo(),
            },
        ),
    ),

    ('interface', 'dot1x', 'server'): APIData(
        unversioned=VersionedAPIData(
            stratify_keys=('interface',),
            fully_understood=True,
            # versioned_fields=[
            #     ([('7.15', '>=')], 'copy-from', KeyInfo(write_only=True)),
            # ],
            fields={
                'accounting': KeyInfo(default=True),
                'auth-timeout': KeyInfo(default='1m'),
                'auth-types': KeyInfo(default='dot1x'),
                'comment': KeyInfo(can_disable=True, remove_value=''),
                'disabled': KeyInfo(default=False),
                'guest-vlan-id': KeyInfo(can_disable=True),
                'interface': KeyInfo(),
                'interim-update': KeyInfo(default='0s'),
                'mac-auth-mode': KeyInfo(default='mac-as-username'),
                'radius-mac-format': KeyInfo(default='XX:XX:XX:XX:XX:XX'),
                'reauth-timeout': KeyInfo(can_disable=True),
                'reject-vlan-id': KeyInfo(can_disable=True),
                'retrans-timeout': KeyInfo(default='30s'),
                'server-fail-vlan-id': KeyInfo(can_disable=True),
            },
        ),
    ),

    ('interface', 'eoip'): APIData(
        unversioned=VersionedAPIData(
            primary_keys=('name',),
            fully_understood=True,
            # versioned_fields=[
            #     ([('7.15', '>=')], 'copy-from', KeyInfo(write_only=True)),
            # ],
            fields={
                'allow-fast-path': KeyInfo(default=True),
                'arp': KeyInfo(default='enabled'),
                'arp-timeout': KeyInfo(default='auto'),
                'clamp-tcp-mss': KeyInfo(default=True),
                'comment': KeyInfo(can_disable=True, remove_value=''),
                'disabled': KeyInfo(default=False),
                'dont-fragment': KeyInfo(default=False),
                'dscp': KeyInfo(default='inherit'),
                'ipsec-secret': KeyInfo(can_disable=True),
                'keepalive': KeyInfo(can_disable=True, default='10s,10'),
                'local-address': KeyInfo(default='0.0.0.0'),
                'loop-protect': KeyInfo(default='default'),
                'loop-protect-disable-time': KeyInfo(default='5m'),
                'loop-protect-send-interval': KeyInfo(default='5s'),
                'mac-address': KeyInfo(),
                'mtu': KeyInfo(default='auto'),
                'name': KeyInfo(),
                'remote-address': KeyInfo(required=True),
                'tunnel-id': KeyInfo(required=True),
            },
        ),
    ),

    ('interface', 'eoipv6'): APIData(
        versioned=[
            ('7.15', '>=', VersionedAPIData(
                fully_understood=True,
                versioned_fields=[
                    ([('7.21', '>=')], 'dont-fragment', KeyInfo()),
                ],
                fields={
                    'arp': KeyInfo(),
                    'arp-timeout': KeyInfo(),
                    'clamp-tcp-mss': KeyInfo(),
                    'comment': KeyInfo(),
                    # 'copy-from': KeyInfo(write_only=True),
                    'disabled': KeyInfo(),
                    'dscp': KeyInfo(),
                    'ipsec-secret': KeyInfo(can_disable=True),
                    'keepalive': KeyInfo(can_disable=True),
                    'local-address': KeyInfo(),
                    'loop-protect': KeyInfo(),
                    'loop-protect-disable-time': KeyInfo(),
                    'loop-protect-send-interval': KeyInfo(),
                    'mac-address': KeyInfo(),
                    'mtu': KeyInfo(),
                    'name': KeyInfo(),
                    'remote-address': KeyInfo(),
                    'tunnel-id': KeyInfo(),
                },
            )),
        ],
    ),

    ('interface', 'ethernet'): APIData(
        unversioned=VersionedAPIData(
            primary_keys=('default-name',),
            fixed_entries=True,
            fully_understood=True,
            versioned_fields=[
                ([('7.15.3', '>=')], 'cable-settings', KeyInfo()),
                ([('7.15.3', '>=')], 'disable-running-check', KeyInfo()),
                ([('7.15', '<')], 'full-duplex', KeyInfo(default=True)),
                ([('7.15', '>=')], 'numbers', KeyInfo()),
                ([('7.15', '>=')], 'sfp-ignore-rx-los', KeyInfo()),
            ],
            fields={
                'advertise': KeyInfo(),
                'arp': KeyInfo(default='enabled'),
                'arp-timeout': KeyInfo(default='auto'),
                'auto-negotiation': KeyInfo(default=True),
                'bandwidth': KeyInfo(default='unlimited/unlimited'),
                'combo-mode': KeyInfo(can_disable=True),
                'comment': KeyInfo(can_disable=True, remove_value=''),
                'default-name': KeyInfo(),
                'disabled': KeyInfo(default=False),
                'fec-mode': KeyInfo(can_disable=True, remove_value='auto'),
                'l2mtu': KeyInfo(),
                'loop-protect': KeyInfo(default='default'),
                'loop-protect-disable-time': KeyInfo(default='5m'),
                'loop-protect-send-interval': KeyInfo(default='5s'),
                'mac-address': KeyInfo(),
                'mdix-enable': KeyInfo(),
                'mtu': KeyInfo(default=1500),
                'name': KeyInfo(),
                'orig-mac-address': KeyInfo(),
                'poe-out': KeyInfo(can_disable=True, remove_value='auto-on'),
                'poe-priority': KeyInfo(can_disable=True, remove_value=10),
                'poe-voltage': KeyInfo(can_disable=True),
                'power-cycle-interval': KeyInfo(),
                'power-cycle-ping-address': KeyInfo(can_disable=True),
                'power-cycle-ping-enabled': KeyInfo(),
                'power-cycle-ping-timeout': KeyInfo(can_disable=True),
                'rx-flow-control': KeyInfo(default='off'),
                'sfp-rate-select': KeyInfo(default='high'),
                'sfp-shutdown-temperature': KeyInfo(can_disable=True, default=95),
                'speed': KeyInfo(),
                'tx-flow-control': KeyInfo(default='off'),
            },
        ),
    ),

    ('interface', 'ethernet', 'poe'): APIData(
        unversioned=VersionedAPIData(
            primary_keys=('name',),
            fixed_entries=True,
            fully_understood=True,
            versioned_fields=[
                ([('7.15', '>=')], 'numbers', KeyInfo()),
            ],
            fields={
                'name': KeyInfo(),
                'poe-out': KeyInfo(default='auto-on'),
                'poe-priority': KeyInfo(default=10),
                'poe-voltage': KeyInfo(default='auto'),
                'power-cycle-interval': KeyInfo(default='none'),
                'power-cycle-ping-address': KeyInfo(can_disable=True),
                'power-cycle-ping-enabled': KeyInfo(default=False),
                'power-cycle-ping-timeout': KeyInfo(can_disable=True),
            },
        ),
    ),

    ('interface', 'ethernet', 'switch'): APIData(
        unversioned=VersionedAPIData(
            primary_keys=('name',),
            fixed_entries=True,
            fully_understood=True,
            versioned_fields=[
                ([('7.15', '>=')], 'l3-hw-offloading', KeyInfo()),
                ([('7.15', '>=')], 'mirror-egress-target', KeyInfo()),
                ([('7.15', '>=')], 'numbers', KeyInfo()),
                ([('7.15', '>=')], 'qos-hw-offloading', KeyInfo()),
                ([('7.15', '>=')], 'rspan', KeyInfo()),
                ([('7.15', '>=')], 'rspan-egress-vlan-id', KeyInfo()),
                ([('7.15', '>=')], 'rspan-ingress-vlan-id', KeyInfo()),
                ([('7.15', '>=')], 'switch-all-ports', KeyInfo()),
            ],
            fields={
                'cpu-flow-control': KeyInfo(default=True),
                'mirror-source': KeyInfo(default='none'),
                'mirror-target': KeyInfo(default='none'),
                'name': KeyInfo(),
            },
        ),
    ),

    ('interface', 'ethernet', 'switch', 'host'): APIData(
        versioned=[
            ('7.15', '>=', VersionedAPIData(
                fully_understood=True,
                fields={
                    # 'copy-from': KeyInfo(write_only=True),
                    'copy-to-cpu': KeyInfo(),
                    'drop': KeyInfo(),
                    'mac-address': KeyInfo(),
                    'mirror': KeyInfo(),
                    'ports': KeyInfo(),
                    'redirect-to-cpu': KeyInfo(),
                    'share-vlan-learned': KeyInfo(),
                    'switch': KeyInfo(),
                    'vlan-id': KeyInfo(),
                },
            )),
        ],
    ),

    ('interface', 'ethernet', 'switch', 'l3hw-settings'): APIData(
        versioned=[
            ('7.15', '>=', VersionedAPIData(
                fixed_entries=True,
                single_value=True,
                fully_understood=True,
                fields={
                    'autorestart': KeyInfo(),
                    'fasttrack-hw': KeyInfo(),
                    'icmp-reply-on-error': KeyInfo(),
                    'ipv6-hw': KeyInfo(),
                },
            )),
        ],
    ),

    ('interface', 'ethernet', 'switch', 'l3hw-settings', 'advanced'): APIData(
        versioned=[
            ('7.15', '>=', VersionedAPIData(
                fixed_entries=True,
                single_value=True,
                fully_understood=True,
                versioned_fields=[
                    ([('7.18', '>=')], 'neigh-dump-retries', KeyInfo()),
                ],
                fields={
                    'neigh-discovery-burst-delay': KeyInfo(),
                    'neigh-discovery-burst-limit': KeyInfo(),
                    'neigh-discovery-interval': KeyInfo(),
                    'neigh-keepalive-interval': KeyInfo(),
                    'partial-offload-chunk': KeyInfo(),
                    'route-index-delay-max': KeyInfo(),
                    'route-index-delay-min': KeyInfo(),
                    'route-queue-limit-high': KeyInfo(),
                    'route-queue-limit-low': KeyInfo(),
                    'shwp-reset-counter': KeyInfo(),
                },
            )),
        ],
    ),

    ('interface', 'ethernet', 'switch', 'port'): APIData(
        unversioned=VersionedAPIData(
            primary_keys=('name',),
            fixed_entries=True,
            fully_understood=True,
            versioned_fields=[
                ([('7.15', '>=')], 'egress-rate', KeyInfo()),
                ([('7.15', '>=')], 'ingress-rate', KeyInfo()),
                ([('7.15', '>=')], 'l3-hw-offloading', KeyInfo()),
                ([('7.15', '>=')], 'limit-broadcasts', KeyInfo()),
                ([('7.15', '>=')], 'limit-unknown-multicasts', KeyInfo()),
                ([('7.15', '>=')], 'limit-unknown-unicasts', KeyInfo()),
                ([('7.15', '>=')], 'mirror-egress', KeyInfo()),
                ([('7.15', '>=')], 'mirror-ingress', KeyInfo()),
                ([('7.15', '>=')], 'mirror-ingress-target', KeyInfo()),
                ([('7.15', '>=')], 'numbers', KeyInfo()),
                ([('7.15', '>=')], 'storm-rate', KeyInfo()),
            ],
            fields={
                'default-vlan-id': KeyInfo(),
                'name': KeyInfo(),
                'vlan-header': KeyInfo(default='leave-as-is'),
                'vlan-mode': KeyInfo(default='disabled'),
            },
        ),
    ),

    ('interface', 'ethernet', 'switch', 'port-isolation'): APIData(
        versioned=[
            ('6.43', '>=', VersionedAPIData(
                primary_keys=('name',),
                fixed_entries=True,
                fully_understood=True,
                versioned_fields=[
                    ([('7.15', '>=')], 'numbers', KeyInfo()),
                ],
                fields={
                    'forwarding-override': KeyInfo(can_disable=True),
                    'name': KeyInfo(),
                },
            )),
        ],
    ),

    ('interface', 'ethernet', 'switch', 'qos', 'map'): APIData(
        versioned=[
            ('7.15', '>=', VersionedAPIData(
                fully_understood=True,
                versioned_fields=[
                    ([('7.21', '>=')], 'disabled', KeyInfo()),
                ],
                fields={
                    'comment': KeyInfo(),
                    # 'copy-from': KeyInfo(write_only=True),
                    'name': KeyInfo(),
                },
            )),
        ],
    ),

    ('interface', 'ethernet', 'switch', 'qos', 'map', 'ip'): APIData(
        versioned=[
            ('7.15', '>=', VersionedAPIData(
                fully_understood=True,
                fields={
                    'comment': KeyInfo(),
                    # 'copy-from': KeyInfo(write_only=True),
                    'disabled': KeyInfo(),
                    'dscp': KeyInfo(),
                    'map': KeyInfo(),
                    'profile': KeyInfo(),
                },
            )),
        ],
    ),

    ('interface', 'ethernet', 'switch', 'qos', 'map', 'vlan'): APIData(
        versioned=[
            ('7.15', '>=', VersionedAPIData(
                fully_understood=True,
                fields={
                    'comment': KeyInfo(),
                    # 'copy-from': KeyInfo(write_only=True),
                    'dei-only': KeyInfo(),
                    'disabled': KeyInfo(),
                    'map': KeyInfo(),
                    'pcp': KeyInfo(),
                    'profile': KeyInfo(),
                },
            )),
        ],
    ),

    ('interface', 'ethernet', 'switch', 'qos', 'port'): APIData(
        versioned=[
            ('7.15', '>=', VersionedAPIData(
                fully_understood=True,
                has_identifier=True,
                # fixed_entries=True,
                # primary_keys=('numbers',),
                fields={
                    'egress-rate-queue0': KeyInfo(),
                    'egress-rate-queue1': KeyInfo(),
                    'egress-rate-queue2': KeyInfo(),
                    'egress-rate-queue3': KeyInfo(),
                    'egress-rate-queue4': KeyInfo(),
                    'egress-rate-queue5': KeyInfo(),
                    'egress-rate-queue6': KeyInfo(),
                    'egress-rate-queue7': KeyInfo(),
                    'map': KeyInfo(),
                    'numbers': KeyInfo(),
                    'pfc': KeyInfo(),
                    'profile': KeyInfo(),
                    'trust-l2': KeyInfo(),
                    'trust-l3': KeyInfo(),
                    'tx-manager': KeyInfo(),
                },
            )),
        ],
    ),

    ('interface', 'ethernet', 'switch', 'qos', 'priority-flow-control'): APIData(
        versioned=[
            ('7.15', '>=', VersionedAPIData(
                fully_understood=True,
                fields={
                    'comment': KeyInfo(),
                    # 'copy-from': KeyInfo(write_only=True),
                    'name': KeyInfo(),
                    'pause-threshold': KeyInfo(),
                    'resume-threshold': KeyInfo(),
                    'rx': KeyInfo(),
                    'traffic-class': KeyInfo(),
                    'tx': KeyInfo(),
                },
            )),
            ('7.16', '>=', 'Not supported anymore in version 7.16'),
        ],
    ),

    ('interface', 'ethernet', 'switch', 'qos', 'profile'): APIData(
        versioned=[
            ('7.15', '>=', VersionedAPIData(
                fully_understood=True,
                versioned_fields=[
                    ([('7.17', '>=')], 'disabled', KeyInfo()),
                ],
                fields={
                    'color': KeyInfo(),
                    'comment': KeyInfo(),
                    # 'copy-from': KeyInfo(write_only=True),
                    'dscp': KeyInfo(),
                    'name': KeyInfo(),
                    'pcp': KeyInfo(),
                    'traffic-class': KeyInfo(),
                },
            )),
        ],
    ),

    ('interface', 'ethernet', 'switch', 'qos', 'settings'): APIData(
        versioned=[
            ('7.15', '>=', VersionedAPIData(
                fixed_entries=True,
                single_value=True,
                fully_understood=True,
                versioned_fields=[
                    ([('7.20', '>=')], 'mirror-buffers', KeyInfo()),
                    ([('7.21', '>=')], 'mirror-profile', KeyInfo()),
                ],
                fields={
                    'multicast-buffers': KeyInfo(),
                    'shared-buffers': KeyInfo(),
                    'shared-buffers-color': KeyInfo(),
                    'shared-pool0': KeyInfo(),
                    'shared-pool1': KeyInfo(),
                    'shared-pool2': KeyInfo(),
                    'shared-pool3': KeyInfo(),
                    'shared-pool4': KeyInfo(),
                    'shared-pool5': KeyInfo(),
                    'shared-pool6': KeyInfo(),
                    'shared-pool7': KeyInfo(),
                    'treat-yellow-as': KeyInfo(),
                    'wred-shared-threshold': KeyInfo(),
                    'wred-threshold': KeyInfo(),
                },
            )),
        ],
    ),

    ('interface', 'ethernet', 'switch', 'qos', 'tx-manager'): APIData(
        versioned=[
            ('7.15', '>=', VersionedAPIData(
                fully_understood=True,
                versioned_fields=[
                    ([('7.21', '>=')], 'disabled', KeyInfo()),
                    ([('7.16', '>=')], 'queue-buffers', KeyInfo()),
                ],
                fields={
                    'comment': KeyInfo(),
                    # 'copy-from': KeyInfo(write_only=True),
                    'ecn': KeyInfo(),
                    'name': KeyInfo(),
                },
            )),
        ],
    ),

    ('interface', 'ethernet', 'switch', 'qos', 'tx-manager', 'queue'): APIData(
        versioned=[
            ('7.15', '>=', VersionedAPIData(
                fully_understood=True,
                has_identifier=True,
                # fixed_entries=True,
                # primary_keys=('numbers',),
                fields={
                    'comment': KeyInfo(),
                    'numbers': KeyInfo(),
                    'queue-buffers': KeyInfo(),
                    'schedule': KeyInfo(),
                    'shared-pool-index': KeyInfo(),
                    'use-shared-buffers': KeyInfo(),
                    'weight': KeyInfo(),
                    'wred': KeyInfo(),
                },
            )),
        ],
    ),

    ('interface', 'ethernet', 'switch', 'rule'): APIData(
        versioned=[
            ('7.15', '>=', VersionedAPIData(
                fully_understood=True,
                fields={
                    'comment': KeyInfo(),
                    # 'copy-from': KeyInfo(write_only=True),
                    'copy-to-cpu': KeyInfo(),
                    'disabled': KeyInfo(),
                    'dscp': KeyInfo(can_disable=True),
                    'dst-address': KeyInfo(can_disable=True),
                    'dst-address6': KeyInfo(can_disable=True),
                    'dst-mac-address': KeyInfo(can_disable=True),
                    'dst-port': KeyInfo(can_disable=True),
                    'flow-label': KeyInfo(can_disable=True),
                    'keep-qos-fields': KeyInfo(),
                    'mac-protocol': KeyInfo(can_disable=True),
                    'mirror': KeyInfo(),
                    'mirror-ports': KeyInfo(),
                    'new-dst-ports': KeyInfo(can_disable=True),
                    'new-qos-profile': KeyInfo(),
                    'new-vlan-id': KeyInfo(can_disable=True),
                    'new-vlan-priority': KeyInfo(can_disable=True),
                    # 'place-before': KeyInfo(write_only=True),
                    'ports': KeyInfo(can_disable=True),
                    'protocol': KeyInfo(can_disable=True),
                    'rate': KeyInfo(can_disable=True),
                    'redirect-to-cpu': KeyInfo(),
                    'src-address': KeyInfo(can_disable=True),
                    'src-address6': KeyInfo(can_disable=True),
                    'src-mac-address': KeyInfo(can_disable=True),
                    'src-port': KeyInfo(can_disable=True),
                    'switch': KeyInfo(),
                    'traffic-class': KeyInfo(can_disable=True),
                    'vlan-header': KeyInfo(can_disable=True),
                    'vlan-id': KeyInfo(can_disable=True),
                    'vlan-priority': KeyInfo(can_disable=True),
                },
            )),
        ],
    ),

    ('interface', 'ethernet', 'switch', 'vlan'): APIData(
        versioned=[
            ('7.15', '>=', VersionedAPIData(
                fully_understood=True,
                fields={
                    'comment': KeyInfo(),
                    # 'copy-from': KeyInfo(write_only=True),
                    'disabled': KeyInfo(),
                    'independent-learning': KeyInfo(),
                    'ports': KeyInfo(),
                    'switch': KeyInfo(),
                    'vlan-id': KeyInfo(),
                },
            )),
        ],
    ),

    ('interface', 'gre'): APIData(
        unversioned=VersionedAPIData(
            primary_keys=('name',),
            fully_understood=True,
            # versioned_fields=[
            #     ([('7.15', '>=')], 'copy-from', KeyInfo(write_only=True)),
            # ],
            fields={
                'allow-fast-path': KeyInfo(default=True),
                'clamp-tcp-mss': KeyInfo(default=True),
                'comment': KeyInfo(can_disable=True, remove_value=''),
                'disabled': KeyInfo(default=False),
                'dont-fragment': KeyInfo(default=False),
                'dscp': KeyInfo(default='inherit'),
                'ipsec-secret': KeyInfo(can_disable=True),
                'keepalive': KeyInfo(can_disable=True, default='10s,10'),
                'local-address': KeyInfo(default='0.0.0.0'),
                'mtu': KeyInfo(default='auto'),
                'name': KeyInfo(),
                'remote-address': KeyInfo(required=True),
            },
        ),
    ),

    ('interface', 'gre6'): APIData(
        unversioned=VersionedAPIData(
            primary_keys=('name',),
            fully_understood=True,
            versioned_fields=[
                # ([('7.15', '>=')], 'copy-from', KeyInfo(write_only=True)),
                ([('7.21', '>=')], 'dont-fragment', KeyInfo()),
            ],
            fields={
                'clamp-tcp-mss': KeyInfo(default=True),
                'comment': KeyInfo(can_disable=True, remove_value=''),
                'disabled': KeyInfo(default=False),
                'dscp': KeyInfo(default='inherit'),
                'ipsec-secret': KeyInfo(can_disable=True),
                'keepalive': KeyInfo(can_disable=True, default='10s,10'),
                'local-address': KeyInfo(default='::'),
                'mtu': KeyInfo(default='auto'),
                'name': KeyInfo(),
                'remote-address': KeyInfo(required=True),
            },
        ),
    ),

    ('interface', 'ipip'): APIData(
        versioned=[
            ('7.15', '>=', VersionedAPIData(
                fully_understood=True,
                fields={
                    'allow-fast-path': KeyInfo(),
                    'clamp-tcp-mss': KeyInfo(),
                    'comment': KeyInfo(),
                    # 'copy-from': KeyInfo(write_only=True),
                    'disabled': KeyInfo(),
                    'dont-fragment': KeyInfo(),
                    'dscp': KeyInfo(),
                    'ipsec-secret': KeyInfo(can_disable=True),
                    'keepalive': KeyInfo(can_disable=True),
                    'local-address': KeyInfo(),
                    'mtu': KeyInfo(),
                    'name': KeyInfo(),
                    'remote-address': KeyInfo(),
                },
            )),
        ],
    ),

    ('interface', 'ipipv6'): APIData(
        versioned=[
            ('7.15', '>=', VersionedAPIData(
                fully_understood=True,
                versioned_fields=[
                    ([('7.21', '>=')], 'dont-fragment', KeyInfo()),
                ],
                fields={
                    'clamp-tcp-mss': KeyInfo(),
                    'comment': KeyInfo(),
                    # 'copy-from': KeyInfo(write_only=True),
                    'disabled': KeyInfo(),
                    'dscp': KeyInfo(),
                    'ipsec-secret': KeyInfo(can_disable=True),
                    'keepalive': KeyInfo(can_disable=True),
                    'local-address': KeyInfo(),
                    'mtu': KeyInfo(),
                    'name': KeyInfo(),
                    'remote-address': KeyInfo(),
                },
            )),
        ],
    ),

    ('interface', 'l2tp-client'): APIData(
        unversioned=VersionedAPIData(
            primary_keys=('name',),
            fully_understood=True,
            versioned_fields=[
                # ([('7.15', '>=')], 'copy-from', KeyInfo(write_only=True)),
                ([('7.15', '>=')], 'l2tpv3-circuit-id', KeyInfo()),
                ([('7.18', '>=')], 'random-source-port', KeyInfo()),
            ],
            fields={
                'add-default-route': KeyInfo(default=False),
                'allow': KeyInfo(default='pap,chap,mschap1,mschap2'),
                'allow-fast-path': KeyInfo(default=False),
                'comment': KeyInfo(can_disable=True, remove_value=''),
                'connect-to': KeyInfo(required=True),
                'default-route-distance': KeyInfo(default=False),
                'dial-on-demand': KeyInfo(default=False),
                'disabled': KeyInfo(default=True),
                'ipsec-secret': KeyInfo(default=''),
                'keepalive-timeout': KeyInfo(default=60),
                'l2tp-proto-version': KeyInfo(default='l2tpv2'),
                'l2tpv3-cookie-length': KeyInfo(default=0),
                'l2tpv3-digest-hash': KeyInfo(default='md5'),
                'max-mru': KeyInfo(default=1450),
                'max-mtu': KeyInfo(default=1450),
                'mrru': KeyInfo(default='disabled'),
                'name': KeyInfo(required=True),
                'password': KeyInfo(),
                'profile': KeyInfo(default='default-encryption'),
                'src-address': KeyInfo(),
                'use-ipsec': KeyInfo(default=False),
                'use-peer-dns': KeyInfo(default=False),
                'user': KeyInfo(required=True),
            },
        ),
    ),

    ('interface', 'l2tp-ether'): APIData(
        versioned=[
            ('7.15', '>=', VersionedAPIData(
                fully_understood=True,
                fields={
                    'allow-fast-path': KeyInfo(),
                    'circuit-id': KeyInfo(),
                    'comment': KeyInfo(),
                    'connect-to': KeyInfo(),
                    'cookie-length': KeyInfo(),
                    # 'copy-from': KeyInfo(write_only=True),
                    'digest-hash': KeyInfo(),
                    'disabled': KeyInfo(),
                    'ipsec-secret': KeyInfo(),
                    'l2tp-proto-version': KeyInfo(),
                    'local-address': KeyInfo(),
                    'local-session-id': KeyInfo(),
                    'local-tunnel-id': KeyInfo(),
                    'mac-address': KeyInfo(can_disable=True),
                    'mtu': KeyInfo(),
                    'name': KeyInfo(),
                    'peer-cookie': KeyInfo(),
                    'remote-session-id': KeyInfo(),
                    'remote-tunnel-id': KeyInfo(),
                    'send-cookie': KeyInfo(),
                    'unmanaged-mode': KeyInfo(),
                    'use-ipsec': KeyInfo(),
                    'use-l2-specific-sublayer': KeyInfo(),
                },
            )),
        ],
    ),

    ('interface', 'l2tp-server'): APIData(
        versioned=[
            ('7.15', '>=', VersionedAPIData(
                fully_understood=True,
                fields={
                    'comment': KeyInfo(),
                    # 'copy-from': KeyInfo(write_only=True),
                    'disabled': KeyInfo(),
                    'name': KeyInfo(),
                    'user': KeyInfo(),
                },
            )),
        ],
    ),

    ('interface', 'l2tp-server', 'server'): APIData(
        unversioned=VersionedAPIData(
            fixed_entries=True,
            single_value=True,
            fully_understood=True,
            versioned_fields=[
                ([('7.15', '>=')], 'accept-proto-version', KeyInfo()),
                ([('7.15', '>=')], 'accept-pseudowire-type', KeyInfo()),
                ([('7.15', '>=')], 'l2tpv3-circuit-id', KeyInfo()),
                ([('7.15', '>=')], 'l2tpv3-cookie-length', KeyInfo()),
                ([('7.15', '>=')], 'l2tpv3-digest-hash', KeyInfo()),
                ([('7.15', '>=')], 'l2tpv3-ether-interface-list', KeyInfo(can_disable=True)),
            ],
            fields={
                'allow-fast-path': KeyInfo(default=False),
                'authentication': KeyInfo(default='pap,chap,mschap1,mschap2'),
                'caller-id-type': KeyInfo(default='ip-address'),
                'default-profile': KeyInfo(default='default-encryption'),
                'enabled': KeyInfo(default=False),
                'ipsec-secret': KeyInfo(default=''),
                'keepalive-timeout': KeyInfo(default=30),
                'max-mru': KeyInfo(default=1450),
                'max-mtu': KeyInfo(default=1450),
                'max-sessions': KeyInfo(default='unlimited'),
                'mrru': KeyInfo(default='disabled'),
                'one-session-per-host': KeyInfo(default=False),
                'use-ipsec': KeyInfo(default=False),
            },
        ),
    ),

    ('interface', 'list'): APIData(
        unversioned=VersionedAPIData(
            primary_keys=('name',),
            fully_understood=True,
            # versioned_fields=[
            #     ([('7.15', '>=')], 'copy-from', KeyInfo(write_only=True)),
            # ],
            fields={
                'comment': KeyInfo(can_disable=True, remove_value=''),
                'exclude': KeyInfo(default=''),
                'include': KeyInfo(default=''),
                'name': KeyInfo(),
            },
        ),
    ),

    ('interface', 'list', 'member'): APIData(
        unversioned=VersionedAPIData(
            primary_keys=('list', 'interface'),
            fully_understood=True,
            # versioned_fields=[
            #     ([('7.15', '>=')], 'copy-from', KeyInfo(write_only=True)),
            # ],
            fields={
                'comment': KeyInfo(can_disable=True, remove_value=''),
                'disabled': KeyInfo(default=False),
                'interface': KeyInfo(),
                'list': KeyInfo(),
            },
        ),
    ),

    ('interface', 'lte'): APIData(
        versioned=[
            ('7.15', '>=', VersionedAPIData(
                fully_understood=True,
                has_identifier=True,
                # fixed_entries=True,
                # primary_keys=('numbers',),
                versioned_fields=[
                    ([('7.16', '>=')], 'sms-protocol', KeyInfo()),
                ],
                fields={
                    'allow-roaming': KeyInfo(can_disable=True),
                    'apn-profiles': KeyInfo(),
                    'band': KeyInfo(),
                    'comment': KeyInfo(),
                    'disabled': KeyInfo(),
                    'modem-init': KeyInfo(can_disable=True),
                    'mtu': KeyInfo(),
                    'name': KeyInfo(),
                    'network-mode': KeyInfo(can_disable=True),
                    'nr-band': KeyInfo(),
                    'numbers': KeyInfo(),
                    'operator': KeyInfo(),
                    'pin': KeyInfo(),
                    'sms-read': KeyInfo(),
                },
            )),
        ],
    ),

    ('interface', 'lte', 'apn'): APIData(
        unversioned=VersionedAPIData(
            fully_understood=True,
            versioned_fields=[
                ([('7.15', '>=')], 'authentication', KeyInfo()),
                ([('7.15', '>=')], 'comment', KeyInfo()),
                # ([('7.15', '>=')], 'copy-from', KeyInfo(write_only=True)),
                ([('7.15', '<')], 'default', KeyInfo()),
                ([('7.15', '>=')], 'ip-type', KeyInfo()),
                ([('7.15', '>=')], 'ipv6-interface', KeyInfo()),
                ([('7.15', '>=')], 'passthrough-interface', KeyInfo()),
                ([('7.15', '>=')], 'passthrough-mac', KeyInfo()),
                ([('7.15', '>=')], 'passthrough-subnet-size', KeyInfo()),
                ([('7.15', '>=')], 'password', KeyInfo()),
                ([('7.15', '>=')], 'use-network-apn', KeyInfo()),
                ([('7.15', '>=')], 'user', KeyInfo()),
            ],
            fields={
                'add-default-route': KeyInfo(),
                'apn': KeyInfo(required=True),
                'default-route-distance': KeyInfo(),
                'name': KeyInfo(),
                'use-peer-dns': KeyInfo(),
            },
        ),
    ),

    ('interface', 'lte', 'settings'): APIData(
        versioned=[
            ('7.15', '>=', VersionedAPIData(
                fixed_entries=True,
                single_value=True,
                fully_understood=True,
                versioned_fields=[
                    ([('7.17', '>=')], 'esim-channel', KeyInfo()),
                    ([('7.19', '>=')], 'link-recovery-timer', KeyInfo()),
                ],
                fields={
                    'firmware-path': KeyInfo(),
                    'info-polling-interval': KeyInfo(),
                    'mode': KeyInfo(),
                },
            )),
        ],
    ),

    ('interface', 'macsec'): APIData(
        versioned=[
            ('7.15', '>=', VersionedAPIData(
                fully_understood=True,
                fields={
                    'cak': KeyInfo(),
                    'ckn': KeyInfo(),
                    'comment': KeyInfo(),
                    # 'copy-from': KeyInfo(write_only=True),
                    'disabled': KeyInfo(),
                    'interface': KeyInfo(),
                    'mtu': KeyInfo(),
                    'name': KeyInfo(),
                    'profile': KeyInfo(),
                },
            )),
        ],
    ),

    ('interface', 'macsec', 'profile'): APIData(
        versioned=[
            ('7.15', '>=', VersionedAPIData(
                fully_understood=True,
                fields={
                    # 'copy-from': KeyInfo(write_only=True),
                    'name': KeyInfo(),
                    'server-priority': KeyInfo(),
                },
            )),
        ],
    ),

    ('interface', 'macvlan'): APIData(
        versioned=[
            ('7.15', '>=', VersionedAPIData(
                fully_understood=True,
                fields={
                    'arp': KeyInfo(),
                    'arp-timeout': KeyInfo(),
                    'comment': KeyInfo(),
                    # 'copy-from': KeyInfo(write_only=True),
                    'disabled': KeyInfo(),
                    'interface': KeyInfo(),
                    'loop-protect': KeyInfo(),
                    'loop-protect-disable-time': KeyInfo(),
                    'loop-protect-send-interval': KeyInfo(),
                    'mac-address': KeyInfo(),
                    'mode': KeyInfo(),
                    'mtu': KeyInfo(),
                    'name': KeyInfo(),
                },
            )),
        ],
    ),

    ('interface', 'mesh'): APIData(
        versioned=[
            ('7.15', '>=', VersionedAPIData(
                fully_understood=True,
                fields={
                    'admin-mac': KeyInfo(),
                    'arp': KeyInfo(),
                    'arp-timeout': KeyInfo(),
                    'auto-mac': KeyInfo(),
                    'comment': KeyInfo(),
                    # 'copy-from': KeyInfo(write_only=True),
                    'disabled': KeyInfo(),
                    'hwmp-default-hoplimit': KeyInfo(),
                    'hwmp-prep-lifetime': KeyInfo(),
                    'hwmp-preq-destination-only': KeyInfo(),
                    'hwmp-preq-reply-and-forward': KeyInfo(),
                    'hwmp-preq-retries': KeyInfo(),
                    'hwmp-preq-waiting-time': KeyInfo(),
                    'hwmp-rann-interval': KeyInfo(),
                    'hwmp-rann-lifetime': KeyInfo(),
                    'hwmp-rann-propagation-delay': KeyInfo(),
                    'mesh-portal': KeyInfo(),
                    'mtu': KeyInfo(),
                    'name': KeyInfo(),
                    'reoptimize-paths': KeyInfo(),
                },
            )),
        ],
    ),

    ('interface', 'mesh', 'port'): APIData(
        versioned=[
            ('7.15', '>=', VersionedAPIData(
                fully_understood=True,
                fields={
                    'comment': KeyInfo(),
                    # 'copy-from': KeyInfo(write_only=True),
                    'disabled': KeyInfo(),
                    'hello-interval': KeyInfo(),
                    'interface': KeyInfo(),
                    'mesh': KeyInfo(),
                    'path-cost': KeyInfo(),
                    'port-type': KeyInfo(),
                },
            )),
        ],
    ),

    ('interface', 'ovpn-client'): APIData(
        unversioned=VersionedAPIData(
            primary_keys=('name',),
            fully_understood=True,
            # versioned_fields=[
            #     ([('7.15', '>=')], 'copy-from', KeyInfo(write_only=True)),
            # ],
            fields={
                'add-default-route': KeyInfo(default=False),
                'auth': KeyInfo(default='sha1'),
                'certificate': KeyInfo(),
                'cipher': KeyInfo(default='blowfish128'),
                'comment': KeyInfo(can_disable=True, remove_value=''),
                'connect-to': KeyInfo(),
                'disabled': KeyInfo(default=True),
                'disconnect-notify': KeyInfo(),
                'mac-address': KeyInfo(),
                'max-mtu': KeyInfo(default=1500),
                'mode': KeyInfo(default='ip'),
                'name': KeyInfo(),
                'password': KeyInfo(),
                'port': KeyInfo(default=1194),
                'profile': KeyInfo(default='default'),
                'protocol': KeyInfo(default='tcp'),
                'route-nopull': KeyInfo(default=False),
                'tls-version': KeyInfo(default='any'),
                'use-peer-dns': KeyInfo(default=True),
                'user': KeyInfo(),
                'verify-server-certificate': KeyInfo(default=False),
            },
        ),
    ),

    ('interface', 'ovpn-server'): APIData(
        versioned=[
            ('7.15', '>=', VersionedAPIData(
                fully_understood=True,
                fields={
                    'comment': KeyInfo(),
                    # 'copy-from': KeyInfo(write_only=True),
                    'disabled': KeyInfo(),
                    'name': KeyInfo(),
                    'user': KeyInfo(),
                },
            )),
        ],
    ),

    ('interface', 'ovpn-server', 'server'): APIData(
        versioned=[
            ('7.17', '>=', VersionedAPIData(
                fully_understood=True,
                versioned_fields=[
                    ([('7.21', '>=')], 'push-routes-ipv6', KeyInfo()),
                ],
                fields={
                    'auth': KeyInfo(),
                    'certificate': KeyInfo(),
                    'cipher': KeyInfo(),
                    'comment': KeyInfo(),
                    # 'copy-from': KeyInfo(write_only=True),
                    'default-profile': KeyInfo(default='default'),
                    'disabled': KeyInfo(),
                    'enable-tun-ipv6': KeyInfo(),
                    'enabled': KeyInfo(default=False),
                    'ipv6-prefix-len': KeyInfo(),
                    'keepalive-timeout': KeyInfo(default=60),
                    'mac-address': KeyInfo(),
                    'max-mtu': KeyInfo(default=1500),
                    'mode': KeyInfo(default='ip'),
                    'name': KeyInfo(default=''),
                    'netmask': KeyInfo(default=24),
                    'port': KeyInfo(default=1194),
                    'protocol': KeyInfo(default='tcp'),
                    'push-routes': KeyInfo(),
                    'redirect-gateway': KeyInfo(),
                    'reneg-sec': KeyInfo(),
                    'require-client-certificate': KeyInfo(default=False),
                    'tls-version': KeyInfo(),
                    'tun-server-ipv6': KeyInfo(),
                    'user-auth-method': KeyInfo(),
                    'vrf': KeyInfo(default='main'),
                },
            )),
            ('7.17', '<', VersionedAPIData(
                single_value=True,
                fully_understood=True,
                versioned_fields=[
                    ([('7.15', '>=')], 'certificate', KeyInfo()),
                    ([('7.15', '>=')], 'enable-tun-ipv6', KeyInfo()),
                    ([('7.15', '>=')], 'ipv6-prefix-len', KeyInfo()),
                    ([('7.15', '>=')], 'push-routes', KeyInfo()),
                    ([('7.15', '>=')], 'redirect-gateway', KeyInfo()),
                    ([('7.15', '>=')], 'reneg-sec', KeyInfo()),
                    ([('7.15', '>=')], 'tls-version', KeyInfo()),
                    ([('7.15', '>=')], 'tun-server-ipv6', KeyInfo()),
                ],
                fields={
                    'auth': KeyInfo(),
                    'cipher': KeyInfo(),
                    'default-profile': KeyInfo(default='default'),
                    'enabled': KeyInfo(default=False),
                    'keepalive-timeout': KeyInfo(default=60),
                    'mac-address': KeyInfo(),
                    'max-mtu': KeyInfo(default=1500),
                    'mode': KeyInfo(default='ip'),
                    'name': KeyInfo(default=''),
                    'netmask': KeyInfo(default=24),
                    'port': KeyInfo(default=1194),
                    'protocol': KeyInfo(default='tcp'),
                    'require-client-certificate': KeyInfo(default=False),
                },
            )),
        ],
    ),

    ('interface', 'ppp-client'): APIData(
        unversioned=VersionedAPIData(
            primary_keys=('name',),
            fully_understood=True,
            versioned_fields=[
                # ([('7.15', '>=')], 'copy-from', KeyInfo(write_only=True)),
                ([('7.20', '>=')], 'network-mode', KeyInfo(can_disable=True)),
                ([('7.15', '>=')], 'remote-address', KeyInfo()),
            ],
            fields={
                'add-default-route': KeyInfo(default=True),
                'allow': KeyInfo(default='pap,chap,mschap1,mschap2'),
                'apn': KeyInfo(default='internet'),
                'comment': KeyInfo(can_disable=True, remove_value=''),
                'data-channel': KeyInfo(default=0),
                'default-route-distance': KeyInfo(default=1),
                'dial-command': KeyInfo(default='ATDT'),
                'dial-on-demand': KeyInfo(default=True),
                'disabled': KeyInfo(default=True),
                'info-channel': KeyInfo(default=0),
                'keepalive-timeout': KeyInfo(default=30),
                'max-mru': KeyInfo(default=1500),
                'max-mtu': KeyInfo(default=1500),
                'modem-init': KeyInfo(default=''),
                'mrru': KeyInfo(default='disabled'),
                'name': KeyInfo(),
                'null-modem': KeyInfo(default=False),
                'password': KeyInfo(default=''),
                'phone': KeyInfo(default=''),
                'pin': KeyInfo(default=''),
                'port': KeyInfo(),
                'profile': KeyInfo(default='default'),
                'use-peer-dns': KeyInfo(default=True),
                'user': KeyInfo(default=''),
            },
        ),
    ),

    ('interface', 'ppp-server'): APIData(
        versioned=[
            ('7.15', '>=', VersionedAPIData(
                fully_understood=True,
                fields={
                    'authentication': KeyInfo(default='pap,chap,mschap1,mschap2'),
                    'comment': KeyInfo(),
                    # 'copy-from': KeyInfo(write_only=True),
                    'data-channel': KeyInfo(default=0),
                    'disabled': KeyInfo(default=True),
                    'max-mru': KeyInfo(default=1500),
                    'max-mtu': KeyInfo(default=1500),
                    'modem-init': KeyInfo(default=''),
                    'mrru': KeyInfo(default='disabled'),
                    'name': KeyInfo(),
                    'null-modem': KeyInfo(default=False),
                    'port': KeyInfo(default='*FFFFFFFF'),
                    'profile': KeyInfo(default='default'),
                    'ring-count': KeyInfo(default=1),
                },
            )),
        ],
    ),

    ('interface', 'pppoe-client'): APIData(
        unversioned=VersionedAPIData(
            primary_keys=('name',),
            fully_understood=True,
            # versioned_fields=[
            #     ([('7.15', '>=')], 'copy-from', KeyInfo(write_only=True)),
            # ],
            fields={
                'ac-name': KeyInfo(default=''),
                'add-default-route': KeyInfo(default=False),
                'allow': KeyInfo(default='pap,chap,mschap1,mschap2'),
                'comment': KeyInfo(can_disable=True, remove_value=''),
                'default-route-distance': KeyInfo(default=1),
                'dial-on-demand': KeyInfo(default=False),
                'disabled': KeyInfo(default=True),
                'host-uniq': KeyInfo(can_disable=True),
                'interface': KeyInfo(required=True),
                'keepalive-timeout': KeyInfo(default=10),
                'max-mru': KeyInfo(default='auto'),
                'max-mtu': KeyInfo(default='auto'),
                'mrru': KeyInfo(default='disabled'),
                'name': KeyInfo(),
                'password': KeyInfo(default=''),
                'profile': KeyInfo(default='default'),
                'service-name': KeyInfo(default=''),
                'use-peer-dns': KeyInfo(default=False),
                'user': KeyInfo(default=''),
            },
        ),
    ),

    ('interface', 'pppoe-server'): APIData(
        versioned=[
            ('7.15', '>=', VersionedAPIData(
                fully_understood=True,
                fields={
                    'comment': KeyInfo(),
                    # 'copy-from': KeyInfo(write_only=True),
                    'disabled': KeyInfo(),
                    'name': KeyInfo(),
                    'service': KeyInfo(),
                    'user': KeyInfo(),
                },
            )),
        ],
    ),

    ('interface', 'pppoe-server', 'server'): APIData(
        unversioned=VersionedAPIData(
            primary_keys=('interface',),
            fully_understood=True,
            versioned_fields=[
                ([('7.20', '>=')], 'accept-untagged', KeyInfo(default=True)),
                # ([('7.15', '>=')], 'copy-from', KeyInfo(write_only=True)),
                ([('7.17', '>=')], 'pppoe-over-vlan-range', KeyInfo(default='')),
            ],
            fields={
                'accept-empty-service': KeyInfo(default=True),
                'authentication': KeyInfo(default='pap,chap,mschap1,mschap2'),
                'comment': KeyInfo(can_disable=True, remove_value=''),
                'default-profile': KeyInfo(default='default'),
                'disabled': KeyInfo(default=True),
                'interface': KeyInfo(required=True),
                'keepalive-timeout': KeyInfo(default=10),
                'max-mru': KeyInfo(default='auto'),
                'max-mtu': KeyInfo(default='auto'),
                'max-sessions': KeyInfo(default='unlimited'),
                'mrru': KeyInfo(default='disabled'),
                'one-session-per-host': KeyInfo(default=False),
                'pado-delay': KeyInfo(default=0),
                'service-name': KeyInfo(default=''),
            },
        ),
    ),

    ('interface', 'pptp-client'): APIData(
        versioned=[
            ('7.15', '>=', VersionedAPIData(
                fully_understood=True,
                fields={
                    'add-default-route': KeyInfo(default=False),
                    'allow': KeyInfo(default='pap,chap,mschap1,mschap2'),
                    'comment': KeyInfo(),
                    'connect-to': KeyInfo(required=True),
                    # 'copy-from': KeyInfo(write_only=True),
                    'default-route-distance': KeyInfo(default=1),
                    'dial-on-demand': KeyInfo(default=False),
                    'disabled': KeyInfo(default=True),
                    'keepalive-timeout': KeyInfo(default=60),
                    'max-mru': KeyInfo(default=1450),
                    'max-mtu': KeyInfo(default=1450),
                    'mrru': KeyInfo(default='disabled'),
                    'name': KeyInfo(),
                    'password': KeyInfo(default=''),
                    'profile': KeyInfo(default='default-encryption'),
                    'use-peer-dns': KeyInfo(default=False),
                    'user': KeyInfo(required=True),
                },
            )),
        ],
    ),

    ('interface', 'pptp-server'): APIData(
        versioned=[
            ('7.15', '>=', VersionedAPIData(
                fully_understood=True,
                fields={
                    'comment': KeyInfo(),
                    # 'copy-from': KeyInfo(write_only=True),
                    'disabled': KeyInfo(default=False),
                    'name': KeyInfo(),
                    'user': KeyInfo(required=True),
                },
            )),
        ],
    ),

    ('interface', 'pptp-server', 'server'): APIData(
        unversioned=VersionedAPIData(
            fixed_entries=True,
            single_value=True,
            fully_understood=True,
            fields={
                'authentication': KeyInfo(default='mschap1,mschap2'),
                'default-profile': KeyInfo(default='default-encryption'),
                'enabled': KeyInfo(default=False),
                'keepalive-timeout': KeyInfo(default=30),
                'max-mru': KeyInfo(default=1450),
                'max-mtu': KeyInfo(default=1450),
                'mrru': KeyInfo(default='disabled'),
            },
        ),
    ),

    ('interface', 'sstp-client'): APIData(
        versioned=[
            ('7.15', '>=', VersionedAPIData(
                fully_understood=True,
                fields={
                    'add-default-route': KeyInfo(default=False),
                    'add-sni': KeyInfo(default=False),
                    'authentication': KeyInfo(default='pap,chap,mschap1,mschap2'),
                    'certificate': KeyInfo(default='none'),
                    'ciphers': KeyInfo(default='aes256-sha'),
                    'comment': KeyInfo(),
                    'connect-to': KeyInfo(required=True),
                    # 'copy-from': KeyInfo(write_only=True),
                    'default-route-distance': KeyInfo(default=1),
                    'dial-on-demand': KeyInfo(default=False),
                    'disabled': KeyInfo(default=True),
                    'http-proxy': KeyInfo(default='::'),
                    'keepalive-timeout': KeyInfo(default=60),
                    'max-mru': KeyInfo(default=1460),
                    'max-mtu': KeyInfo(default=1460),
                    'mrru': KeyInfo(default=False),
                    'name': KeyInfo(),
                    'password': KeyInfo(default=''),
                    'pfs': KeyInfo(default=False),
                    'port': KeyInfo(default=443),
                    'profile': KeyInfo(default='default'),
                    'proxy-port': KeyInfo(default=443),
                    'tls-version': KeyInfo(default='any'),
                    'user': KeyInfo(required=True),
                    'verify-server-address-from-certificate': KeyInfo(default=False),
                    'verify-server-certificate': KeyInfo(default=False),
                },
            )),
        ],
    ),

    ('interface', 'sstp-server'): APIData(
        versioned=[
            ('7.15', '>=', VersionedAPIData(
                fully_understood=True,
                fields={
                    'comment': KeyInfo(),
                    # 'copy-from': KeyInfo(write_only=True),
                    'disabled': KeyInfo(default=False),
                    'name': KeyInfo(),
                    'user': KeyInfo(required=True),
                },
            )),
        ],
    ),

    ('interface', 'sstp-server', 'server'): APIData(
        unversioned=VersionedAPIData(
            fixed_entries=True,
            single_value=True,
            fully_understood=True,
            versioned_fields=[
                ([('7.15', '>=')], 'ciphers', KeyInfo(default='aes256-sha,aes256-gcm-sha384')),
                ([('7.15', '<')], 'force-aes', KeyInfo(default=False)),
            ],
            fields={
                'authentication': KeyInfo(default='pap,chap,mschap1,mschap2'),
                'certificate': KeyInfo(default='none'),
                'default-profile': KeyInfo(default='default'),
                'enabled': KeyInfo(default=False),
                'keepalive-timeout': KeyInfo(default=60),
                'max-mru': KeyInfo(default=1500),
                'max-mtu': KeyInfo(default=1500),
                'mrru': KeyInfo(default='disabled'),
                'pfs': KeyInfo(default=False),
                'port': KeyInfo(default=443),
                'tls-version': KeyInfo(default='any'),
                'verify-client-certificate': KeyInfo(default='no'),
            },
        ),
    ),

    ('interface', 'veth'): APIData(
        versioned=[
            ('7.15', '>=', VersionedAPIData(
                fully_understood=True,
                versioned_fields=[
                    ([('7.21', '>=')], 'container-mac-address', KeyInfo()),
                    ([('7.20', '>=')], 'dhcp', KeyInfo(default=False)),
                    ([('7.20', '>=')], 'mac-address', KeyInfo(default='00:00:00:00:00:00')),
                ],
                fields={
                    'address': KeyInfo(default=''),
                    'comment': KeyInfo(),
                    # 'copy-from': KeyInfo(write_only=True),
                    'disabled': KeyInfo(default=False),
                    'gateway': KeyInfo(default=''),
                    'gateway6': KeyInfo(default=''),
                    'name': KeyInfo(),
                },
            )),
        ],
    ),

    ('interface', 'vlan'): APIData(
        unversioned=VersionedAPIData(
            primary_keys=('name',),
            fully_understood=True,
            versioned_fields=[
                # ([('7.15', '>=')], 'copy-from', KeyInfo(write_only=True)),
                ([('7.21', '>=')], 'l3-hw-offloading', KeyInfo()),
                ([('7.15', '>=')], 'mvrp', KeyInfo()),
            ],
            fields={
                'arp': KeyInfo(default='enabled'),
                'arp-timeout': KeyInfo(default='auto'),
                'comment': KeyInfo(can_disable=True, remove_value=''),
                'disabled': KeyInfo(default=False),
                'interface': KeyInfo(required=True),
                'loop-protect': KeyInfo(default='default'),
                'loop-protect-disable-time': KeyInfo(default='5m'),
                'loop-protect-send-interval': KeyInfo(default='5s'),
                'mtu': KeyInfo(default=1500),
                'name': KeyInfo(),
                'use-service-tag': KeyInfo(default=False),
                'vlan-id': KeyInfo(required=True),
            },
        ),
    ),

    ('interface', 'vpls'): APIData(
        versioned=[
            ('7.15', '>=', VersionedAPIData(
                required_one_of=[['cisco-static-id', 'vpls-id']],
                fully_understood=True,
                versioned_fields=[
                    ([('7.17', '>=')], 'bridge-pvid', KeyInfo(can_disable=True, default=1)),
                ],
                fields={
                    'arp': KeyInfo(default='enabled'),
                    'arp-timeout': KeyInfo(default='auto'),
                    'bridge': KeyInfo(can_disable=True),
                    'bridge-cost': KeyInfo(can_disable=True, default=1),
                    'bridge-horizon': KeyInfo(can_disable=True, default='none'),
                    'cisco-static-id': KeyInfo(can_disable=True),
                    'comment': KeyInfo(),
                    # 'copy-from': KeyInfo(write_only=True),
                    'disable-running-check': KeyInfo(default=False),
                    'disabled': KeyInfo(default=True),
                    'mac-address': KeyInfo(),
                    'mtu': KeyInfo(default=1500),
                    'name': KeyInfo(),
                    'peer': KeyInfo(required=True),
                    'pw-control-word': KeyInfo(can_disable=True, default='default'),
                    'pw-l2mtu': KeyInfo(can_disable=True, default=1500),
                    'pw-type': KeyInfo(can_disable=True, default='raw-ethernet'),
                    'vpls-id': KeyInfo(can_disable=True),
                },
            )),
        ],
    ),

    ('interface', 'vrrp'): APIData(
        unversioned=VersionedAPIData(
            primary_keys=('name',),
            fully_understood=True,
            versioned_fields=[
                ([('7.20', '>=')], 'connection-tracking-mode', KeyInfo(default='passive-active')),
                ([('7.20', '>=')], 'connection-tracking-port', KeyInfo(default=8275)),
                # ([('7.15', '>=')], 'copy-from', KeyInfo(write_only=True)),
                ([('7.11', '>=')], 'group-authority', KeyInfo(default='')),
                ([('7.11', '<')], 'group-master', KeyInfo(default='')),
                ([('7.11', '>=')], 'group-master', KeyInfo(write_only=True)),
                ([('7.20', '<')], 'mtu', KeyInfo(default=1500)),
            ],
            fields={
                'arp': KeyInfo(default='enabled'),
                'arp-timeout': KeyInfo(default='auto'),
                'authentication': KeyInfo(default='none'),
                'comment': KeyInfo(can_disable=True, remove_value=''),
                'disabled': KeyInfo(default=False),
                'interface': KeyInfo(required=True),
                'interval': KeyInfo(default='1s'),
                'name': KeyInfo(),
                'on-backup': KeyInfo(default=''),
                'on-fail': KeyInfo(default=''),
                'on-master': KeyInfo(default=''),
                'password': KeyInfo(default=''),
                'preemption-mode': KeyInfo(default=True),
                'priority': KeyInfo(default=100),
                'remote-address': KeyInfo(),
                'sync-connection-tracking': KeyInfo(default=False),
                'v3-protocol': KeyInfo(default='ipv4'),
                'version': KeyInfo(default=3),
                'vrid': KeyInfo(default=1),
            },
        ),
    ),

    ('interface', 'vxlan'): APIData(
        versioned=[
            ('7.15', '>=', VersionedAPIData(
                fully_understood=True,
                versioned_fields=[
                    ([('7.18', '>=')], 'bridge', KeyInfo(can_disable=True)),
                    ([('7.18', '>=')], 'bridge-pvid', KeyInfo(default=1)),
                    ([('7.20', '>=')], 'checksum', KeyInfo(default=False)),
                    ([('7.18', '>=')], 'hw', KeyInfo(default=True)),
                    ([('7.20', '>=')], 'learning', KeyInfo(default=True)),
                    ([('7.20', '>=')], 'rem-csum', KeyInfo(default='none')),
                    ([('7.18', '>=')], 'ttl', KeyInfo(default='auto')),
                    ([('7.20', '>=')], 'vtep-vrf', KeyInfo(default='main')),
                ],
                fields={
                    'allow-fast-path': KeyInfo(default=True),
                    'arp': KeyInfo(default='enabled'),
                    'arp-timeout': KeyInfo(default='auto'),
                    'comment': KeyInfo(),
                    # 'copy-from': KeyInfo(write_only=True),
                    'disabled': KeyInfo(default=False),
                    'dont-fragment': KeyInfo(default='auto'),
                    'group': KeyInfo(can_disable=True),
                    'interface': KeyInfo(can_disable=True),
                    'local-address': KeyInfo(can_disable=True),
                    'loop-protect': KeyInfo(default='default'),
                    'loop-protect-disable-time': KeyInfo(default='5m'),
                    'loop-protect-send-interval': KeyInfo(default='5s'),
                    'mac-address': KeyInfo(),
                    'max-fdb-size': KeyInfo(default=4096),
                    'mtu': KeyInfo(default=1500),
                    'name': KeyInfo(default='vxlan1'),
                    'port': KeyInfo(default=4789),
                    'vni': KeyInfo(required=True),
                    'vrf': KeyInfo(),
                    'vteps-ip-version': KeyInfo(default='ipv4'),
                },
            )),
        ],
    ),

    ('interface', 'vxlan', 'vteps'): APIData(
        versioned=[
            ('7.15', '>=', VersionedAPIData(
                fully_understood=True,
                versioned_fields=[
                    ([('7.16', '>=')], 'comment', KeyInfo()),
                    ([('7.18', '>=')], 'disabled', KeyInfo()),
                ],
                fields={
                    # 'copy-from': KeyInfo(write_only=True),
                    'interface': KeyInfo(),
                    'port': KeyInfo(),
                    'remote-ip': KeyInfo(),
                },
            )),
        ],
    ),

    ('interface', 'wifi'): APIData(
        versioned=[
            ('7.13', '>=', VersionedAPIData(
                primary_keys=('name',),
                required_one_of=[['default-name', 'radio-mac', 'master-interface']],
                fully_understood=True,
                versioned_fields=[
                    ([('7.20', '>=')], 'channel.deprioritize-unii-3-4', KeyInfo(can_disable=True)),
                    ([('7.15', '>=')], 'channel.reselect-interval', KeyInfo(can_disable=True)),
                    ([('7.19', '>=')], 'channel.reselect-time', KeyInfo(can_disable=True)),
                    ([('7.15', '>=')], 'configuration.distance', KeyInfo(can_disable=True)),
                    ([('7.21', '>=')], 'configuration.hw-protection-mode', KeyInfo()),
                    ([('7.17', '>=')], 'configuration.installation', KeyInfo(can_disable=True)),
                    ([('7.18', '>=')], 'configuration.max-clients', KeyInfo(can_disable=True)),
                    ([('7.17', '>=')], 'configuration.station-roaming', KeyInfo(can_disable=True)),
                    ([('7.15', '>=')], 'configuration.tx-chains', KeyInfo(can_disable=True)),
                    # ([('7.15', '>=')], 'copy-from', KeyInfo(write_only=True)),
                    ([('7.20', '>=')], 'datapath.openflow-switch', KeyInfo()),
                    ([('7.19', '>=')], 'datapath.traffic-processing', KeyInfo(can_disable=True)),
                    ([('7.21', '>=')], 'interworking.3gpp-info-raw', KeyInfo()),
                    ([('7.21', '>=')], 'interworking.realms-raw', KeyInfo()),
                    ([('7.21', '>=')], 'security.beacon-protection', KeyInfo()),
                    ([('7.17', '>=')], 'security.multi-passphrase-group', KeyInfo(can_disable=True)),
                    ([('7.18', '>=')], 'steering.2g-probe-delay', KeyInfo(can_disable=True)),
                    ([('7.21', '>=')], 'steering.transition-request-count', KeyInfo()),
                    ([('7.21', '>=')], 'steering.transition-request-period', KeyInfo()),
                    ([('7.21', '>=')], 'steering.transition-threshold', KeyInfo()),
                    ([('7.21', '>=')], 'steering.transition-threshold-time', KeyInfo()),
                    ([('7.21', '>=')], 'steering.transition-time', KeyInfo()),
                ],
                fields={
                    'aaa': KeyInfo(can_disable=True),
                    'aaa.called-format': KeyInfo(can_disable=True),
                    'aaa.calling-format': KeyInfo(can_disable=True),
                    'aaa.interim-update': KeyInfo(can_disable=True),
                    'aaa.mac-caching': KeyInfo(can_disable=True),
                    'aaa.nas-identifier': KeyInfo(can_disable=True),
                    'aaa.password-format': KeyInfo(can_disable=True),
                    'aaa.username-format': KeyInfo(can_disable=True),
                    'arp': KeyInfo(can_disable=True),
                    'arp-timeout': KeyInfo(default='auto'),
                    'channel': KeyInfo(can_disable=True),
                    'channel.band': KeyInfo(can_disable=True),
                    'channel.frequency': KeyInfo(can_disable=True),
                    'channel.secondary-frequency': KeyInfo(can_disable=True),
                    'channel.skip-dfs-channels': KeyInfo(can_disable=True),
                    'channel.width': KeyInfo(can_disable=True),
                    'comment': KeyInfo(can_disable=True, remove_value=''),
                    'configuration': KeyInfo(can_disable=True),
                    'configuration.antenna-gain': KeyInfo(can_disable=True),
                    'configuration.beacon-interval': KeyInfo(can_disable=True),
                    'configuration.chains': KeyInfo(can_disable=True),
                    'configuration.country': KeyInfo(can_disable=True),
                    'configuration.dtim-period': KeyInfo(can_disable=True),
                    'configuration.hide-ssid': KeyInfo(can_disable=True),
                    'configuration.manager': KeyInfo(can_disable=True),
                    'configuration.mode': KeyInfo(can_disable=True),
                    'configuration.multicast-enhance': KeyInfo(can_disable=True),
                    'configuration.qos-classifier': KeyInfo(can_disable=True),
                    'configuration.ssid': KeyInfo(can_disable=True),
                    'configuration.tx-chain': KeyInfo(can_disable=True),
                    'configuration.tx-power': KeyInfo(can_disable=True),
                    'datapath': KeyInfo(can_disable=True),
                    'datapath.bridge': KeyInfo(can_disable=True),
                    'datapath.bridge-cost': KeyInfo(can_disable=True),
                    'datapath.bridge-horizon': KeyInfo(can_disable=True),
                    'datapath.client-isolation': KeyInfo(can_disable=True),
                    'datapath.interface-list': KeyInfo(can_disable=True),
                    'datapath.vlan-id': KeyInfo(can_disable=True),
                    'default-name': KeyInfo(),
                    'disable-running-check': KeyInfo(can_disable=True),
                    'disabled': KeyInfo(default=True),
                    'interworking': KeyInfo(can_disable=True),
                    'interworking.3gpp-info': KeyInfo(can_disable=True),
                    'interworking.authentication-types': KeyInfo(can_disable=True),
                    'interworking.connection-capabilities': KeyInfo(can_disable=True),
                    'interworking.domain-names': KeyInfo(can_disable=True),
                    'interworking.esr': KeyInfo(can_disable=True),
                    'interworking.hessid': KeyInfo(can_disable=True),
                    'interworking.hotspot20': KeyInfo(can_disable=True),
                    'interworking.hotspot20-dgaf': KeyInfo(can_disable=True),
                    'interworking.internet': KeyInfo(can_disable=True),
                    'interworking.ipv4-availability': KeyInfo(can_disable=True),
                    'interworking.ipv6-availability': KeyInfo(can_disable=True),
                    'interworking.network-type': KeyInfo(can_disable=True),
                    'interworking.operational-classes': KeyInfo(can_disable=True),
                    'interworking.operator-names': KeyInfo(can_disable=True),
                    'interworking.realms': KeyInfo(can_disable=True),
                    'interworking.roaming-ois': KeyInfo(can_disable=True),
                    'interworking.uesa': KeyInfo(can_disable=True),
                    'interworking.venue': KeyInfo(can_disable=True),
                    'interworking.venue-names': KeyInfo(can_disable=True),
                    'interworking.wan-at-capacity': KeyInfo(can_disable=True),
                    'interworking.wan-downlink': KeyInfo(can_disable=True),
                    'interworking.wan-downlink-load': KeyInfo(can_disable=True),
                    'interworking.wan-measurement-duration': KeyInfo(can_disable=True),
                    'interworking.wan-status': KeyInfo(can_disable=True),
                    'interworking.wan-symmetric': KeyInfo(can_disable=True),
                    'interworking.wan-uplink': KeyInfo(can_disable=True),
                    'interworking.wan-uplink-load': KeyInfo(can_disable=True),
                    'l2mtu': KeyInfo(can_disable=True, default=1560),
                    'mac-address': KeyInfo(),
                    'master-interface': KeyInfo(can_disable=True),
                    'mtu': KeyInfo(can_disable=True, default=1500),
                    'name': KeyInfo(),
                    'radio-mac': KeyInfo(can_disable=True),
                    'security': KeyInfo(can_disable=True),
                    'security.authentication-types': KeyInfo(can_disable=True),
                    'security.connect-group': KeyInfo(can_disable=True),
                    'security.connect-priority': KeyInfo(can_disable=True),
                    'security.dh-groups': KeyInfo(can_disable=True),
                    'security.disable-pmkid': KeyInfo(can_disable=True),
                    'security.eap-accounting': KeyInfo(can_disable=True),
                    'security.eap-anonymous-identity': KeyInfo(can_disable=True),
                    'security.eap-certificate-mode': KeyInfo(can_disable=True),
                    'security.eap-methods': KeyInfo(can_disable=True),
                    'security.eap-password': KeyInfo(can_disable=True),
                    'security.eap-tls-certificate': KeyInfo(can_disable=True),
                    'security.eap-username': KeyInfo(can_disable=True),
                    'security.encryption': KeyInfo(can_disable=True),
                    'security.ft': KeyInfo(can_disable=True),
                    'security.ft-mobility-domain': KeyInfo(can_disable=True),
                    'security.ft-nas-identifier': KeyInfo(can_disable=True),
                    'security.ft-over-ds': KeyInfo(can_disable=True),
                    'security.ft-preserve-vlanid': KeyInfo(can_disable=True),
                    'security.ft-r0-key-lifetime': KeyInfo(can_disable=True),
                    'security.ft-reassociation-deadline': KeyInfo(can_disable=True),
                    'security.group-encryption': KeyInfo(can_disable=True),
                    'security.group-key-update': KeyInfo(can_disable=True),
                    'security.management-encryption': KeyInfo(can_disable=True),
                    'security.management-protection': KeyInfo(can_disable=True),
                    'security.owe-transition-interface': KeyInfo(can_disable=True),
                    'security.passphrase': KeyInfo(can_disable=True),
                    'security.sae-anti-clogging-threshold': KeyInfo(can_disable=True),
                    'security.sae-max-failure-rate': KeyInfo(can_disable=True),
                    'security.sae-pwe': KeyInfo(can_disable=True),
                    'security.wps': KeyInfo(can_disable=True),
                    'steering': KeyInfo(can_disable=True),
                    'steering.neighbor-group': KeyInfo(can_disable=True),
                    'steering.rrm': KeyInfo(can_disable=True),
                    'steering.wnm': KeyInfo(can_disable=True),
                },
            )),
        ],
    ),

    ('interface', 'wifi', 'aaa'): APIData(
        versioned=[
            ('7.13', '>=', VersionedAPIData(
                primary_keys=('name',),
                fully_understood=True,
                # versioned_fields=[
                #     ([('7.15', '>=')], 'copy-from', KeyInfo(write_only=True)),
                # ],
                fields={
                    'called-format': KeyInfo(can_disable=True),
                    'calling-format': KeyInfo(can_disable=True),
                    'comment': KeyInfo(can_disable=True, remove_value=''),
                    'disabled': KeyInfo(default=False),
                    'interim-update': KeyInfo(can_disable=True),
                    'mac-caching': KeyInfo(can_disable=True),
                    'name': KeyInfo(),
                    'nas-identifier': KeyInfo(can_disable=True),
                    'password-format': KeyInfo(can_disable=True),
                    'username-format': KeyInfo(can_disable=True),
                },
            )),
        ],
    ),

    ('interface', 'wifi', 'access-list'): APIData(
        versioned=[
            ('7.13', '>=', VersionedAPIData(
                fully_understood=True,
                versioned_fields=[
                    # ([('7.15', '>=')], 'copy-from', KeyInfo(write_only=True)),
                    ([('7.21', '>=')], 'days', KeyInfo()),
                    ([('7.17', '>=')], 'multi-passphrase-group', KeyInfo(can_disable=True)),
                    # ([('7.15', '>=')], 'place-before', KeyInfo(write_only=True)),
                ],
                fields={
                    'action': KeyInfo(can_disable=True, default='accept'),
                    'allow-signal-out-of-range': KeyInfo(can_disable=True),
                    'client-isolation': KeyInfo(can_disable=True),
                    'comment': KeyInfo(can_disable=True, remove_value=''),
                    'disabled': KeyInfo(default=False),
                    'interface': KeyInfo(can_disable=True),
                    'mac-address': KeyInfo(can_disable=True),
                    'mac-address-mask': KeyInfo(can_disable=True),
                    'passphrase': KeyInfo(can_disable=True),
                    'radius-accounting': KeyInfo(can_disable=True),
                    'signal-range': KeyInfo(can_disable=True),
                    'ssid-regexp': KeyInfo(can_disable=True),
                    'time': KeyInfo(can_disable=True),
                    'vlan-id': KeyInfo(can_disable=True),
                },
            )),
        ],
    ),

    ('interface', 'wifi', 'cap'): APIData(
        versioned=[
            ('7.13', '>=', VersionedAPIData(
                fixed_entries=True,
                single_value=True,
                fully_understood=True,
                fields={
                    'caps-man-addresses': KeyInfo(can_disable=True, default=''),
                    'caps-man-certificate-common-names': KeyInfo(can_disable=True, default=''),
                    'caps-man-names': KeyInfo(can_disable=True, default=''),
                    'certificate': KeyInfo(can_disable=True, default='none'),
                    'discovery-interfaces': KeyInfo(can_disable=True, default=''),
                    'enabled': KeyInfo(default=False),
                    'lock-to-caps-man': KeyInfo(can_disable=True, default=False),
                    'slaves-datapath': KeyInfo(can_disable=True),
                    'slaves-static': KeyInfo(can_disable=True),
                },
            )),
        ],
    ),

    ('interface', 'wifi', 'capsman'): APIData(
        versioned=[
            ('7.13', '>=', VersionedAPIData(
                fixed_entries=True,
                single_value=True,
                fully_understood=True,
                fields={
                    'ca-certificate': KeyInfo(can_disable=True, default=''),
                    'certificate': KeyInfo(can_disable=True, default='none'),
                    'enabled': KeyInfo(default=False),
                    'interfaces': KeyInfo(can_disable=True, default=''),
                    'package-path': KeyInfo(default=''),
                    'require-peer-certificate': KeyInfo(default=False),
                    'upgrade-policy': KeyInfo(default='none'),
                },
            )),
        ],
    ),

    ('interface', 'wifi', 'channel'): APIData(
        versioned=[
            ('7.13', '>=', VersionedAPIData(
                primary_keys=('name',),
                fully_understood=True,
                versioned_fields=[
                    # ([('7.15', '>=')], 'copy-from', KeyInfo(write_only=True)),
                    ([('7.20', '>=')], 'deprioritize-unii-3-4', KeyInfo(can_disable=True)),
                    ([('7.18', '>=')], 'reselect-interval', KeyInfo(can_disable=True)),
                    ([('7.19', '>=')], 'reselect-time', KeyInfo(can_disable=True)),
                ],
                fields={
                    'band': KeyInfo(can_disable=True),
                    'comment': KeyInfo(can_disable=True, remove_value=''),
                    'disabled': KeyInfo(default=False),
                    'frequency': KeyInfo(can_disable=True),
                    'name': KeyInfo(),
                    'secondary-frequency': KeyInfo(can_disable=True),
                    'skip-dfs-channels': KeyInfo(can_disable=True),
                    'width': KeyInfo(can_disable=True),
                },
            )),
        ],
    ),

    ('interface', 'wifi', 'configuration'): APIData(
        versioned=[
            ('7.13', '>=', VersionedAPIData(
                primary_keys=('name',),
                fully_understood=True,
                versioned_fields=[
                    ([('7.13', '>=')], 'aaa.called-format', KeyInfo(can_disable=True)),
                    ([('7.13', '>=')], 'aaa.calling-format', KeyInfo(can_disable=True)),
                    ([('7.13', '>=')], 'aaa.interim-update', KeyInfo(can_disable=True)),
                    ([('7.13', '>=')], 'aaa.mac-caching', KeyInfo(can_disable=True)),
                    ([('7.13', '>=')], 'aaa.nas-identifier', KeyInfo(can_disable=True)),
                    ([('7.13', '>=')], 'aaa.password-format', KeyInfo(can_disable=True)),
                    ([('7.13', '>=')], 'aaa.username-format', KeyInfo(can_disable=True)),
                    ([('7.13', '>=')], 'channel.band', KeyInfo(can_disable=True)),
                    ([('7.20', '>=')], 'channel.deprioritize-unii-3-4', KeyInfo(can_disable=True)),
                    ([('7.13', '>=')], 'channel.frequency', KeyInfo(can_disable=True)),
                    ([('7.18', '>=')], 'channel.reselect-interval', KeyInfo(can_disable=True)),
                    ([('7.19', '>=')], 'channel.reselect-time', KeyInfo(can_disable=True)),
                    ([('7.13', '>=')], 'channel.secondary-frequency', KeyInfo(can_disable=True)),
                    ([('7.13', '>=')], 'channel.skip-dfs-channels', KeyInfo(can_disable=True)),
                    ([('7.13', '>=')], 'channel.width', KeyInfo(can_disable=True)),
                    # ([('7.15', '>=')], 'copy-from', KeyInfo(write_only=True)),
                    ([('7.13', '>=')], 'datapath.bridge', KeyInfo(can_disable=True)),
                    ([('7.13', '>=')], 'datapath.bridge-cost', KeyInfo(can_disable=True)),
                    ([('7.13', '>=')], 'datapath.bridge-horizon', KeyInfo(can_disable=True)),
                    ([('7.13', '>=')], 'datapath.client-isolation', KeyInfo(can_disable=True)),
                    ([('7.13', '>=')], 'datapath.interface-list', KeyInfo(can_disable=True)),
                    ([('7.20', '>=')], 'datapath.openflow-switch', KeyInfo()),
                    ([('7.19', '>=')], 'datapath.traffic-processing', KeyInfo(can_disable=True)),
                    ([('7.13', '>=')], 'datapath.vlan-id', KeyInfo(can_disable=True)),
                    ([('7.15', '>=')], 'distance', KeyInfo(can_disable=True)),
                    ([('7.21', '>=')], 'hw-protection-mode', KeyInfo()),
                    ([('7.17', '>=')], 'installation', KeyInfo(can_disable=True)),
                    ([('7.13', '>=')], 'interworking.3gpp-info', KeyInfo(can_disable=True)),
                    ([('7.21', '>=')], 'interworking.3gpp-info-raw', KeyInfo()),
                    ([('7.13', '>=')], 'interworking.authentication-types', KeyInfo(can_disable=True)),
                    ([('7.13', '>=')], 'interworking.connection-capabilities', KeyInfo(can_disable=True)),
                    ([('7.13', '>=')], 'interworking.domain-names', KeyInfo(can_disable=True)),
                    ([('7.13', '>=')], 'interworking.esr', KeyInfo(can_disable=True)),
                    ([('7.13', '>=')], 'interworking.hessid', KeyInfo(can_disable=True)),
                    ([('7.13', '>=')], 'interworking.hotspot20', KeyInfo(can_disable=True)),
                    ([('7.13', '>=')], 'interworking.hotspot20-dgaf', KeyInfo(can_disable=True)),
                    ([('7.13', '>=')], 'interworking.internet', KeyInfo(can_disable=True)),
                    ([('7.13', '>=')], 'interworking.ipv4-availability', KeyInfo(can_disable=True)),
                    ([('7.13', '>=')], 'interworking.ipv6-availability', KeyInfo(can_disable=True)),
                    ([('7.13', '>=')], 'interworking.network-type', KeyInfo(can_disable=True)),
                    ([('7.13', '>=')], 'interworking.operational-classes', KeyInfo(can_disable=True)),
                    ([('7.13', '>=')], 'interworking.operator-names', KeyInfo(can_disable=True)),
                    ([('7.13', '>=')], 'interworking.realms', KeyInfo(can_disable=True)),
                    ([('7.21', '>=')], 'interworking.realms-raw', KeyInfo()),
                    ([('7.13', '>=')], 'interworking.roaming-ois', KeyInfo(can_disable=True)),
                    ([('7.13', '>=')], 'interworking.uesa', KeyInfo(can_disable=True)),
                    ([('7.13', '>=')], 'interworking.venue', KeyInfo(can_disable=True)),
                    ([('7.13', '>=')], 'interworking.venue-names', KeyInfo(can_disable=True)),
                    ([('7.13', '>=')], 'interworking.wan-at-capacity', KeyInfo(can_disable=True)),
                    ([('7.13', '>=')], 'interworking.wan-downlink', KeyInfo(can_disable=True)),
                    ([('7.13', '>=')], 'interworking.wan-downlink-load', KeyInfo(can_disable=True)),
                    ([('7.13', '>=')], 'interworking.wan-measurement-duration', KeyInfo(can_disable=True)),
                    ([('7.13', '>=')], 'interworking.wan-status', KeyInfo(can_disable=True)),
                    ([('7.15', '>=')], 'interworking.wan-symmetric', KeyInfo(can_disable=True)),
                    ([('7.13', '>=')], 'interworking.wan-uplink', KeyInfo(can_disable=True)),
                    ([('7.13', '>=')], 'interworking.wan-uplink-load', KeyInfo(can_disable=True)),
                    ([('7.18', '>=')], 'max-clients', KeyInfo(can_disable=True)),
                    ([('7.13', '>=')], 'security.authentication-types', KeyInfo(can_disable=True)),
                    ([('7.21', '>=')], 'security.beacon-protection', KeyInfo()),
                    ([('7.13', '>=')], 'security.connect-group', KeyInfo(can_disable=True)),
                    ([('7.13', '>=')], 'security.connect-priority', KeyInfo(can_disable=True)),
                    ([('7.13', '>=')], 'security.dh-groups', KeyInfo(can_disable=True)),
                    ([('7.13', '>=')], 'security.disable-pmkid', KeyInfo(can_disable=True)),
                    ([('7.13', '>=')], 'security.eap-accounting', KeyInfo(can_disable=True)),
                    ([('7.13', '>=')], 'security.eap-anonymous-identity', KeyInfo(can_disable=True)),
                    ([('7.13', '>=')], 'security.eap-certificate-mode', KeyInfo(can_disable=True)),
                    ([('7.13', '>=')], 'security.eap-methods', KeyInfo(can_disable=True)),
                    ([('7.13', '>=')], 'security.eap-password', KeyInfo(can_disable=True)),
                    ([('7.13', '>=')], 'security.eap-tls-certificate', KeyInfo(can_disable=True)),
                    ([('7.13', '>=')], 'security.eap-username', KeyInfo(can_disable=True)),
                    ([('7.13', '>=')], 'security.encryption', KeyInfo(can_disable=True)),
                    ([('7.13', '>=')], 'security.ft', KeyInfo(can_disable=True)),
                    ([('7.13', '>=')], 'security.ft-mobility-domain', KeyInfo(can_disable=True)),
                    ([('7.13', '>=')], 'security.ft-nas-identifier', KeyInfo(can_disable=True)),
                    ([('7.13', '>=')], 'security.ft-over-ds', KeyInfo(can_disable=True)),
                    ([('7.13', '>=')], 'security.ft-preserve-vlanid', KeyInfo(can_disable=True)),
                    ([('7.13', '>=')], 'security.ft-r0-key-lifetime', KeyInfo(can_disable=True)),
                    ([('7.13', '>=')], 'security.ft-reassociation-deadline', KeyInfo(can_disable=True)),
                    ([('7.13', '>=')], 'security.group-encryption', KeyInfo(can_disable=True)),
                    ([('7.13', '>=')], 'security.group-key-update', KeyInfo(can_disable=True)),
                    ([('7.13', '>=')], 'security.management-encryption', KeyInfo(can_disable=True)),
                    ([('7.13', '>=')], 'security.management-protection', KeyInfo(can_disable=True)),
                    ([('7.17', '>=')], 'security.multi-passphrase-group', KeyInfo(can_disable=True)),
                    ([('7.13', '>=')], 'security.owe-transition-interface', KeyInfo(can_disable=True)),
                    ([('7.13', '>=')], 'security.passphrase', KeyInfo(can_disable=True)),
                    ([('7.13', '>=')], 'security.sae-anti-clogging-threshold', KeyInfo(can_disable=True)),
                    ([('7.13', '>=')], 'security.sae-max-failure-rate', KeyInfo(can_disable=True)),
                    ([('7.13', '>=')], 'security.sae-pwe', KeyInfo(can_disable=True)),
                    ([('7.13', '>=')], 'security.wps', KeyInfo(can_disable=True)),
                    ([('7.17', '>=')], 'station-roaming', KeyInfo(can_disable=True)),
                    ([('7.18', '>=')], 'steering.2g-probe-delay', KeyInfo(can_disable=True)),
                    ([('7.13', '>=')], 'steering.neighbor-group', KeyInfo(can_disable=True)),
                    ([('7.13', '>=')], 'steering.rrm', KeyInfo(can_disable=True)),
                    ([('7.21', '>=')], 'steering.transition-request-count', KeyInfo()),
                    ([('7.21', '>=')], 'steering.transition-request-period', KeyInfo()),
                    ([('7.21', '>=')], 'steering.transition-threshold', KeyInfo()),
                    ([('7.21', '>=')], 'steering.transition-threshold-time', KeyInfo()),
                    ([('7.21', '>=')], 'steering.transition-time', KeyInfo()),
                    ([('7.13', '>=')], 'steering.wnm', KeyInfo(can_disable=True)),
                ],
                fields={
                    'aaa': KeyInfo(can_disable=True),
                    'antenna-gain': KeyInfo(can_disable=True),
                    'beacon-interval': KeyInfo(can_disable=True),
                    'chains': KeyInfo(can_disable=True),
                    'channel': KeyInfo(can_disable=True),
                    'comment': KeyInfo(can_disable=True, remove_value=''),
                    'country': KeyInfo(can_disable=True),
                    'datapath': KeyInfo(can_disable=True),
                    'disabled': KeyInfo(default=False),
                    'dtim-period': KeyInfo(can_disable=True),
                    'hide-ssid': KeyInfo(default=False),
                    'interworking': KeyInfo(can_disable=True),
                    'manager': KeyInfo(can_disable=True),
                    'mode': KeyInfo(can_disable=True),
                    'multicast-enhance': KeyInfo(can_disable=True),
                    'name': KeyInfo(),
                    'qos-classifier': KeyInfo(can_disable=True),
                    'security': KeyInfo(can_disable=True),
                    'ssid': KeyInfo(can_disable=True),
                    'steering': KeyInfo(can_disable=True),
                    'tx-chains': KeyInfo(can_disable=True),
                    'tx-power': KeyInfo(can_disable=True),
                },
            )),
        ],
    ),

    ('interface', 'wifi', 'datapath'): APIData(
        versioned=[
            ('7.13', '>=', VersionedAPIData(
                primary_keys=('name',),
                fully_understood=True,
                versioned_fields=[
                    # ([('7.15', '>=')], 'copy-from', KeyInfo(write_only=True)),
                    ([('7.20', '>=')], 'openflow-switch', KeyInfo()),
                    ([('7.19', '>=')], 'traffic-processing', KeyInfo(can_disable=True)),
                ],
                fields={
                    'bridge': KeyInfo(can_disable=True),
                    'bridge-cost': KeyInfo(can_disable=True),
                    'bridge-horizon': KeyInfo(can_disable=True),
                    'client-isolation': KeyInfo(can_disable=True),
                    'comment': KeyInfo(can_disable=True, remove_value=''),
                    'disabled': KeyInfo(default=False),
                    'interface-list': KeyInfo(can_disable=True),
                    'name': KeyInfo(),
                    'vlan-id': KeyInfo(can_disable=True),
                },
            )),
        ],
    ),

    ('interface', 'wifi', 'interworking'): APIData(
        versioned=[
            ('7.13', '>=', VersionedAPIData(
                primary_keys=('name',),
                fully_understood=True,
                versioned_fields=[
                    ([('7.21', '>=')], '3gpp-info-raw', KeyInfo()),
                    # ([('7.15', '>=')], 'copy-from', KeyInfo(write_only=True)),
                    ([('7.21', '>=')], 'realms-raw', KeyInfo()),
                ],
                fields={
                    '3gpp-info': KeyInfo(can_disable=True),
                    'authentication-types': KeyInfo(can_disable=True),
                    'comment': KeyInfo(can_disable=True, remove_value=''),
                    'connection-capabilities': KeyInfo(can_disable=True),
                    'disabled': KeyInfo(default=False),
                    'domain-names': KeyInfo(can_disable=True),
                    'esr': KeyInfo(can_disable=True),
                    'hessid': KeyInfo(can_disable=True),
                    'hotspot20': KeyInfo(can_disable=True),
                    'hotspot20-dgaf': KeyInfo(can_disable=True),
                    'internet': KeyInfo(can_disable=True),
                    'ipv4-availability': KeyInfo(can_disable=True),
                    'ipv6-availability': KeyInfo(can_disable=True),
                    'name': KeyInfo(),
                    'network-type': KeyInfo(can_disable=True),
                    'operational-classes': KeyInfo(can_disable=True),
                    'operator-names': KeyInfo(can_disable=True),
                    'realms': KeyInfo(can_disable=True),
                    'roaming-ois': KeyInfo(can_disable=True),
                    'uesa': KeyInfo(can_disable=True),
                    'venue': KeyInfo(can_disable=True),
                    'venue-names': KeyInfo(can_disable=True),
                    'wan-at-capacity': KeyInfo(can_disable=True),
                    'wan-downlink': KeyInfo(can_disable=True),
                    'wan-downlink-load': KeyInfo(can_disable=True),
                    'wan-measurement-duration': KeyInfo(can_disable=True),
                    'wan-status': KeyInfo(can_disable=True),
                    'wan-symmetric': KeyInfo(can_disable=True),
                    'wan-uplink': KeyInfo(can_disable=True),
                    'wan-uplink-load': KeyInfo(can_disable=True),
                },
            )),
        ],
    ),

    ('interface', 'wifi', 'provisioning'): APIData(
        versioned=[
            ('7.13', '>=', VersionedAPIData(
                fully_understood=True,
                versioned_fields=[
                    # ([('7.15', '>=')], 'copy-from', KeyInfo(write_only=True)),
                    # ([('7.15', '>=')], 'place-before', KeyInfo(write_only=True)),
                    ([('7.16', '>=')], 'slave-name-format', KeyInfo()),
                ],
                fields={
                    'action': KeyInfo(default='none'),
                    'address-ranges': KeyInfo(can_disable=True),
                    'comment': KeyInfo(can_disable=True, remove_value=''),
                    'common-name-regexp': KeyInfo(can_disable=True),
                    'disabled': KeyInfo(default=False),
                    'identity-regexp': KeyInfo(can_disable=True),
                    'master-configuration': KeyInfo(can_disable=True),
                    'name-format': KeyInfo(),
                    'radio-mac': KeyInfo(can_disable=True),
                    'slave-configurations': KeyInfo(can_disable=True),
                    'supported-bands': KeyInfo(can_disable=True),
                },
            )),
        ],
    ),

    ('interface', 'wifi', 'radio', 'settings'): APIData(
        versioned=[
            ('7.17', '>=', VersionedAPIData(
                fixed_entries=True,
                single_value=True,
                fully_understood=True,
                fields={
                    'external-antenna': KeyInfo(can_disable=True),
                    'wifi-band': KeyInfo(can_disable=True),
                },
            )),
        ],
    ),

    ('interface', 'wifi', 'security'): APIData(
        versioned=[
            ('7.13', '>=', VersionedAPIData(
                primary_keys=('name',),
                fully_understood=True,
                versioned_fields=[
                    ([('7.21', '>=')], 'beacon-protection', KeyInfo()),
                    # ([('7.15', '>=')], 'copy-from', KeyInfo(write_only=True)),
                    ([('7.17', '>=')], 'multi-passphrase-group', KeyInfo(can_disable=True)),
                ],
                fields={
                    'authentication-types': KeyInfo(can_disable=True),
                    'comment': KeyInfo(can_disable=True, remove_value=''),
                    'connect-group': KeyInfo(can_disable=True),
                    'connect-priority': KeyInfo(can_disable=True),
                    'dh-groups': KeyInfo(can_disable=True),
                    'disable-pmkid': KeyInfo(can_disable=True),
                    'disabled': KeyInfo(default=False),
                    'eap-accounting': KeyInfo(can_disable=True),
                    'eap-anonymous-identity': KeyInfo(can_disable=True),
                    'eap-certificate-mode': KeyInfo(can_disable=True),
                    'eap-methods': KeyInfo(can_disable=True),
                    'eap-password': KeyInfo(can_disable=True),
                    'eap-tls-certificate': KeyInfo(can_disable=True),
                    'eap-username': KeyInfo(can_disable=True),
                    'encryption': KeyInfo(can_disable=True),
                    'ft': KeyInfo(can_disable=True),
                    'ft-mobility-domain': KeyInfo(can_disable=True),
                    'ft-nas-identifier': KeyInfo(can_disable=True),
                    'ft-over-ds': KeyInfo(can_disable=True),
                    'ft-preserve-vlanid': KeyInfo(can_disable=True),
                    'ft-r0-key-lifetime': KeyInfo(can_disable=True),
                    'ft-reassociation-deadline': KeyInfo(can_disable=True),
                    'group-encryption': KeyInfo(can_disable=True),
                    'group-key-update': KeyInfo(can_disable=True),
                    'management-encryption': KeyInfo(can_disable=True),
                    'management-protection': KeyInfo(can_disable=True),
                    'name': KeyInfo(),
                    'owe-transition-interface': KeyInfo(can_disable=True),
                    'passphrase': KeyInfo(can_disable=True),
                    'sae-anti-clogging-threshold': KeyInfo(can_disable=True),
                    'sae-max-failure-rate': KeyInfo(can_disable=True),
                    'sae-pwe': KeyInfo(can_disable=True),
                    'wps': KeyInfo(can_disable=True),
                },
            )),
        ],
    ),

    ('interface', 'wifi', 'security', 'multi-passphrase'): APIData(
        versioned=[
            ('7.17', '>=', VersionedAPIData(
                fully_understood=True,
                fields={
                    'comment': KeyInfo(),
                    # 'copy-from': KeyInfo(write_only=True),
                    'disabled': KeyInfo(),
                    'expires': KeyInfo(can_disable=True),
                    'group': KeyInfo(),
                    'isolation': KeyInfo(can_disable=True),
                    'passphrase': KeyInfo(),
                    'vlan-id': KeyInfo(can_disable=True),
                },
            )),
        ],
    ),

    ('interface', 'wifi', 'steering'): APIData(
        versioned=[
            ('7.13', '>=', VersionedAPIData(
                primary_keys=('name',),
                fully_understood=True,
                versioned_fields=[
                    ([('7.18', '>=')], '2g-probe-delay', KeyInfo(can_disable=True)),
                    # ([('7.15', '>=')], 'copy-from', KeyInfo(write_only=True)),
                    ([('7.21', '>=')], 'transition-request-count', KeyInfo()),
                    ([('7.21', '>=')], 'transition-request-period', KeyInfo()),
                    ([('7.21', '>=')], 'transition-threshold', KeyInfo()),
                    ([('7.21', '>=')], 'transition-threshold-time', KeyInfo()),
                    ([('7.21', '>=')], 'transition-time', KeyInfo()),
                ],
                fields={
                    'comment': KeyInfo(can_disable=True, remove_value=''),
                    'disabled': KeyInfo(default=False),
                    'name': KeyInfo(),
                    'neighbor-group': KeyInfo(can_disable=True),
                    'rrm': KeyInfo(can_disable=True),
                    'wnm': KeyInfo(can_disable=True),
                },
            )),
        ],
    ),

    ('interface', 'wifi', 'steering', 'neighbor-group'): APIData(
        versioned=[
            ('7.15', '>=', VersionedAPIData(
                fully_understood=True,
                has_identifier=True,
                # fixed_entries=True,
                # primary_keys=('numbers',),
                fields={
                    'comment': KeyInfo(),
                    'numbers': KeyInfo(),
                },
            )),
        ],
    ),

    ('interface', 'wifiwave2'): APIData(
        versioned=[
            ('7.13', '>=', 'RouterOS 7.13 uses WiFi package'),
            ('7.8', '>=', VersionedAPIData(
                primary_keys=('name',),
                required_one_of=[['default-name', 'master-interface']],
                fully_understood=True,
                fields={
                    'aaa': KeyInfo(),
                    'arp': KeyInfo(default='enabled'),
                    'arp-timeout': KeyInfo(default='auto'),
                    'channel': KeyInfo(),
                    'configuration': KeyInfo(),
                    'datapath': KeyInfo(),
                    'default-name': KeyInfo(),
                    'disable-running-check': KeyInfo(default=False),
                    'interworking': KeyInfo(),
                    'l2mtu': KeyInfo(default=1600),
                    'mac-address': KeyInfo(),
                    'master-interface': KeyInfo(),
                    'mtu': KeyInfo(default=1500),
                    'name': KeyInfo(),
                    'security': KeyInfo(),
                    'steering': KeyInfo(),
                },
            )),
        ],
    ),

    ('interface', 'wifiwave2', 'aaa'): APIData(
        versioned=[
            ('7.13', '>=', 'RouterOS 7.13 uses WiFi package'),
            ('7.8', '>=', VersionedAPIData(
                primary_keys=('name',),
                fully_understood=True,
                fields={
                    'called-format': KeyInfo(can_disable=True),
                    'calling-format': KeyInfo(can_disable=True),
                    'comment': KeyInfo(can_disable=True, remove_value=''),
                    'disabled': KeyInfo(default=True),
                    'interim-update': KeyInfo(can_disable=True),
                    'mac-caching': KeyInfo(can_disable=True),
                    'name': KeyInfo(),
                    'nas-identifier': KeyInfo(can_disable=True),
                    'password-format': KeyInfo(can_disable=True),
                    'username-format': KeyInfo(can_disable=True),
                },
            )),
        ],
    ),

    ('interface', 'wifiwave2', 'access-list'): APIData(
        versioned=[
            ('7.13', '>=', 'RouterOS 7.13 uses WiFi package'),
            ('7.8', '>=', VersionedAPIData(
                fully_understood=True,
                fields={
                    'action': KeyInfo(can_disable=True),
                    'allow-signal-out-of-range': KeyInfo(can_disable=True),
                    'client-isolation': KeyInfo(can_disable=True),
                    'comment': KeyInfo(can_disable=True, remove_value=''),
                    'disabled': KeyInfo(default=True),
                    'interface': KeyInfo(can_disable=True),
                    'mac-address': KeyInfo(can_disable=True),
                    'mac-address-mask': KeyInfo(can_disable=True),
                    'passphrase': KeyInfo(can_disable=True),
                    'radius-accounting': KeyInfo(can_disable=True),
                    'signal-range': KeyInfo(can_disable=True),
                    'ssid-regexp': KeyInfo(),
                    'time': KeyInfo(can_disable=True),
                    'vlan-id': KeyInfo(can_disable=True),
                },
            )),
        ],
    ),

    ('interface', 'wifiwave2', 'cap'): APIData(
        versioned=[
            ('7.13', '>=', 'RouterOS 7.13 uses WiFi package'),
            ('7.8', '>=', VersionedAPIData(
                single_value=True,
                fully_understood=True,
                fields={
                    'caps-man-addresses': KeyInfo(default=''),
                    'caps-man-certificate-common-names': KeyInfo(default=''),
                    'caps-man-names': KeyInfo(default=''),
                    'certificate': KeyInfo(default='none'),
                    'discovery-interfaces': KeyInfo(default=''),
                    'enabled': KeyInfo(default=False),
                    'lock-to-caps-man': KeyInfo(default=False),
                    'slaves-datapath': KeyInfo(),
                    'slaves-static': KeyInfo(),
                },
            )),
        ],
    ),

    ('interface', 'wifiwave2', 'capsman'): APIData(
        versioned=[
            ('7.13', '>=', 'RouterOS 7.13 uses WiFi package'),
            ('7.8', '>=', VersionedAPIData(
                single_value=True,
                fully_understood=True,
                fields={
                    'ca-certificate': KeyInfo(default=''),
                    'certificate': KeyInfo(default='none'),
                    'enabled': KeyInfo(default=False),
                    'interfaces': KeyInfo(default=''),
                    'package-path': KeyInfo(default=''),
                    'require-peer-certificate': KeyInfo(default=False),
                    'upgrade-policy': KeyInfo(default='none'),
                },
            )),
        ],
    ),

    ('interface', 'wifiwave2', 'channel'): APIData(
        versioned=[
            ('7.13', '>=', 'RouterOS 7.13 uses WiFi package'),
            ('7.8', '>=', VersionedAPIData(
                primary_keys=('name',),
                fully_understood=True,
                fields={
                    'band': KeyInfo(),
                    'frequency': KeyInfo(),
                    'name': KeyInfo(),
                    'secondary-frequency': KeyInfo(),
                    'skip-dfs-channels': KeyInfo(default='disabled'),
                    'width': KeyInfo(),
                },
            )),
        ],
    ),

    ('interface', 'wifiwave2', 'configuration'): APIData(
        versioned=[
            ('7.13', '>=', 'RouterOS 7.13 uses WiFi package'),
            ('7.8', '>=', VersionedAPIData(
                primary_keys=('name',),
                fully_understood=True,
                fields={
                    'aaa': KeyInfo(),
                    'antenna-gain': KeyInfo(),
                    'beacon-interval': KeyInfo(default=100),
                    'chains': KeyInfo(),
                    'channel': KeyInfo(),
                    'country': KeyInfo(default='United States'),
                    'datapath': KeyInfo(),
                    'dtim-period': KeyInfo(default=1),
                    'hide-ssid': KeyInfo(default=False),
                    'interworking': KeyInfo(),
                    'manager': KeyInfo(),
                    'mode': KeyInfo(default='ap'),
                    'name': KeyInfo(),
                    'security': KeyInfo(),
                    'ssid': KeyInfo(),
                    'steering': KeyInfo(),
                    'tx-chains': KeyInfo(),
                    'tx-power': KeyInfo(),
                },
            )),
        ],
    ),

    ('interface', 'wifiwave2', 'datapath'): APIData(
        versioned=[
            ('7.13', '>=', 'RouterOS 7.13 uses WiFi package'),
            ('7.8', '>=', VersionedAPIData(
                primary_keys=('name',),
                fully_understood=True,
                fields={
                    'bridge': KeyInfo(),
                    'bridge-cost': KeyInfo(),
                    'bridge-horizon': KeyInfo(),
                    'client-isolation': KeyInfo(default=False),
                    'interface-list': KeyInfo(),
                    'name': KeyInfo(),
                    'openflow-switch': KeyInfo(),
                    'vlan-id': KeyInfo(),
                },
            )),
        ],
    ),

    ('interface', 'wifiwave2', 'interworking'): APIData(
        versioned=[
            ('7.13', '>=', 'RouterOS 7.13 uses WiFi package'),
            ('7.8', '>=', VersionedAPIData(
                primary_keys=('name',),
                fully_understood=True,
                fields={
                    '3gpp-info': KeyInfo(),
                    'authentication-types': KeyInfo(),
                    'comment': KeyInfo(can_disable=True, remove_value=''),
                    'connection-capabilities': KeyInfo(),
                    'disabled': KeyInfo(default=False),
                    'domain-names': KeyInfo(),
                    'esr': KeyInfo(),
                    'hessid': KeyInfo(),
                    'hotspot20': KeyInfo(),
                    'hotspot20-dgaf': KeyInfo(),
                    'internet': KeyInfo(),
                    'ipv4-availability': KeyInfo(),
                    'ipv6-availability': KeyInfo(),
                    'name': KeyInfo(),
                    'network-type': KeyInfo(),
                    'operational-classes': KeyInfo(),
                    'operator-names': KeyInfo(),
                    'realms': KeyInfo(),
                    'roaming-ois': KeyInfo(),
                    'uesa': KeyInfo(),
                    'venue': KeyInfo(),
                    'venue-names': KeyInfo(),
                    'wan-at-capacity': KeyInfo(),
                    'wan-downlink': KeyInfo(),
                    'wan-downlink-load': KeyInfo(),
                    'wan-measurement-duration': KeyInfo(),
                    'wan-status': KeyInfo(),
                    'wan-symmetric': KeyInfo(),
                    'wan-uplink': KeyInfo(),
                    'wan-uplink-load': KeyInfo(),
                },
            )),
        ],
    ),

    ('interface', 'wifiwave2', 'provisioning'): APIData(
        versioned=[
            ('7.13', '>=', 'RouterOS 7.13 uses WiFi package'),
            ('7.8', '>=', VersionedAPIData(
                primary_keys=('action',),
                fully_understood=True,
                fields={
                    'action': KeyInfo(default='none'),
                    'address-ranges': KeyInfo(),
                    'comment': KeyInfo(can_disable=True, remove_value=''),
                    'common-name-regexp': KeyInfo(),
                    'disabled': KeyInfo(default=False),
                    'identity-regexp': KeyInfo(),
                    'master-configuration': KeyInfo(),
                    'name-format': KeyInfo(),
                    'radio-mac': KeyInfo(),
                    'slave-configurations': KeyInfo(),
                    'supported-bands': KeyInfo(),
                },
            )),
        ],
    ),

    ('interface', 'wifiwave2', 'security'): APIData(
        versioned=[
            ('7.13', '>=', 'RouterOS 7.13 uses WiFi package'),
            ('7.8', '>=', VersionedAPIData(
                primary_keys=('name',),
                fully_understood=True,
                fields={
                    'authentication-types': KeyInfo(),
                    'connect-group': KeyInfo(can_disable=True),
                    'connect-priority': KeyInfo(),
                    'dh-groups': KeyInfo(),
                    'disable-pmkid': KeyInfo(default=False),
                    'eap-accounting': KeyInfo(default=False),
                    'eap-anonymous-identity': KeyInfo(),
                    'eap-certificate-mode': KeyInfo(default='dont-verify-certificate'),
                    'eap-methods': KeyInfo(),
                    'eap-password': KeyInfo(),
                    'eap-tls-certificate': KeyInfo(),
                    'eap-username': KeyInfo(),
                    'encryption': KeyInfo(default='ccmp'),
                    'ft': KeyInfo(default=False),
                    'ft-mobility-domain': KeyInfo(default=44484),
                    'ft-nas-identifier': KeyInfo(),
                    'ft-over-ds': KeyInfo(default=False),
                    'ft-preserve-vlanid': KeyInfo(default=True),
                    'ft-r0-key-lifetime': KeyInfo(default='600000s'),
                    'ft-reassociation-deadline': KeyInfo(default='20s'),
                    'group-encryption': KeyInfo(default='ccmp'),
                    'group-key-update': KeyInfo(default='24h'),
                    'management-encryption': KeyInfo(default='cmac'),
                    'management-protection': KeyInfo(),
                    'name': KeyInfo(),
                    'owe-transition-interface': KeyInfo(),
                    'passphrase': KeyInfo(default=''),
                    'sae-anti-clogging-threshold': KeyInfo(can_disable=True),
                    'sae-max-failure-rate': KeyInfo(can_disable=True),
                    'sae-pwe': KeyInfo(default='both'),
                    'wps': KeyInfo(default='push-button'),
                },
            )),
        ],
    ),

    ('interface', 'wifiwave2', 'steering'): APIData(
        versioned=[
            ('7.13', '>=', 'RouterOS 7.13 uses WiFi package'),
            ('7.8', '>=', VersionedAPIData(
                primary_keys=('name',),
                fully_understood=True,
                fields={
                    'comment': KeyInfo(can_disable=True, remove_value=''),
                    'disabled': KeyInfo(default=False),
                    'name': KeyInfo(),
                    'neighbor-group': KeyInfo(),
                    'rrm': KeyInfo(),
                    'wnm': KeyInfo(),
                },
            )),
        ],
    ),

    ('interface', 'wireguard'): APIData(
        unversioned=VersionedAPIData(
            primary_keys=('name',),
            fully_understood=True,
            versioned_fields=[
                # ([('7.15', '>=')], 'copy-from', KeyInfo(write_only=True)),
                ([('7.21', '>=')], 'vrf', KeyInfo()),
            ],
            fields={
                'comment': KeyInfo(can_disable=True, remove_value=''),
                'disabled': KeyInfo(default=False),
                'listen-port': KeyInfo(),
                'mtu': KeyInfo(default=1420),
                'name': KeyInfo(),
                'private-key': KeyInfo(),
            },
        ),
    ),

    ('interface', 'wireguard', 'peers'): APIData(
        unversioned=VersionedAPIData(
            primary_keys=('public-key', 'interface'),
            fully_understood=True,
            versioned_fields=[
                ([('7.15', '>=')], 'client-address', KeyInfo()),
                ([('7.21', '>=')], 'client-allowed-address', KeyInfo()),
                ([('7.15', '>=')], 'client-dns', KeyInfo()),
                ([('7.15', '>=')], 'client-endpoint', KeyInfo()),
                ([('7.15', '>=')], 'client-keepalive', KeyInfo()),
                ([('7.15', '>=')], 'client-listen-port', KeyInfo()),
                # ([('7.15', '>=')], 'copy-from', KeyInfo(write_only=True)),
                ([('7.17', '<'), ('7.15', '>=')], 'is-responder', KeyInfo()),
                ([('7.15', '>=')], 'name', KeyInfo()),
                # ([('7.15', '>=')], 'place-before', KeyInfo(write_only=True)),
                ([('7.15', '>=')], 'private-key', KeyInfo()),
                ([('7.17', '>=')], 'responder', KeyInfo()),
            ],
            fields={
                'allowed-address': KeyInfo(required=True),
                'comment': KeyInfo(can_disable=True, remove_value=''),
                'disabled': KeyInfo(default=False),
                'endpoint-address': KeyInfo(default=''),
                'endpoint-port': KeyInfo(default=0),
                'interface': KeyInfo(),
                'persistent-keepalive': KeyInfo(can_disable=True, remove_value=0),
                'preshared-key': KeyInfo(can_disable=True, remove_value=''),
                'public-key': KeyInfo(),
            },
        ),
    ),

    ('interface', 'wireless'): APIData(
        unversioned=VersionedAPIData(
            primary_keys=('name',),
            required_one_of=[['default-name', 'master-interface']],
            fully_understood=True,
            versioned_fields=[
                ([('7.15', '>=')], 'burst-time', KeyInfo()),
                # ([('7.15', '>=')], 'copy-from', KeyInfo(write_only=True)),
                ([('7.15', '>=')], 'prism-cardtype', KeyInfo()),
                ([('7.15', '>=')], 'vht-basic-mcs', KeyInfo()),
                ([('7.15', '>=')], 'vht-supported-mcs', KeyInfo()),
            ],
            fields={
                'adaptive-noise-immunity': KeyInfo(default='none'),
                'allow-sharedkey': KeyInfo(default=False),
                'ampdu-priorities': KeyInfo(default=0),
                'amsdu-limit': KeyInfo(default=8192),
                'amsdu-threshold': KeyInfo(default=8192),
                'antenna-gain': KeyInfo(default=0),
                'antenna-mode': KeyInfo(),
                'area': KeyInfo(default=''),
                'arp': KeyInfo(default='enabled'),
                'arp-timeout': KeyInfo(default='auto'),
                'band': KeyInfo(),
                'basic-rates-a/g': KeyInfo(default='6Mbps'),
                'basic-rates-b': KeyInfo(default='1Mbps'),
                'bridge-mode': KeyInfo(default='enabled'),
                'channel-width': KeyInfo(default='20mhz'),
                'comment': KeyInfo(can_disable=True, remove_value=''),
                'compression': KeyInfo(default=False),
                'country': KeyInfo(default='etsi'),
                'default-ap-tx-limit': KeyInfo(default=0),
                'default-authentication': KeyInfo(default=True),
                'default-client-tx-limit': KeyInfo(default=0),
                'default-forwarding': KeyInfo(default=True),
                'default-name': KeyInfo(),
                'disable-running-check': KeyInfo(default=False),
                'disabled': KeyInfo(default=True),
                'disconnect-timeout': KeyInfo(default='3s'),
                'distance': KeyInfo(default='dynamic'),
                'frame-lifetime': KeyInfo(default=0),
                'frequency': KeyInfo(),
                'frequency-mode': KeyInfo(default='regulatory-domain'),
                'frequency-offset': KeyInfo(default=0),
                'guard-interval': KeyInfo(default='any'),
                'hide-ssid': KeyInfo(default=False),
                'ht-basic-mcs': KeyInfo(),
                'ht-supported-mcs': KeyInfo(),
                'hw-fragmentation-threshold': KeyInfo(default='disabled'),
                'hw-protection-mode': KeyInfo(default='none'),
                'hw-protection-threshold': KeyInfo(default=0),
                'hw-retries': KeyInfo(default=7),
                'installation': KeyInfo(default='any'),
                'interworking-profile': KeyInfo(default='disabled'),
                'keepalive-frames': KeyInfo(default='enabled'),
                'l2mtu': KeyInfo(default=1600),
                'mac-address': KeyInfo(),
                'master-interface': KeyInfo(),
                'max-station-count': KeyInfo(default=2007),
                'mode': KeyInfo(default='ap-bridge'),
                'mtu': KeyInfo(default=1500),
                'multicast-buffering': KeyInfo(default='enabled'),
                'multicast-helper': KeyInfo(default='default'),
                'name': KeyInfo(),
                'noise-floor-threshold': KeyInfo(default='default'),
                'nv2-cell-radius': KeyInfo(default=30),
                'nv2-downlink-ratio': KeyInfo(default=50),
                'nv2-mode': KeyInfo(default='dynamic-downlink'),
                'nv2-noise-floor-offset': KeyInfo(default='default'),
                'nv2-preshared-key': KeyInfo(default=''),
                'nv2-qos': KeyInfo(default='default'),
                'nv2-queue-count': KeyInfo(default=2),
                'nv2-security': KeyInfo(default='disabled'),
                'nv2-sync-secret': KeyInfo(default=''),
                'on-fail-retry-time': KeyInfo(default='100ms'),
                'preamble-mode': KeyInfo(default='both'),
                'radio-name': KeyInfo(),
                'rate-selection': KeyInfo(default='advanced'),
                'rate-set': KeyInfo(default='default'),
                'running': KeyInfo(read_only=True),
                'rx-chains': KeyInfo(default='0,1'),
                'scan-list': KeyInfo(default='default'),
                'secondary-frequency': KeyInfo(default=''),
                'security-profile': KeyInfo(default='default'),
                'skip-dfs-channels': KeyInfo(default='disabled'),
                'ssid': KeyInfo(required=True),
                'station-bridge-clone-mac': KeyInfo(),
                'station-roaming': KeyInfo(default='disabled'),
                'supported-rates-a/g': KeyInfo(),
                'supported-rates-b': KeyInfo(),
                'tdma-period-size': KeyInfo(default=2),
                'tx-chains': KeyInfo(),
                'tx-power': KeyInfo(default=''),
                'tx-power-mode': KeyInfo(default='default'),
                'update-stats-interval': KeyInfo(default='disabled'),
                'vlan-id': KeyInfo(default=1),
                'vlan-mode': KeyInfo(default='no-tag'),
                'wds-cost-range': KeyInfo(default='50-150'),
                'wds-default-bridge': KeyInfo(default='none'),
                'wds-default-cost': KeyInfo(default=100),
                'wds-ignore-ssid': KeyInfo(default=False),
                'wds-mode': KeyInfo(default='disabled'),
                'wireless-protocol': KeyInfo(default='any'),
                'wmm-support': KeyInfo(default='disabled'),
                'wps-mode': KeyInfo(default='push-button'),
            },
        ),
    ),

    ('interface', 'wireless', 'access-list'): APIData(
        unversioned=VersionedAPIData(
            fully_understood=True,
            # versioned_fields=[
            #     ([('7.15', '>=')], 'copy-from', KeyInfo(write_only=True)),
            #     ([('7.15', '>=')], 'place-before', KeyInfo(write_only=True)),
            # ],
            fields={
                'allow-signal-out-of-range': KeyInfo(default='10s'),
                'ap-tx-limit': KeyInfo(default=0),
                'authentication': KeyInfo(default=True),
                'client-tx-limit': KeyInfo(default=0),
                'comment': KeyInfo(can_disable=True, remove_value=''),
                'disabled': KeyInfo(default=False),
                'forwarding': KeyInfo(default=True),
                'interface': KeyInfo(default='any'),
                'mac-address': KeyInfo(default='00:00:00:00:00:00'),
                'management-protection-key': KeyInfo(default=''),
                'private-algo': KeyInfo(default='none'),
                'private-key': KeyInfo(default=''),
                'private-pre-shared-key': KeyInfo(default=''),
                'signal-range': KeyInfo(default='-120..120'),
                'time': KeyInfo(can_disable=True),
                'vlan-id': KeyInfo(default=1),
                'vlan-mode': KeyInfo(default='default'),
            },
        ),
    ),

    ('interface', 'wireless', 'align'): APIData(
        unversioned=VersionedAPIData(
            fixed_entries=True,
            single_value=True,
            fully_understood=True,
            fields={
                'active-mode': KeyInfo(default=True),
                'audio-max': KeyInfo(default=-20),
                'audio-min': KeyInfo(default=-100),
                'audio-monitor': KeyInfo(default='00:00:00:00:00:00'),
                'filter-mac': KeyInfo(default='00:00:00:00:00:00'),
                'frame-size': KeyInfo(default=300),
                'frames-per-second': KeyInfo(default=25),
                'receive-all': KeyInfo(default=False),
                'ssid-all': KeyInfo(default=False),
            },
        ),
    ),

    ('interface', 'wireless', 'cap'): APIData(
        unversioned=VersionedAPIData(
            fixed_entries=True,
            single_value=True,
            fully_understood=True,
            fields={
                'bridge': KeyInfo(default='none'),
                'caps-man-addresses': KeyInfo(default=''),
                'caps-man-certificate-common-names': KeyInfo(default=''),
                'caps-man-names': KeyInfo(default=''),
                'certificate': KeyInfo(default='none'),
                'discovery-interfaces': KeyInfo(default=''),
                'enabled': KeyInfo(default=False),
                'interfaces': KeyInfo(default=''),
                'lock-to-caps-man': KeyInfo(default=False),
                'static-virtual': KeyInfo(default=False),
            },
        ),
    ),

    ('interface', 'wireless', 'channels'): APIData(
        versioned=[
            ('7.15', '>=', VersionedAPIData(
                fully_understood=True,
                fields={
                    'band': KeyInfo(),
                    'comment': KeyInfo(),
                    # 'copy-from': KeyInfo(write_only=True),
                    'disabled': KeyInfo(),
                    'extension-channel': KeyInfo(),
                    'frequency': KeyInfo(),
                    'list': KeyInfo(),
                    'name': KeyInfo(),
                    # 'place-before': KeyInfo(write_only=True),
                    'width': KeyInfo(),
                },
            )),
        ],
    ),

    ('interface', 'wireless', 'connect-list'): APIData(
        unversioned=VersionedAPIData(
            fully_understood=True,
            # versioned_fields=[
            #     ([('7.15', '>=')], 'copy-from', KeyInfo(write_only=True)),
            #     ([('7.15', '>=')], 'place-before', KeyInfo(write_only=True)),
            # ],
            fields={
                '3gpp': KeyInfo(default=''),
                'allow-signal-out-of-range': KeyInfo(default='10s'),
                'area-prefix': KeyInfo(default=''),
                'comment': KeyInfo(can_disable=True, remove_value=''),
                'connect': KeyInfo(default=True),
                'disabled': KeyInfo(default=False),
                'interface': KeyInfo(required=True),
                'interworking': KeyInfo(default='any'),
                'iw-asra': KeyInfo(default='any'),
                'iw-authentication-types': KeyInfo(),
                'iw-connection-capabilities': KeyInfo(),
                'iw-esr': KeyInfo(default='any'),
                'iw-hessid': KeyInfo(default='00:00:00:00:00:00'),
                'iw-hotspot20': KeyInfo(default='any'),
                'iw-hotspot20-dgaf': KeyInfo(default='any'),
                'iw-internet': KeyInfo(default='any'),
                'iw-ipv4-availability': KeyInfo(default='any'),
                'iw-ipv6-availability': KeyInfo(default='any'),
                'iw-network-type': KeyInfo(default='wildcard'),
                'iw-realms': KeyInfo(),
                'iw-roaming-ois': KeyInfo(default=''),
                'iw-uesa': KeyInfo(default='any'),
                'iw-venue': KeyInfo(default='any'),
                'mac-address': KeyInfo(default='00:00:00:00:00:00'),
                'security-profile': KeyInfo(default='none'),
                'signal-range': KeyInfo(default='-120..120'),
                'ssid': KeyInfo(default=''),
                'wireless-protocol': KeyInfo(default='any'),
            },
        ),
    ),

    ('interface', 'wireless', 'interworking-profiles'): APIData(
        versioned=[
            ('7.15', '>=', VersionedAPIData(
                fully_understood=True,
                fields={
                    '3gpp-info': KeyInfo(),
                    '3gpp-raw': KeyInfo(),
                    'asra': KeyInfo(),
                    'authentication-types': KeyInfo(),
                    'comment': KeyInfo(),
                    'connection-capabilities': KeyInfo(),
                    # 'copy-from': KeyInfo(write_only=True),
                    'domain-names': KeyInfo(),
                    'esr': KeyInfo(),
                    'hessid': KeyInfo(),
                    'hotspot20': KeyInfo(),
                    'hotspot20-dgaf': KeyInfo(),
                    'internet': KeyInfo(),
                    'ipv4-availability': KeyInfo(),
                    'ipv6-availability': KeyInfo(),
                    'name': KeyInfo(),
                    'network-type': KeyInfo(),
                    'operational-classes': KeyInfo(),
                    'operator-names': KeyInfo(),
                    'realms': KeyInfo(),
                    'realms-raw': KeyInfo(),
                    'roaming-ois': KeyInfo(),
                    'uesa': KeyInfo(),
                    'venue': KeyInfo(),
                    'venue-names': KeyInfo(),
                    'wan-at-capacity': KeyInfo(),
                    'wan-downlink': KeyInfo(),
                    'wan-downlink-load': KeyInfo(),
                    'wan-measurement-duration': KeyInfo(),
                    'wan-status': KeyInfo(),
                    'wan-symmetric': KeyInfo(),
                    'wan-uplink': KeyInfo(),
                    'wan-uplink-load': KeyInfo(),
                },
            )),
        ],
    ),

    ('interface', 'wireless', 'manual-tx-power-table'): APIData(
        versioned=[
            ('7.15', '>=', VersionedAPIData(
                fully_understood=True,
                has_identifier=True,
                # fixed_entries=True,
                # primary_keys=('numbers',),
                fields={
                    'comment': KeyInfo(),
                    'manual-tx-powers': KeyInfo(),
                    'numbers': KeyInfo(),
                },
            )),
        ],
    ),

    ('interface', 'wireless', 'nstreme'): APIData(
        versioned=[
            ('7.15', '>=', VersionedAPIData(
                fully_understood=True,
                has_identifier=True,
                # fixed_entries=True,
                # primary_keys=('numbers',),
                fields={
                    'comment': KeyInfo(),
                    'disable-csma': KeyInfo(),
                    'enable-nstreme': KeyInfo(),
                    'enable-polling': KeyInfo(),
                    'framer-limit': KeyInfo(),
                    'framer-policy': KeyInfo(),
                    'numbers': KeyInfo(),
                },
            )),
        ],
    ),

    ('interface', 'wireless', 'nstreme-dual'): APIData(
        versioned=[
            ('7.15', '>=', VersionedAPIData(
                fully_understood=True,
                fields={
                    'arp': KeyInfo(),
                    'arp-timeout': KeyInfo(),
                    'comment': KeyInfo(),
                    # 'copy-from': KeyInfo(write_only=True),
                    'disable-csma': KeyInfo(),
                    'disable-running-check': KeyInfo(),
                    'disabled': KeyInfo(),
                    'framer-limit': KeyInfo(),
                    'framer-policy': KeyInfo(),
                    'ht-channel-width': KeyInfo(),
                    'ht-guard-interval': KeyInfo(),
                    'ht-rates': KeyInfo(),
                    'ht-streams': KeyInfo(),
                    'l2mtu': KeyInfo(),
                    'mtu': KeyInfo(),
                    'name': KeyInfo(),
                    'rates-a/g': KeyInfo(),
                    'rates-b': KeyInfo(),
                    'remote-mac': KeyInfo(),
                    'rx-band': KeyInfo(),
                    'rx-channel-width': KeyInfo(),
                    'rx-frequency': KeyInfo(),
                    'rx-radio': KeyInfo(),
                    'tx-band': KeyInfo(),
                    'tx-channel-width': KeyInfo(),
                    'tx-frequency': KeyInfo(),
                    'tx-radio': KeyInfo(),
                },
            )),
        ],
    ),

    ('interface', 'wireless', 'security-profiles'): APIData(
        unversioned=VersionedAPIData(
            primary_keys=('name',),
            fully_understood=True,
            versioned_fields=[
                ([('7.15', '>=')], 'comment', KeyInfo()),
                # ([('7.15', '>=')], 'copy-from', KeyInfo(write_only=True)),
                ([('7.15', '<')], 'disabled', KeyInfo(default=True)),
            ],
            fields={
                'authentication-types': KeyInfo(),
                'disable-pmkid': KeyInfo(default=False),
                'eap-methods': KeyInfo(),
                'group-ciphers': KeyInfo(),
                'group-key-update': KeyInfo(default='5m'),
                'interim-update': KeyInfo(),
                'management-protection': KeyInfo(default='disabled'),
                'management-protection-key': KeyInfo(default=''),
                'mode': KeyInfo(default='none'),
                'mschapv2-password': KeyInfo(default=''),
                'mschapv2-username': KeyInfo(default=''),
                'name': KeyInfo(),
                'radius-called-format': KeyInfo(),
                'radius-eap-accounting': KeyInfo(default=False),
                'radius-mac-accounting': KeyInfo(default=False),
                'radius-mac-authentication': KeyInfo(default=False),
                'radius-mac-caching': KeyInfo(default='disabled'),
                'radius-mac-format': KeyInfo(default='XX:XX:XX:XX:XX:XX'),
                'radius-mac-mode': KeyInfo(default='as-username'),
                'static-algo-0': KeyInfo(default='none'),
                'static-algo-1': KeyInfo(default='none'),
                'static-algo-2': KeyInfo(default='none'),
                'static-algo-3': KeyInfo(default='none'),
                'static-key-0': KeyInfo(),
                'static-key-1': KeyInfo(),
                'static-key-2': KeyInfo(),
                'static-key-3': KeyInfo(),
                'static-sta-private-algo': KeyInfo(default='none'),
                'static-sta-private-key': KeyInfo(),
                'static-transmit-key': KeyInfo(),
                'supplicant-identity': KeyInfo(default='MikroTik'),
                'tls-certificate': KeyInfo(default='none'),
                'tls-mode': KeyInfo(),
                'unicast-ciphers': KeyInfo(),
                'wpa-pre-shared-key': KeyInfo(),
                'wpa2-pre-shared-key': KeyInfo(),
            },
        ),
    ),

    ('interface', 'wireless', 'sniffer'): APIData(
        unversioned=VersionedAPIData(
            fixed_entries=True,
            single_value=True,
            fully_understood=True,
            fields={
                'channel-time': KeyInfo(default='200ms'),
                'file-limit': KeyInfo(default=10),
                'file-name': KeyInfo(default=''),
                'memory-limit': KeyInfo(default=10),
                'multiple-channels': KeyInfo(default=False),
                'only-headers': KeyInfo(default=False),
                'receive-errors': KeyInfo(default=False),
                'streaming-enabled': KeyInfo(default=False),
                'streaming-max-rate': KeyInfo(default=0),
                'streaming-server': KeyInfo(default='0.0.0.0'),
            },
        ),
    ),

    ('interface', 'wireless', 'snooper'): APIData(
        unversioned=VersionedAPIData(
            fixed_entries=True,
            single_value=True,
            fully_understood=True,
            fields={
                'channel-time': KeyInfo(default='200ms'),
                'multiple-channels': KeyInfo(default=True),
                'receive-errors': KeyInfo(default=False),
            },
        ),
    ),

    ('interface', 'wireless', 'wds'): APIData(
        versioned=[
            ('7.15', '>=', VersionedAPIData(
                fully_understood=True,
                fields={
                    'arp': KeyInfo(),
                    'arp-timeout': KeyInfo(),
                    'comment': KeyInfo(),
                    # 'copy-from': KeyInfo(write_only=True),
                    'disable-running-check': KeyInfo(),
                    'disabled': KeyInfo(),
                    'l2mtu': KeyInfo(),
                    'master-interface': KeyInfo(),
                    'mtu': KeyInfo(),
                    'name': KeyInfo(),
                    'wds-address': KeyInfo(),
                },
            )),
        ],
    ),

    ('iot', 'bluetooth'): APIData(
        versioned=[
            ('7.15', '>=', VersionedAPIData(
                fully_understood=True,
                has_identifier=True,
                # fixed_entries=True,
                # primary_keys=('numbers',),
                fields={
                    'antenna': KeyInfo(),
                    'name': KeyInfo(),
                    'numbers': KeyInfo(),
                    'random-static-address': KeyInfo(),
                },
            )),
        ],
    ),

    ('iot', 'bluetooth', 'advertisers'): APIData(
        versioned=[
            ('7.15', '>=', VersionedAPIData(
                fully_understood=True,
                has_identifier=True,
                # fixed_entries=True,
                # primary_keys=('numbers',),
                versioned_fields=[
                    ([('7.21', '>=')], 'legacy', KeyInfo()),
                    ([('7.21', '>=')], 'phy', KeyInfo()),
                ],
                fields={
                    'ad-structures': KeyInfo(),
                    'channel-map': KeyInfo(),
                    'disabled': KeyInfo(),
                    'max-interval': KeyInfo(),
                    'min-interval': KeyInfo(),
                    'numbers': KeyInfo(),
                    'own-address-type': KeyInfo(),
                },
            )),
        ],
    ),

    ('iot', 'bluetooth', 'advertisers', 'ad-structures'): APIData(
        versioned=[
            ('7.15', '>=', VersionedAPIData(
                fully_understood=True,
                fields={
                    # 'copy-from': KeyInfo(write_only=True),
                    'data': KeyInfo(),
                    'name': KeyInfo(),
                    'type': KeyInfo(),
                },
            )),
        ],
    ),

    ('iot', 'bluetooth', 'peripheral-devices'): APIData(
        versioned=[
            ('7.15', '>=', VersionedAPIData(
                fully_understood=True,
                has_identifier=True,
                # fixed_entries=True,
                # primary_keys=('numbers',),
                fields={
                    'address': KeyInfo(),
                    'address-type': KeyInfo(),
                    'mtik-key': KeyInfo(),
                    'name': KeyInfo(),
                    'numbers': KeyInfo(),
                    'persist': KeyInfo(),
                },
            )),
        ],
    ),

    ('iot', 'bluetooth', 'scanners'): APIData(
        versioned=[
            ('7.15', '>=', VersionedAPIData(
                fully_understood=True,
                has_identifier=True,
                # fixed_entries=True,
                # primary_keys=('numbers',),
                versioned_fields=[
                    ([('7.21', '>=')], 'phy', KeyInfo()),
                ],
                fields={
                    'disabled': KeyInfo(),
                    'filter-duplicates': KeyInfo(),
                    'filter-policy': KeyInfo(),
                    'interval': KeyInfo(),
                    'numbers': KeyInfo(),
                    'own-address-type': KeyInfo(),
                    'type': KeyInfo(),
                    'window': KeyInfo(),
                },
            )),
        ],
    ),

    ('iot', 'bluetooth', 'whitelist'): APIData(
        versioned=[
            ('7.15', '>=', VersionedAPIData(
                fully_understood=True,
                fields={
                    'address': KeyInfo(),
                    'address-type': KeyInfo(),
                    'comment': KeyInfo(),
                    # 'copy-from': KeyInfo(write_only=True),
                    'device': KeyInfo(),
                    'disabled': KeyInfo(),
                },
            )),
        ],
    ),

    ('iot', 'lora'): APIData(
        versioned=[
            ('7.15', '>=', VersionedAPIData(
                fully_understood=True,
                has_identifier=True,
                # fixed_entries=True,
                # primary_keys=('numbers',),
                versioned_fields=[
                    ([('7.16', '>=')], 'alt', KeyInfo()),
                    ([('7.16', '>=')], 'lat', KeyInfo()),
                    ([('7.16', '>=')], 'long', KeyInfo()),
                ],
                fields={
                    'antenna': KeyInfo(),
                    'antenna-gain': KeyInfo(),
                    'channel-plan': KeyInfo(),
                    'disabled': KeyInfo(),
                    'forward': KeyInfo(),
                    'gateway-id': KeyInfo(),
                    'lbt-enabled': KeyInfo(),
                    'listen-time': KeyInfo(),
                    'name': KeyInfo(),
                    'network': KeyInfo(),
                    'numbers': KeyInfo(),
                    'rssi-threshold': KeyInfo(),
                    'servers': KeyInfo(),
                    'spoof-gps': KeyInfo(),
                    'src-address': KeyInfo(),
                },
            )),
        ],
    ),

    ('iot', 'lora', 'channels'): APIData(
        versioned=[
            ('7.15', '>=', VersionedAPIData(
                fully_understood=True,
                has_identifier=True,
                # fixed_entries=True,
                # primary_keys=('numbers',),
                fields={
                    'bandwidth': KeyInfo(),
                    'datarate': KeyInfo(),
                    'disabled': KeyInfo(),
                    'freq-off': KeyInfo(),
                    'numbers': KeyInfo(),
                    'radio': KeyInfo(),
                    'spread-factor': KeyInfo(),
                },
            )),
        ],
    ),

    ('iot', 'lora', 'joineui'): APIData(
        versioned=[
            ('7.15', '>=', VersionedAPIData(
                fully_understood=True,
                versioned_fields=[
                    ([('7.16', '>=')], 'logging', KeyInfo()),
                    ([('7.19', '>=')], 'type', KeyInfo()),
                ],
                fields={
                    # 'copy-from': KeyInfo(write_only=True),
                    'joineuis': KeyInfo(),
                    'name': KeyInfo(),
                },
            )),
        ],
    ),

    ('iot', 'lora', 'netid'): APIData(
        versioned=[
            ('7.15', '>=', VersionedAPIData(
                fully_understood=True,
                versioned_fields=[
                    ([('7.16', '>=')], 'logging', KeyInfo()),
                    ([('7.19', '>=')], 'type', KeyInfo()),
                ],
                fields={
                    # 'copy-from': KeyInfo(write_only=True),
                    'name': KeyInfo(),
                    'netids': KeyInfo(),
                },
            )),
        ],
    ),

    ('iot', 'lora', 'radios'): APIData(
        versioned=[
            ('7.15', '>=', VersionedAPIData(
                fully_understood=True,
                has_identifier=True,
                # fixed_entries=True,
                # primary_keys=('numbers',),
                fields={
                    'center-freq': KeyInfo(),
                    'disabled': KeyInfo(),
                    'numbers': KeyInfo(),
                    'rssi-off': KeyInfo(),
                    'tx-enabled': KeyInfo(),
                    'tx-freq-max': KeyInfo(),
                    'tx-freq-min': KeyInfo(),
                },
            )),
        ],
    ),

    ('iot', 'lora', 'servers'): APIData(
        versioned=[
            ('7.15', '>=', VersionedAPIData(
                fully_understood=True,
                fields={
                    'address': KeyInfo(),
                    'certificate': KeyInfo(),
                    # 'copy-from': KeyInfo(write_only=True),
                    'down-port': KeyInfo(),
                    'interval': KeyInfo(),
                    'joineui': KeyInfo(),
                    'key': KeyInfo(),
                    'name': KeyInfo(),
                    'netid': KeyInfo(),
                    'port': KeyInfo(),
                    'protocol': KeyInfo(),
                    'ssl': KeyInfo(),
                    'up-port': KeyInfo(),
                },
            )),
        ],
    ),

    ('iot', 'lora', 'traffic', 'options'): APIData(
        versioned=[
            ('7.17', '>=', VersionedAPIData(
                fixed_entries=True,
                single_value=True,
                fully_understood=True,
                versioned_fields=[
                    ([('7.19', '>=')], 'pckt-limit', KeyInfo()),
                ],
                fields={
                    'crc-errors': KeyInfo(),
                },
            )),
        ],
    ),

    ('iot', 'modbus'): APIData(
        unversioned=VersionedAPIData(
            fixed_entries=True,
            single_value=True,
            fully_understood=True,
            versioned_fields=[
                ([('7.15', '>=')], 'disable-security-rules', KeyInfo()),
                ([('7.21', '>=')], 'rx-switch-offset', KeyInfo()),
            ],
            fields={
                'disabled': KeyInfo(default=True),
                'hardware-port': KeyInfo(default='modbus'),
                'tcp-port': KeyInfo(default=502),
                'timeout': KeyInfo(default=1000),
            },
        ),
    ),

    ('iot', 'modbus', 'security-rules'): APIData(
        versioned=[
            ('7.15', '>=', VersionedAPIData(
                fully_understood=True,
                fields={
                    'allowed-function-codes': KeyInfo(),
                    'comment': KeyInfo(),
                    # 'copy-from': KeyInfo(write_only=True),
                    'disabled': KeyInfo(),
                    'ip-range': KeyInfo(),
                },
            )),
        ],
    ),

    ('iot', 'mqtt', 'brokers'): APIData(
        versioned=[
            ('7.15', '>=', VersionedAPIData(
                fully_understood=True,
                versioned_fields=[
                    ([('7.20', '>=')], 'will-message', KeyInfo()),
                    ([('7.20', '>=')], 'will-qos', KeyInfo()),
                    ([('7.20', '>=')], 'will-retain', KeyInfo()),
                    ([('7.20', '>=')], 'will-topic', KeyInfo()),
                ],
                fields={
                    'address': KeyInfo(),
                    'auto-connect': KeyInfo(),
                    'certificate': KeyInfo(),
                    'client-id': KeyInfo(),
                    # 'copy-from': KeyInfo(write_only=True),
                    'keep-alive': KeyInfo(),
                    'name': KeyInfo(),
                    'parallel-scripts-limit': KeyInfo(),
                    'password': KeyInfo(),
                    'port': KeyInfo(),
                    'ssl': KeyInfo(),
                    'username': KeyInfo(),
                },
            )),
        ],
    ),

    ('iot', 'mqtt', 'subscriptions'): APIData(
        versioned=[
            ('7.15', '>=', VersionedAPIData(
                fully_understood=True,
                fields={
                    'broker': KeyInfo(),
                    # 'copy-from': KeyInfo(write_only=True),
                    'on-message': KeyInfo(),
                    'qos': KeyInfo(),
                    'topic': KeyInfo(),
                },
            )),
        ],
    ),

    ('ip', 'accounting'): APIData(
        versioned=[
            ('7.15', '<', VersionedAPIData(
                single_value=True,
                fully_understood=True,
                fields={
                    'account-local-traffic': KeyInfo(default=False),
                    'enabled': KeyInfo(default=False),
                    'threshold': KeyInfo(default=256),
                },
            )),
            ('7.15', '>=', 'Not supported anymore in version 7.15'),
        ],
    ),

    ('ip', 'accounting', 'web-access'): APIData(
        versioned=[
            ('7.15', '<', VersionedAPIData(
                single_value=True,
                fully_understood=True,
                fields={
                    'accessible-via-web': KeyInfo(default=False),
                    'address': KeyInfo(default='0.0.0.0/0'),
                },
            )),
            ('7.15', '>=', 'Not supported anymore in version 7.15'),
        ],
    ),

    ('ip', 'address'): APIData(
        unversioned=VersionedAPIData(
            primary_keys=('address', 'interface'),
            fully_understood=True,
            versioned_fields=[
                ([('7.15', '>=')], 'broadcast', KeyInfo()),
                # ([('7.15', '>=')], 'copy-from', KeyInfo(write_only=True)),
                ([('7.15', '>=')], 'netmask', KeyInfo()),
            ],
            fields={
                'address': KeyInfo(),
                'comment': KeyInfo(can_disable=True, remove_value=''),
                'disabled': KeyInfo(default=False),
                'interface': KeyInfo(),
                'network': KeyInfo(automatically_computed_from=('address',)),
            },
        ),
    ),

    ('ip', 'arp'): APIData(
        unversioned=VersionedAPIData(
            fully_understood=True,
            # versioned_fields=[
            #     ([('7.15', '>=')], 'copy-from', KeyInfo(write_only=True)),
            # ],
            fields={
                'address': KeyInfo(default='0.0.0.0'),
                'comment': KeyInfo(can_disable=True, remove_value=''),
                'disabled': KeyInfo(default=False),
                'interface': KeyInfo(required=True),
                'mac-address': KeyInfo(default='00:00:00:00:00:00'),
                'published': KeyInfo(default=False),
            },
        ),
    ),

    ('ip', 'cloud'): APIData(
        unversioned=VersionedAPIData(
            fixed_entries=True,
            single_value=True,
            fully_understood=True,
            versioned_fields=[
                ([('7.15', '>=')], 'back-to-home-vpn', KeyInfo()),
                ([('7.17', '<')], 'ddns-enabled', KeyInfo(default=False)),
                ([('7.17', '>=')], 'ddns-enabled', KeyInfo(default='auto')),
                ([('7.15', '>=')], 'vpn-prefer-relay-code', KeyInfo()),
            ],
            fields={
                'ddns-update-interval': KeyInfo(default='none'),
                'update-time': KeyInfo(default=True),
            },
        ),
    ),

    ('ip', 'cloud', 'advanced'): APIData(
        unversioned=VersionedAPIData(
            fixed_entries=True,
            single_value=True,
            fully_understood=True,
            fields={
                'use-local-address': KeyInfo(default=False),
            },
        ),
    ),

    ('ip', 'cloud', 'back-to-home-file'): APIData(
        versioned=[
            ('7.18', '>=', VersionedAPIData(
                fully_understood=True,
                fields={
                    'allow-uploads': KeyInfo(),
                    'comment': KeyInfo(),
                    # 'copy-from': KeyInfo(write_only=True),
                    'disabled': KeyInfo(),
                    'expires': KeyInfo(),
                    'path': KeyInfo(),
                },
            )),
        ],
    ),

    ('ip', 'cloud', 'back-to-home-file', 'settings'): APIData(
        versioned=[
            ('7.18', '>=', VersionedAPIData(
                fixed_entries=True,
                single_value=True,
                fully_understood=True,
                fields={
                    'prefer-relay-code': KeyInfo(),
                },
            )),
        ],
    ),

    ('ip', 'cloud', 'back-to-home-user'): APIData(
        versioned=[
            ('7.18', '>=', VersionedAPIData(
                fully_understood=True,
                fields={
                    'allow-lan': KeyInfo(),
                    'comment': KeyInfo(),
                    # 'copy-from': KeyInfo(write_only=True),
                    'disabled': KeyInfo(),
                    'expires': KeyInfo(),
                    'file-access': KeyInfo(),
                    'file-access-path': KeyInfo(),
                    'name': KeyInfo(),
                    'private-key': KeyInfo(),
                    'public-key': KeyInfo(),
                },
            )),
        ],
    ),

    ('ip', 'cloud', 'back-to-home-users'): APIData(
        versioned=[
            ('7.15', '>=', VersionedAPIData(
                fully_understood=True,
                versioned_fields=[
                    ([('7.17', '>=')], 'file-access', KeyInfo()),
                    ([('7.17', '>=')], 'file-access-path', KeyInfo()),
                ],
                fields={
                    'allow-lan': KeyInfo(),
                    'comment': KeyInfo(),
                    # 'copy-from': KeyInfo(write_only=True),
                    'disabled': KeyInfo(),
                    'expires': KeyInfo(),
                    'name': KeyInfo(),
                    'private-key': KeyInfo(),
                    'public-key': KeyInfo(),
                },
            )),
            ('7.18', '>=', 'Not supported anymore in version 7.18'),
        ],
    ),

    ('ip', 'dhcp-client'): APIData(
        unversioned=VersionedAPIData(
            primary_keys=('interface',),
            fully_understood=True,
            versioned_fields=[
                ([('7.19', '>=')], 'allow-reconfigure', KeyInfo(default=False)),
                ([('7.19', '>=')], 'check-gateway', KeyInfo(default='none')),
                # ([('7.15', '>=')], 'copy-from', KeyInfo(write_only=True)),
                ([('7.18', '>=')], 'default-route-tables', KeyInfo()),
                ([('7.20', '>=')], 'dscp', KeyInfo(default=0)),
                ([('7.20', '>=')], 'use-broadcast', KeyInfo(default='both')),
                ([('7.20', '>=')], 'vlan-priority', KeyInfo(default=0)),
            ],
            fields={
                'add-default-route': KeyInfo(default=True),
                'comment': KeyInfo(can_disable=True, remove_value=''),
                'default-route-distance': KeyInfo(default=1),
                'dhcp-options': KeyInfo(can_disable=True, default='hostname,clientid', remove_value=''),
                'disabled': KeyInfo(default=False),
                'interface': KeyInfo(),
                'script': KeyInfo(),
                'use-peer-dns': KeyInfo(default=True),
                'use-peer-ntp': KeyInfo(default=True),
            },
        ),
    ),

    ('ip', 'dhcp-client', 'option'): APIData(
        unversioned=VersionedAPIData(
            primary_keys=('name',),
            fully_understood=True,
            versioned_fields=[
                ([('7.16', '>=')], 'comment', KeyInfo()),
                # ([('7.15', '>=')], 'copy-from', KeyInfo(write_only=True)),
            ],
            fields={
                'code': KeyInfo(),
                'name': KeyInfo(),
                'value': KeyInfo(),
            },
        ),
    ),

    ('ip', 'dhcp-relay'): APIData(
        unversioned=VersionedAPIData(
            primary_keys=('name',),
            fully_understood=True,
            versioned_fields=[
                # ([('7.15', '>=')], 'copy-from', KeyInfo(write_only=True)),
                ([('7.15', '>=')], 'dhcp-server-vrf', KeyInfo()),
                ([('7.17', '>=')], 'local-address-as-src-ip', KeyInfo()),
            ],
            fields={
                'add-relay-info': KeyInfo(default=False),
                'delay-threshold': KeyInfo(can_disable=True, remove_value='none'),
                'dhcp-server': KeyInfo(required=True),
                'disabled': KeyInfo(default=False),
                'interface': KeyInfo(required=True),
                'local-address': KeyInfo(can_disable=True, remove_value='0.0.0.0'),
                'name': KeyInfo(),
                'relay-info-remote-id': KeyInfo(can_disable=True),
            },
        ),
    ),

    ('ip', 'dhcp-server'): APIData(
        unversioned=VersionedAPIData(
            primary_keys=('name',),
            fully_understood=True,
            versioned_fields=[
                ([('7.15', '>=')], 'add-arp', KeyInfo()),
                ([('7.17', '>=')], 'address-lists', KeyInfo()),
                # ([('7.15', '>=')], 'copy-from', KeyInfo(write_only=True)),
                ([('7.21', '>=')], 'dynamic-lease-identifiers', KeyInfo()),
                ([('7.21', '>=')], 'support-broadband-tr101', KeyInfo()),
                ([('7.19', '>=')], 'use-reconfigure', KeyInfo()),
            ],
            fields={
                'address-pool': KeyInfo(default='static-only'),
                'allow-dual-stack-queue': KeyInfo(can_disable=True, remove_value=True),
                'always-broadcast': KeyInfo(can_disable=True, remove_value=False),
                'authoritative': KeyInfo(default=True),
                'bootp-lease-time': KeyInfo(default='forever'),
                'bootp-support': KeyInfo(can_disable=True, remove_value='static'),
                'client-mac-limit': KeyInfo(can_disable=True, remove_value='unlimited'),
                'comment': KeyInfo(can_disable=True, remove_value=''),
                'conflict-detection': KeyInfo(can_disable=True, remove_value=True),
                'delay-threshold': KeyInfo(can_disable=True, remove_value='none'),
                'dhcp-option-set': KeyInfo(can_disable=True, remove_value='none'),
                'disabled': KeyInfo(default=False),
                'insert-queue-before': KeyInfo(can_disable=True, remove_value='first'),
                'interface': KeyInfo(required=True),
                'lease-script': KeyInfo(default=''),
                'lease-time': KeyInfo(default='10m'),
                'name': KeyInfo(),
                'parent-queue': KeyInfo(can_disable=True, remove_value='none'),
                'relay': KeyInfo(can_disable=True, remove_value='0.0.0.0'),
                'server-address': KeyInfo(can_disable=True, remove_value='0.0.0.0'),
                'use-framed-as-classless': KeyInfo(can_disable=True, remove_value=True),
                'use-radius': KeyInfo(default=False),
            },
        ),
    ),

    ('ip', 'dhcp-server', 'alert'): APIData(
        versioned=[
            ('7.15', '>=', VersionedAPIData(
                fully_understood=True,
                fields={
                    'alert-timeout': KeyInfo(),
                    'comment': KeyInfo(),
                    # 'copy-from': KeyInfo(write_only=True),
                    'disabled': KeyInfo(),
                    'interface': KeyInfo(),
                    'on-alert': KeyInfo(),
                    'valid-server': KeyInfo(),
                },
            )),
        ],
    ),

    ('ip', 'dhcp-server', 'config'): APIData(
        unversioned=VersionedAPIData(
            fixed_entries=True,
            single_value=True,
            fully_understood=True,
            versioned_fields=[
                ([('7.15', '>=')], 'radius-password', KeyInfo()),
            ],
            fields={
                'accounting': KeyInfo(default=True),
                'interim-update': KeyInfo(default='0s'),
                'store-leases-disk': KeyInfo(default='5m'),
            },
        ),
    ),

    ('ip', 'dhcp-server', 'lease'): APIData(
        unversioned=VersionedAPIData(
            primary_keys=('server', 'address'),
            fully_understood=True,
            versioned_fields=[
                ([('7.21', '>=')], 'agent-circuit-id', KeyInfo()),
                ([('7.21', '>=')], 'agent-remote-id', KeyInfo()),
                ([('7.15', '>=')], 'allow-dual-stack-queue', KeyInfo(can_disable=True)),
                ([('7.15', '>=')], 'block-access', KeyInfo()),
                # ([('7.15', '>=')], 'copy-from', KeyInfo(write_only=True)),
                ([('7.15', '>=')], 'dhcp-option-set', KeyInfo()),
                ([('7.15', '>=')], 'lease-time', KeyInfo()),
                ([('7.15', '>=')], 'parent-queue', KeyInfo(can_disable=True)),
                ([('7.15', '>=')], 'queue-type', KeyInfo(can_disable=True)),
                ([('7.15', '>=')], 'rate-limit', KeyInfo()),
                ([('7.15', '>=')], 'routes', KeyInfo()),
                ([('7.15', '>=')], 'use-src-mac', KeyInfo()),
            ],
            fields={
                'address': KeyInfo(),
                'address-lists': KeyInfo(default=''),
                'always-broadcast': KeyInfo(),
                'client-id': KeyInfo(can_disable=True, remove_value=''),
                'comment': KeyInfo(can_disable=True, remove_value=''),
                'dhcp-option': KeyInfo(default=''),
                'disabled': KeyInfo(default=False),
                'insert-queue-before': KeyInfo(can_disable=True),
                'mac-address': KeyInfo(can_disable=True, remove_value=''),
                'server': KeyInfo(absent_value='all'),
            },
        ),
    ),

    ('ip', 'dhcp-server', 'matcher'): APIData(
        versioned=[
            ('7.4', '>=', VersionedAPIData(
                primary_keys=('name',),
                fully_understood=True,
                versioned_fields=[
                    ([('7.16', '>=')], 'comment', KeyInfo(can_disable=True, remove_value='')),
                    # ([('7.15', '>=')], 'copy-from', KeyInfo(write_only=True)),
                    ([('7.16', '>=')], 'matching-type', KeyInfo()),
                ],
                fields={
                    'address-pool': KeyInfo(default='none'),
                    'code': KeyInfo(required=True),
                    'disabled': KeyInfo(default=False),
                    'name': KeyInfo(required=True),
                    'option-set': KeyInfo(),
                    'server': KeyInfo(default='all'),
                    'value': KeyInfo(required=True),
                },
            )),
        ],
    ),

    ('ip', 'dhcp-server', 'network'): APIData(
        unversioned=VersionedAPIData(
            primary_keys=('address',),
            fully_understood=True,
            versioned_fields=[
                # ([('7.15', '>=')], 'copy-from', KeyInfo(write_only=True)),
                ([('7.20', '>=')], 'ntp-none', KeyInfo()),
            ],
            fields={
                'address': KeyInfo(),
                'boot-file-name': KeyInfo(default=''),
                'caps-manager': KeyInfo(default=''),
                'comment': KeyInfo(can_disable=True, remove_value=''),
                'dhcp-option': KeyInfo(default=''),
                'dhcp-option-set': KeyInfo(default=''),
                'dns-none': KeyInfo(default=False),
                'dns-server': KeyInfo(default=''),
                'domain': KeyInfo(default=''),
                'gateway': KeyInfo(default=''),
                'netmask': KeyInfo(can_disable=True, remove_value=0),
                'next-server': KeyInfo(can_disable=True),
                'ntp-server': KeyInfo(default=''),
                'wins-server': KeyInfo(default=''),
            },
        ),
    ),

    ('ip', 'dhcp-server', 'option'): APIData(
        unversioned=VersionedAPIData(
            primary_keys=('name',),
            fully_understood=True,
            versioned_fields=[
                ([('7.16', '>=')], 'comment', KeyInfo(can_disable=True, remove_value='')),
                # ([('7.15', '>=')], 'copy-from', KeyInfo(write_only=True)),
            ],
            fields={
                'code': KeyInfo(required=True),
                'force': KeyInfo(default=False),
                'name': KeyInfo(),
                'value': KeyInfo(default=''),
            },
        ),
    ),

    ('ip', 'dhcp-server', 'option', 'sets'): APIData(
        unversioned=VersionedAPIData(
            primary_keys=('name',),
            fully_understood=True,
            versioned_fields=[
                ([('7.16', '>=')], 'comment', KeyInfo(can_disable=True, remove_value='')),
                # ([('7.15', '>=')], 'copy-from', KeyInfo(write_only=True)),
            ],
            fields={
                'name': KeyInfo(required=True),
                'options': KeyInfo(),
            },
        ),
    ),

    ('ip', 'dns'): APIData(
        unversioned=VersionedAPIData(
            fixed_entries=True,
            single_value=True,
            fully_understood=True,
            versioned_fields=[
                ([('7.15', '>=')], 'address-list-extra-time', KeyInfo()),
                ([('7.8', '>=')], 'doh-max-concurrent-queries', KeyInfo(default=50)),
                ([('7.8', '>=')], 'doh-max-server-connections', KeyInfo(default=5)),
                ([('7.8', '>=')], 'doh-timeout', KeyInfo(default='5s')),
                ([('7.16', '>=')], 'mdns-repeat-ifaces', KeyInfo()),
                ([('7.15', '>=')], 'vrf', KeyInfo()),
            ],
            fields={
                'allow-remote-requests': KeyInfo(),
                'cache-max-ttl': KeyInfo(default='1w'),
                'cache-size': KeyInfo(default='2048KiB'),
                'max-concurrent-queries': KeyInfo(default=100),
                'max-concurrent-tcp-sessions': KeyInfo(default=20),
                'max-udp-packet-size': KeyInfo(default=4096),
                'query-server-timeout': KeyInfo(default='2s'),
                'query-total-timeout': KeyInfo(default='10s'),
                'servers': KeyInfo(default=''),
                'use-doh-server': KeyInfo(default=''),
                'verify-doh-cert': KeyInfo(default=False),
            },
        ),
    ),

    ('ip', 'dns', 'adlist'): APIData(
        versioned=[
            ('7.15', '>=', VersionedAPIData(
                fully_understood=True,
                fields={
                    'comment': KeyInfo(can_disable=True, remove_value=''),
                    # 'copy-from': KeyInfo(write_only=True),
                    'disabled': KeyInfo(default=False),
                    'file': KeyInfo(default=''),
                    'match-count': KeyInfo(read_only=True),
                    'name-count': KeyInfo(read_only=True),
                    'ssl-verify': KeyInfo(default=True),
                    'url': KeyInfo(default=''),
                },
            )),
        ],
    ),

    ('ip', 'dns', 'forwarders'): APIData(
        versioned=[
            ('7.17', '>=', VersionedAPIData(
                required_one_of=[['dns-servers', 'doh-servers']],
                fully_understood=True,
                fields={
                    'comment': KeyInfo(can_disable=True, remove_value=''),
                    # 'copy-from': KeyInfo(write_only=True),
                    'disabled': KeyInfo(default=False),
                    'dns-servers': KeyInfo(default=''),
                    'doh-servers': KeyInfo(default=''),
                    'name': KeyInfo(required=True),
                    'verify-doh-cert': KeyInfo(default=True),
                },
            )),
        ],
    ),

    ('ip', 'dns', 'static'): APIData(
        unversioned=VersionedAPIData(
            required_one_of=[['name', 'regexp']],
            mutually_exclusive=[['name', 'regexp']],
            fully_understood=True,
            versioned_fields=[
                ([('7.5', '>=')], 'address-list', KeyInfo()),
                # ([('7.15', '>=')], 'copy-from', KeyInfo(write_only=True)),
                ([('7.5', '>=')], 'match-subdomain', KeyInfo(default=False)),
                # ([('7.15', '>=')], 'place-before', KeyInfo(write_only=True)),
            ],
            fields={
                'address': KeyInfo(),
                'cname': KeyInfo(),
                'comment': KeyInfo(can_disable=True, remove_value=''),
                'disabled': KeyInfo(default=False),
                'forward-to': KeyInfo(),
                'mx-exchange': KeyInfo(),
                'mx-preference': KeyInfo(),
                'name': KeyInfo(),
                'ns': KeyInfo(),
                'regexp': KeyInfo(),
                'srv-port': KeyInfo(),
                'srv-priority': KeyInfo(),
                'srv-target': KeyInfo(),
                'srv-weight': KeyInfo(),
                'text': KeyInfo(),
                'ttl': KeyInfo(default='1d'),
                'type': KeyInfo(),
            },
        ),
    ),

    ('ip', 'firewall', 'address-list'): APIData(
        unversioned=VersionedAPIData(
            primary_keys=('address', 'list'),
            fully_understood=True,
            versioned_fields=[
                # ([('7.15', '>=')], 'copy-from', KeyInfo(write_only=True)),
                ([('7.15', '>=')], 'dynamic', KeyInfo()),
                ([('7.15', '>=')], 'timeout', KeyInfo()),
            ],
            fields={
                'address': KeyInfo(),
                'comment': KeyInfo(can_disable=True, remove_value=''),
                'disabled': KeyInfo(default=False),
                'list': KeyInfo(),
            },
        ),
    ),

    ('ip', 'firewall', 'calea'): APIData(
        versioned=[
            ('7.15', '>=', VersionedAPIData(
                fully_understood=True,
                versioned_fields=[
                    ([('7.21', '>=')], 'tos', KeyInfo()),
                ],
                fields={
                    'action': KeyInfo(),
                    'address-list': KeyInfo(),
                    'address-list-timeout': KeyInfo(),
                    'chain': KeyInfo(),
                    'comment': KeyInfo(),
                    'connection-bytes': KeyInfo(can_disable=True),
                    'connection-limit': KeyInfo(can_disable=True),
                    'connection-mark': KeyInfo(can_disable=True),
                    'connection-rate': KeyInfo(can_disable=True),
                    'connection-type': KeyInfo(can_disable=True),
                    'content': KeyInfo(can_disable=True),
                    # 'copy-from': KeyInfo(write_only=True),
                    'disabled': KeyInfo(),
                    'dscp': KeyInfo(can_disable=True),
                    'dst-address': KeyInfo(can_disable=True),
                    'dst-address-list': KeyInfo(can_disable=True),
                    'dst-address-type': KeyInfo(can_disable=True),
                    'dst-limit': KeyInfo(can_disable=True),
                    'dst-port': KeyInfo(can_disable=True),
                    'fragment': KeyInfo(can_disable=True),
                    'hotspot': KeyInfo(can_disable=True),
                    'icmp-options': KeyInfo(can_disable=True),
                    'in-bridge-port': KeyInfo(can_disable=True),
                    'in-bridge-port-list': KeyInfo(can_disable=True),
                    'in-interface': KeyInfo(can_disable=True),
                    'in-interface-list': KeyInfo(can_disable=True),
                    'ingress-priority': KeyInfo(can_disable=True),
                    'ipsec-policy': KeyInfo(can_disable=True),
                    'ipv4-options': KeyInfo(can_disable=True),
                    'layer7-protocol': KeyInfo(can_disable=True),
                    'limit': KeyInfo(can_disable=True),
                    'log': KeyInfo(),
                    'log-prefix': KeyInfo(),
                    'nth': KeyInfo(can_disable=True),
                    'out-bridge-port': KeyInfo(can_disable=True),
                    'out-bridge-port-list': KeyInfo(can_disable=True),
                    'out-interface': KeyInfo(can_disable=True),
                    'out-interface-list': KeyInfo(can_disable=True),
                    'packet-mark': KeyInfo(can_disable=True),
                    'packet-size': KeyInfo(can_disable=True),
                    'per-connection-classifier': KeyInfo(can_disable=True),
                    # 'place-before': KeyInfo(write_only=True),
                    'port': KeyInfo(can_disable=True),
                    'priority': KeyInfo(can_disable=True),
                    'protocol': KeyInfo(can_disable=True),
                    'psd': KeyInfo(can_disable=True),
                    'random': KeyInfo(can_disable=True),
                    'realm': KeyInfo(can_disable=True),
                    'routing-mark': KeyInfo(can_disable=True),
                    'sniff-id': KeyInfo(),
                    'sniff-target': KeyInfo(),
                    'sniff-target-port': KeyInfo(),
                    'src-address': KeyInfo(can_disable=True),
                    'src-address-list': KeyInfo(can_disable=True),
                    'src-address-type': KeyInfo(can_disable=True),
                    'src-mac-address': KeyInfo(can_disable=True),
                    'src-port': KeyInfo(can_disable=True),
                    'tcp-mss': KeyInfo(can_disable=True),
                    'time': KeyInfo(can_disable=True),
                    'tls-host': KeyInfo(can_disable=True),
                    'ttl': KeyInfo(can_disable=True),
                },
            )),
        ],
    ),

    ('ip', 'firewall', 'connection', 'tracking'): APIData(
        unversioned=VersionedAPIData(
            fixed_entries=True,
            single_value=True,
            fully_understood=True,
            versioned_fields=[
                ([('7.20', '>=')], 'liberal-tcp-tracking', KeyInfo()),
            ],
            fields={
                'enabled': KeyInfo(default='auto'),
                'generic-timeout': KeyInfo(default='10m'),
                'icmp-timeout': KeyInfo(default='10s'),
                'loose-tcp-tracking': KeyInfo(default=True),
                'tcp-close-timeout': KeyInfo(default='10s'),
                'tcp-close-wait-timeout': KeyInfo(default='10s'),
                'tcp-established-timeout': KeyInfo(default='1d'),
                'tcp-fin-wait-timeout': KeyInfo(default='10s'),
                'tcp-last-ack-timeout': KeyInfo(default='10s'),
                'tcp-max-retrans-timeout': KeyInfo(default='5m'),
                'tcp-syn-received-timeout': KeyInfo(default='5s'),
                'tcp-syn-sent-timeout': KeyInfo(default='5s'),
                'tcp-time-wait-timeout': KeyInfo(default='10s'),
                'tcp-unacked-timeout': KeyInfo(default='5m'),
                'udp-stream-timeout': KeyInfo(default='3m'),
                'udp-timeout': KeyInfo(default='10s'),
            },
        ),
    ),

    ('ip', 'firewall', 'filter'): APIData(
        unversioned=VersionedAPIData(
            stratify_keys=('chain',),
            fully_understood=True,
            versioned_fields=[
                # ([('7.15', '>=')], 'copy-from', KeyInfo(write_only=True)),
                # ([('7.15', '>=')], 'place-before', KeyInfo(write_only=True)),
                ([('7.15', '<')], 'routing-table', KeyInfo(can_disable=True)),
                ([('7.21', '>=')], 'tos', KeyInfo()),
            ],
            fields={
                'action': KeyInfo(),
                'address-list': KeyInfo(can_disable=True),
                'address-list-timeout': KeyInfo(can_disable=True),
                'chain': KeyInfo(),
                'comment': KeyInfo(can_disable=True, remove_value=''),
                'connection-bytes': KeyInfo(can_disable=True),
                'connection-limit': KeyInfo(can_disable=True),
                'connection-mark': KeyInfo(can_disable=True),
                'connection-nat-state': KeyInfo(can_disable=True),
                'connection-rate': KeyInfo(can_disable=True),
                'connection-state': KeyInfo(can_disable=True),
                'connection-type': KeyInfo(can_disable=True),
                'content': KeyInfo(can_disable=True),
                'disabled': KeyInfo(default=False),
                'dscp': KeyInfo(can_disable=True),
                'dst-address': KeyInfo(can_disable=True),
                'dst-address-list': KeyInfo(can_disable=True),
                'dst-address-type': KeyInfo(can_disable=True),
                'dst-limit': KeyInfo(can_disable=True),
                'dst-port': KeyInfo(can_disable=True),
                'fragment': KeyInfo(can_disable=True),
                'hotspot': KeyInfo(can_disable=True),
                'hw-offload': KeyInfo(can_disable=True),
                'icmp-options': KeyInfo(can_disable=True),
                'in-bridge-port': KeyInfo(can_disable=True),
                'in-bridge-port-list': KeyInfo(can_disable=True),
                'in-interface': KeyInfo(can_disable=True),
                'in-interface-list': KeyInfo(can_disable=True),
                'ingress-priority': KeyInfo(can_disable=True),
                'ipsec-policy': KeyInfo(can_disable=True),
                'ipv4-options': KeyInfo(can_disable=True),
                'jump-target': KeyInfo(can_disable=True),
                'layer7-protocol': KeyInfo(can_disable=True),
                'limit': KeyInfo(can_disable=True),
                'log': KeyInfo(default=False),
                'log-prefix': KeyInfo(default=''),
                'nth': KeyInfo(can_disable=True),
                'out-bridge-port': KeyInfo(can_disable=True),
                'out-bridge-port-list': KeyInfo(can_disable=True),
                'out-interface': KeyInfo(can_disable=True),
                'out-interface-list': KeyInfo(can_disable=True),
                'p2p': KeyInfo(can_disable=True),
                'packet-mark': KeyInfo(can_disable=True),
                'packet-size': KeyInfo(can_disable=True),
                'per-connection-classifier': KeyInfo(can_disable=True),
                'port': KeyInfo(can_disable=True),
                'priority': KeyInfo(can_disable=True),
                'protocol': KeyInfo(can_disable=True),
                'psd': KeyInfo(can_disable=True),
                'random': KeyInfo(can_disable=True),
                'realm': KeyInfo(can_disable=True),
                'reject-with': KeyInfo(can_disable=True),
                'routing-mark': KeyInfo(can_disable=True),
                'src-address': KeyInfo(can_disable=True),
                'src-address-list': KeyInfo(can_disable=True),
                'src-address-type': KeyInfo(can_disable=True),
                'src-mac-address': KeyInfo(can_disable=True),
                'src-port': KeyInfo(can_disable=True),
                'tcp-flags': KeyInfo(can_disable=True),
                'tcp-mss': KeyInfo(can_disable=True),
                'time': KeyInfo(can_disable=True),
                'tls-host': KeyInfo(can_disable=True),
                'ttl': KeyInfo(can_disable=True),
            },
        ),
    ),

    ('ip', 'firewall', 'layer7-protocol'): APIData(
        unversioned=VersionedAPIData(
            primary_keys=('name',),
            fully_understood=True,
            # versioned_fields=[
            #     ([('7.15', '>=')], 'copy-from', KeyInfo(write_only=True)),
            # ],
            fields={
                'comment': KeyInfo(can_disable=True, remove_value=''),
                'name': KeyInfo(),
                'regexp': KeyInfo(),
            },
        ),
    ),

    ('ip', 'firewall', 'mangle'): APIData(
        unversioned=VersionedAPIData(
            stratify_keys=('chain',),
            fully_understood=True,
            versioned_fields=[
                # ([('7.15', '>=')], 'copy-from', KeyInfo(write_only=True)),
                ([('7.19', '<')], 'passthrough', KeyInfo(can_disable=True)),
                ([('7.19', '>=')], 'passthrough', KeyInfo(default=True)),
                # ([('7.15', '>=')], 'place-before', KeyInfo(write_only=True)),
                ([('7.15', '<')], 'routing-table', KeyInfo(can_disable=True)),
                ([('7.21', '>=')], 'tos', KeyInfo()),
            ],
            fields={
                'action': KeyInfo(),
                'address-list': KeyInfo(can_disable=True),
                'address-list-timeout': KeyInfo(can_disable=True),
                'chain': KeyInfo(),
                'comment': KeyInfo(can_disable=True, remove_value=''),
                'connection-bytes': KeyInfo(can_disable=True),
                'connection-limit': KeyInfo(can_disable=True),
                'connection-mark': KeyInfo(can_disable=True),
                'connection-nat-state': KeyInfo(can_disable=True),
                'connection-rate': KeyInfo(can_disable=True),
                'connection-state': KeyInfo(can_disable=True),
                'connection-type': KeyInfo(can_disable=True),
                'content': KeyInfo(can_disable=True),
                'disabled': KeyInfo(default=False),
                'dscp': KeyInfo(can_disable=True),
                'dst-address': KeyInfo(can_disable=True),
                'dst-address-list': KeyInfo(can_disable=True),
                'dst-address-type': KeyInfo(can_disable=True),
                'dst-limit': KeyInfo(can_disable=True),
                'dst-port': KeyInfo(can_disable=True),
                'fragment': KeyInfo(can_disable=True),
                'hotspot': KeyInfo(can_disable=True),
                'icmp-options': KeyInfo(can_disable=True),
                'in-bridge-port': KeyInfo(can_disable=True),
                'in-bridge-port-list': KeyInfo(can_disable=True),
                'in-interface': KeyInfo(can_disable=True),
                'in-interface-list': KeyInfo(can_disable=True),
                'ingress-priority': KeyInfo(can_disable=True),
                'ipsec-policy': KeyInfo(can_disable=True),
                'ipv4-options': KeyInfo(can_disable=True),
                'jump-target': KeyInfo(can_disable=True),
                'layer7-protocol': KeyInfo(can_disable=True),
                'limit': KeyInfo(can_disable=True),
                'log': KeyInfo(default=False),
                'log-prefix': KeyInfo(default=''),
                'new-connection-mark': KeyInfo(can_disable=True),
                'new-dscp': KeyInfo(can_disable=True),
                'new-mss': KeyInfo(can_disable=True),
                'new-packet-mark': KeyInfo(can_disable=True),
                'new-priority': KeyInfo(can_disable=True),
                'new-routing-mark': KeyInfo(can_disable=True),
                'new-ttl': KeyInfo(can_disable=True),
                'nth': KeyInfo(can_disable=True),
                'out-bridge-port': KeyInfo(can_disable=True),
                'out-bridge-port-list': KeyInfo(can_disable=True),
                'out-interface': KeyInfo(can_disable=True),
                'out-interface-list': KeyInfo(can_disable=True),
                'p2p': KeyInfo(can_disable=True),
                'packet-mark': KeyInfo(can_disable=True),
                'packet-size': KeyInfo(can_disable=True),
                'per-connection-classifier': KeyInfo(can_disable=True),
                'port': KeyInfo(can_disable=True),
                'priority': KeyInfo(can_disable=True),
                'protocol': KeyInfo(can_disable=True),
                'psd': KeyInfo(can_disable=True),
                'random': KeyInfo(can_disable=True),
                'realm': KeyInfo(can_disable=True),
                'route-dst': KeyInfo(can_disable=True),
                'routing-mark': KeyInfo(can_disable=True),
                'sniff-id': KeyInfo(can_disable=True),
                'sniff-target': KeyInfo(can_disable=True),
                'sniff-target-port': KeyInfo(can_disable=True),
                'src-address': KeyInfo(can_disable=True),
                'src-address-list': KeyInfo(can_disable=True),
                'src-address-type': KeyInfo(can_disable=True),
                'src-mac-address': KeyInfo(can_disable=True),
                'src-port': KeyInfo(can_disable=True),
                'tcp-flags': KeyInfo(can_disable=True),
                'tcp-mss': KeyInfo(can_disable=True),
                'time': KeyInfo(can_disable=True),
                'tls-host': KeyInfo(can_disable=True),
                'ttl': KeyInfo(can_disable=True),
            },
        ),
    ),

    ('ip', 'firewall', 'nat'): APIData(
        unversioned=VersionedAPIData(
            stratify_keys=('chain',),
            fully_understood=True,
            versioned_fields=[
                # ([('7.15', '>=')], 'copy-from', KeyInfo(write_only=True)),
                # ([('7.15', '>=')], 'place-before', KeyInfo(write_only=True)),
                ([('7.20', '>=')], 'socks5-port', KeyInfo()),
                ([('7.20', '>=')], 'socks5-server', KeyInfo()),
                ([('7.20', '>=')], 'socksify-service', KeyInfo()),
                ([('7.16', '<')], 'tls-host', KeyInfo(can_disable=True)),
                ([('7.21', '>=')], 'tos', KeyInfo()),
            ],
            fields={
                'action': KeyInfo(),
                'address-list': KeyInfo(can_disable=True),
                'address-list-timeout': KeyInfo(can_disable=True),
                'chain': KeyInfo(),
                'comment': KeyInfo(can_disable=True, remove_value=''),
                'connection-bytes': KeyInfo(can_disable=True),
                'connection-limit': KeyInfo(can_disable=True),
                'connection-mark': KeyInfo(can_disable=True),
                'connection-rate': KeyInfo(can_disable=True),
                'connection-type': KeyInfo(can_disable=True),
                'content': KeyInfo(can_disable=True),
                'disabled': KeyInfo(default=False),
                'dscp': KeyInfo(can_disable=True),
                'dst-address': KeyInfo(can_disable=True),
                'dst-address-list': KeyInfo(can_disable=True),
                'dst-address-type': KeyInfo(can_disable=True),
                'dst-limit': KeyInfo(can_disable=True),
                'dst-port': KeyInfo(can_disable=True),
                'fragment': KeyInfo(can_disable=True),
                'hotspot': KeyInfo(can_disable=True),
                'icmp-options': KeyInfo(can_disable=True),
                'in-bridge-port': KeyInfo(can_disable=True),
                'in-bridge-port-list': KeyInfo(can_disable=True),
                'in-interface': KeyInfo(can_disable=True),
                'in-interface-list': KeyInfo(can_disable=True),
                'ingress-priority': KeyInfo(can_disable=True),
                'ipsec-policy': KeyInfo(can_disable=True),
                'ipv4-options': KeyInfo(can_disable=True),
                'jump-target': KeyInfo(can_disable=True),
                'layer7-protocol': KeyInfo(can_disable=True),
                'limit': KeyInfo(can_disable=True),
                'log': KeyInfo(default=False),
                'log-prefix': KeyInfo(default=''),
                'nth': KeyInfo(can_disable=True),
                'out-bridge-port': KeyInfo(can_disable=True),
                'out-bridge-port-list': KeyInfo(can_disable=True),
                'out-interface': KeyInfo(can_disable=True),
                'out-interface-list': KeyInfo(can_disable=True),
                'packet-mark': KeyInfo(can_disable=True),
                'packet-size': KeyInfo(can_disable=True),
                'per-connection-classifier': KeyInfo(can_disable=True),
                'port': KeyInfo(can_disable=True),
                'priority': KeyInfo(can_disable=True),
                'protocol': KeyInfo(can_disable=True),
                'psd': KeyInfo(can_disable=True),
                'random': KeyInfo(can_disable=True),
                'randomise-ports': KeyInfo(can_disable=True),
                'realm': KeyInfo(can_disable=True),
                'routing-mark': KeyInfo(can_disable=True),
                'same-not-by-dst': KeyInfo(can_disable=True),
                'src-address': KeyInfo(can_disable=True),
                'src-address-list': KeyInfo(can_disable=True),
                'src-address-type': KeyInfo(can_disable=True),
                'src-mac-address': KeyInfo(can_disable=True),
                'src-port': KeyInfo(can_disable=True),
                'tcp-mss': KeyInfo(can_disable=True),
                'time': KeyInfo(can_disable=True),
                'to-addresses': KeyInfo(can_disable=True),
                'to-ports': KeyInfo(can_disable=True),
                'ttl': KeyInfo(can_disable=True),
            },
        ),
    ),

    ('ip', 'firewall', 'raw'): APIData(
        unversioned=VersionedAPIData(
            stratify_keys=('chain',),
            fully_understood=True,
            versioned_fields=[
                # ([('7.15', '>=')], 'copy-from', KeyInfo(write_only=True)),
                # ([('7.15', '>=')], 'place-before', KeyInfo(write_only=True)),
                ([('7.21', '>=')], 'tos', KeyInfo()),
            ],
            fields={
                'action': KeyInfo(),
                'address-list': KeyInfo(can_disable=True),
                'address-list-timeout': KeyInfo(can_disable=True),
                'chain': KeyInfo(),
                'comment': KeyInfo(can_disable=True, remove_value=''),
                'content': KeyInfo(can_disable=True),
                'disabled': KeyInfo(default=False),
                'dscp': KeyInfo(can_disable=True),
                'dst-address': KeyInfo(can_disable=True),
                'dst-address-list': KeyInfo(can_disable=True),
                'dst-address-type': KeyInfo(can_disable=True),
                'dst-limit': KeyInfo(can_disable=True),
                'dst-port': KeyInfo(can_disable=True),
                'fragment': KeyInfo(can_disable=True),
                'hotspot': KeyInfo(can_disable=True),
                'icmp-options': KeyInfo(can_disable=True),
                'in-bridge-port': KeyInfo(can_disable=True),
                'in-bridge-port-list': KeyInfo(can_disable=True),
                'in-interface': KeyInfo(can_disable=True),
                'in-interface-list': KeyInfo(can_disable=True),
                'ingress-priority': KeyInfo(can_disable=True),
                'ipsec-policy': KeyInfo(can_disable=True),
                'ipv4-options': KeyInfo(can_disable=True),
                'jump-target': KeyInfo(can_disable=True),
                'limit': KeyInfo(can_disable=True),
                'log': KeyInfo(default=False),
                'log-prefix': KeyInfo(default=''),
                'nth': KeyInfo(can_disable=True),
                'out-bridge-port': KeyInfo(can_disable=True),
                'out-bridge-port-list': KeyInfo(can_disable=True),
                'out-interface': KeyInfo(can_disable=True),
                'out-interface-list': KeyInfo(can_disable=True),
                'packet-mark': KeyInfo(can_disable=True),
                'packet-size': KeyInfo(can_disable=True),
                'per-connection-classifier': KeyInfo(can_disable=True),
                'port': KeyInfo(can_disable=True),
                'priority': KeyInfo(can_disable=True),
                'protocol': KeyInfo(can_disable=True),
                'psd': KeyInfo(can_disable=True),
                'random': KeyInfo(can_disable=True),
                'src-address': KeyInfo(can_disable=True),
                'src-address-list': KeyInfo(can_disable=True),
                'src-address-type': KeyInfo(can_disable=True),
                'src-mac-address': KeyInfo(can_disable=True),
                'src-port': KeyInfo(can_disable=True),
                'tcp-flags': KeyInfo(can_disable=True),
                'tcp-mss': KeyInfo(can_disable=True),
                'time': KeyInfo(can_disable=True),
                'tls-host': KeyInfo(can_disable=True),
                'ttl': KeyInfo(can_disable=True),
            },
        ),
    ),

    ('ip', 'firewall', 'service-port'): APIData(
        unversioned=VersionedAPIData(
            primary_keys=('name',),
            fixed_entries=True,
            fully_understood=True,
            versioned_fields=[
                ([('7.15', '>=')], 'numbers', KeyInfo()),
            ],
            fields={
                'disabled': KeyInfo(default=False),
                'name': KeyInfo(),
                'ports': KeyInfo(),
                'sip-direct-media': KeyInfo(),
                'sip-timeout': KeyInfo(),
            },
        ),
    ),

    ('ip', 'hotspot'): APIData(
        unversioned=VersionedAPIData(
            primary_keys=('name', 'interface'),
            fully_understood=True,
            # versioned_fields=[
            #     ([('7.15', '>=')], 'copy-from', KeyInfo(write_only=True)),
            # ],
            fields={
                'address-pool': KeyInfo(default='none'),
                'addresses-per-mac': KeyInfo(default='2'),
                'disabled': KeyInfo(default=False),
                'idle-timeout': KeyInfo(default='5m'),
                'interface': KeyInfo(required=True),
                'keepalive-timeout': KeyInfo(default='none'),
                'login-timeout': KeyInfo(default='none'),
                'name': KeyInfo(),
                'profile': KeyInfo(default='default'),
            },
        ),
    ),

    ('ip', 'hotspot', 'ip-binding'): APIData(
        versioned=[
            ('7.15', '>=', VersionedAPIData(
                fully_understood=True,
                fields={
                    'address': KeyInfo(),
                    'comment': KeyInfo(),
                    # 'copy-from': KeyInfo(write_only=True),
                    'disabled': KeyInfo(),
                    'mac-address': KeyInfo(),
                    # 'place-before': KeyInfo(write_only=True),
                    'server': KeyInfo(),
                    'to-address': KeyInfo(),
                    'type': KeyInfo(),
                },
            )),
        ],
    ),

    ('ip', 'hotspot', 'profile'): APIData(
        unversioned=VersionedAPIData(
            primary_keys=('name',),
            fully_understood=True,
            # versioned_fields=[
            #     ([('7.15', '>=')], 'copy-from', KeyInfo(write_only=True)),
            # ],
            fields={
                'dns-name': KeyInfo(default=''),
                'hotspot-address': KeyInfo(default='0.0.0.0'),
                'html-directory': KeyInfo(default='flash/hotspot'),
                'html-directory-override': KeyInfo(default=''),
                'http-cookie-lifetime': KeyInfo(default='3d'),
                'http-proxy': KeyInfo(default='0.0.0.0:0'),
                'install-hotspot-queue': KeyInfo(default=False),
                'login-by': KeyInfo(default='cookie,http-chap'),
                'mac-auth-mode': KeyInfo(default='mac-as-username'),
                'mac-auth-password': KeyInfo(),
                'name': KeyInfo(),
                'nas-port-type': KeyInfo(default='wireless-802.11'),
                'radius-accounting': KeyInfo(default=True),
                'radius-default-domain': KeyInfo(default=''),
                'radius-interim-update': KeyInfo(default='received'),
                'radius-location-id': KeyInfo(default=''),
                'radius-location-name': KeyInfo(default=''),
                'radius-mac-format': KeyInfo(default='XX:XX:XX:XX:XX:XX'),
                'rate-limit': KeyInfo(),
                'smtp-server': KeyInfo(default='0.0.0.0'),
                'split-user-domain': KeyInfo(default=False),
                'ssl-certificate': KeyInfo(),
                'trial-uptime-limit': KeyInfo(default='30m'),
                'trial-uptime-reset': KeyInfo(default='1d'),
                'trial-user-profile': KeyInfo(default='default'),
                'use-radius': KeyInfo(default=False),
            },
        ),
    ),

    ('ip', 'hotspot', 'service-port'): APIData(
        unversioned=VersionedAPIData(
            primary_keys=('name',),
            fixed_entries=True,
            fully_understood=True,
            versioned_fields=[
                ([('7.15', '>=')], 'numbers', KeyInfo()),
            ],
            fields={
                'disabled': KeyInfo(default=False),
                'name': KeyInfo(),
                'ports': KeyInfo(),
            },
        ),
    ),

    ('ip', 'hotspot', 'user'): APIData(
        unversioned=VersionedAPIData(
            primary_keys=('name',),
            fully_understood=True,
            versioned_fields=[
                # ([('7.15', '>=')], 'copy-from', KeyInfo(write_only=True)),
                ([('7.21', '>=')], 'totp-secret', KeyInfo()),
            ],
            fields={
                'address': KeyInfo(),
                'comment': KeyInfo(can_disable=True, remove_value=''),
                'disabled': KeyInfo(default=False),
                'email': KeyInfo(),
                'limit-bytes-in': KeyInfo(),
                'limit-bytes-out': KeyInfo(),
                'limit-bytes-total': KeyInfo(),
                'limit-uptime': KeyInfo(),
                'mac-address': KeyInfo(),
                'name': KeyInfo(),
                'password': KeyInfo(),
                'profile': KeyInfo(default='default'),
                'routes': KeyInfo(),
                'server': KeyInfo(default='all'),
            },
        ),
    ),

    ('ip', 'hotspot', 'user', 'profile'): APIData(
        unversioned=VersionedAPIData(
            primary_keys=('name',),
            fully_understood=True,
            versioned_fields=[
                # ([('7.15', '>=')], 'copy-from', KeyInfo(write_only=True)),
                ([('7.15', '>=')], 'on-login', KeyInfo()),
                ([('7.15', '>=')], 'on-logout', KeyInfo()),
            ],
            fields={
                'add-mac-cookie': KeyInfo(default=True),
                'address-list': KeyInfo(default=''),
                'address-pool': KeyInfo(default='none'),
                'advertise': KeyInfo(default=False),
                'advertise-interval': KeyInfo(),
                'advertise-timeout': KeyInfo(),
                'advertise-url': KeyInfo(),
                'idle-timeout': KeyInfo(can_disable=True, default='none'),
                'incoming-filter': KeyInfo(),
                'incoming-packet-mark': KeyInfo(),
                'insert-queue-before': KeyInfo(can_disable=True),
                'keepalive-timeout': KeyInfo(can_disable=True, default='2m'),
                'mac-cookie-timeout': KeyInfo(can_disable=True, default='3d'),
                'name': KeyInfo(),
                'open-status-page': KeyInfo(default='always'),
                'outgoing-filter': KeyInfo(),
                'outgoing-packet-mark': KeyInfo(),
                'parent-queue': KeyInfo(can_disable=True),
                'queue-type': KeyInfo(can_disable=True),
                'rate-limit': KeyInfo(),
                'session-timeout': KeyInfo(),
                'shared-users': KeyInfo(default=1),
                'status-autorefresh': KeyInfo(default='1m'),
                'transparent-proxy': KeyInfo(default=False),
            },
        ),
    ),

    ('ip', 'hotspot', 'walled-garden'): APIData(
        unversioned=VersionedAPIData(
            fully_understood=True,
            # versioned_fields=[
            #     ([('7.15', '>=')], 'copy-from', KeyInfo(write_only=True)),
            #     ([('7.15', '>=')], 'place-before', KeyInfo(write_only=True)),
            # ],
            fields={
                'action': KeyInfo(default='allow'),
                'comment': KeyInfo(can_disable=True, remove_value=''),
                'disabled': KeyInfo(default=False),
                'dst-host': KeyInfo(can_disable=True),
                'dst-port': KeyInfo(can_disable=True),
                'method': KeyInfo(can_disable=True),
                'path': KeyInfo(can_disable=True),
                'server': KeyInfo(can_disable=True),
                'src-address': KeyInfo(can_disable=True),
            },
        ),
    ),

    ('ip', 'hotspot', 'walled-garden', 'ip'): APIData(
        unversioned=VersionedAPIData(
            fully_understood=True,
            # versioned_fields=[
            #     ([('7.15', '>=')], 'copy-from', KeyInfo(write_only=True)),
            #     ([('7.15', '>=')], 'place-before', KeyInfo(write_only=True)),
            # ],
            fields={
                'action': KeyInfo(default='accept'),
                'comment': KeyInfo(can_disable=True, remove_value=''),
                'disabled': KeyInfo(default='no'),
                'dst-address': KeyInfo(can_disable=True, remove_value=''),
                'dst-address-list': KeyInfo(can_disable=True, remove_value=''),
                'dst-host': KeyInfo(),
                'dst-port': KeyInfo(can_disable=True),
                'protocol': KeyInfo(can_disable=True),
                'server': KeyInfo(can_disable=True),
                'src-address': KeyInfo(can_disable=True),
                'src-address-list': KeyInfo(can_disable=True),
            },
        ),
    ),

    ('ip', 'ipsec', 'identity'): APIData(
        unversioned=VersionedAPIData(
            fully_understood=True,
            # versioned_fields=[
            #     ([('7.15', '>=')], 'copy-from', KeyInfo(write_only=True)),
            # ],
            fields={
                'auth-method': KeyInfo(default='pre-shared-key'),
                'certificate': KeyInfo(),
                'comment': KeyInfo(can_disable=True, remove_value=''),
                'disabled': KeyInfo(default=False),
                'eap-methods': KeyInfo(default='eap-tls'),
                'generate-policy': KeyInfo(default=False),
                'key': KeyInfo(),
                'match-by': KeyInfo(can_disable=True, remove_value='remote-id'),
                'mode-config': KeyInfo(can_disable=True, remove_value='none'),
                'my-id': KeyInfo(can_disable=True, remove_value='auto'),
                'notrack-chain': KeyInfo(can_disable=True, remove_value=''),
                'password': KeyInfo(),
                'peer': KeyInfo(),
                'policy-template-group': KeyInfo(can_disable=True, remove_value='default'),
                'remote-certificate': KeyInfo(),
                'remote-id': KeyInfo(can_disable=True, remove_value='auto'),
                'remote-key': KeyInfo(),
                'secret': KeyInfo(default=''),
                'username': KeyInfo(),
            },
        ),
    ),

    ('ip', 'ipsec', 'key'): APIData(
        versioned=[
            ('7.15', '>=', VersionedAPIData(
                fully_understood=True,
                has_identifier=True,
                # fixed_entries=True,
                # primary_keys=('numbers',),
                fields={
                    'name': KeyInfo(),
                    'numbers': KeyInfo(),
                },
            )),
            ('7.20', '>=', 'Not supported anymore in version 7.20'),
        ],
    ),

    ('ip', 'ipsec', 'key', 'psk'): APIData(
        versioned=[
            ('7.21', '>=', VersionedAPIData(
                fully_understood=True,
                fields={
                    # 'copy-from': KeyInfo(write_only=True),
                    'id': KeyInfo(),
                    'key': KeyInfo(),
                    'peer': KeyInfo(),
                },
            )),
        ],
    ),

    ('ip', 'ipsec', 'key', 'qkd'): APIData(
        versioned=[
            ('7.21', '>=', VersionedAPIData(
                fixed_entries=True,
                single_value=True,
                fully_understood=True,
                fields={
                    'address': KeyInfo(),
                    'cache-size': KeyInfo(),
                    'certificate': KeyInfo(),
                    'enabled': KeyInfo(),
                    'key-size': KeyInfo(),
                    'kme-id': KeyInfo(),
                    'peer-sae-id': KeyInfo(),
                },
            )),
        ],
    ),

    ('ip', 'ipsec', 'key', 'rsa'): APIData(
        versioned=[
            ('7.20', '>=', VersionedAPIData(
                primary_keys=('numbers',),
                fixed_entries=True,
                fully_understood=True,
                fields={
                    'name': KeyInfo(),
                    'numbers': KeyInfo(),
                },
            )),
        ],
    ),

    ('ip', 'ipsec', 'mode-config'): APIData(
        unversioned=VersionedAPIData(
            primary_keys=('name',),
            fully_understood=True,
            versioned_fields=[
                ([('6.44', '>=')], 'address', KeyInfo(can_disable=True, remove_value='0.0.0.0')),
                ([('7.15', '<')], 'comment', KeyInfo(can_disable=True, remove_value='')),
                ([('7.15', '>=')], 'connection-mark', KeyInfo()),
                # ([('7.15', '>=')], 'copy-from', KeyInfo(write_only=True)),
                ([('6.43', '>=')], 'responder', KeyInfo(default=False)),
                ([('7.15', '>=')], 'use-responder-dns', KeyInfo()),
            ],
            fields={
                'address-pool': KeyInfo(can_disable=True, remove_value='none'),
                'address-prefix-length': KeyInfo(),
                'name': KeyInfo(),
                'split-dns': KeyInfo(can_disable=True, remove_value=''),
                'split-include': KeyInfo(can_disable=True, remove_value=''),
                'src-address-list': KeyInfo(can_disable=True, remove_value=''),
                'static-dns': KeyInfo(can_disable=True, remove_value=''),
                'system-dns': KeyInfo(default=False),
            },
        ),
    ),

    ('ip', 'ipsec', 'peer'): APIData(
        unversioned=VersionedAPIData(
            primary_keys=('name',),
            fully_understood=True,
            versioned_fields=[
                # ([('7.15', '>=')], 'copy-from', KeyInfo(write_only=True)),
                ([('7.21', '>=')], 'ppk-secret', KeyInfo()),
            ],
            fields={
                'address': KeyInfo(can_disable=True, remove_value=''),
                'comment': KeyInfo(can_disable=True, remove_value=''),
                'disabled': KeyInfo(default=False),
                'exchange-mode': KeyInfo(default='main'),
                'local-address': KeyInfo(can_disable=True, remove_value='0.0.0.0'),
                'name': KeyInfo(),
                'passive': KeyInfo(can_disable=True, remove_value=False),
                'port': KeyInfo(can_disable=True, remove_value=500),
                'profile': KeyInfo(default='default'),
                'send-initial-contact': KeyInfo(default=True),
            },
        ),
    ),

    ('ip', 'ipsec', 'policy'): APIData(
        unversioned=VersionedAPIData(
            fully_understood=True,
            versioned_fields=[
                # ([('7.15', '>=')], 'copy-from', KeyInfo(write_only=True)),
                # ([('7.15', '>=')], 'place-before', KeyInfo(write_only=True)),
                ([('7.15', '>=')], 'sa-dst-address', KeyInfo()),
                ([('7.15', '>=')], 'sa-src-address', KeyInfo()),
            ],
            fields={
                'action': KeyInfo(default='encrypt'),
                'comment': KeyInfo(can_disable=True, remove_value=''),
                'disabled': KeyInfo(default=False),
                'dst-address': KeyInfo(),
                'dst-port': KeyInfo(default='any'),
                'group': KeyInfo(can_disable=True, remove_value='default'),
                'ipsec-protocols': KeyInfo(default='esp'),
                'level': KeyInfo(default='require'),
                'peer': KeyInfo(),
                'proposal': KeyInfo(default='default'),
                'protocol': KeyInfo(default='all'),
                'src-address': KeyInfo(),
                'src-port': KeyInfo(default='any'),
                'template': KeyInfo(can_disable=True, remove_value=False),
                'tunnel': KeyInfo(default=False),
            },
        ),
    ),

    ('ip', 'ipsec', 'policy', 'group'): APIData(
        unversioned=VersionedAPIData(
            fully_understood=True,
            versioned_fields=[
                ([('7.15', '>=')], 'comment', KeyInfo()),
                # ([('7.15', '>=')], 'copy-from', KeyInfo(write_only=True)),
                ([('7.15', '<')], 'default', KeyInfo()),
            ],
            fields={
                'name': KeyInfo(),
            },
        ),
    ),

    ('ip', 'ipsec', 'profile'): APIData(
        unversioned=VersionedAPIData(
            primary_keys=('name',),
            fully_understood=True,
            versioned_fields=[
                # ([('7.15', '>=')], 'copy-from', KeyInfo(write_only=True)),
                ([('7.21', '>=')], 'ppk', KeyInfo()),
            ],
            fields={
                'dh-group': KeyInfo(default='modp2048,modp1024'),
                'dpd-interval': KeyInfo(default='2m'),
                'dpd-maximum-failures': KeyInfo(default=5),
                'enc-algorithm': KeyInfo(default='aes-128,3des'),
                'hash-algorithm': KeyInfo(default='sha1'),
                'lifebytes': KeyInfo(can_disable=True, remove_value=0),
                'lifetime': KeyInfo(default='1d'),
                'name': KeyInfo(),
                'nat-traversal': KeyInfo(default=True),
                'prf-algorithm': KeyInfo(can_disable=True, remove_value='auto'),
                'proposal-check': KeyInfo(default='obey'),
            },
        ),
    ),

    ('ip', 'ipsec', 'proposal'): APIData(
        unversioned=VersionedAPIData(
            primary_keys=('name',),
            fully_understood=True,
            versioned_fields=[
                ([('7.15', '>=')], 'comment', KeyInfo()),
                # ([('7.15', '>=')], 'copy-from', KeyInfo(write_only=True)),
            ],
            fields={
                'auth-algorithms': KeyInfo(default='sha1'),
                'disabled': KeyInfo(default=False),
                'enc-algorithms': KeyInfo(default='aes-256-cbc,aes-192-cbc,aes-128-cbc'),
                'lifetime': KeyInfo(default='30m'),
                'name': KeyInfo(),
                'pfs-group': KeyInfo(default='modp1024'),
            },
        ),
    ),

    ('ip', 'ipsec', 'settings'): APIData(
        unversioned=VersionedAPIData(
            fixed_entries=True,
            single_value=True,
            fully_understood=True,
            fields={
                'accounting': KeyInfo(default=True),
                'interim-update': KeyInfo(default='0s'),
                'xauth-use-radius': KeyInfo(default=False),
            },
        ),
    ),

    ('ip', 'kid-control'): APIData(
        versioned=[
            ('7.15', '>=', VersionedAPIData(
                fully_understood=True,
                fields={
                    # 'copy-from': KeyInfo(write_only=True),
                    'disabled': KeyInfo(),
                    'fri': KeyInfo(),
                    'mon': KeyInfo(),
                    'name': KeyInfo(),
                    'rate-limit': KeyInfo(),
                    'sat': KeyInfo(),
                    'sun': KeyInfo(),
                    'thu': KeyInfo(),
                    'tue': KeyInfo(),
                    'tur-fri': KeyInfo(),
                    'tur-mon': KeyInfo(),
                    'tur-sat': KeyInfo(),
                    'tur-sun': KeyInfo(),
                    'tur-thu': KeyInfo(),
                    'tur-tue': KeyInfo(),
                    'tur-wed': KeyInfo(),
                    'wed': KeyInfo(),
                },
            )),
        ],
    ),

    ('ip', 'kid-control', 'device'): APIData(
        versioned=[
            ('7.15', '>=', VersionedAPIData(
                fully_understood=True,
                fields={
                    # 'copy-from': KeyInfo(write_only=True),
                    'disabled': KeyInfo(),
                    'mac-address': KeyInfo(),
                    'name': KeyInfo(),
                    'user': KeyInfo(),
                },
            )),
        ],
    ),

    ('ip', 'media'): APIData(
        versioned=[
            ('7.15', '>=', VersionedAPIData(
                fully_understood=True,
                fields={
                    'allowed-hostname': KeyInfo(),
                    'allowed-ip': KeyInfo(),
                    # 'copy-from': KeyInfo(write_only=True),
                    'disabled': KeyInfo(),
                    'friendly-name': KeyInfo(),
                    'interface': KeyInfo(),
                    'path': KeyInfo(),
                },
            )),
        ],
    ),

    ('ip', 'media', 'settings'): APIData(
        versioned=[
            ('7.15', '>=', VersionedAPIData(
                fixed_entries=True,
                single_value=True,
                fully_understood=True,
                fields={
                    'thumbnails': KeyInfo(),
                },
            )),
        ],
    ),

    ('ip', 'nat-pmp'): APIData(
        versioned=[
            ('7.15', '>=', VersionedAPIData(
                fixed_entries=True,
                single_value=True,
                fully_understood=True,
                fields={
                    'enabled': KeyInfo(),
                },
            )),
        ],
    ),

    ('ip', 'nat-pmp', 'interfaces'): APIData(
        versioned=[
            ('7.15', '>=', VersionedAPIData(
                fully_understood=True,
                fields={
                    # 'copy-from': KeyInfo(write_only=True),
                    'disabled': KeyInfo(),
                    'forced-ip': KeyInfo(),
                    'interface': KeyInfo(),
                    'type': KeyInfo(),
                },
            )),
        ],
    ),

    ('ip', 'neighbor', 'discovery-settings'): APIData(
        unversioned=VersionedAPIData(
            fixed_entries=True,
            single_value=True,
            fully_understood=True,
            versioned_fields=[
                ([('7.16', '>=')], 'discover-interval', KeyInfo(default='30s')),
                ([('7.17', '>=')], 'lldp-dcbx', KeyInfo(default=False)),
                ([('7.15', '>=')], 'lldp-mac-phy-config', KeyInfo(default=False)),
                ([('7.15', '>=')], 'lldp-max-frame-size', KeyInfo()),
                ([('7.15', '>=')], 'lldp-poe-power', KeyInfo()),
                ([('7.16', '>=')], 'lldp-vlan-info', KeyInfo(default=False)),
                ([('7.7', '>=')], 'mode', KeyInfo(default='tx-and-rx')),
            ],
            fields={
                'discover-interface-list': KeyInfo(),
                'lldp-med-net-policy-vlan': KeyInfo(default='disabled'),
                'protocol': KeyInfo(default='cdp,lldp,mndp'),
            },
        ),
    ),

    ('ip', 'packing'): APIData(
        versioned=[
            ('7.15', '>=', VersionedAPIData(
                fully_understood=True,
                fields={
                    'aggregated-size': KeyInfo(),
                    # 'copy-from': KeyInfo(write_only=True),
                    'disabled': KeyInfo(),
                    'interface': KeyInfo(),
                    'packing': KeyInfo(),
                    'unpacking': KeyInfo(),
                },
            )),
        ],
    ),

    ('ip', 'pool'): APIData(
        unversioned=VersionedAPIData(
            primary_keys=('name',),
            fully_understood=True,
            # versioned_fields=[
            #     ([('7.15', '>=')], 'copy-from', KeyInfo(write_only=True)),
            # ],
            fields={
                'comment': KeyInfo(),
                'name': KeyInfo(),
                'next-pool': KeyInfo(),
                'ranges': KeyInfo(),
            },
        ),
    ),

    ('ip', 'pool', 'used'): APIData(
        versioned=[
            ('7.15', '>=', VersionedAPIData(
                fully_understood=True,
                has_identifier=True,
                # fixed_entries=True,
                # primary_keys=('numbers',),
                fields={
                    'address': KeyInfo(),
                    'info': KeyInfo(),
                    'numbers': KeyInfo(),
                    'owner': KeyInfo(),
                    'pool': KeyInfo(),
                },
            )),
        ],
    ),

    ('ip', 'proxy'): APIData(
        unversioned=VersionedAPIData(
            fixed_entries=True,
            single_value=True,
            fully_understood=True,
            fields={
                'always-from-cache': KeyInfo(default=False),
                'anonymous': KeyInfo(default=False),
                'cache-administrator': KeyInfo(default='webmaster'),
                'cache-hit-dscp': KeyInfo(default=4),
                'cache-on-disk': KeyInfo(default=False),
                'cache-path': KeyInfo(default='web-proxy'),
                'enabled': KeyInfo(default=False),
                'max-cache-object-size': KeyInfo(default='2048KiB'),
                'max-cache-size': KeyInfo(default='unlimited'),
                'max-client-connections': KeyInfo(default=600),
                'max-fresh-time': KeyInfo(default='3d'),
                'max-server-connections': KeyInfo(default=600),
                'parent-proxy': KeyInfo(default='::'),
                'parent-proxy-port': KeyInfo(default=0),
                'port': KeyInfo(default=8080),
                'serialize-connections': KeyInfo(default=False),
                'src-address': KeyInfo(default='::'),
            },
        ),
    ),

    ('ip', 'proxy', 'access'): APIData(
        versioned=[
            ('7.15', '>=', VersionedAPIData(
                fully_understood=True,
                fields={
                    'action': KeyInfo(),
                    'action-data': KeyInfo(),
                    'comment': KeyInfo(),
                    # 'copy-from': KeyInfo(write_only=True),
                    'disabled': KeyInfo(),
                    'dst-address': KeyInfo(),
                    'dst-host': KeyInfo(),
                    'dst-port': KeyInfo(),
                    'local-port': KeyInfo(),
                    'method': KeyInfo(),
                    'path': KeyInfo(),
                    # 'place-before': KeyInfo(write_only=True),
                    'src-address': KeyInfo(),
                },
            )),
        ],
    ),

    ('ip', 'proxy', 'cache'): APIData(
        versioned=[
            ('7.15', '>=', VersionedAPIData(
                fully_understood=True,
                fields={
                    'action': KeyInfo(),
                    'comment': KeyInfo(),
                    # 'copy-from': KeyInfo(write_only=True),
                    'disabled': KeyInfo(),
                    'dst-address': KeyInfo(),
                    'dst-host': KeyInfo(),
                    'dst-port': KeyInfo(),
                    'local-port': KeyInfo(),
                    'method': KeyInfo(),
                    'path': KeyInfo(),
                    # 'place-before': KeyInfo(write_only=True),
                    'src-address': KeyInfo(),
                },
            )),
        ],
    ),

    ('ip', 'proxy', 'connections'): APIData(
        versioned=[
            ('7.15', '>=', VersionedAPIData(
                fully_understood=True,
                has_identifier=True,
                # fixed_entries=True,
                # primary_keys=('numbers',),
                fields={
                    'comment': KeyInfo(),
                    'numbers': KeyInfo(),
                },
            )),
        ],
    ),

    ('ip', 'proxy', 'direct'): APIData(
        versioned=[
            ('7.15', '>=', VersionedAPIData(
                fully_understood=True,
                fields={
                    'action': KeyInfo(),
                    'comment': KeyInfo(),
                    # 'copy-from': KeyInfo(write_only=True),
                    'disabled': KeyInfo(),
                    'dst-address': KeyInfo(),
                    'dst-host': KeyInfo(),
                    'dst-port': KeyInfo(),
                    'local-port': KeyInfo(),
                    'method': KeyInfo(),
                    'path': KeyInfo(),
                    # 'place-before': KeyInfo(write_only=True),
                    'src-address': KeyInfo(),
                },
            )),
        ],
    ),

    ('ip', 'route'): APIData(
        unversioned=VersionedAPIData(
            fully_understood=True,
            versioned_fields=[
                # ([('7.15', '>=')], 'copy-from', KeyInfo(write_only=True)),
                ([('7.15', '<')], 'route-tag', KeyInfo(can_disable=True)),
                ([('7.15', '<')], 'routing-mark', KeyInfo(can_disable=True)),
                ([('7.15', '<')], 'type', KeyInfo(can_disable=True, remove_value='unicast')),
            ],
            fields={
                'blackhole': KeyInfo(can_disable=True),
                'check-gateway': KeyInfo(can_disable=True),
                'comment': KeyInfo(can_disable=True, remove_value=''),
                'disabled': KeyInfo(default=False),
                'distance': KeyInfo(),
                'dst-address': KeyInfo(),
                'gateway': KeyInfo(),
                'pref-src': KeyInfo(),
                'routing-table': KeyInfo(default='main'),
                'scope': KeyInfo(),
                'suppress-hw-offload': KeyInfo(default=False),
                'target-scope': KeyInfo(),
                'vrf-interface': KeyInfo(can_disable=True),
            },
        ),
    ),

    ('ip', 'route', 'rule'): APIData(
        versioned=[
            ('7', '<', VersionedAPIData(
                fully_understood=True,
                fields={
                    'action': KeyInfo(default='lookup'),
                    'comment': KeyInfo(can_disable=True, remove_value=''),
                    'disabled': KeyInfo(default=False),
                    'dst-address': KeyInfo(can_disable=True),
                    'interface': KeyInfo(can_disable=True),
                    'routing-mark': KeyInfo(can_disable=True),
                    'src-address': KeyInfo(can_disable=True),
                    'table': KeyInfo(default='main'),
                },
            )),
            ('7', '>=', 'Not supported anymore in version 7'),
        ],
    ),

    ('ip', 'route', 'vrf'): APIData(
        versioned=[
            ('7', '<', VersionedAPIData(
                primary_keys=('routing-mark',),
                fully_understood=True,
                fields={
                    'comment': KeyInfo(can_disable=True, remove_value=''),
                    'disabled': KeyInfo(default=False),
                    'interfaces': KeyInfo(),
                    'routing-mark': KeyInfo(),
                },
            )),
            ('7', '>=', 'Not supported anymore in version 7'),
        ],
    ),

    ('ip', 'service'): APIData(
        unversioned=VersionedAPIData(
            primary_keys=('name',),
            fixed_entries=True,
            fully_understood=True,
            versioned_fields=[
                ([('7.16', '>=')], 'max-sessions', KeyInfo(default=20)),
                ([('7.15', '>=')], 'numbers', KeyInfo()),
                ([('7.15', '>=')], 'vrf', KeyInfo()),
            ],
            fields={
                'address': KeyInfo(),
                'certificate': KeyInfo(),
                'disabled': KeyInfo(default=False),
                'name': KeyInfo(),
                'port': KeyInfo(),
                'tls-version': KeyInfo(),
            },
        ),
    ),

    ('ip', 'service', 'webserver'): APIData(
        versioned=[
            ('7.21', '>=', VersionedAPIData(
                fixed_entries=True,
                single_value=True,
                fully_understood=True,
                fields={
                    'acme-plain': KeyInfo(),
                    'crl-plain': KeyInfo(),
                    'graphs-plain': KeyInfo(),
                    'graphs-secure': KeyInfo(),
                    'index-plain': KeyInfo(),
                    'index-secure': KeyInfo(),
                    'rest-plain': KeyInfo(),
                    'rest-secure': KeyInfo(),
                    'scep-plain': KeyInfo(),
                    'webfig-plain': KeyInfo(),
                    'webfig-secure': KeyInfo(),
                },
            )),
        ],
    ),

    ('ip', 'settings'): APIData(
        unversioned=VersionedAPIData(
            fixed_entries=True,
            single_value=True,
            fully_understood=True,
            versioned_fields=[
                ([('7.17', '>=')], 'icmp-errors-use-inbound-interface-address', KeyInfo()),
                ([('7.16', '>=')], 'ipv4-multipath-hash-policy', KeyInfo(default='l3')),
                ([('7.15', '<')], 'route-cache', KeyInfo(default=True)),
                ([('7.17', '>=')], 'tcp-timestamps', KeyInfo()),
            ],
            fields={
                'accept-redirects': KeyInfo(default=False),
                'accept-source-route': KeyInfo(default=False),
                'allow-fast-path': KeyInfo(default=True),
                'arp-timeout': KeyInfo(default='30s'),
                'icmp-rate-limit': KeyInfo(default=10),
                'icmp-rate-mask': KeyInfo(default='0x1818'),
                'ip-forward': KeyInfo(default=True),
                'max-neighbor-entries': KeyInfo(default=8192),
                'rp-filter': KeyInfo(default=False),
                'secure-redirects': KeyInfo(default=True),
                'send-redirects': KeyInfo(default=True),
                'tcp-syncookies': KeyInfo(default=False),
            },
        ),
    ),

    ('ip', 'smb'): APIData(
        unversioned=VersionedAPIData(
            fixed_entries=True,
            single_value=True,
            fully_understood=True,
            versioned_fields=[
                ([('7.15', '<')], 'allow-guests', KeyInfo(default=True)),
            ],
            fields={
                'comment': KeyInfo(default='MikrotikSMB'),
                'domain': KeyInfo(default='MSHOME'),
                'enabled': KeyInfo(default=False),
                'interfaces': KeyInfo(default='all'),
            },
        ),
    ),

    ('ip', 'smb', 'shares'): APIData(
        unversioned=VersionedAPIData(
            fully_understood=True,
            versioned_fields=[
                # ([('7.15', '>=')], 'copy-from', KeyInfo(write_only=True)),
                ([('7.15', '<')], 'default', KeyInfo()),
                ([('7.15', '>=')], 'invalid-users', KeyInfo()),
                ([('7.15', '<')], 'max-sessions', KeyInfo()),
                ([('7.15', '>=')], 'read-only', KeyInfo()),
                ([('7.15', '>=')], 'require-encryption', KeyInfo()),
                ([('7.15', '>=')], 'valid-users', KeyInfo()),
            ],
            fields={
                'comment': KeyInfo(can_disable=True, remove_value=''),
                'directory': KeyInfo(),
                'disabled': KeyInfo(),
                'name': KeyInfo(),
            },
        ),
    ),

    ('ip', 'smb', 'users'): APIData(
        unversioned=VersionedAPIData(
            fully_understood=True,
            versioned_fields=[
                ([('7.15', '>=')], 'comment', KeyInfo()),
                # ([('7.15', '>=')], 'copy-from', KeyInfo(write_only=True)),
                ([('7.15', '<')], 'default', KeyInfo()),
            ],
            fields={
                'disabled': KeyInfo(),
                'name': KeyInfo(),
                'password': KeyInfo(),
                'read-only': KeyInfo(),
            },
        ),
    ),

    ('ip', 'socks'): APIData(
        unversioned=VersionedAPIData(
            fixed_entries=True,
            single_value=True,
            fully_understood=True,
            versioned_fields=[
                ([('7.15', '>=')], 'vrf', KeyInfo()),
            ],
            fields={
                'auth-method': KeyInfo(default='none'),
                'connection-idle-timeout': KeyInfo(default='2m'),
                'enabled': KeyInfo(default=False),
                'max-connections': KeyInfo(default=200),
                'port': KeyInfo(default=1080),
                'version': KeyInfo(default=4),
            },
        ),
    ),

    ('ip', 'socks', 'access'): APIData(
        unversioned=VersionedAPIData(
            fully_understood=True,
            versioned_fields=[
                # ([('7.15', '>=')], 'copy-from', KeyInfo(write_only=True)),
                # ([('7.15', '>=')], 'place-before', KeyInfo(write_only=True)),
                ([('7.15', '>=')], 'src-port', KeyInfo(can_disable=True)),
            ],
            fields={
                'action': KeyInfo(default='allow'),
                'comment': KeyInfo(can_disable=True, remove_value=''),
                'disabled': KeyInfo(default=False),
                'dst-address': KeyInfo(can_disable=True),
                'dst-port': KeyInfo(can_disable=True),
                'src-address': KeyInfo(can_disable=True),
            },
        ),
    ),

    ('ip', 'socks', 'connections'): APIData(
        versioned=[
            ('7.15', '>=', VersionedAPIData(
                fully_understood=True,
                has_identifier=True,
                # fixed_entries=True,
                # primary_keys=('numbers',),
                fields={
                    'dst-address': KeyInfo(read_only=True),
                    'numbers': KeyInfo(),
                    'rx': KeyInfo(read_only=True),
                    'src-address': KeyInfo(read_only=True),
                    'tx': KeyInfo(read_only=True),
                    'type': KeyInfo(read_only=True),
                },
            )),
        ],
    ),

    ('ip', 'socks', 'users'): APIData(
        versioned=[
            ('7.15', '>=', VersionedAPIData(
                fully_understood=True,
                fields={
                    # 'copy-from': KeyInfo(write_only=True),
                    'disabled': KeyInfo(default=False),
                    'name': KeyInfo(required=True),
                    'only-one': KeyInfo(default=False),
                    'password': KeyInfo(required=True),
                    'rate-limit': KeyInfo(),
                },
            )),
        ],
    ),

    ('ip', 'socksify'): APIData(
        versioned=[
            ('7.20', '>=', VersionedAPIData(
                fully_understood=True,
                fields={
                    'comment': KeyInfo(),
                    'connection-timeout': KeyInfo(default=60),
                    # 'copy-from': KeyInfo(write_only=True),
                    'disabled': KeyInfo(default=True),
                    'name': KeyInfo(),
                    'port': KeyInfo(default=952),
                    'socks5-password': KeyInfo(),
                    'socks5-port': KeyInfo(default=1080),
                    'socks5-server': KeyInfo(default='0.0.0.0'),
                    'socks5-user': KeyInfo(),
                },
            )),
        ],
    ),

    ('ip', 'ssh'): APIData(
        unversioned=VersionedAPIData(
            fixed_entries=True,
            single_value=True,
            fully_understood=True,
            versioned_fields=[
                ([('7.17', '<')], 'allow-none-crypto', KeyInfo(default=False)),
                ([('7.21', '<')], 'always-allow-password-login', KeyInfo(default=False)),
                ([('7.17', '>=')], 'ciphers', KeyInfo()),
                ([('7.9', '>=')], 'host-key-type', KeyInfo(default='rsa')),
                ([('7.21', '>=')], 'password-authentication', KeyInfo()),
                ([('7.21', '>=')], 'publickey-authentication-options', KeyInfo()),
            ],
            fields={
                'forwarding-enabled': KeyInfo(default=False),
                'host-key-size': KeyInfo(default=2048),
                'strong-crypto': KeyInfo(default=False),
            },
        ),
    ),

    ('ip', 'tftp'): APIData(
        versioned=[
            ('7.15', '>=', VersionedAPIData(
                fully_understood=True,
                fields={
                    'allow': KeyInfo(),
                    'allow-overwrite': KeyInfo(),
                    'allow-rollover': KeyInfo(),
                    'comment': KeyInfo(),
                    # 'copy-from': KeyInfo(write_only=True),
                    'disabled': KeyInfo(),
                    'ip-addresses': KeyInfo(),
                    # 'place-before': KeyInfo(write_only=True),
                    'read-only': KeyInfo(),
                    'reading-window-size': KeyInfo(),
                    'real-filename': KeyInfo(),
                    'req-filename': KeyInfo(),
                },
            )),
        ],
    ),

    ('ip', 'tftp', 'settings'): APIData(
        unversioned=VersionedAPIData(
            fixed_entries=True,
            single_value=True,
            fully_understood=True,
            fields={
                'max-block-size': KeyInfo(default=4096),
            },
        ),
    ),

    ('ip', 'traffic-flow'): APIData(
        unversioned=VersionedAPIData(
            fixed_entries=True,
            single_value=True,
            fully_understood=True,
            fields={
                'active-flow-timeout': KeyInfo(default='30m'),
                'cache-entries': KeyInfo(default='32k'),
                'enabled': KeyInfo(default=False),
                'inactive-flow-timeout': KeyInfo(default='15s'),
                'interfaces': KeyInfo(default='all'),
                'packet-sampling': KeyInfo(default=False),
                'sampling-interval': KeyInfo(default=0),
                'sampling-space': KeyInfo(default=0),
            },
        ),
    ),

    ('ip', 'traffic-flow', 'ipfix'): APIData(
        unversioned=VersionedAPIData(
            fixed_entries=True,
            single_value=True,
            fully_understood=True,
            fields={
                'bytes': KeyInfo(default=True),
                'dst-address': KeyInfo(default=True),
                'dst-address-mask': KeyInfo(default=True),
                'dst-mac-address': KeyInfo(default=True),
                'dst-port': KeyInfo(default=True),
                'first-forwarded': KeyInfo(default=True),
                'gateway': KeyInfo(default=True),
                'icmp-code': KeyInfo(default=True),
                'icmp-type': KeyInfo(default=True),
                'igmp-type': KeyInfo(default=True),
                'in-interface': KeyInfo(default=True),
                'ip-header-length': KeyInfo(default=True),
                'ip-total-length': KeyInfo(default=True),
                'ipv6-flow-label': KeyInfo(default=True),
                'is-multicast': KeyInfo(default=True),
                'last-forwarded': KeyInfo(default=True),
                'nat-dst-address': KeyInfo(default=True),
                'nat-dst-port': KeyInfo(default=True),
                'nat-events': KeyInfo(default=False),
                'nat-src-address': KeyInfo(default=True),
                'nat-src-port': KeyInfo(default=True),
                'out-interface': KeyInfo(default=True),
                'packets': KeyInfo(default=True),
                'protocol': KeyInfo(default=True),
                'src-address': KeyInfo(default=True),
                'src-address-mask': KeyInfo(default=True),
                'src-mac-address': KeyInfo(default=True),
                'src-port': KeyInfo(default=True),
                'sys-init-time': KeyInfo(default=True),
                'tcp-ack-num': KeyInfo(default=True),
                'tcp-flags': KeyInfo(default=True),
                'tcp-seq-num': KeyInfo(default=True),
                'tcp-window-size': KeyInfo(default=True),
                'tos': KeyInfo(default=True),
                'ttl': KeyInfo(default=True),
                'udp-length': KeyInfo(default=True),
            },
        ),
    ),

    ('ip', 'traffic-flow', 'target'): APIData(
        unversioned=VersionedAPIData(
            fully_understood=True,
            versioned_fields=[
                ([('7.15', '<')], 'address', KeyInfo()),
                # ([('7.15', '>=')], 'copy-from', KeyInfo(write_only=True)),
            ],
            fields={
                'disabled': KeyInfo(default=False),
                'dst-address': KeyInfo(),
                'port': KeyInfo(default=2055),
                'src-address': KeyInfo(),
                'v9-template-refresh': KeyInfo(default=20),
                'v9-template-timeout': KeyInfo(),
                'version': KeyInfo(),
            },
        ),
    ),

    ('ip', 'upnp'): APIData(
        unversioned=VersionedAPIData(
            fixed_entries=True,
            single_value=True,
            fully_understood=True,
            fields={
                'allow-disable-external-interface': KeyInfo(default=False),
                'enabled': KeyInfo(default=False),
                'show-dummy-rule': KeyInfo(default=True),
            },
        ),
    ),

    ('ip', 'upnp', 'interfaces'): APIData(
        unversioned=VersionedAPIData(
            primary_keys=('interface', 'type'),
            fully_understood=True,
            # versioned_fields=[
            #     ([('7.15', '>=')], 'copy-from', KeyInfo(write_only=True)),
            # ],
            fields={
                'disabled': KeyInfo(default=False),
                'forced-ip': KeyInfo(can_disable=True),
                'interface': KeyInfo(),
                'type': KeyInfo(),
            },
        ),
    ),

    ('ip', 'vrf'): APIData(
        versioned=[
            ('7', '>=', VersionedAPIData(
                primary_keys=('name',),
                fully_understood=True,
                # versioned_fields=[
                #     ([('7.15', '>=')], 'copy-from', KeyInfo(write_only=True)),
                #     ([('7.15', '>=')], 'place-before', KeyInfo(write_only=True)),
                # ],
                fields={
                    'comment': KeyInfo(can_disable=True, remove_value=''),
                    'disabled': KeyInfo(default=False),
                    'interfaces': KeyInfo(),
                    'name': KeyInfo(),
                },
            )),
        ],
    ),

    ('ipv6', 'address'): APIData(
        unversioned=VersionedAPIData(
            fully_understood=True,
            versioned_fields=[
                ([('7.18', '>=')], 'auto-link-local', KeyInfo()),
                # ([('7.15', '>=')], 'copy-from', KeyInfo(write_only=True)),
            ],
            fields={
                'address': KeyInfo(),
                'advertise': KeyInfo(default=True),
                'comment': KeyInfo(can_disable=True, remove_value=''),
                'disabled': KeyInfo(default=False),
                'eui-64': KeyInfo(default=False),
                'from-pool': KeyInfo(default=''),
                'interface': KeyInfo(required=True),
                'no-dad': KeyInfo(default=False),
            },
        ),
    ),

    ('ipv6', 'dhcp-client'): APIData(
        unversioned=VersionedAPIData(
            primary_keys=('interface', 'request'),
            fully_understood=True,
            versioned_fields=[
                ([('7.20', '>=')], 'accept-prefix-without-address', KeyInfo()),
                ([('7.17', '>=')], 'allow-reconfigure', KeyInfo()),
                ([('7.19', '>=')], 'check-gateway', KeyInfo()),
                # ([('7.15', '>=')], 'copy-from', KeyInfo(write_only=True)),
                ([('7.15', '>=')], 'custom-duid', KeyInfo(default='')),
                ([('7.20', '>=')], 'custom-iana-id', KeyInfo()),
                ([('7.20', '>=')], 'custom-iapd-id', KeyInfo()),
                ([('7.19', '>=')], 'default-route-tables', KeyInfo()),
                ([('7.17', '>=')], 'prefix-address-lists', KeyInfo()),
                ([('7.15', '>=')], 'rapid-commit', KeyInfo()),
                ([('7.15', '>=')], 'script', KeyInfo(default='')),
                ([('7.15', '>=')], 'use-interface-duid', KeyInfo(default=False)),
                ([('7.15', '>=')], 'validate-server-duid', KeyInfo(default=True)),
            ],
            fields={
                'add-default-route': KeyInfo(default=False),
                'comment': KeyInfo(can_disable=True, remove_value=''),
                'default-route-distance': KeyInfo(default=1),
                'dhcp-options': KeyInfo(default=''),
                'disabled': KeyInfo(default=False),
                'interface': KeyInfo(),
                'pool-name': KeyInfo(required=True),
                'pool-prefix-length': KeyInfo(default=64),
                'prefix-hint': KeyInfo(default='::/0'),
                'request': KeyInfo(),
                'use-peer-dns': KeyInfo(default=True),
            },
        ),
    ),

    ('ipv6', 'dhcp-client', 'option'): APIData(
        versioned=[
            ('7.15', '>=', VersionedAPIData(
                fully_understood=True,
                versioned_fields=[
                    ([('7.16', '>=')], 'comment', KeyInfo()),
                ],
                fields={
                    'code': KeyInfo(),
                    # 'copy-from': KeyInfo(write_only=True),
                    'name': KeyInfo(),
                    'value': KeyInfo(),
                },
            )),
        ],
    ),

    ('ipv6', 'dhcp-relay'): APIData(
        versioned=[
            ('7.15', '>=', VersionedAPIData(
                fully_understood=True,
                versioned_fields=[
                    ([('7.21', '>=')], 'dhcp-options', KeyInfo()),
                    ([('7.18', '>=')], 'store-relayed-bindings', KeyInfo()),
                ],
                fields={
                    'comment': KeyInfo(),
                    # 'copy-from': KeyInfo(write_only=True),
                    'delay-threshold': KeyInfo(),
                    'dhcp-server': KeyInfo(),
                    'disabled': KeyInfo(),
                    'interface': KeyInfo(),
                    'link-address': KeyInfo(),
                    'name': KeyInfo(),
                },
            )),
        ],
    ),

    ('ipv6', 'dhcp-relay', 'option'): APIData(
        versioned=[
            ('7.21', '>=', VersionedAPIData(
                fully_understood=True,
                fields={
                    'code': KeyInfo(),
                    'comment': KeyInfo(),
                    # 'copy-from': KeyInfo(write_only=True),
                    'name': KeyInfo(),
                    'only-if-mac-available': KeyInfo(),
                    'value': KeyInfo(),
                },
            )),
        ],
    ),

    ('ipv6', 'dhcp-server'): APIData(
        unversioned=VersionedAPIData(
            primary_keys=('name',),
            fully_understood=True,
            versioned_fields=[
                ([('7.17', '>=')], 'address-lists', KeyInfo(default='')),
                # ([('7.15', '>=')], 'copy-from', KeyInfo(write_only=True)),
                ([('7.20', '>=')], 'ignore-ia-na-bindings', KeyInfo(default=False)),
                ([('7.17', '>=')], 'prefix-pool', KeyInfo(default='static-only')),
                ([('7.17', '>=')], 'use-reconfigure', KeyInfo(default=False)),
            ],
            fields={
                'address-pool': KeyInfo(default='static-only'),
                'allow-dual-stack-queue': KeyInfo(can_disable=True, remove_value=True),
                'binding-script': KeyInfo(can_disable=True, remove_value=''),
                'comment': KeyInfo(can_disable=True, remove_value=''),
                'dhcp-option': KeyInfo(default=''),
                'disabled': KeyInfo(default=False),
                'insert-queue-before': KeyInfo(can_disable=True, remove_value='first'),
                'interface': KeyInfo(required=True),
                'lease-time': KeyInfo(default='3d'),
                'name': KeyInfo(required=True),
                'parent-queue': KeyInfo(can_disable=True, remove_value='none'),
                'preference': KeyInfo(default=255),
                'rapid-commit': KeyInfo(default=True),
                'route-distance': KeyInfo(default=1),
                'use-radius': KeyInfo(default=False),
            },
        ),
    ),

    ('ipv6', 'dhcp-server', 'binding'): APIData(
        versioned=[
            ('7.15', '>=', VersionedAPIData(
                fully_understood=True,
                versioned_fields=[
                    ([('7.17', '>=')], 'ia-type', KeyInfo()),
                    ([('7.16', '>=')], 'parent-queue', KeyInfo()),
                ],
                fields={
                    'address': KeyInfo(),
                    'address-lists': KeyInfo(),
                    'allow-dual-stack-queue': KeyInfo(),
                    'comment': KeyInfo(),
                    # 'copy-from': KeyInfo(write_only=True),
                    'dhcp-option': KeyInfo(),
                    'disabled': KeyInfo(),
                    'duid': KeyInfo(),
                    'iaid': KeyInfo(),
                    'insert-queue-before': KeyInfo(),
                    'life-time': KeyInfo(),
                    'prefix-pool': KeyInfo(),
                    'queue-type': KeyInfo(),
                    'rate-limit': KeyInfo(),
                    'server': KeyInfo(),
                },
            )),
        ],
    ),

    ('ipv6', 'dhcp-server', 'option'): APIData(
        unversioned=VersionedAPIData(
            primary_keys=('name',),
            fully_understood=True,
            versioned_fields=[
                ([('7.16', '>=')], 'comment', KeyInfo()),
                # ([('7.15', '>=')], 'copy-from', KeyInfo(write_only=True)),
            ],
            fields={
                'code': KeyInfo(required=True),
                'name': KeyInfo(),
                'value': KeyInfo(default=''),
            },
        ),
    ),

    ('ipv6', 'dhcp-server', 'option', 'sets'): APIData(
        versioned=[
            ('7.15', '>=', VersionedAPIData(
                fully_understood=True,
                fields={
                    # 'copy-from': KeyInfo(write_only=True),
                    'name': KeyInfo(),
                    'options': KeyInfo(),
                },
            )),
        ],
    ),

    ('ipv6', 'firewall', 'address-list'): APIData(
        unversioned=VersionedAPIData(
            primary_keys=('address', 'list'),
            fully_understood=True,
            versioned_fields=[
                # ([('7.15', '>=')], 'copy-from', KeyInfo(write_only=True)),
                ([('7.15', '>=')], 'dynamic', KeyInfo()),
                ([('7.15', '>=')], 'timeout', KeyInfo()),
            ],
            fields={
                'address': KeyInfo(),
                'comment': KeyInfo(can_disable=True, remove_value=''),
                'disabled': KeyInfo(default=False),
                'list': KeyInfo(),
            },
        ),
    ),

    ('ipv6', 'firewall', 'filter'): APIData(
        unversioned=VersionedAPIData(
            stratify_keys=('chain',),
            fully_understood=True,
            versioned_fields=[
                ([('7.15', '>=')], 'connection-nat-state', KeyInfo()),
                # ([('7.15', '>=')], 'copy-from', KeyInfo(write_only=True)),
                # ([('7.15', '>=')], 'place-before', KeyInfo(write_only=True)),
                ([('7.15', '>=')], 'routing-mark', KeyInfo()),
                ([('7.15', '>=')], 'tls-host', KeyInfo()),
                ([('7.21', '>=')], 'tos', KeyInfo()),
            ],
            fields={
                'action': KeyInfo(),
                'address-list': KeyInfo(can_disable=True),
                'address-list-timeout': KeyInfo(can_disable=True),
                'chain': KeyInfo(),
                'comment': KeyInfo(can_disable=True, remove_value=''),
                'connection-bytes': KeyInfo(can_disable=True),
                'connection-limit': KeyInfo(can_disable=True),
                'connection-mark': KeyInfo(can_disable=True),
                'connection-rate': KeyInfo(can_disable=True),
                'connection-state': KeyInfo(can_disable=True),
                'connection-type': KeyInfo(can_disable=True),
                'content': KeyInfo(can_disable=True),
                'disabled': KeyInfo(default=False),
                'dscp': KeyInfo(can_disable=True),
                'dst-address': KeyInfo(can_disable=True),
                'dst-address-list': KeyInfo(can_disable=True),
                'dst-address-type': KeyInfo(can_disable=True),
                'dst-limit': KeyInfo(can_disable=True),
                'dst-port': KeyInfo(can_disable=True),
                'headers': KeyInfo(can_disable=True),
                'hop-limit': KeyInfo(can_disable=True),
                'icmp-options': KeyInfo(can_disable=True),
                'in-bridge-port': KeyInfo(can_disable=True),
                'in-bridge-port-list': KeyInfo(can_disable=True),
                'in-interface': KeyInfo(can_disable=True),
                'in-interface-list': KeyInfo(can_disable=True),
                'ingress-priority': KeyInfo(can_disable=True),
                'ipsec-policy': KeyInfo(can_disable=True),
                'jump-target': KeyInfo(can_disable=True),
                'limit': KeyInfo(can_disable=True),
                'log': KeyInfo(),
                'log-prefix': KeyInfo(),
                'nth': KeyInfo(can_disable=True),
                'out-bridge-port': KeyInfo(can_disable=True),
                'out-bridge-port-list': KeyInfo(can_disable=True),
                'out-interface': KeyInfo(can_disable=True),
                'out-interface-list': KeyInfo(can_disable=True),
                'packet-mark': KeyInfo(can_disable=True),
                'packet-size': KeyInfo(can_disable=True),
                'per-connection-classifier': KeyInfo(can_disable=True),
                'port': KeyInfo(can_disable=True),
                'priority': KeyInfo(can_disable=True),
                'protocol': KeyInfo(can_disable=True),
                'random': KeyInfo(can_disable=True),
                'reject-with': KeyInfo(),
                'src-address': KeyInfo(can_disable=True),
                'src-address-list': KeyInfo(can_disable=True),
                'src-address-type': KeyInfo(can_disable=True),
                'src-mac-address': KeyInfo(can_disable=True),
                'src-port': KeyInfo(can_disable=True),
                'tcp-flags': KeyInfo(can_disable=True),
                'tcp-mss': KeyInfo(can_disable=True),
                'time': KeyInfo(can_disable=True),
            },
        ),
    ),

    ('ipv6', 'firewall', 'mangle'): APIData(
        unversioned=VersionedAPIData(
            stratify_keys=('chain',),
            fully_understood=True,
            versioned_fields=[
                ([('7.15', '>=')], 'connection-nat-state', KeyInfo()),
                # ([('7.15', '>=')], 'copy-from', KeyInfo(write_only=True)),
                # ([('7.15', '>=')], 'place-before', KeyInfo(write_only=True)),
                ([('7.21', '>=')], 'tos', KeyInfo()),
            ],
            fields={
                'action': KeyInfo(),
                'address-list': KeyInfo(),
                'address-list-timeout': KeyInfo(),
                'chain': KeyInfo(),
                'comment': KeyInfo(can_disable=True, remove_value=''),
                'connection-bytes': KeyInfo(can_disable=True),
                'connection-limit': KeyInfo(can_disable=True),
                'connection-mark': KeyInfo(can_disable=True),
                'connection-rate': KeyInfo(can_disable=True),
                'connection-state': KeyInfo(can_disable=True),
                'connection-type': KeyInfo(can_disable=True),
                'content': KeyInfo(can_disable=True),
                'disabled': KeyInfo(default=False),
                'dscp': KeyInfo(can_disable=True),
                'dst-address': KeyInfo(can_disable=True),
                'dst-address-list': KeyInfo(can_disable=True),
                'dst-address-type': KeyInfo(can_disable=True),
                'dst-limit': KeyInfo(can_disable=True),
                'dst-port': KeyInfo(can_disable=True),
                'dst-prefix': KeyInfo(),
                'headers': KeyInfo(can_disable=True),
                'hop-limit': KeyInfo(can_disable=True),
                'icmp-options': KeyInfo(can_disable=True),
                'in-bridge-port': KeyInfo(can_disable=True),
                'in-bridge-port-list': KeyInfo(can_disable=True),
                'in-interface': KeyInfo(can_disable=True),
                'in-interface-list': KeyInfo(can_disable=True),
                'ingress-priority': KeyInfo(can_disable=True),
                'ipsec-policy': KeyInfo(can_disable=True),
                'jump-target': KeyInfo(),
                'limit': KeyInfo(can_disable=True),
                'log': KeyInfo(),
                'log-prefix': KeyInfo(),
                'new-connection-mark': KeyInfo(),
                'new-dscp': KeyInfo(),
                'new-hop-limit': KeyInfo(),
                'new-mss': KeyInfo(),
                'new-packet-mark': KeyInfo(),
                'new-priority': KeyInfo(can_disable=True),
                'new-routing-mark': KeyInfo(),
                'nth': KeyInfo(can_disable=True),
                'out-bridge-port': KeyInfo(can_disable=True),
                'out-bridge-port-list': KeyInfo(can_disable=True),
                'out-interface': KeyInfo(can_disable=True),
                'out-interface-list': KeyInfo(can_disable=True),
                'packet-mark': KeyInfo(can_disable=True),
                'packet-size': KeyInfo(can_disable=True),
                'passthrough': KeyInfo(),
                'per-connection-classifier': KeyInfo(can_disable=True),
                'port': KeyInfo(can_disable=True),
                'priority': KeyInfo(can_disable=True),
                'protocol': KeyInfo(can_disable=True),
                'random': KeyInfo(can_disable=True),
                'routing-mark': KeyInfo(can_disable=True),
                'sniff-id': KeyInfo(),
                'sniff-target': KeyInfo(),
                'sniff-target-port': KeyInfo(),
                'src-address': KeyInfo(can_disable=True),
                'src-address-list': KeyInfo(can_disable=True),
                'src-address-type': KeyInfo(can_disable=True),
                'src-mac-address': KeyInfo(can_disable=True),
                'src-port': KeyInfo(can_disable=True),
                'src-prefix': KeyInfo(),
                'tcp-flags': KeyInfo(can_disable=True),
                'tcp-mss': KeyInfo(can_disable=True),
                'time': KeyInfo(can_disable=True),
                'tls-host': KeyInfo(can_disable=True),
            },
        ),
    ),

    ('ipv6', 'firewall', 'nat'): APIData(
        unversioned=VersionedAPIData(
            stratify_keys=('chain',),
            fully_understood=True,
            versioned_fields=[
                # ([('7.15', '>=')], 'copy-from', KeyInfo(write_only=True)),
                ([('7.15', '>=')], 'headers', KeyInfo()),
                ([('7.15', '>=')], 'hop-limit', KeyInfo()),
                ([('7.15', '<')], 'layer7-protocol', KeyInfo(can_disable=True)),
                ([('7.15', '>=')], 'nth', KeyInfo()),
                # ([('7.15', '>=')], 'place-before', KeyInfo(write_only=True)),
                ([('7.16', '<')], 'tls-host', KeyInfo(can_disable=True)),
                ([('7.15', '>=')], 'to-address', KeyInfo()),
                ([('7.15', '<')], 'to-addresses', KeyInfo(can_disable=True)),
                ([('7.21', '>=')], 'tos', KeyInfo()),
            ],
            fields={
                'action': KeyInfo(),
                'address-list': KeyInfo(),
                'address-list-timeout': KeyInfo(),
                'chain': KeyInfo(),
                'comment': KeyInfo(can_disable=True, remove_value=''),
                'connection-bytes': KeyInfo(can_disable=True),
                'connection-limit': KeyInfo(can_disable=True),
                'connection-mark': KeyInfo(can_disable=True),
                'connection-rate': KeyInfo(can_disable=True),
                'connection-state': KeyInfo(can_disable=True),
                'connection-type': KeyInfo(can_disable=True),
                'content': KeyInfo(can_disable=True),
                'disabled': KeyInfo(default=False),
                'dscp': KeyInfo(can_disable=True),
                'dst-address': KeyInfo(can_disable=True),
                'dst-address-list': KeyInfo(can_disable=True),
                'dst-address-type': KeyInfo(can_disable=True),
                'dst-limit': KeyInfo(can_disable=True),
                'dst-port': KeyInfo(can_disable=True),
                'icmp-options': KeyInfo(can_disable=True),
                'in-bridge-port': KeyInfo(can_disable=True),
                'in-bridge-port-list': KeyInfo(can_disable=True),
                'in-interface': KeyInfo(can_disable=True),
                'in-interface-list': KeyInfo(can_disable=True),
                'ingress-priority': KeyInfo(can_disable=True),
                'ipsec-policy': KeyInfo(can_disable=True),
                'jump-target': KeyInfo(),
                'limit': KeyInfo(can_disable=True),
                'log': KeyInfo(),
                'log-prefix': KeyInfo(),
                'out-bridge-port': KeyInfo(can_disable=True),
                'out-bridge-port-list': KeyInfo(can_disable=True),
                'out-interface': KeyInfo(can_disable=True),
                'out-interface-list': KeyInfo(can_disable=True),
                'packet-mark': KeyInfo(can_disable=True),
                'packet-size': KeyInfo(can_disable=True),
                'per-connection-classifier': KeyInfo(can_disable=True),
                'port': KeyInfo(can_disable=True),
                'priority': KeyInfo(can_disable=True),
                'protocol': KeyInfo(can_disable=True),
                'random': KeyInfo(can_disable=True),
                'routing-mark': KeyInfo(can_disable=True),
                'src-address': KeyInfo(can_disable=True),
                'src-address-list': KeyInfo(can_disable=True),
                'src-address-type': KeyInfo(can_disable=True),
                'src-mac-address': KeyInfo(can_disable=True),
                'src-port': KeyInfo(can_disable=True),
                'tcp-flags': KeyInfo(can_disable=True),
                'tcp-mss': KeyInfo(can_disable=True),
                'time': KeyInfo(can_disable=True),
                'to-ports': KeyInfo(can_disable=True),
            },
        ),
    ),

    ('ipv6', 'firewall', 'raw'): APIData(
        unversioned=VersionedAPIData(
            stratify_keys=('chain',),
            fully_understood=True,
            versioned_fields=[
                # ([('7.15', '>=')], 'copy-from', KeyInfo(write_only=True)),
                # ([('7.15', '>=')], 'place-before', KeyInfo(write_only=True)),
                ([('7.21', '>=')], 'tos', KeyInfo()),
            ],
            fields={
                'action': KeyInfo(),
                'address-list': KeyInfo(),
                'address-list-timeout': KeyInfo(),
                'chain': KeyInfo(),
                'comment': KeyInfo(can_disable=True, remove_value=''),
                'content': KeyInfo(can_disable=True),
                'disabled': KeyInfo(default=False),
                'dscp': KeyInfo(can_disable=True),
                'dst-address': KeyInfo(can_disable=True),
                'dst-address-list': KeyInfo(can_disable=True),
                'dst-address-type': KeyInfo(can_disable=True),
                'dst-limit': KeyInfo(can_disable=True),
                'dst-port': KeyInfo(can_disable=True),
                'headers': KeyInfo(can_disable=True),
                'hop-limit': KeyInfo(can_disable=True),
                'icmp-options': KeyInfo(can_disable=True),
                'in-bridge-port': KeyInfo(can_disable=True),
                'in-bridge-port-list': KeyInfo(can_disable=True),
                'in-interface': KeyInfo(can_disable=True),
                'in-interface-list': KeyInfo(can_disable=True),
                'ingress-priority': KeyInfo(can_disable=True),
                'ipsec-policy': KeyInfo(can_disable=True),
                'jump-target': KeyInfo(),
                'limit': KeyInfo(can_disable=True),
                'log': KeyInfo(),
                'log-prefix': KeyInfo(),
                'nth': KeyInfo(can_disable=True),
                'out-bridge-port': KeyInfo(can_disable=True),
                'out-bridge-port-list': KeyInfo(can_disable=True),
                'out-interface': KeyInfo(can_disable=True),
                'out-interface-list': KeyInfo(can_disable=True),
                'packet-mark': KeyInfo(can_disable=True),
                'packet-size': KeyInfo(can_disable=True),
                'per-connection-classifier': KeyInfo(can_disable=True),
                'port': KeyInfo(can_disable=True),
                'priority': KeyInfo(can_disable=True),
                'protocol': KeyInfo(can_disable=True),
                'random': KeyInfo(can_disable=True),
                'src-address': KeyInfo(can_disable=True),
                'src-address-list': KeyInfo(can_disable=True),
                'src-address-type': KeyInfo(can_disable=True),
                'src-mac-address': KeyInfo(can_disable=True),
                'src-port': KeyInfo(can_disable=True),
                'tcp-flags': KeyInfo(can_disable=True),
                'tcp-mss': KeyInfo(can_disable=True),
                'time': KeyInfo(can_disable=True),
                'tls-host': KeyInfo(can_disable=True),
            },
        ),
    ),

    ('ipv6', 'nd'): APIData(
        unversioned=VersionedAPIData(
            primary_keys=('interface',),
            fully_understood=True,
            versioned_fields=[
                ([('7.15', '>=')], 'comment', KeyInfo()),
                # ([('7.15', '>=')], 'copy-from', KeyInfo(write_only=True)),
                ([('7.15', '>=')], 'pref64', KeyInfo()),
            ],
            fields={
                'advertise-dns': KeyInfo(default=True),
                'advertise-mac-address': KeyInfo(default=True),
                'disabled': KeyInfo(default=False),
                'dns': KeyInfo(default=''),
                'hop-limit': KeyInfo(default='unspecified'),
                'interface': KeyInfo(),
                'managed-address-configuration': KeyInfo(default=False),
                'mtu': KeyInfo(default='unspecified'),
                'other-configuration': KeyInfo(default=False),
                'ra-delay': KeyInfo(default='3s'),
                'ra-interval': KeyInfo(default='3m20s-10m'),
                'ra-lifetime': KeyInfo(default='30m'),
                'ra-preference': KeyInfo(default='medium'),
                'reachable-time': KeyInfo(default='unspecified'),
                'retransmit-interval': KeyInfo(default='unspecified'),
            },
        ),
    ),

    ('ipv6', 'nd', 'prefix'): APIData(
        unversioned=VersionedAPIData(
            fully_understood=True,
            # versioned_fields=[
            #     ([('7.15', '>=')], 'copy-from', KeyInfo(write_only=True)),
            # ],
            fields={
                '6to4-interface': KeyInfo(default='none'),
                'autonomous': KeyInfo(),
                'comment': KeyInfo(can_disable=True, remove_value=''),
                'disabled': KeyInfo(default=False),
                'interface': KeyInfo(required=True),
                'on-link': KeyInfo(default=True),
                'preferred-lifetime': KeyInfo(),
                'prefix': KeyInfo(),
                'valid-lifetime': KeyInfo(),
            },
        ),
    ),

    ('ipv6', 'nd', 'prefix', 'default'): APIData(
        unversioned=VersionedAPIData(
            fixed_entries=True,
            single_value=True,
            fully_understood=True,
            fields={
                'autonomous': KeyInfo(default=True),
                'preferred-lifetime': KeyInfo(default='1w'),
                'valid-lifetime': KeyInfo(default='4w2d'),
            },
        ),
    ),

    ('ipv6', 'nd', 'proxy'): APIData(
        versioned=[
            ('7.20', '>=', VersionedAPIData(
                fully_understood=True,
                fields={
                    'address': KeyInfo(),
                    'comment': KeyInfo(),
                    # 'copy-from': KeyInfo(write_only=True),
                    'disabled': KeyInfo(),
                    'interface': KeyInfo(),
                },
            )),
        ],
    ),

    ('ipv6', 'neighbor'): APIData(
        versioned=[
            ('7.18', '>=', VersionedAPIData(
                fully_understood=True,
                fields={
                    'address': KeyInfo(),
                    'comment': KeyInfo(),
                    # 'copy-from': KeyInfo(write_only=True),
                    'disabled': KeyInfo(),
                    'interface': KeyInfo(),
                    'mac-address': KeyInfo(),
                },
            )),
        ],
    ),

    ('ipv6', 'pool'): APIData(
        versioned=[
            ('7.15', '>=', VersionedAPIData(
                fully_understood=True,
                fields={
                    'comment': KeyInfo(),
                    # 'copy-from': KeyInfo(write_only=True),
                    'name': KeyInfo(),
                    'prefix': KeyInfo(),
                    'prefix-length': KeyInfo(),
                },
            )),
        ],
    ),

    ('ipv6', 'route'): APIData(
        unversioned=VersionedAPIData(
            fully_understood=True,
            versioned_fields=[
                ([('7.15', '<')], 'bgp-as-path', KeyInfo(can_disable=True)),
                ([('7.15', '<')], 'bgp-atomic-aggregate', KeyInfo(can_disable=True)),
                ([('7.15', '<')], 'bgp-communities', KeyInfo(can_disable=True)),
                ([('7.15', '<')], 'bgp-local-pref', KeyInfo(can_disable=True)),
                ([('7.15', '<')], 'bgp-med', KeyInfo(can_disable=True)),
                ([('7.15', '<')], 'bgp-origin', KeyInfo(can_disable=True)),
                ([('7.15', '<')], 'bgp-prepend', KeyInfo(can_disable=True)),
                # ([('7.15', '>=')], 'copy-from', KeyInfo(write_only=True)),
                ([('7.20', '>=')], 'pref-src', KeyInfo()),
                ([('7.15', '<')], 'route-tag', KeyInfo(can_disable=True)),
                ([('7.15', '>=')], 'suppress-hw-offload', KeyInfo()),
                ([('7.15', '<')], 'type', KeyInfo(can_disable=True, remove_value='unicast')),
            ],
            fields={
                'blackhole': KeyInfo(can_disable=True),
                'check-gateway': KeyInfo(can_disable=True),
                'comment': KeyInfo(can_disable=True, remove_value=''),
                'disabled': KeyInfo(default=False),
                'distance': KeyInfo(default=1),
                'dst-address': KeyInfo(),
                'gateway': KeyInfo(),
                'routing-table': KeyInfo(default='main'),
                'scope': KeyInfo(default=30),
                'target-scope': KeyInfo(default=10),
                'vrf-interface': KeyInfo(can_disable=True),
            },
        ),
    ),

    ('ipv6', 'settings'): APIData(
        unversioned=VersionedAPIData(
            fixed_entries=True,
            single_value=True,
            fully_understood=True,
            versioned_fields=[
                ([('7.21', '>=')], 'accept-router-advertisements-on', KeyInfo()),
                ([('7.18', '>=')], 'allow-fast-path', KeyInfo(default=True)),
                ([('7.17', '>=')], 'disable-link-local-address', KeyInfo(default=False)),
                ([('7.18', '<')], 'max-neighbor-entries', KeyInfo(default=8192)),
                ([('7.18', '>=')], 'max-neighbor-entries', KeyInfo()),
                ([('7.18', '>=')], 'min-neighbor-entries', KeyInfo()),
                ([('7.16', '>=')], 'multipath-hash-policy', KeyInfo(default='l3')),
                ([('7.18', '>=')], 'soft-max-neighbor-entries', KeyInfo()),
                ([('7.17', '>=')], 'stale-neighbor-detect-interval', KeyInfo()),
                ([('7.17', '>=')], 'stale-neighbor-timeout', KeyInfo(default=60)),
            ],
            fields={
                'accept-redirects': KeyInfo(default='yes-if-forwarding-disabled'),
                'accept-router-advertisements': KeyInfo(default='yes-if-forwarding-disabled'),
                'disable-ipv6': KeyInfo(default=False),
                'forward': KeyInfo(default=True),
            },
        ),
    ),

    ('lcd',): APIData(
        versioned=[
            ('7.15', '>=', VersionedAPIData(
                fixed_entries=True,
                single_value=True,
                fully_understood=True,
                fields={
                    'backlight-timeout': KeyInfo(),
                    'color-scheme': KeyInfo(),
                    'default-screen': KeyInfo(),
                    'enabled': KeyInfo(),
                    'flip-screen': KeyInfo(),
                    'read-only-mode': KeyInfo(),
                    'time-interval': KeyInfo(),
                    'touch-screen': KeyInfo(),
                },
            )),
        ],
    ),

    ('lcd', 'interface'): APIData(
        versioned=[
            ('7.15', '>=', VersionedAPIData(
                fully_understood=True,
                fields={
                    # 'copy-from': KeyInfo(write_only=True),
                    'disabled': KeyInfo(),
                    'interface': KeyInfo(),
                    'max-speed': KeyInfo(),
                    'timeout': KeyInfo(),
                },
            )),
        ],
    ),

    ('lcd', 'interface', 'pages'): APIData(
        versioned=[
            ('7.15', '>=', VersionedAPIData(
                fully_understood=True,
                fields={
                    # 'copy-from': KeyInfo(write_only=True),
                    'interfaces': KeyInfo(),
                    # 'place-before': KeyInfo(write_only=True),
                },
            )),
        ],
    ),

    ('lcd', 'pin'): APIData(
        versioned=[
            ('7.15', '>=', VersionedAPIData(
                fixed_entries=True,
                single_value=True,
                fully_understood=True,
                fields={
                    'hide-pin-number': KeyInfo(),
                    'pin-number': KeyInfo(),
                },
            )),
        ],
    ),

    ('lcd', 'screen'): APIData(
        versioned=[
            ('7.15', '>=', VersionedAPIData(
                fully_understood=True,
                has_identifier=True,
                # fixed_entries=True,
                # primary_keys=('numbers',),
                fields={
                    'disabled': KeyInfo(),
                    'numbers': KeyInfo(),
                    'timeout': KeyInfo(),
                },
            )),
        ],
    ),

    ('lora',): APIData(
        versioned=[
            ('7.15', '>=', VersionedAPIData(
                fully_understood=True,
                has_identifier=True,
                # fixed_entries=True,
                # primary_keys=('numbers',),
                versioned_fields=[
                    ([('7.16', '>=')], 'alt', KeyInfo()),
                    ([('7.16', '>=')], 'lat', KeyInfo()),
                    ([('7.16', '>=')], 'long', KeyInfo()),
                ],
                fields={
                    'antenna': KeyInfo(),
                    'antenna-gain': KeyInfo(),
                    'channel-plan': KeyInfo(),
                    'disabled': KeyInfo(),
                    'forward': KeyInfo(),
                    'gateway-id': KeyInfo(),
                    'lbt-enabled': KeyInfo(),
                    'listen-time': KeyInfo(),
                    'name': KeyInfo(),
                    'network': KeyInfo(),
                    'numbers': KeyInfo(),
                    'rssi-threshold': KeyInfo(),
                    'servers': KeyInfo(),
                    'spoof-gps': KeyInfo(),
                    'src-address': KeyInfo(),
                },
            )),
        ],
    ),

    ('lora', 'channels'): APIData(
        versioned=[
            ('7.15', '>=', VersionedAPIData(
                fully_understood=True,
                has_identifier=True,
                # fixed_entries=True,
                # primary_keys=('numbers',),
                fields={
                    'bandwidth': KeyInfo(),
                    'datarate': KeyInfo(),
                    'disabled': KeyInfo(),
                    'freq-off': KeyInfo(),
                    'numbers': KeyInfo(),
                    'radio': KeyInfo(),
                    'spread-factor': KeyInfo(),
                },
            )),
        ],
    ),

    ('lora', 'joineui'): APIData(
        versioned=[
            ('7.15', '>=', VersionedAPIData(
                fully_understood=True,
                versioned_fields=[
                    ([('7.16', '>=')], 'logging', KeyInfo()),
                    ([('7.19', '>=')], 'type', KeyInfo()),
                ],
                fields={
                    # 'copy-from': KeyInfo(write_only=True),
                    'joineuis': KeyInfo(),
                    'name': KeyInfo(),
                },
            )),
        ],
    ),

    ('lora', 'netid'): APIData(
        versioned=[
            ('7.15', '>=', VersionedAPIData(
                fully_understood=True,
                versioned_fields=[
                    ([('7.16', '>=')], 'logging', KeyInfo()),
                    ([('7.19', '>=')], 'type', KeyInfo()),
                ],
                fields={
                    # 'copy-from': KeyInfo(write_only=True),
                    'name': KeyInfo(),
                    'netids': KeyInfo(),
                },
            )),
        ],
    ),

    ('lora', 'radios'): APIData(
        versioned=[
            ('7.15', '>=', VersionedAPIData(
                fully_understood=True,
                has_identifier=True,
                # fixed_entries=True,
                # primary_keys=('numbers',),
                fields={
                    'center-freq': KeyInfo(),
                    'disabled': KeyInfo(),
                    'numbers': KeyInfo(),
                    'rssi-off': KeyInfo(),
                    'tx-enabled': KeyInfo(),
                    'tx-freq-max': KeyInfo(),
                    'tx-freq-min': KeyInfo(),
                },
            )),
        ],
    ),

    ('lora', 'servers'): APIData(
        versioned=[
            ('7.15', '>=', VersionedAPIData(
                fully_understood=True,
                fields={
                    'address': KeyInfo(),
                    'certificate': KeyInfo(),
                    # 'copy-from': KeyInfo(write_only=True),
                    'down-port': KeyInfo(),
                    'interval': KeyInfo(),
                    'joineui': KeyInfo(),
                    'key': KeyInfo(),
                    'name': KeyInfo(),
                    'netid': KeyInfo(),
                    'port': KeyInfo(),
                    'protocol': KeyInfo(),
                    'ssl': KeyInfo(),
                    'up-port': KeyInfo(),
                },
            )),
        ],
    ),

    ('lora', 'traffic', 'options'): APIData(
        versioned=[
            ('7.17', '>=', VersionedAPIData(
                fixed_entries=True,
                single_value=True,
                fully_understood=True,
                versioned_fields=[
                    ([('7.19', '>=')], 'pckt-limit', KeyInfo()),
                ],
                fields={
                    'crc-errors': KeyInfo(),
                },
            )),
        ],
    ),

    ('mpls',): APIData(
        versioned=[
            ('7.15', '<', VersionedAPIData(
                single_value=True,
                fully_understood=True,
                fields={
                    'allow-fast-path': KeyInfo(default=True),
                    'dynamic-label-range': KeyInfo(default='16-1048575'),
                    'propagate-ttl': KeyInfo(default=True),
                },
            )),
            ('7.15', '>=', 'Not supported anymore in version 7.15'),
        ],
    ),

    ('mpls', 'interface'): APIData(
        unversioned=VersionedAPIData(
            fully_understood=True,
            versioned_fields=[
                # ([('7.15', '>=')], 'copy-from', KeyInfo(write_only=True)),
                ([('7.15', '<')], 'info', KeyInfo(can_disable=True)),
                ([('7.15', '>=')], 'input', KeyInfo(can_disable=True)),
                # ([('7.15', '>=')], 'place-before', KeyInfo(write_only=True)),
            ],
            fields={
                'comment': KeyInfo(can_disable=True, remove_value=''),
                'disabled': KeyInfo(default=False),
                'interface': KeyInfo(required=True),
                'mpls-mtu': KeyInfo(can_disable=True),
            },
        ),
    ),

    ('mpls', 'ldp'): APIData(
        versioned=[
            ('7.1', '>=', VersionedAPIData(
                primary_keys=('vrf',),
                fully_understood=True,
                # versioned_fields=[
                #     ([('7.15', '>=')], 'copy-from', KeyInfo(write_only=True)),
                # ],
                fields={
                    'afi': KeyInfo(can_disable=True),
                    'comment': KeyInfo(can_disable=True, remove_value=''),
                    'disabled': KeyInfo(default=False),
                    'distribute-for-default': KeyInfo(can_disable=True),
                    'hop-limit': KeyInfo(can_disable=True),
                    'loop-detect': KeyInfo(can_disable=True),
                    'lsr-id': KeyInfo(can_disable=True),
                    'path-vector-limit': KeyInfo(can_disable=True),
                    'preferred-afi': KeyInfo(can_disable=True),
                    'transport-addresses': KeyInfo(can_disable=True),
                    'use-explicit-null': KeyInfo(can_disable=True),
                    'vrf': KeyInfo(),
                },
            )),
            ('7.1', '<', VersionedAPIData(
                single_value=True,
                fully_understood=True,
                fields={
                    'distribute-for-default-route': KeyInfo(default=False),
                    'enabled': KeyInfo(default=False),
                    'hop-limit': KeyInfo(default=255),
                    'loop-detect': KeyInfo(default=False),
                    'lsr-id': KeyInfo(default='0.0.0.0'),
                    'path-vector-limit': KeyInfo(default=255),
                    'transport-address': KeyInfo(default='0.0.0.0'),
                    'use-explicit-null': KeyInfo(default=False),
                },
            )),
        ],
    ),

    ('mpls', 'ldp', 'accept-filter'): APIData(
        unversioned=VersionedAPIData(
            fully_understood=True,
            # versioned_fields=[
            #     ([('7.15', '>=')], 'copy-from', KeyInfo(write_only=True)),
            #     ([('7.15', '>=')], 'place-before', KeyInfo(write_only=True)),
            # ],
            fields={
                'accept': KeyInfo(can_disable=True),
                'comment': KeyInfo(can_disable=True, remove_value=''),
                'disabled': KeyInfo(default=False),
                'neighbor': KeyInfo(can_disable=True),
                'prefix': KeyInfo(can_disable=True),
                'vrf': KeyInfo(can_disable=True),
            },
        ),
    ),

    ('mpls', 'ldp', 'advertise-filter'): APIData(
        unversioned=VersionedAPIData(
            fully_understood=True,
            # versioned_fields=[
            #     ([('7.15', '>=')], 'copy-from', KeyInfo(write_only=True)),
            #     ([('7.15', '>=')], 'place-before', KeyInfo(write_only=True)),
            # ],
            fields={
                'advertise': KeyInfo(default=''),
                'comment': KeyInfo(can_disable=True, remove_value=''),
                'disabled': KeyInfo(default=False),
                'neighbor': KeyInfo(),
                'prefix': KeyInfo(),
                'vrf': KeyInfo(),
            },
        ),
    ),

    ('mpls', 'ldp', 'interface'): APIData(
        unversioned=VersionedAPIData(
            fully_understood=True,
            # versioned_fields=[
            #     ([('7.15', '>=')], 'copy-from', KeyInfo(write_only=True)),
            # ],
            fields={
                'accept-dynamic-neighbors': KeyInfo(can_disable=True),
                'afi': KeyInfo(can_disable=True),
                'comment': KeyInfo(can_disable=True, remove_value=''),
                'disabled': KeyInfo(default=False),
                'hello-interval': KeyInfo(can_disable=True),
                'hold-time': KeyInfo(can_disable=True),
                'interface': KeyInfo(required=True),
                'transport-addresses': KeyInfo(can_disable=True),
            },
        ),
    ),

    ('mpls', 'ldp', 'local-mapping'): APIData(
        versioned=[
            ('7.15', '>=', VersionedAPIData(
                fully_understood=True,
                fields={
                    'comment': KeyInfo(),
                    # 'copy-from': KeyInfo(write_only=True),
                    'disabled': KeyInfo(),
                    'dst-address': KeyInfo(can_disable=True),
                    'label': KeyInfo(),
                    'vrf': KeyInfo(can_disable=True),
                },
            )),
        ],
    ),

    ('mpls', 'ldp', 'neighbor'): APIData(
        versioned=[
            ('7.15', '>=', VersionedAPIData(
                fully_understood=True,
                fields={
                    'comment': KeyInfo(),
                    # 'copy-from': KeyInfo(write_only=True),
                    'disabled': KeyInfo(),
                    'send-targeted': KeyInfo(can_disable=True),
                    'transport': KeyInfo(),
                },
            )),
        ],
    ),

    ('mpls', 'ldp', 'remote-mapping'): APIData(
        versioned=[
            ('7.15', '>=', VersionedAPIData(
                fully_understood=True,
                fields={
                    'comment': KeyInfo(),
                    # 'copy-from': KeyInfo(write_only=True),
                    'disabled': KeyInfo(),
                    'dst-address': KeyInfo(),
                    'label': KeyInfo(),
                    'nexthop': KeyInfo(),
                    'vrf': KeyInfo(can_disable=True),
                },
            )),
        ],
    ),

    ('mpls', 'mangle'): APIData(
        versioned=[
            ('7.17', '>=', VersionedAPIData(
                fully_understood=True,
                fields={
                    'chain': KeyInfo(can_disable=True),
                    'comment': KeyInfo(),
                    # 'copy-from': KeyInfo(write_only=True),
                    'disabled': KeyInfo(),
                    'exp': KeyInfo(can_disable=True),
                    'set-exp': KeyInfo(can_disable=True),
                    'set-mark': KeyInfo(can_disable=True),
                },
            )),
        ],
    ),

    ('mpls', 'settings'): APIData(
        versioned=[
            ('7.15', '>=', VersionedAPIData(
                fixed_entries=True,
                single_value=True,
                fully_understood=True,
                fields={
                    'allow-fast-path': KeyInfo(),
                    'dynamic-label-range': KeyInfo(),
                    'propagate-ttl': KeyInfo(),
                },
            )),
        ],
    ),

    ('mpls', 'traffic-eng', 'interface'): APIData(
        versioned=[
            ('7.15', '>=', VersionedAPIData(
                fully_understood=True,
                fields={
                    'bandwidth': KeyInfo(can_disable=True),
                    'blockade-k-factor': KeyInfo(can_disable=True),
                    'comment': KeyInfo(),
                    # 'copy-from': KeyInfo(write_only=True),
                    'disabled': KeyInfo(),
                    'down-flood-thresholds': KeyInfo(can_disable=True),
                    'igp-flood-period': KeyInfo(can_disable=True),
                    'interface': KeyInfo(),
                    'k-factor': KeyInfo(can_disable=True),
                    'refresh-time': KeyInfo(can_disable=True),
                    'resource-class': KeyInfo(can_disable=True),
                    'te-metric': KeyInfo(can_disable=True),
                    'up-flood-thresholds': KeyInfo(can_disable=True),
                    'use-udp': KeyInfo(can_disable=True),
                },
            )),
        ],
    ),

    ('mpls', 'traffic-eng', 'path'): APIData(
        versioned=[
            ('7.15', '>=', VersionedAPIData(
                fully_understood=True,
                fields={
                    'affinity-exclude': KeyInfo(can_disable=True),
                    'affinity-include-all': KeyInfo(can_disable=True),
                    'affinity-include-any': KeyInfo(can_disable=True),
                    'comment': KeyInfo(),
                    # 'copy-from': KeyInfo(write_only=True),
                    'disabled': KeyInfo(),
                    'holding-priority': KeyInfo(can_disable=True),
                    'hops': KeyInfo(can_disable=True),
                    'name': KeyInfo(),
                    'record-route': KeyInfo(can_disable=True),
                    'reoptimize-interval': KeyInfo(can_disable=True),
                    'setup-priority': KeyInfo(can_disable=True),
                    'use-cspf': KeyInfo(can_disable=True),
                },
            )),
        ],
    ),

    ('mpls', 'traffic-eng', 'tunnel'): APIData(
        versioned=[
            ('7.15', '>=', VersionedAPIData(
                fully_understood=True,
                fields={
                    'affinity-exclude': KeyInfo(can_disable=True),
                    'affinity-include-all': KeyInfo(can_disable=True),
                    'affinity-include-any': KeyInfo(can_disable=True),
                    'auto-bandwidth-avg-interval': KeyInfo(can_disable=True),
                    'auto-bandwidth-range': KeyInfo(can_disable=True),
                    'auto-bandwidth-reserve': KeyInfo(can_disable=True),
                    'auto-bandwidth-update-interval': KeyInfo(can_disable=True),
                    'bandwidth': KeyInfo(can_disable=True),
                    'bandwidth-limit': KeyInfo(can_disable=True),
                    'comment': KeyInfo(),
                    # 'copy-from': KeyInfo(write_only=True),
                    'disabled': KeyInfo(),
                    'from-address': KeyInfo(can_disable=True),
                    'holding-priority': KeyInfo(can_disable=True),
                    'name': KeyInfo(),
                    'primary-path': KeyInfo(can_disable=True),
                    'primary-retry-interval': KeyInfo(can_disable=True),
                    'record-route': KeyInfo(can_disable=True),
                    'reoptimize-interval': KeyInfo(can_disable=True),
                    'secondary-paths': KeyInfo(can_disable=True),
                    'secondary-standby': KeyInfo(can_disable=True),
                    'setup-priority': KeyInfo(can_disable=True),
                    'to-address': KeyInfo(),
                    'vrf': KeyInfo(can_disable=True),
                },
            )),
        ],
    ),

    ('openflow',): APIData(
        versioned=[
            ('7.20', '>=', VersionedAPIData(
                fully_understood=True,
                fields={
                    'certificate': KeyInfo(can_disable=True),
                    'comment': KeyInfo(),
                    'controllers': KeyInfo(),
                    # 'copy-from': KeyInfo(write_only=True),
                    'datapath-id': KeyInfo(),
                    'disabled': KeyInfo(),
                    'isolate-controllers': KeyInfo(can_disable=True),
                    'name': KeyInfo(),
                    'passive-port': KeyInfo(),
                    'verify-peer': KeyInfo(can_disable=True),
                    'version': KeyInfo(),
                },
            )),
        ],
    ),

    ('openflow', 'port'): APIData(
        versioned=[
            ('7.20', '>=', VersionedAPIData(
                fully_understood=True,
                fields={
                    'comment': KeyInfo(),
                    # 'copy-from': KeyInfo(write_only=True),
                    'disabled': KeyInfo(),
                    'interface': KeyInfo(),
                    'port-id': KeyInfo(),
                    'switch': KeyInfo(),
                },
            )),
        ],
    ),

    ('partitions',): APIData(
        versioned=[
            ('7.15', '>=', VersionedAPIData(
                fully_understood=True,
                has_identifier=True,
                # fixed_entries=True,
                # primary_keys=('numbers',),
                fields={
                    'comment': KeyInfo(),
                    'fallback-to': KeyInfo(),
                    'name': KeyInfo(),
                    'numbers': KeyInfo(),
                },
            )),
        ],
    ),

    ('port',): APIData(
        versioned=[
            ('7.15', '>=', VersionedAPIData(
                fully_understood=True,
                has_identifier=True,
                # fixed_entries=True,
                # primary_keys=('numbers',),
                fields={
                    'baud-rate': KeyInfo(),
                    'data-bits': KeyInfo(),
                    'dtr': KeyInfo(),
                    'flow-control': KeyInfo(),
                    'name': KeyInfo(),
                    'numbers': KeyInfo(),
                    'parity': KeyInfo(),
                    'rts': KeyInfo(),
                    'stop-bits': KeyInfo(),
                },
            )),
        ],
    ),

    ('port', 'firmware'): APIData(
        versioned=[
            ('7.15', '<', VersionedAPIData(
                single_value=True,
                fully_understood=True,
                fields={
                    'directory': KeyInfo(default='firmware'),
                    'ignore-directip-modem': KeyInfo(default=False),
                },
            )),
            ('7.15', '>=', 'Not supported anymore in version 7.15'),
        ],
    ),

    ('port', 'remote-access'): APIData(
        unversioned=VersionedAPIData(
            fully_understood=True,
            versioned_fields=[
                ([('7.21', '>=')], 'comment', KeyInfo()),
                # ([('7.15', '>=')], 'copy-from', KeyInfo(write_only=True)),
                ([('7.15', '>=')], 'local-address', KeyInfo()),
            ],
            fields={
                'allowed-addresses': KeyInfo(default='0.0.0.0/0'),
                'channel': KeyInfo(default=0),
                'disabled': KeyInfo(default=False),
                'log-file': KeyInfo(default=''),
                'port': KeyInfo(required=True),
                'protocol': KeyInfo(default='rfc2217'),
                'tcp-port': KeyInfo(default=0),
            },
        ),
    ),

    ('ppp', 'aaa'): APIData(
        unversioned=VersionedAPIData(
            fixed_entries=True,
            single_value=True,
            fully_understood=True,
            versioned_fields=[
                ([('7.15', '>=')], 'enable-ipv6-accounting', KeyInfo()),
            ],
            fields={
                'accounting': KeyInfo(default=True),
                'interim-update': KeyInfo(default='0s'),
                'use-circuit-id-in-nas-port-id': KeyInfo(default=False),
                'use-radius': KeyInfo(default=False),
            },
        ),
    ),

    ('ppp', 'l2tp-secret'): APIData(
        versioned=[
            ('7.15', '>=', VersionedAPIData(
                fully_understood=True,
                fields={
                    'address': KeyInfo(),
                    'comment': KeyInfo(),
                    # 'copy-from': KeyInfo(write_only=True),
                    'secret': KeyInfo(),
                },
            )),
        ],
    ),

    ('ppp', 'profile'): APIData(
        unversioned=VersionedAPIData(
            primary_keys=('name',),
            fully_understood=True,
            versioned_fields=[
                ([('7.17', '>=')], 'bridge-port-trusted', KeyInfo()),
                ([('7.17', '>=')], 'bridge-port-vid', KeyInfo()),
                ([('7.15', '>=')], 'comment', KeyInfo()),
                # ([('7.15', '>=')], 'copy-from', KeyInfo(write_only=True)),
                ([('7.20', '>=')], 'dhcpv6-lease-time', KeyInfo()),
                ([('7.15', '>=')], 'dhcpv6-pd-pool', KeyInfo()),
                ([('7.20', '>=')], 'dhcpv6-use-radius', KeyInfo()),
                ([('7.15', '>=')], 'remote-ipv6-prefix-pool', KeyInfo()),
                ([('7.20', '>=')], 'remote-ipv6-prefix-reuse', KeyInfo()),
            ],
            fields={
                'address-list': KeyInfo(default=''),
                'bridge': KeyInfo(can_disable=True),
                'bridge-horizon': KeyInfo(can_disable=True),
                'bridge-learning': KeyInfo(default='default'),
                'bridge-path-cost': KeyInfo(can_disable=True),
                'bridge-port-priority': KeyInfo(can_disable=True),
                'change-tcp-mss': KeyInfo(default=True),
                'dns-server': KeyInfo(can_disable=True),
                'idle-timeout': KeyInfo(can_disable=True),
                'incoming-filter': KeyInfo(can_disable=True),
                'insert-queue-before': KeyInfo(can_disable=True),
                'interface-list': KeyInfo(can_disable=True),
                'local-address': KeyInfo(can_disable=True),
                'name': KeyInfo(required=True),
                'on-down': KeyInfo(default=''),
                'on-up': KeyInfo(default=''),
                'only-one': KeyInfo(default='default'),
                'outgoing-filter': KeyInfo(can_disable=True),
                'parent-queue': KeyInfo(can_disable=True),
                'queue-type': KeyInfo(can_disable=True),
                'rate-limit': KeyInfo(can_disable=True),
                'remote-address': KeyInfo(can_disable=True),
                'session-timeout': KeyInfo(can_disable=True),
                'use-compression': KeyInfo(default='default'),
                'use-encryption': KeyInfo(default='default'),
                'use-ipv6': KeyInfo(default=True),
                'use-mpls': KeyInfo(default='default'),
                'use-upnp': KeyInfo(default='default'),
                'wins-server': KeyInfo(can_disable=True),
            },
        ),
    ),

    ('ppp', 'secret'): APIData(
        unversioned=VersionedAPIData(
            primary_keys=('name',),
            fully_understood=True,
            versioned_fields=[
                ([('7.15', '>=')], 'comment', KeyInfo()),
                # ([('7.15', '>=')], 'copy-from', KeyInfo(write_only=True)),
            ],
            fields={
                'caller-id': KeyInfo(default=''),
                'disabled': KeyInfo(default=False),
                'ipv6-routes': KeyInfo(default=''),
                'limit-bytes-in': KeyInfo(default=0),
                'limit-bytes-out': KeyInfo(default=0),
                'local-address': KeyInfo(can_disable=True),
                'name': KeyInfo(required=True),
                'password': KeyInfo(),
                'profile': KeyInfo(default='default'),
                'remote-address': KeyInfo(can_disable=True),
                'remote-ipv6-prefix': KeyInfo(can_disable=True),
                'routes': KeyInfo(can_disable=True),
                'service': KeyInfo(default='any'),
            },
        ),
    ),

    ('queue', 'interface'): APIData(
        unversioned=VersionedAPIData(
            primary_keys=('interface',),
            fixed_entries=True,
            fully_understood=True,
            versioned_fields=[
                ([('7.15', '>=')], 'numbers', KeyInfo()),
            ],
            fields={
                'interface': KeyInfo(required=True),
                'queue': KeyInfo(required=True),
            },
        ),
    ),

    ('queue', 'simple'): APIData(
        unversioned=VersionedAPIData(
            primary_keys=('name',),
            fully_understood=True,
            versioned_fields=[
                # ([('7.15', '>=')], 'copy-from', KeyInfo(write_only=True)),
                # ([('7.15', '>=')], 'place-before', KeyInfo(write_only=True)),
                ([('7.15', '>=')], 'total-bucket-size', KeyInfo()),
                ([('7.15', '>=')], 'total-burst-limit', KeyInfo()),
                ([('7.15', '>=')], 'total-burst-threshold', KeyInfo()),
                ([('7.15', '>=')], 'total-burst-time', KeyInfo()),
                ([('7.15', '>=')], 'total-limit-at', KeyInfo()),
                ([('7.15', '>=')], 'total-max-limit', KeyInfo()),
                ([('7.15', '>=')], 'total-priority', KeyInfo()),
                ([('7.15', '>=')], 'total-queue', KeyInfo()),
            ],
            fields={
                'bucket-size': KeyInfo(default='0.1/0.1'),
                'burst-limit': KeyInfo(default='0/0'),
                'burst-threshold': KeyInfo(default='0/0'),
                'burst-time': KeyInfo(default='0s/0s'),
                'comment': KeyInfo(can_disable=True, remove_value=''),
                'disabled': KeyInfo(default=False),
                'dst': KeyInfo(can_disable=True, remove_value=''),
                'limit-at': KeyInfo(default='0/0'),
                'max-limit': KeyInfo(default='0/0'),
                'name': KeyInfo(),
                'packet-marks': KeyInfo(default=''),
                'parent': KeyInfo(default='none'),
                'priority': KeyInfo(default='8/8'),
                'queue': KeyInfo(default='default-small/default-small'),
                'target': KeyInfo(required=True),
                'time': KeyInfo(can_disable=True, remove_value=''),
            },
        ),
    ),

    ('queue', 'tree'): APIData(
        unversioned=VersionedAPIData(
            primary_keys=('name',),
            fully_understood=True,
            # versioned_fields=[
            #     ([('7.15', '>=')], 'copy-from', KeyInfo(write_only=True)),
            # ],
            fields={
                'bucket-size': KeyInfo(default='0.1'),
                'burst-limit': KeyInfo(default=0),
                'burst-threshold': KeyInfo(default=0),
                'burst-time': KeyInfo(default='0s'),
                'comment': KeyInfo(can_disable=True, remove_value=''),
                'disabled': KeyInfo(default=False),
                'limit-at': KeyInfo(default=0),
                'max-limit': KeyInfo(default=0),
                'name': KeyInfo(),
                'packet-mark': KeyInfo(default=''),
                'parent': KeyInfo(required=True),
                'priority': KeyInfo(default=8),
                'queue': KeyInfo(default='default-small'),
            },
        ),
    ),

    ('queue', 'type'): APIData(
        unversioned=VersionedAPIData(
            primary_keys=('name',),
            fully_understood=True,
            # versioned_fields=[
            #     ([('7.15', '>=')], 'copy-from', KeyInfo(write_only=True)),
            # ],
            fields={
                'bfifo-limit': KeyInfo(default=15000),
                'cake-ack-filter': KeyInfo(default='none'),
                'cake-atm': KeyInfo(default='none'),
                'cake-autorate-ingress': KeyInfo(can_disable=True),
                'cake-bandwidth': KeyInfo(can_disable=True, remove_value=0),
                'cake-diffserv': KeyInfo(default='diffserv3'),
                'cake-flowmode': KeyInfo(default='triple-isolate'),
                'cake-memlimit': KeyInfo(default=0),
                'cake-mpu': KeyInfo(can_disable=True, remove_value=''),
                'cake-nat': KeyInfo(can_disable=True, remove_value=False),
                'cake-overhead': KeyInfo(default=0),
                'cake-overhead-scheme': KeyInfo(can_disable=True, remove_value=''),
                'cake-rtt': KeyInfo(default='100ms'),
                'cake-rtt-scheme': KeyInfo(default='none'),
                'cake-wash': KeyInfo(can_disable=True, remove_value=False),
                'codel-ce-threshold': KeyInfo(can_disable=True, remove_value=''),
                'codel-ecn': KeyInfo(can_disable=True, remove_value=False),
                'codel-interval': KeyInfo(default='100ms'),
                'codel-limit': KeyInfo(default=1000),
                'codel-target': KeyInfo(default='5ms'),
                'fq-codel-ce-threshold': KeyInfo(can_disable=True, remove_value=''),
                'fq-codel-ecn': KeyInfo(default=True),
                'fq-codel-flows': KeyInfo(default=1024),
                'fq-codel-interval': KeyInfo(default='100ms'),
                'fq-codel-limit': KeyInfo(default=10240),
                'fq-codel-memlimit': KeyInfo(default=33554432),
                'fq-codel-quantum': KeyInfo(default=1514),
                'fq-codel-target': KeyInfo(default='5ms'),
                'kind': KeyInfo(required=True),
                'mq-pfifo-limit': KeyInfo(default=50),
                'name': KeyInfo(),
                'pcq-burst-rate': KeyInfo(default=0),
                'pcq-burst-threshold': KeyInfo(default=0),
                'pcq-burst-time': KeyInfo(default='10s'),
                'pcq-classifier': KeyInfo(can_disable=True, remove_value=''),
                'pcq-dst-address-mask': KeyInfo(default=32),
                'pcq-dst-address6-mask': KeyInfo(default=128),
                'pcq-limit': KeyInfo(default=50),
                'pcq-rate': KeyInfo(default=0),
                'pcq-src-address-mask': KeyInfo(default=32),
                'pcq-src-address6-mask': KeyInfo(default=128),
                'pcq-total-limit': KeyInfo(default=2000),
                'pfifo-limit': KeyInfo(default=50),
                'red-avg-packet': KeyInfo(default=1000),
                'red-burst': KeyInfo(default=20),
                'red-limit': KeyInfo(default=60),
                'red-max-threshold': KeyInfo(default=50),
                'red-min-threshold': KeyInfo(default=10),
                'sfq-allot': KeyInfo(default=1514),
                'sfq-perturb': KeyInfo(default=5),
            },
        ),
    ),

    ('radius',): APIData(
        unversioned=VersionedAPIData(
            fully_understood=True,
            versioned_fields=[
                # ([('7.15', '>=')], 'copy-from', KeyInfo(write_only=True)),
                # ([('7.15', '>=')], 'place-before', KeyInfo(write_only=True)),
                ([('7.19.6', '>=')], 'radsec-timeout', KeyInfo(default='3300ms')),
                ([('7.15', '>=')], 'require-message-auth', KeyInfo(default='yes-for-request-resp')),
            ],
            fields={
                'accounting-backup': KeyInfo(default=False),
                'accounting-port': KeyInfo(default=1813),
                'address': KeyInfo(default='0.0.0.0'),
                'authentication-port': KeyInfo(default=1812),
                'called-id': KeyInfo(),
                'certificate': KeyInfo(),
                'comment': KeyInfo(can_disable=True, remove_value=''),
                'disabled': KeyInfo(default=False),
                'domain': KeyInfo(),
                'protocol': KeyInfo(default='udp'),
                'realm': KeyInfo(),
                'secret': KeyInfo(),
                'service': KeyInfo(),
                'src-address': KeyInfo(default='0.0.0.0'),
                'timeout': KeyInfo(default='300ms'),
            },
        ),
    ),

    ('radius', 'incoming'): APIData(
        unversioned=VersionedAPIData(
            fixed_entries=True,
            single_value=True,
            fully_understood=True,
            versioned_fields=[
                ([('7.15', '>=')], 'vrf', KeyInfo()),
            ],
            fields={
                'accept': KeyInfo(default=False),
                'port': KeyInfo(default=3799),
            },
        ),
    ),

    ('routing', 'bfd', 'configuration'): APIData(
        versioned=[
            ('7.11', '>=', VersionedAPIData(
                fully_understood=True,
                fields={
                    'address-list': KeyInfo(),
                    'addresses': KeyInfo(),
                    'comment': KeyInfo(can_disable=True, remove_value=''),
                    'copy-from': KeyInfo(write_only=True),
                    'disabled': KeyInfo(default=False),
                    'forbid-bfd': KeyInfo(),
                    'interfaces': KeyInfo(),
                    'min-echo-rx': KeyInfo(),
                    'min-rx': KeyInfo(),
                    'min-tx': KeyInfo(),
                    'multiplier': KeyInfo(),
                    'place-before': KeyInfo(write_only=True),
                    'vrf': KeyInfo(),
                },
            )),
        ],
    ),

    ('routing', 'bfd', 'interface'): APIData(
        versioned=[
            ('7.15', '<', VersionedAPIData(
                unknown_mechanism=True,
                fields={
                    'default': KeyInfo(),
                    'disabled': KeyInfo(),
                    'interface': KeyInfo(),
                    'interval': KeyInfo(),
                    'min-rx': KeyInfo(),
                    'multiplier': KeyInfo(),
                },
            )),
            ('7.15', '>=', 'Not supported anymore in version 7.15'),
        ],
    ),

    ('routing', 'bgp', 'aggregate'): APIData(
        versioned=[
            ('7.15', '<', VersionedAPIData(
                primary_keys=('prefix',),
                fully_understood=True,
                fields={
                    'advertise-filter': KeyInfo(),
                    'attribute-filter': KeyInfo(),
                    'disabled': KeyInfo(default=False),
                    'include-igp': KeyInfo(default=False),
                    'inherit-attributes': KeyInfo(default=True),
                    'instance': KeyInfo(required=True),
                    'prefix': KeyInfo(required=True),
                    'summary-only': KeyInfo(default=True),
                    'suppress-filter': KeyInfo(),
                },
            )),
            ('7.15', '>=', 'Not supported anymore in version 7.15'),
        ],
    ),

    ('routing', 'bgp', 'connection'): APIData(
        unversioned=VersionedAPIData(
            fully_understood=True,
            versioned_fields=[
                ([('7.19', '<')], 'address-families', KeyInfo()),
                ([('7.19', '>=')], 'afi', KeyInfo()),
                ([('7.20', '<')], 'cluster-id', KeyInfo()),
                # ([('7.15', '>=')], 'copy-from', KeyInfo(write_only=True)),
                ([('7.19', '<')], 'input.accept-unknown', KeyInfo()),
                ([('7.21.2', '>=')], 'input.attr-error-handling', KeyInfo()),
                ([('7.19', '>=')], 'input.filter-communities', KeyInfo()),
                ([('7.19', '>=')], 'input.filter-ext-communities', KeyInfo()),
                ([('7.19', '>=')], 'input.filter-large-communities', KeyInfo()),
                ([('7.20', '>=')], 'input.filter-nlri', KeyInfo()),
                ([('7.19', '>=')], 'input.filter-unknown', KeyInfo()),
                ([('7.20', '<')], 'input.ignore-as-path-len', KeyInfo()),
                ([('7.20', '>=')], 'instance', KeyInfo(required=True)),
                ([('7.20.1', '>=')], 'output.network-blackhole', KeyInfo()),
                ([('7.20', '<')], 'router-id', KeyInfo()),
            ],
            fields={
                'add-path-out': KeyInfo(),
                'as': KeyInfo(),
                'cisco-vpls-nlri-len-fmt': KeyInfo(),
                'comment': KeyInfo(),
                'connect': KeyInfo(default=True),
                'disabled': KeyInfo(default=False),
                'hold-time': KeyInfo(),
                'input.accept-communities': KeyInfo(),
                'input.accept-ext-communities': KeyInfo(),
                'input.accept-large-communities': KeyInfo(),
                'input.accept-nlri': KeyInfo(),
                'input.affinity': KeyInfo(),
                'input.allow-as': KeyInfo(),
                'input.filter': KeyInfo(),
                'input.limit-process-routes-ipv4': KeyInfo(),
                'input.limit-process-routes-ipv6': KeyInfo(),
                'keepalive-time': KeyInfo(),
                'listen': KeyInfo(default=True),
                'local.address': KeyInfo(),
                'local.port': KeyInfo(),
                'local.role': KeyInfo(required=True),
                'local.ttl': KeyInfo(),
                'multihop': KeyInfo(),
                'name': KeyInfo(required=True),
                'nexthop-choice': KeyInfo(),
                'output.affinity': KeyInfo(),
                'output.as-override': KeyInfo(),
                'output.default-originate': KeyInfo(),
                'output.default-prepend': KeyInfo(),
                'output.filter-chain': KeyInfo(),
                'output.filter-select': KeyInfo(),
                'output.keep-sent-attributes': KeyInfo(),
                'output.network': KeyInfo(),
                'output.no-client-to-client-reflection': KeyInfo(),
                'output.no-early-cut': KeyInfo(),
                'output.redistribute': KeyInfo(),
                'output.remove-private-as': KeyInfo(),
                'remote.address': KeyInfo(required=True),
                'remote.allowed-as': KeyInfo(),
                'remote.as': KeyInfo(),
                'remote.port': KeyInfo(),
                'remote.ttl': KeyInfo(),
                'routing-table': KeyInfo(),
                'save-to': KeyInfo(),
                'tcp-md5-key': KeyInfo(),
                'templates': KeyInfo(),
                'use-bfd': KeyInfo(),
                'vrf': KeyInfo(),
            },
        ),
    ),

    ('routing', 'bgp', 'evpn'): APIData(
        versioned=[
            ('7.20', '>=', VersionedAPIData(
                fully_understood=True,
                fields={
                    'comment': KeyInfo(),
                    # 'copy-from': KeyInfo(write_only=True),
                    'disabled': KeyInfo(),
                    'export.route-targets': KeyInfo(),
                    'import.route-targets': KeyInfo(),
                    'instance': KeyInfo(),
                    'name': KeyInfo(),
                    # 'place-before': KeyInfo(write_only=True),
                    'rd': KeyInfo(),
                    'vni': KeyInfo(),
                    'vrf': KeyInfo(),
                },
            )),
        ],
    ),

    ('routing', 'bgp', 'instance'): APIData(
        versioned=[
            ('7.15', '<', VersionedAPIData(
                primary_keys=('name',),
                fully_understood=True,
                fields={
                    'as': KeyInfo(),
                    'client-to-client-reflection': KeyInfo(),
                    'cluster-id': KeyInfo(can_disable=True),
                    'confederation': KeyInfo(can_disable=True),
                    'disabled': KeyInfo(default=False),
                    'ignore-as-path-len': KeyInfo(),
                    'name': KeyInfo(),
                    'out-filter': KeyInfo(),
                    'redistribute-connected': KeyInfo(),
                    'redistribute-ospf': KeyInfo(),
                    'redistribute-other-bgp': KeyInfo(),
                    'redistribute-rip': KeyInfo(),
                    'redistribute-static': KeyInfo(),
                    'router-id': KeyInfo(),
                    'routing-table': KeyInfo(),
                },
            )),
            ('7.15', '>=', 'Not supported from 7.15 until reintroduced in 7.20'),
            ('7.20', '>=', VersionedAPIData(
                fully_understood=True,
                fields={
                    'as': KeyInfo(can_disable=True),
                    'cluster-id': KeyInfo(can_disable=True),
                    'comment': KeyInfo(),
                    # 'copy-from': KeyInfo(write_only=True),
                    'disabled': KeyInfo(default=False),
                    'ignore-as-path-len': KeyInfo(can_disable=True),
                    'name': KeyInfo(),
                    'router-id': KeyInfo(can_disable=True),
                    'routing-table': KeyInfo(can_disable=True),
                    'vrf': KeyInfo(can_disable=True),
                },
            )),
        ],
    ),

    ('routing', 'bgp', 'network'): APIData(
        versioned=[
            ('7.15', '<', VersionedAPIData(
                primary_keys=('network',),
                fully_understood=True,
                fields={
                    'comment': KeyInfo(can_disable=True, remove_value=''),
                    'disabled': KeyInfo(default=False),
                    'network': KeyInfo(required=True),
                    'synchronize': KeyInfo(default=True),
                },
            )),
            ('7.15', '>=', 'Not supported anymore in version 7.15'),
        ],
    ),

    ('routing', 'bgp', 'peer'): APIData(
        versioned=[
            ('7.15', '<', VersionedAPIData(
                primary_keys=('name',),
                fully_understood=True,
                fields={
                    'address-families': KeyInfo(default='ip'),
                    'allow-as-in': KeyInfo(can_disable=True, remove_value=''),
                    'as-override': KeyInfo(default=False),
                    'cisco-vpls-nlri-len-fmt': KeyInfo(),
                    'comment': KeyInfo(can_disable=True, remove_value=''),
                    'default-originate': KeyInfo(default='never'),
                    'disabled': KeyInfo(default=False),
                    'hold-time': KeyInfo(default='3m'),
                    'in-filter': KeyInfo(),
                    'instance': KeyInfo(),
                    'keepalive-time': KeyInfo(can_disable=True, remove_value=''),
                    'max-prefix-limit': KeyInfo(can_disable=True, remove_value=''),
                    'max-prefix-restart-time': KeyInfo(can_disable=True, remove_value=''),
                    'multihop': KeyInfo(default=False),
                    'name': KeyInfo(),
                    'nexthop-choice': KeyInfo(default='default'),
                    'out-filter': KeyInfo(),
                    'passive': KeyInfo(default=False),
                    'remote-address': KeyInfo(required=True),
                    'remote-as': KeyInfo(required=True),
                    'remote-port': KeyInfo(can_disable=True, remove_value=''),
                    'remove-private-as': KeyInfo(default=False),
                    'route-reflect': KeyInfo(default=False),
                    'tcp-md5-key': KeyInfo(),
                    'ttl': KeyInfo(default='default'),
                    'update-source': KeyInfo(can_disable=True, remove_value='none'),
                    'use-bfd': KeyInfo(default=False),
                },
            )),
            ('7.15', '>=', 'Not supported anymore in version 7.15'),
        ],
    ),

    ('routing', 'bgp', 'template'): APIData(
        unversioned=VersionedAPIData(
            primary_keys=('name',),
            fully_understood=True,
            versioned_fields=[
                ([('7.19', '<')], 'address-families', KeyInfo()),
                ([('7.19', '>=')], 'afi', KeyInfo()),
                ([('7.15', '<')], 'as-override', KeyInfo(default=False)),
                ([('7.20', '<')], 'cluster-id', KeyInfo()),
                # ([('7.15', '>=')], 'copy-from', KeyInfo(write_only=True)),
                ([('7.19', '<')], 'input.accept-unknown', KeyInfo()),
                ([('7.21.2', '>=')], 'input.attr-error-handling', KeyInfo()),
                ([('7.19', '>=')], 'input.filter-communities', KeyInfo()),
                ([('7.19', '>=')], 'input.filter-ext-communities', KeyInfo()),
                ([('7.19', '>=')], 'input.filter-large-communities', KeyInfo()),
                ([('7.20', '>=')], 'input.filter-nlri', KeyInfo()),
                ([('7.19', '>=')], 'input.filter-unknown', KeyInfo()),
                ([('7.20', '<')], 'input.ignore-as-path-len', KeyInfo(default=False)),
                ([('7.15', '<')], 'input.limit-nlri-diversity', KeyInfo()),
                ([('7.15', '>=')], 'output.as-override', KeyInfo()),
                ([('7.15', '>=')], 'output.default-prepend', KeyInfo()),
                ([('7.15', '<')], 'output.default-prepent', KeyInfo()),
                ([('7.20.1', '>=')], 'output.network-blackhole', KeyInfo()),
                ([('7.20', '<')], 'router-id', KeyInfo(default='main')),
            ],
            fields={
                'add-path-out': KeyInfo(),
                'as': KeyInfo(),
                'cisco-vpls-nlri-len-fmt': KeyInfo(),
                'comment': KeyInfo(can_disable=True, remove_value=''),
                'disabled': KeyInfo(default=False),
                'hold-time': KeyInfo(default='3m'),
                'input.accept-communities': KeyInfo(),
                'input.accept-ext-communities': KeyInfo(),
                'input.accept-large-communities': KeyInfo(),
                'input.accept-nlri': KeyInfo(),
                'input.affinity': KeyInfo(),
                'input.allow-as': KeyInfo(),
                'input.filter': KeyInfo(),
                'input.limit-process-routes-ipv4': KeyInfo(),
                'input.limit-process-routes-ipv6': KeyInfo(),
                'keepalive-time': KeyInfo(default='3m'),
                'multihop': KeyInfo(default=False),
                'name': KeyInfo(),
                'nexthop-choice': KeyInfo(default='default'),
                'output.affinity': KeyInfo(),
                'output.default-originate': KeyInfo(default='never'),
                'output.filter-chain': KeyInfo(),
                'output.filter-select': KeyInfo(),
                'output.keep-sent-attributes': KeyInfo(default=False),
                'output.network': KeyInfo(),
                'output.no-client-to-client-reflection': KeyInfo(),
                'output.no-early-cut': KeyInfo(),
                'output.redistribute': KeyInfo(),
                'output.remove-private-as': KeyInfo(default=False),
                'routing-table': KeyInfo(default='main'),
                'save-to': KeyInfo(),
                'templates': KeyInfo(),
                'use-bfd': KeyInfo(default=False),
                'vrf': KeyInfo(default='main'),
            },
        ),
    ),

    ('routing', 'bgp', 'vpls'): APIData(
        versioned=[
            ('7.15', '>=', VersionedAPIData(
                fully_understood=True,
                versioned_fields=[
                    ([('7.17', '>=')], 'bridge-pvid', KeyInfo()),
                ],
                fields={
                    'bridge': KeyInfo(),
                    'bridge-cost': KeyInfo(),
                    'bridge-horizon': KeyInfo(),
                    'cisco-id': KeyInfo(),
                    'comment': KeyInfo(),
                    # 'copy-from': KeyInfo(write_only=True),
                    'disabled': KeyInfo(),
                    'export-route-targets': KeyInfo(),
                    'import-route-targets': KeyInfo(),
                    'local-pref': KeyInfo(),
                    'name': KeyInfo(),
                    'pw-control-word': KeyInfo(),
                    'pw-l2mtu': KeyInfo(),
                    'pw-type': KeyInfo(),
                    'rd': KeyInfo(),
                    'site-id': KeyInfo(),
                    'vrf': KeyInfo(),
                },
            )),
        ],
    ),

    ('routing', 'bgp', 'vpn'): APIData(
        versioned=[
            ('7.15', '>=', VersionedAPIData(
                fully_understood=True,
                versioned_fields=[
                    ([('7.20', '>=')], 'instance', KeyInfo()),
                ],
                fields={
                    'comment': KeyInfo(),
                    # 'copy-from': KeyInfo(write_only=True),
                    'disabled': KeyInfo(),
                    'export.filter-chain': KeyInfo(),
                    'export.filter-select': KeyInfo(),
                    'export.redistribute': KeyInfo(),
                    'export.route-targets': KeyInfo(),
                    'import.filter-chain': KeyInfo(),
                    'import.route-targets': KeyInfo(),
                    'import.router-id': KeyInfo(),
                    'label-allocation-policy': KeyInfo(),
                    'name': KeyInfo(),
                    'route-distinguisher': KeyInfo(),
                    'vrf': KeyInfo(),
                },
            )),
        ],
    ),

    ('routing', 'fantasy'): APIData(
        versioned=[
            ('7.15', '>=', VersionedAPIData(
                fully_understood=True,
                fields={
                    'comment': KeyInfo(),
                    # 'copy-from': KeyInfo(write_only=True),
                    'count': KeyInfo(),
                    'dealer-id': KeyInfo(),
                    'disabled': KeyInfo(),
                    'dst-address': KeyInfo(),
                    'gateway': KeyInfo(),
                    'instance-id': KeyInfo(),
                    'name': KeyInfo(),
                    'offset': KeyInfo(),
                    'prefix-length': KeyInfo(),
                    'priv-offs': KeyInfo(),
                    'priv-size': KeyInfo(),
                    'scope': KeyInfo(),
                    'seed': KeyInfo(),
                    'target-scope': KeyInfo(),
                    'use-hold': KeyInfo(),
                },
            )),
        ],
    ),

    ('routing', 'filter'): APIData(
        versioned=[
            ('7', '<', VersionedAPIData(
                fully_understood=True,
                fields={
                    'action': KeyInfo(default='passthrough'),
                    'address-family': KeyInfo(can_disable=True),
                    'append-bgp-communities': KeyInfo(can_disable=True),
                    'append-route-targets': KeyInfo(can_disable=True),
                    'bgp-as-path': KeyInfo(can_disable=True),
                    'bgp-as-path-length': KeyInfo(can_disable=True),
                    'bgp-atomic-aggregate': KeyInfo(can_disable=True),
                    'bgp-communities': KeyInfo(can_disable=True),
                    'bgp-local-pref': KeyInfo(can_disable=True),
                    'bgp-med': KeyInfo(can_disable=True),
                    'bgp-origin': KeyInfo(can_disable=True),
                    'bgp-weight': KeyInfo(can_disable=True),
                    'chain': KeyInfo(required=True),
                    'comment': KeyInfo(can_disable=True, remove_value=''),
                    'disabled': KeyInfo(default=False),
                    'distance': KeyInfo(can_disable=True),
                    'invert-match': KeyInfo(default=False),
                    'jump-target': KeyInfo(),
                    'locally-originated-bgp': KeyInfo(can_disable=True),
                    'match-chain': KeyInfo(can_disable=True),
                    'ospf-type': KeyInfo(can_disable=True),
                    'pref-src': KeyInfo(can_disable=True),
                    'prefix': KeyInfo(default='0.0.0.0/0'),
                    'prefix-length': KeyInfo(can_disable=True),
                    'protocol': KeyInfo(can_disable=True),
                    'route-comment': KeyInfo(can_disable=True),
                    'route-tag': KeyInfo(can_disable=True),
                    'route-targets': KeyInfo(can_disable=True),
                    'routing-mark': KeyInfo(can_disable=True),
                    'scope': KeyInfo(can_disable=True),
                    'set-bgp-communities': KeyInfo(can_disable=True),
                    'set-bgp-local-pref': KeyInfo(can_disable=True),
                    'set-bgp-med': KeyInfo(can_disable=True),
                    'set-bgp-prepend': KeyInfo(can_disable=True),
                    'set-bgp-prepend-path': KeyInfo(),
                    'set-bgp-weight': KeyInfo(can_disable=True),
                    'set-check-gateway': KeyInfo(can_disable=True),
                    'set-disabled': KeyInfo(can_disable=True),
                    'set-distance': KeyInfo(can_disable=True),
                    'set-in-nexthop': KeyInfo(can_disable=True),
                    'set-in-nexthop-direct': KeyInfo(can_disable=True),
                    'set-in-nexthop-ipv6': KeyInfo(can_disable=True),
                    'set-in-nexthop-linklocal': KeyInfo(can_disable=True),
                    'set-out-nexthop': KeyInfo(can_disable=True),
                    'set-out-nexthop-ipv6': KeyInfo(can_disable=True),
                    'set-out-nexthop-linklocal': KeyInfo(can_disable=True),
                    'set-pref-src': KeyInfo(can_disable=True),
                    'set-route-comment': KeyInfo(can_disable=True),
                    'set-route-tag': KeyInfo(can_disable=True),
                    'set-route-targets': KeyInfo(can_disable=True),
                    'set-routing-mark': KeyInfo(can_disable=True),
                    'set-scope': KeyInfo(can_disable=True),
                    'set-site-of-origin': KeyInfo(can_disable=True),
                    'set-target-scope': KeyInfo(can_disable=True),
                    'set-type': KeyInfo(can_disable=True),
                    'set-use-te-nexthop': KeyInfo(can_disable=True),
                    'site-of-origin': KeyInfo(can_disable=True),
                    'target-scope': KeyInfo(can_disable=True),
                },
            )),
            ('7', '>=', 'Not supported anymore in version 7'),
        ],
    ),

    ('routing', 'filter', 'community-ext-list'): APIData(
        versioned=[
            ('7.15', '>=', VersionedAPIData(
                fully_understood=True,
                fields={
                    'comment': KeyInfo(),
                    'communities': KeyInfo(),
                    # 'copy-from': KeyInfo(write_only=True),
                    'disabled': KeyInfo(),
                    'list': KeyInfo(),
                    # 'place-before': KeyInfo(write_only=True),
                    'regexp': KeyInfo(),
                },
            )),
        ],
    ),

    ('routing', 'filter', 'community-large-list'): APIData(
        versioned=[
            ('7.15', '>=', VersionedAPIData(
                fully_understood=True,
                fields={
                    'comment': KeyInfo(),
                    'communities': KeyInfo(),
                    # 'copy-from': KeyInfo(write_only=True),
                    'disabled': KeyInfo(),
                    'list': KeyInfo(),
                    # 'place-before': KeyInfo(write_only=True),
                    'regexp': KeyInfo(),
                },
            )),
        ],
    ),

    ('routing', 'filter', 'community-list'): APIData(
        versioned=[
            ('7', '>=', VersionedAPIData(
                fully_understood=True,
                # versioned_fields=[
                #     ([('7.15', '>=')], 'copy-from', KeyInfo(write_only=True)),
                #     ([('7.15', '>=')], 'place-before', KeyInfo(write_only=True)),
                # ],
                fields={
                    'comment': KeyInfo(can_disable=True, remove_value=''),
                    'communities': KeyInfo(can_disable=True),
                    'disabled': KeyInfo(can_disable=True),
                    'list': KeyInfo(required=True),
                    'regexp': KeyInfo(can_disable=True),
                },
            )),
        ],
    ),

    ('routing', 'filter', 'num-list'): APIData(
        versioned=[
            ('7', '>=', VersionedAPIData(
                fully_understood=True,
                # versioned_fields=[
                #     ([('7.15', '>=')], 'copy-from', KeyInfo(write_only=True)),
                #     ([('7.15', '>=')], 'place-before', KeyInfo(write_only=True)),
                # ],
                fields={
                    'comment': KeyInfo(can_disable=True, remove_value=''),
                    'disabled': KeyInfo(can_disable=True),
                    'list': KeyInfo(required=True),
                    'range': KeyInfo(can_disable=True),
                },
            )),
        ],
    ),

    ('routing', 'filter', 'rule'): APIData(
        versioned=[
            ('7', '>=', VersionedAPIData(
                fully_understood=True,
                # versioned_fields=[
                #     ([('7.15', '>=')], 'copy-from', KeyInfo(write_only=True)),
                #     ([('7.15', '>=')], 'place-before', KeyInfo(write_only=True)),
                # ],
                fields={
                    'chain': KeyInfo(required=True),
                    'comment': KeyInfo(can_disable=True, remove_value=''),
                    'disabled': KeyInfo(can_disable=True),
                    'rule': KeyInfo(can_disable=True),
                },
            )),
        ],
    ),

    ('routing', 'filter', 'select-rule'): APIData(
        versioned=[
            ('7', '>=', VersionedAPIData(
                fully_understood=True,
                # versioned_fields=[
                #     ([('7.15', '>=')], 'copy-from', KeyInfo(write_only=True)),
                #     ([('7.15', '>=')], 'place-before', KeyInfo(write_only=True)),
                # ],
                fields={
                    'chain': KeyInfo(required=True),
                    'comment': KeyInfo(can_disable=True, remove_value=''),
                    'disabled': KeyInfo(can_disable=True),
                    'do-group-num': KeyInfo(can_disable=True),
                    'do-group-prfx': KeyInfo(can_disable=True),
                    'do-jump': KeyInfo(can_disable=True),
                    'do-select-num': KeyInfo(can_disable=True),
                    'do-select-prfx': KeyInfo(can_disable=True),
                    'do-take': KeyInfo(can_disable=True),
                    'do-where': KeyInfo(can_disable=True),
                },
            )),
        ],
    ),

    ('routing', 'gmp'): APIData(
        versioned=[
            ('7.15', '>=', VersionedAPIData(
                fully_understood=True,
                fields={
                    # 'copy-from': KeyInfo(write_only=True),
                    'disabled': KeyInfo(),
                    'exclude': KeyInfo(),
                    'groups': KeyInfo(),
                    'interfaces': KeyInfo(),
                    'sources': KeyInfo(),
                },
            )),
        ],
    ),

    ('routing', 'id'): APIData(
        unversioned=VersionedAPIData(
            fully_understood=True,
            # versioned_fields=[
            #     ([('7.15', '>=')], 'copy-from', KeyInfo(write_only=True)),
            # ],
            fields={
                'comment': KeyInfo(can_disable=True, remove_value=''),
                'disabled': KeyInfo(default=False),
                'id': KeyInfo(),
                'name': KeyInfo(),
                'select-dynamic-id': KeyInfo(),
                'select-from-vrf': KeyInfo(),
            },
        ),
    ),

    ('routing', 'igmp-proxy'): APIData(
        unversioned=VersionedAPIData(
            fixed_entries=True,
            single_value=True,
            fully_understood=True,
            fields={
                'query-interval': KeyInfo(),
                'query-response-interval': KeyInfo(),
                'quick-leave': KeyInfo(default=False),
            },
        ),
    ),

    ('routing', 'igmp-proxy', 'interface'): APIData(
        unversioned=VersionedAPIData(
            primary_keys=('interface',),
            fully_understood=True,
            # versioned_fields=[
            #     ([('7.15', '>=')], 'copy-from', KeyInfo(write_only=True)),
            # ],
            fields={
                'alternative-subnets': KeyInfo(default=''),
                'comment': KeyInfo(can_disable=True, remove_value=''),
                'disabled': KeyInfo(default=False),
                'interface': KeyInfo(),
                'threshold': KeyInfo(),
                'upstream': KeyInfo(default=False),
            },
        ),
    ),

    ('routing', 'igmp-proxy', 'mfc'): APIData(
        versioned=[
            ('7.15', '>=', VersionedAPIData(
                fully_understood=True,
                fields={
                    # 'copy-from': KeyInfo(write_only=True),
                    'disabled': KeyInfo(),
                    'downstream-interfaces': KeyInfo(),
                    'group': KeyInfo(),
                    'source': KeyInfo(),
                    'upstream-interface': KeyInfo(),
                },
            )),
        ],
    ),

    ('routing', 'isis', 'instance'): APIData(
        versioned=[
            ('7.15', '>=', VersionedAPIData(
                fully_understood=True,
                fields={
                    'afi': KeyInfo(),
                    'areas': KeyInfo(),
                    'areas-max': KeyInfo(),
                    'comment': KeyInfo(),
                    # 'copy-from': KeyInfo(write_only=True),
                    'disabled': KeyInfo(),
                    'in-filter-chain': KeyInfo(can_disable=True),
                    'l1.lsp-max-age': KeyInfo(can_disable=True),
                    'l1.lsp-max-size': KeyInfo(can_disable=True),
                    'l1.lsp-refresh-interval': KeyInfo(can_disable=True),
                    'l1.lsp-update-interval': KeyInfo(can_disable=True),
                    'l1.originate-default': KeyInfo(can_disable=True),
                    'l1.out-filter-chain': KeyInfo(can_disable=True),
                    'l1.out-filter-select': KeyInfo(can_disable=True),
                    'l1.redistribute': KeyInfo(can_disable=True),
                    'l2.lsp-max-age': KeyInfo(can_disable=True),
                    'l2.lsp-max-size': KeyInfo(can_disable=True),
                    'l2.lsp-update-interval': KeyInfo(can_disable=True),
                    'l2.originate-default': KeyInfo(can_disable=True),
                    'l2.out-filter-chain': KeyInfo(can_disable=True),
                    'l2.out-filter-select': KeyInfo(can_disable=True),
                    'l2.redistribute': KeyInfo(can_disable=True),
                    'name': KeyInfo(),
                    'system-id': KeyInfo(),
                    'vrf': KeyInfo(),
                },
            )),
        ],
    ),

    ('routing', 'isis', 'interface'): APIData(
        versioned=[
            ('7.15', '>=', VersionedAPIData(
                fully_understood=True,
                has_identifier=True,
                # fixed_entries=True,
                # primary_keys=('numbers',),
                fields={
                    'hello-interval': KeyInfo(can_disable=True),
                    'instance': KeyInfo(),
                    'interface': KeyInfo(),
                    'l1.csnp-interval': KeyInfo(can_disable=True),
                    'l1.hello-dr-interval': KeyInfo(can_disable=True),
                    'l1.hello-interval': KeyInfo(can_disable=True),
                    'l1.hello-multiplier': KeyInfo(can_disable=True),
                    'l1.metric': KeyInfo(can_disable=True),
                    'l1.passive': KeyInfo(),
                    'l1.priority': KeyInfo(can_disable=True),
                    'l1.psnp-interval': KeyInfo(can_disable=True),
                    'l2.csnp-interval': KeyInfo(can_disable=True),
                    'l2.hello-dr-interval': KeyInfo(can_disable=True),
                    'l2.hello-interval': KeyInfo(can_disable=True),
                    'l2.hello-multiplier': KeyInfo(can_disable=True),
                    'l2.metric': KeyInfo(can_disable=True),
                    'l2.passive': KeyInfo(),
                    'l2.priority': KeyInfo(can_disable=True),
                    'l2.psnp-interval': KeyInfo(can_disable=True),
                    'numbers': KeyInfo(),
                    'ptp': KeyInfo(),
                    'ptp.3way-state': KeyInfo(can_disable=True),
                    'ptp.usage': KeyInfo(can_disable=True),
                },
            )),
        ],
    ),

    ('routing', 'isis', 'interface-template'): APIData(
        versioned=[
            ('7.15', '>=', VersionedAPIData(
                fully_understood=True,
                versioned_fields=[
                    ([('7.17', '>=')], 'disabled', KeyInfo()),
                    ([('7.20', '>=')], 'passive', KeyInfo(can_disable=True)),
                ],
                fields={
                    'bcast.l1.csnp-interval': KeyInfo(can_disable=True),
                    'bcast.l1.hello-interval': KeyInfo(can_disable=True),
                    'bcast.l1.hello-interval-dr': KeyInfo(can_disable=True),
                    'bcast.l1.hello-multiplier': KeyInfo(can_disable=True),
                    'bcast.l1.metric': KeyInfo(can_disable=True),
                    'bcast.l1.priority': KeyInfo(can_disable=True),
                    'bcast.l1.psnp-interval': KeyInfo(can_disable=True),
                    'bcast.l2.csnp-interval': KeyInfo(can_disable=True),
                    'bcast.l2.hello-interval': KeyInfo(can_disable=True),
                    'bcast.l2.hello-interval-dr': KeyInfo(can_disable=True),
                    'bcast.l2.hello-multiplier': KeyInfo(can_disable=True),
                    'bcast.l2.metric': KeyInfo(can_disable=True),
                    'bcast.l2.priority': KeyInfo(can_disable=True),
                    'bcast.l2.psnp-interval': KeyInfo(can_disable=True),
                    'comment': KeyInfo(),
                    # 'copy-from': KeyInfo(write_only=True),
                    'instance': KeyInfo(),
                    'interfaces': KeyInfo(can_disable=True),
                    'levels': KeyInfo(),
                    # 'place-before': KeyInfo(write_only=True),
                    'ptp': KeyInfo(can_disable=True),
                    'ptp.hello-3way': KeyInfo(can_disable=True),
                    'ptp.hello-interval': KeyInfo(can_disable=True),
                    'ptp.hello-multiplier': KeyInfo(can_disable=True),
                    'ptp.l1.csnp-interval': KeyInfo(can_disable=True),
                    'ptp.l1.metric': KeyInfo(can_disable=True),
                    'ptp.l1.psnp-interval': KeyInfo(can_disable=True),
                    'ptp.l2.csnp-interval': KeyInfo(can_disable=True),
                    'ptp.l2.metric': KeyInfo(can_disable=True),
                    'ptp.l2.psnp-interval': KeyInfo(can_disable=True),
                },
            )),
        ],
    ),

    ('routing', 'isis', 'lsp'): APIData(
        versioned=[
            ('7.15', '>=', VersionedAPIData(
                fully_understood=True,
                has_identifier=True,
                # fixed_entries=True,
                # primary_keys=('numbers',),
                fields={
                    'age': KeyInfo(),
                    'body': KeyInfo(can_disable=True),
                    'checksum': KeyInfo(),
                    'instance': KeyInfo(),
                    'level': KeyInfo(),
                    'lsp-id': KeyInfo(),
                    'numbers': KeyInfo(),
                    'sequence': KeyInfo(),
                },
            )),
        ],
    ),

    ('routing', 'isis', 'neighbor'): APIData(
        versioned=[
            ('7.15', '>=', VersionedAPIData(
                fully_understood=True,
                has_identifier=True,
                # fixed_entries=True,
                # primary_keys=('numbers',),
                fields={
                    'instance': KeyInfo(),
                    'interface': KeyInfo(),
                    'level-type': KeyInfo(),
                    'numbers': KeyInfo(),
                    'snpa': KeyInfo(),
                    'srcid': KeyInfo(),
                    'state': KeyInfo(can_disable=True),
                },
            )),
        ],
    ),

    ('routing', 'mme'): APIData(
        versioned=[
            ('7.15', '<', VersionedAPIData(
                single_value=True,
                fully_understood=True,
                fields={
                    'bidirectional-timeout': KeyInfo(default=2),
                    'gateway-class': KeyInfo(default='none'),
                    'gateway-keepalive': KeyInfo(default='1m'),
                    'gateway-selection': KeyInfo(default='no-gateway'),
                    'origination-interval': KeyInfo(default='5s'),
                    'preferred-gateway': KeyInfo(default='0.0.0.0'),
                    'timeout': KeyInfo(default='1m'),
                    'ttl': KeyInfo(default=50),
                },
            )),
            ('7.15', '>=', 'Not supported anymore in version 7.15'),
        ],
    ),

    ('routing', 'ospf', 'area'): APIData(
        unversioned=VersionedAPIData(
            primary_keys=('name',),
            fully_understood=True,
            # versioned_fields=[
            #     ([('7.15', '>=')], 'copy-from', KeyInfo(write_only=True)),
            # ],
            fields={
                'area-id': KeyInfo(default='0.0.0.0'),
                'comment': KeyInfo(can_disable=True, remove_value=''),
                'default-cost': KeyInfo(can_disable=True),
                'disabled': KeyInfo(default=False),
                'instance': KeyInfo(required=True),
                'name': KeyInfo(),
                'no-summaries': KeyInfo(can_disable=True),
                'nssa-translator': KeyInfo(can_disable=True),
                'type': KeyInfo(default='default'),
            },
        ),
    ),

    ('routing', 'ospf', 'area', 'range'): APIData(
        unversioned=VersionedAPIData(
            primary_keys=('area', 'prefix'),
            fully_understood=True,
            # versioned_fields=[
            #     ([('7.15', '>=')], 'copy-from', KeyInfo(write_only=True)),
            # ],
            fields={
                'advertise': KeyInfo(default=True),
                'area': KeyInfo(),
                'comment': KeyInfo(can_disable=True, remove_value=''),
                'cost': KeyInfo(can_disable=True),
                'disabled': KeyInfo(default=False),
                'prefix': KeyInfo(),
            },
        ),
    ),

    ('routing', 'ospf', 'instance'): APIData(
        unversioned=VersionedAPIData(
            primary_keys=('name',),
            fully_understood=True,
            # versioned_fields=[
            #     ([('7.15', '>=')], 'copy-from', KeyInfo(write_only=True)),
            # ],
            fields={
                'comment': KeyInfo(can_disable=True, remove_value=''),
                'disabled': KeyInfo(default=False),
                'domain-id': KeyInfo(can_disable=True),
                'domain-tag': KeyInfo(can_disable=True),
                'in-filter-chain': KeyInfo(can_disable=True),
                'mpls-te-address': KeyInfo(can_disable=True),
                'mpls-te-area': KeyInfo(can_disable=True),
                'name': KeyInfo(),
                'originate-default': KeyInfo(can_disable=True),
                'out-filter-chain': KeyInfo(can_disable=True),
                'out-filter-select': KeyInfo(can_disable=True),
                'redistribute': KeyInfo(can_disable=True),
                'router-id': KeyInfo(default='main'),
                'routing-table': KeyInfo(can_disable=True),
                'use-dn': KeyInfo(can_disable=True),
                'version': KeyInfo(default=2),
                'vrf': KeyInfo(default='main'),
            },
        ),
    ),

    ('routing', 'ospf', 'interface-template'): APIData(
        unversioned=VersionedAPIData(
            fully_understood=True,
            versioned_fields=[
                # ([('7.15', '>=')], 'copy-from', KeyInfo(write_only=True)),
                # ([('7.15', '>=')], 'place-before', KeyInfo(write_only=True)),
                ([('7.10', '>=')], 'use-bfd', KeyInfo(can_disable=True, default=False)),
            ],
            fields={
                'area': KeyInfo(required=True),
                'auth': KeyInfo(can_disable=True),
                'auth-id': KeyInfo(can_disable=True),
                'auth-key': KeyInfo(can_disable=True),
                'comment': KeyInfo(can_disable=True, remove_value=''),
                'cost': KeyInfo(default=1),
                'dead-interval': KeyInfo(default='40s'),
                'disabled': KeyInfo(default=False),
                'hello-interval': KeyInfo(default='10s'),
                'instance-id': KeyInfo(default=0),
                'interfaces': KeyInfo(can_disable=True),
                'networks': KeyInfo(can_disable=True),
                'passive': KeyInfo(can_disable=True),
                'prefix-list': KeyInfo(can_disable=True),
                'priority': KeyInfo(default=128),
                'retransmit-interval': KeyInfo(default='5s'),
                'transmit-delay': KeyInfo(default='1s'),
                'type': KeyInfo(default='broadcast'),
                'vlink-neighbor-id': KeyInfo(can_disable=True),
                'vlink-transit-area': KeyInfo(can_disable=True),
            },
        ),
    ),

    ('routing', 'ospf', 'neighbor'): APIData(
        versioned=[
            ('7.15', '>=', VersionedAPIData(
                fully_understood=True,
                has_identifier=True,
                # fixed_entries=True,
                # primary_keys=('numbers',),
                fields={
                    'comment': KeyInfo(),
                    'numbers': KeyInfo(),
                },
            )),
        ],
    ),

    ('routing', 'ospf', 'static-neighbor'): APIData(
        versioned=[
            ('7', '>=', VersionedAPIData(
                fully_understood=True,
                # versioned_fields=[
                #     ([('7.15', '>=')], 'copy-from', KeyInfo(write_only=True)),
                # ],
                fields={
                    'address': KeyInfo(required=True),
                    'area': KeyInfo(required=True),
                    'comment': KeyInfo(can_disable=True, remove_value=''),
                    'disabled': KeyInfo(default=False),
                    'instance-id': KeyInfo(default=0),
                    'poll-interval': KeyInfo(default='2m'),
                },
            )),
        ],
    ),

    ('routing', 'ospf-v3', 'area'): APIData(
        versioned=[
            ('7.15', '<', VersionedAPIData(
                unknown_mechanism=True,
                fields={
                    'area-id': KeyInfo(),
                    'default': KeyInfo(),
                    'disabled': KeyInfo(),
                    'instance': KeyInfo(),
                    'name': KeyInfo(),
                    'type': KeyInfo(),
                },
            )),
            ('7.15', '>=', 'Not supported anymore in version 7.15'),
        ],
    ),

    ('routing', 'ospf-v3', 'instance'): APIData(
        versioned=[
            ('7.15', '<', VersionedAPIData(
                unknown_mechanism=True,
                fields={
                    'default': KeyInfo(),
                    'disabled': KeyInfo(),
                    'distribute-default': KeyInfo(),
                    'metric-bgp': KeyInfo(),
                    'metric-connected': KeyInfo(),
                    'metric-default': KeyInfo(),
                    'metric-other-ospf': KeyInfo(),
                    'metric-rip': KeyInfo(),
                    'metric-static': KeyInfo(),
                    'name': KeyInfo(),
                    'redistribute-bgp': KeyInfo(),
                    'redistribute-connected': KeyInfo(),
                    'redistribute-other-ospf': KeyInfo(),
                    'redistribute-rip': KeyInfo(),
                    'redistribute-static': KeyInfo(),
                    'router-id': KeyInfo(),
                },
            )),
            ('7.15', '>=', 'Not supported anymore in version 7.15'),
        ],
    ),

    ('routing', 'pimsm', 'bsr', 'candidate'): APIData(
        versioned=[
            ('7.15', '>=', VersionedAPIData(
                fully_understood=True,
                fields={
                    'address': KeyInfo(),
                    # 'copy-from': KeyInfo(write_only=True),
                    'disabled': KeyInfo(),
                    'hashmask-length': KeyInfo(),
                    'instance': KeyInfo(),
                    'priority': KeyInfo(),
                    'scope4': KeyInfo(),
                    'scope6': KeyInfo(),
                },
            )),
        ],
    ),

    ('routing', 'pimsm', 'bsr', 'rp-candidate'): APIData(
        versioned=[
            ('7.15', '>=', VersionedAPIData(
                fully_understood=True,
                fields={
                    'address': KeyInfo(),
                    # 'copy-from': KeyInfo(write_only=True),
                    'disabled': KeyInfo(),
                    'group': KeyInfo(),
                    'holdtime': KeyInfo(),
                    'instance': KeyInfo(),
                    'priority': KeyInfo(),
                },
            )),
        ],
    ),

    ('routing', 'pimsm', 'igmp-interface-template'): APIData(
        versioned=[
            ('7.15', '>=', VersionedAPIData(
                fully_understood=True,
                has_identifier=True,
                # fixed_entries=True,
                # primary_keys=('numbers',),
                fields={
                    'instance': KeyInfo(),
                    'interfaces': KeyInfo(),
                    'numbers': KeyInfo(),
                },
            )),
        ],
    ),

    ('routing', 'pimsm', 'instance'): APIData(
        unversioned=VersionedAPIData(
            primary_keys=('name',),
            fully_understood=True,
            # versioned_fields=[
            #     ([('7.15', '>=')], 'copy-from', KeyInfo(write_only=True)),
            # ],
            fields={
                'afi': KeyInfo(default='ipv4'),
                'bsm-forward-back': KeyInfo(),
                'crp-advertise-contained': KeyInfo(),
                'disabled': KeyInfo(default=False),
                'name': KeyInfo(),
                'rp-hash-mask-length': KeyInfo(),
                'rp-static-override': KeyInfo(default=False),
                'ssm-range': KeyInfo(),
                'switch-to-spt': KeyInfo(default=True),
                'switch-to-spt-bytes': KeyInfo(default=0),
                'switch-to-spt-interval': KeyInfo(),
                'vrf': KeyInfo(default='main'),
            },
        ),
    ),

    ('routing', 'pimsm', 'interface-template'): APIData(
        unversioned=VersionedAPIData(
            fully_understood=True,
            # versioned_fields=[
            #     ([('7.15', '>=')], 'copy-from', KeyInfo(write_only=True)),
            #     ([('7.15', '>=')], 'place-before', KeyInfo(write_only=True)),
            # ],
            fields={
                'disabled': KeyInfo(default=False),
                'hello-delay': KeyInfo(default='5s'),
                'hello-period': KeyInfo(default='30s'),
                'instance': KeyInfo(required=True),
                'interfaces': KeyInfo(can_disable=True),
                'join-prune-period': KeyInfo(default='1m'),
                'join-tracking-support': KeyInfo(default=True),
                'override-interval': KeyInfo(default='2s500ms'),
                'priority': KeyInfo(default=1),
                'propagation-delay': KeyInfo(default='500ms'),
                'source-addresses': KeyInfo(can_disable=True),
            },
        ),
    ),

    ('routing', 'pimsm', 'static-rp'): APIData(
        versioned=[
            ('7.15', '>=', VersionedAPIData(
                fully_understood=True,
                versioned_fields=[
                    ([('7.20.5', '>=')], 'comment', KeyInfo()),
                ],
                fields={
                    'address': KeyInfo(),
                    # 'copy-from': KeyInfo(write_only=True),
                    'disabled': KeyInfo(),
                    'group': KeyInfo(),
                    'instance': KeyInfo(),
                },
            )),
        ],
    ),

    ('routing', 'rip'): APIData(
        versioned=[
            ('7.15', '<', VersionedAPIData(
                single_value=True,
                fully_understood=True,
                fields={
                    'distribute-default': KeyInfo(default='never'),
                    'garbage-timer': KeyInfo(default='2m'),
                    'metric-bgp': KeyInfo(default=1),
                    'metric-connected': KeyInfo(default=1),
                    'metric-default': KeyInfo(default=1),
                    'metric-ospf': KeyInfo(default=1),
                    'metric-static': KeyInfo(default=1),
                    'redistribute-bgp': KeyInfo(default=False),
                    'redistribute-connected': KeyInfo(default=False),
                    'redistribute-ospf': KeyInfo(default=False),
                    'redistribute-static': KeyInfo(default=False),
                    'routing-table': KeyInfo(default='main'),
                    'timeout-timer': KeyInfo(default='3m'),
                    'update-timer': KeyInfo(default='30s'),
                },
            )),
            ('7.15', '>=', 'Not supported anymore in version 7.15'),
        ],
    ),

    ('routing', 'rip', 'instance'): APIData(
        versioned=[
            ('7.15', '>=', VersionedAPIData(
                fully_understood=True,
                fields={
                    'afi': KeyInfo(),
                    # 'copy-from': KeyInfo(write_only=True),
                    'disabled': KeyInfo(),
                    'in-filter-chain': KeyInfo(can_disable=True),
                    'name': KeyInfo(),
                    'originate-default': KeyInfo(can_disable=True),
                    'out-filter-chain': KeyInfo(can_disable=True),
                    'out-filter-select': KeyInfo(can_disable=True),
                    'redistribute': KeyInfo(can_disable=True),
                    'route-gc-timeout': KeyInfo(),
                    'route-timeout': KeyInfo(),
                    'routing-table': KeyInfo(can_disable=True),
                    'update-interval': KeyInfo(),
                    'vrf': KeyInfo(),
                },
            )),
        ],
    ),

    ('routing', 'rip', 'interface-template'): APIData(
        versioned=[
            ('7.15', '>=', VersionedAPIData(
                fully_understood=True,
                fields={
                    # 'copy-from': KeyInfo(write_only=True),
                    'cost': KeyInfo(),
                    'disabled': KeyInfo(),
                    'instance': KeyInfo(),
                    'interfaces': KeyInfo(can_disable=True),
                    'key-chain': KeyInfo(can_disable=True),
                    'mode': KeyInfo(can_disable=True),
                    'password': KeyInfo(can_disable=True),
                    'poison-reverse': KeyInfo(),
                    'source-addresses': KeyInfo(can_disable=True),
                    'split-horizon': KeyInfo(),
                    'use-bfd': KeyInfo(can_disable=True),
                },
            )),
        ],
    ),

    ('routing', 'rip', 'keys'): APIData(
        versioned=[
            ('7.15', '>=', VersionedAPIData(
                fully_understood=True,
                fields={
                    'chain': KeyInfo(),
                    # 'copy-from': KeyInfo(write_only=True),
                    'disabled': KeyInfo(),
                    'key': KeyInfo(),
                    'key-id': KeyInfo(),
                    'valid-from': KeyInfo(),
                    'valid-till': KeyInfo(),
                },
            )),
        ],
    ),

    ('routing', 'rip', 'static-neighbor'): APIData(
        versioned=[
            ('7.15', '>=', VersionedAPIData(
                fully_understood=True,
                fields={
                    'address': KeyInfo(),
                    # 'copy-from': KeyInfo(write_only=True),
                    'disabled': KeyInfo(),
                    'instance': KeyInfo(),
                },
            )),
        ],
    ),

    ('routing', 'ripng'): APIData(
        unversioned=VersionedAPIData(
            single_value=True,
            fully_understood=True,
            fields={
                'distribute-default': KeyInfo(default='never'),
                'garbage-timer': KeyInfo(default='2m'),
                'metric-bgp': KeyInfo(default=1),
                'metric-connected': KeyInfo(default=1),
                'metric-default': KeyInfo(default=1),
                'metric-ospf': KeyInfo(default=1),
                'metric-static': KeyInfo(default=1),
                'redistribute-bgp': KeyInfo(default=False),
                'redistribute-connected': KeyInfo(default=False),
                'redistribute-ospf': KeyInfo(default=False),
                'redistribute-static': KeyInfo(default=False),
                'timeout-timer': KeyInfo(default='3m'),
                'update-timer': KeyInfo(default='30s'),
            },
        ),
    ),

    ('routing', 'route'): APIData(
        versioned=[
            ('7.15', '>=', VersionedAPIData(
                fully_understood=True,
                has_identifier=True,
                # fixed_entries=True,
                # primary_keys=('numbers',),
                fields={
                    'comment': KeyInfo(),
                    'disabled': KeyInfo(),
                    'numbers': KeyInfo(),
                },
            )),
        ],
    ),

    ('routing', 'route', 'rule'): APIData(
        versioned=[
            ('7.15', '>=', VersionedAPIData(
                fully_understood=True,
                has_identifier=True,
                # fixed_entries=True,
                # primary_keys=('numbers',),
                fields={
                    'action': KeyInfo(),
                    'comment': KeyInfo(),
                    'disabled': KeyInfo(),
                    'dst-address': KeyInfo(can_disable=True),
                    'interface': KeyInfo(can_disable=True),
                    'min-prefix': KeyInfo(can_disable=True),
                    'numbers': KeyInfo(),
                    'routing-mark': KeyInfo(can_disable=True),
                    'src-address': KeyInfo(can_disable=True),
                    'table': KeyInfo(),
                },
            )),
        ],
    ),

    ('routing', 'rpki'): APIData(
        versioned=[
            ('7.15', '>=', VersionedAPIData(
                fully_understood=True,
                fields={
                    'address': KeyInfo(),
                    'comment': KeyInfo(),
                    # 'copy-from': KeyInfo(write_only=True),
                    'disabled': KeyInfo(),
                    'expire-interval': KeyInfo(),
                    'group': KeyInfo(),
                    'port': KeyInfo(),
                    'preference': KeyInfo(),
                    'refresh-interval': KeyInfo(),
                    'retry-interval': KeyInfo(),
                    'vrf': KeyInfo(),
                },
            )),
        ],
    ),

    ('routing', 'rule'): APIData(
        versioned=[
            ('7', '>=', VersionedAPIData(
                fully_understood=True,
                # versioned_fields=[
                #     ([('7.15', '>=')], 'copy-from', KeyInfo(write_only=True)),
                #     ([('7.15', '>=')], 'place-before', KeyInfo(write_only=True)),
                # ],
                fields={
                    'action': KeyInfo(can_disable=True),
                    'comment': KeyInfo(can_disable=True, remove_value=''),
                    'disabled': KeyInfo(default=False),
                    'dst-address': KeyInfo(can_disable=True),
                    'interface': KeyInfo(can_disable=True),
                    'min-prefix': KeyInfo(can_disable=True),
                    'routing-mark': KeyInfo(can_disable=True),
                    'src-address': KeyInfo(can_disable=True),
                    'table': KeyInfo(can_disable=True),
                },
            )),
        ],
    ),

    ('routing', 'settings'): APIData(
        versioned=[
            ('7.15', '>=', VersionedAPIData(
                fixed_entries=True,
                single_value=True,
                fully_understood=True,
                versioned_fields=[
                    ([('7.21', '>=')], 'check-gateway-ping-count', KeyInfo()),
                    ([('7.21', '>=')], 'check-gateway-ping-interval', KeyInfo()),
                    ([('7.21', '>=')], 'check-gateway-ping-timeout', KeyInfo()),
                    ([('7.19', '>=')], 'connected-in-chain', KeyInfo()),
                    ([('7.19', '>=')], 'dynamic-in-chain', KeyInfo()),
                ],
                fields={
                    'single-process': KeyInfo(),
                },
            )),
        ],
    ),

    ('routing', 'table'): APIData(
        versioned=[
            ('7', '>=', VersionedAPIData(
                fully_understood=True,
                # versioned_fields=[
                #     ([('7.15', '>=')], 'copy-from', KeyInfo(write_only=True)),
                # ],
                fields={
                    'comment': KeyInfo(can_disable=True, remove_value=''),
                    'disabled': KeyInfo(default=False),
                    'fib': KeyInfo(can_disable=True),
                    'name': KeyInfo(required=True),
                },
            )),
        ],
    ),

    ('rsync-daemon',): APIData(
        versioned=[
            ('7.15', '>=', VersionedAPIData(
                fixed_entries=True,
                single_value=True,
                fully_understood=True,
                fields={
                    'enabled': KeyInfo(),
                },
            )),
            ('7.16', '>=', 'Not supported anymore in version 7.16'),
        ],
    ),

    ('snmp',): APIData(
        unversioned=VersionedAPIData(
            fixed_entries=True,
            single_value=True,
            fully_understood=True,
            versioned_fields=[
                ([('7.10', '<')], 'engine-id', KeyInfo(default='')),
                ([('7.10', '>=')], 'engine-id', KeyInfo(read_only=True)),
                ([('7.10', '>=')], 'engine-id-suffix', KeyInfo(default='')),
                ([('7.3', '>=')], 'vrf', KeyInfo(default='main')),
            ],
            fields={
                'contact': KeyInfo(default=''),
                'enabled': KeyInfo(default=False),
                'location': KeyInfo(default=''),
                'src-address': KeyInfo(default='::'),
                'trap-community': KeyInfo(default='public'),
                'trap-generators': KeyInfo(default='temp-exception'),
                'trap-interfaces': KeyInfo(default=''),
                'trap-target': KeyInfo(default=''),
                'trap-version': KeyInfo(default=1),
            },
        ),
    ),

    ('snmp', 'community'): APIData(
        unversioned=VersionedAPIData(
            primary_keys=('name',),
            fully_understood=True,
            # versioned_fields=[
            #     ([('7.15', '>=')], 'copy-from', KeyInfo(write_only=True)),
            # ],
            fields={
                'addresses': KeyInfo(default='::/0'),
                'authentication-password': KeyInfo(default=''),
                'authentication-protocol': KeyInfo(default='MD5'),
                'comment': KeyInfo(can_disable=True, remove_value=''),
                'default': KeyInfo(read_only=True),
                'disabled': KeyInfo(default=False),
                'encryption-password': KeyInfo(default=''),
                'encryption-protocol': KeyInfo(default='DES'),
                'name': KeyInfo(required=True),
                'read-access': KeyInfo(default=True),
                'security': KeyInfo(default='none'),
                'write-access': KeyInfo(default=False),
            },
        ),
    ),

    ('special-login',): APIData(
        versioned=[
            ('7.15', '>=', VersionedAPIData(
                fully_understood=True,
                fields={
                    'channel': KeyInfo(),
                    # 'copy-from': KeyInfo(write_only=True),
                    'disabled': KeyInfo(),
                    'port': KeyInfo(),
                    'user': KeyInfo(),
                },
            )),
        ],
    ),

    ('system', 'clock'): APIData(
        unversioned=VersionedAPIData(
            fixed_entries=True,
            single_value=True,
            fully_understood=True,
            versioned_fields=[
                ([('7.15', '<')], 'gmt-offset', KeyInfo()),
            ],
            fields={
                'date': KeyInfo(),
                'time': KeyInfo(),
                'time-zone-autodetect': KeyInfo(default=True),
                'time-zone-name': KeyInfo(default='manual'),
            },
        ),
    ),

    ('system', 'clock', 'manual'): APIData(
        unversioned=VersionedAPIData(
            fixed_entries=True,
            single_value=True,
            fully_understood=True,
            fields={
                'dst-delta': KeyInfo(default='00:00'),
                'dst-end': KeyInfo(default='jan/01/1970 00:00:00'),
                'dst-start': KeyInfo(default='jan/01/1970 00:00:00'),
                'time-zone': KeyInfo(default='+00:00'),
            },
        ),
    ),

    ('system', 'console'): APIData(
        versioned=[
            ('7.15', '>=', VersionedAPIData(
                fully_understood=True,
                fields={
                    'channel': KeyInfo(),
                    # 'copy-from': KeyInfo(write_only=True),
                    'disabled': KeyInfo(),
                    'port': KeyInfo(),
                    'term': KeyInfo(),
                },
            )),
        ],
    ),

    ('system', 'console', 'screen'): APIData(
        versioned=[
            ('7.15.3', '>=', VersionedAPIData(
                fixed_entries=True,
                single_value=True,
                fully_understood=True,
                fields={
                    'blank-interval': KeyInfo(),
                    'line-count': KeyInfo(),
                },
            )),
            ('7.16.1', '>=', 'Not supported anymore in version 7.16.1'),
        ],
    ),

    ('system', 'gps'): APIData(
        versioned=[
            ('7.15', '>=', VersionedAPIData(
                fixed_entries=True,
                single_value=True,
                fully_understood=True,
                fields={
                    'channel': KeyInfo(),
                    'coordinate-format': KeyInfo(),
                    'enabled': KeyInfo(),
                    'init-channel': KeyInfo(),
                    'init-string': KeyInfo(),
                    'port': KeyInfo(),
                    'set-system-time': KeyInfo(),
                },
            )),
        ],
    ),

    ('system', 'hardware'): APIData(
        versioned=[
            ('7.15.3', '>=', VersionedAPIData(
                fixed_entries=True,
                single_value=True,
                fully_understood=True,
                fields={
                    'multi-cpu': KeyInfo(),
                },
            )),
            ('7.16.1', '>=', 'Not supported anymore in version 7.16.1'),
        ],
    ),

    ('system', 'health'): APIData(
        versioned=[
            ('7.15.3', '>=', VersionedAPIData(
                fixed_entries=True,
                single_value=True,
                fully_understood=True,
                fields={
                    'state-after-reboot': KeyInfo(),
                },
            )),
            ('7.16.1', '>=', 'Not supported anymore in version 7.16.1'),
        ],
    ),

    ('system', 'health', 'settings'): APIData(
        versioned=[
            ('7.14', '<', VersionedAPIData(
                fixed_entries=True,
                single_value=True,
                fully_understood=True,
                fields={
                    'cpu-overtemp-check': KeyInfo(),
                    'cpu-overtemp-startup-delay': KeyInfo(),
                    'cpu-overtemp-threshold': KeyInfo(),
                    'fan-control-interval': KeyInfo(can_disable=True, default='30s'),
                    'fan-full-speed-temp': KeyInfo(default=65),
                    'fan-min-speed-percent': KeyInfo(default=0),
                    'fan-mode': KeyInfo(),
                    'fan-on-threshold': KeyInfo(),
                    'fan-switch': KeyInfo(),
                    'fan-target-temp': KeyInfo(default=58),
                    'use-fan': KeyInfo(),
                },
            )),
            ('7.14', '>=', VersionedAPIData(
                fixed_entries=True,
                single_value=True,
                fully_understood=True,
                fields={
                    'cpu-overtemp-check': KeyInfo(),
                    'cpu-overtemp-startup-delay': KeyInfo(),
                    'cpu-overtemp-threshold': KeyInfo(),
                    'fan-control-interval': KeyInfo(default=30),
                    'fan-full-speed-temp': KeyInfo(default=65),
                    'fan-min-speed-percent': KeyInfo(default=12),
                    'fan-mode': KeyInfo(),
                    'fan-on-threshold': KeyInfo(),
                    'fan-switch': KeyInfo(),
                    'fan-target-temp': KeyInfo(default=58),
                    'use-fan': KeyInfo(),
                },
            )),
        ],
    ),

    ('system', 'identity'): APIData(
        unversioned=VersionedAPIData(
            fixed_entries=True,
            single_value=True,
            fully_understood=True,
            fields={
                'name': KeyInfo(default='Mikrotik'),
            },
        ),
    ),

    ('system', 'leds'): APIData(
        versioned=[
            ('7.15', '>=', VersionedAPIData(
                fully_understood=True,
                fields={
                    # 'copy-from': KeyInfo(write_only=True),
                    'disabled': KeyInfo(),
                    'interface': KeyInfo(),
                    'leds': KeyInfo(),
                    'modem-signal-threshold': KeyInfo(),
                    'type': KeyInfo(),
                },
            )),
        ],
    ),

    ('system', 'leds', 'settings'): APIData(
        unversioned=VersionedAPIData(
            fixed_entries=True,
            single_value=True,
            fully_understood=True,
            fields={
                'all-leds-off': KeyInfo(default='never'),
            },
        ),
    ),

    ('system', 'logging'): APIData(
        unversioned=VersionedAPIData(
            fully_understood=True,
            versioned_fields=[
                # ([('7.15', '>=')], 'copy-from', KeyInfo(write_only=True)),
                ([('7.17', '>=')], 'regex', KeyInfo()),
            ],
            fields={
                'action': KeyInfo(default='memory'),
                'disabled': KeyInfo(default=False),
                'prefix': KeyInfo(default=''),
                'topics': KeyInfo(default=''),
            },
        ),
    ),

    ('system', 'logging', 'action'): APIData(
        unversioned=VersionedAPIData(
            primary_keys=('name',),
            fully_understood=True,
            versioned_fields=[
                ([('7.18', '<')], 'bsd-syslog', KeyInfo(default=False)),
                ([('7.18', '>=')], 'cef-event-delimiter', KeyInfo(default='\r\n')),
                # ([('7.15', '>=')], 'copy-from', KeyInfo(write_only=True)),
                ([('7.18', '>=')], 'remote-log-format', KeyInfo(default='default')),
                ([('7.18', '>=')], 'remote-protocol', KeyInfo(default='udp')),
                ([('7.19.6', '>=')], 'vrf', KeyInfo(default='main')),
            ],
            fields={
                'comment': KeyInfo(can_disable=True, remove_value=''),
                'disk-file-count': KeyInfo(default=2),
                'disk-file-name': KeyInfo(default='log'),
                'disk-lines-per-file': KeyInfo(default=1000),
                'disk-stop-on-full': KeyInfo(default=False),
                'email-start-tls': KeyInfo(default=False),
                'email-to': KeyInfo(default=''),
                'memory-lines': KeyInfo(default=1000),
                'memory-stop-on-full': KeyInfo(default=False),
                'name': KeyInfo(),
                'remember': KeyInfo(default=True),
                'remote': KeyInfo(default='0.0.0.0'),
                'remote-port': KeyInfo(default=514),
                'src-address': KeyInfo(default='0.0.0.0'),
                'syslog-facility': KeyInfo(default='daemon'),
                'syslog-severity': KeyInfo(default='auto'),
                'syslog-time-format': KeyInfo(default='bsd-syslog'),
                'target': KeyInfo(required=True),
            },
        ),
    ),

    ('system', 'note'): APIData(
        unversioned=VersionedAPIData(
            fixed_entries=True,
            single_value=True,
            fully_understood=True,
            versioned_fields=[
                ([('7.14', '>=')], 'show-at-cli-login', KeyInfo(default=False)),
            ],
            fields={
                'note': KeyInfo(default=''),
                'show-at-login': KeyInfo(default=True),
            },
        ),
    ),

    ('system', 'ntp', 'client'): APIData(
        unversioned=VersionedAPIData(
            fixed_entries=True,
            single_value=True,
            fully_understood=True,
            versioned_fields=[
                ([('7.15', '<')], 'primary-ntp', KeyInfo(default='0.0.0.0')),
                ([('7.15', '<')], 'secondary-ntp', KeyInfo(default='0.0.0.0')),
                ([('7.15', '<')], 'server-dns-names', KeyInfo(default='')),
            ],
            fields={
                'enabled': KeyInfo(default=False),
                'mode': KeyInfo(default='unicast'),
                'servers': KeyInfo(default=''),
                'vrf': KeyInfo(default='main'),
            },
        ),
    ),

    ('system', 'ntp', 'client', 'servers'): APIData(
        unversioned=VersionedAPIData(
            primary_keys=('address',),
            fully_understood=True,
            # versioned_fields=[
            #     ([('7.15', '>=')], 'copy-from', KeyInfo(write_only=True)),
            # ],
            fields={
                'address': KeyInfo(),
                'auth-key': KeyInfo(default='none'),
                'comment': KeyInfo(can_disable=True, remove_value=''),
                'disabled': KeyInfo(default=False),
                'iburst': KeyInfo(default=True),
                'max-poll': KeyInfo(default=10),
                'min-poll': KeyInfo(default=6),
            },
        ),
    ),

    ('system', 'ntp', 'key'): APIData(
        versioned=[
            ('7.15', '>=', VersionedAPIData(
                fully_understood=True,
                fields={
                    'comment': KeyInfo(),
                    # 'copy-from': KeyInfo(write_only=True),
                    'key-id': KeyInfo(),
                    'key-val': KeyInfo(),
                },
            )),
        ],
    ),

    ('system', 'ntp', 'server'): APIData(
        unversioned=VersionedAPIData(
            fixed_entries=True,
            single_value=True,
            fully_understood=True,
            fields={
                'auth-key': KeyInfo(default='none'),
                'broadcast': KeyInfo(default=False),
                'broadcast-addresses': KeyInfo(default=''),
                'enabled': KeyInfo(default=False),
                'local-clock-stratum': KeyInfo(default=5),
                'manycast': KeyInfo(default=False),
                'multicast': KeyInfo(default=False),
                'use-local-clock': KeyInfo(default=False),
                'vrf': KeyInfo(default='main'),
            },
        ),
    ),

    ('system', 'package', 'local-update'): APIData(
        versioned=[
            ('7.17', '>=', VersionedAPIData(
                fully_understood=True,
                has_identifier=True,
                # fixed_entries=True,
                # primary_keys=('numbers',),
                fields={
                    'download': KeyInfo(),
                    'numbers': KeyInfo(),
                },
            )),
        ],
    ),

    ('system', 'package', 'local-update', 'mirror'): APIData(
        versioned=[
            ('7.17', '>=', VersionedAPIData(
                fixed_entries=True,
                single_value=True,
                fully_understood=True,
                fields={
                    'check-interval': KeyInfo(),
                    'enabled': KeyInfo(),
                    'password': KeyInfo(),
                    'primary-server': KeyInfo(),
                    'secondary-server': KeyInfo(),
                    'user': KeyInfo(),
                },
            )),
        ],
    ),

    ('system', 'package', 'local-update', 'update-package-source'): APIData(
        versioned=[
            ('7.17', '>=', VersionedAPIData(
                fully_understood=True,
                fields={
                    'address': KeyInfo(),
                    # 'copy-from': KeyInfo(write_only=True),
                    'user': KeyInfo(),
                },
            )),
        ],
    ),

    ('system', 'package', 'update'): APIData(
        unversioned=VersionedAPIData(
            fixed_entries=True,
            single_value=True,
            fully_understood=True,
            fields={
                'channel': KeyInfo(default='stable'),
                'installed-version': KeyInfo(read_only=True),
                'latest-version': KeyInfo(read_only=True),
                'status': KeyInfo(read_only=True),
            },
        ),
    ),

    ('system', 'resource', 'hardware', 'usb-settings'): APIData(
        versioned=[
            ('7.20', '>=', VersionedAPIData(
                fixed_entries=True,
                single_value=True,
                fully_understood=True,
                fields={
                    'authorization': KeyInfo(),
                },
            )),
        ],
    ),

    ('system', 'resource', 'irq'): APIData(
        unversioned=VersionedAPIData(
            fully_understood=True,
            has_identifier=True,
            # fixed_entries=True,
            # primary_keys=('numbers',),
            fields={
                'cpu': KeyInfo(),
                'numbers': KeyInfo(),
            },
        ),
    ),

    ('system', 'resource', 'irq', 'rps'): APIData(
        unversioned=VersionedAPIData(
            primary_keys=('name',),
            fixed_entries=True,
            fully_understood=True,
            versioned_fields=[
                ([('7.15', '>=')], 'numbers', KeyInfo()),
            ],
            fields={
                'disabled': KeyInfo(default=False),
                'name': KeyInfo(),
            },
        ),
    ),

    ('system', 'resource', 'usb'): APIData(
        versioned=[
            ('7.15', '>=', VersionedAPIData(
                fully_understood=True,
                has_identifier=True,
                # fixed_entries=True,
                # primary_keys=('numbers',),
                fields={
                    'device': KeyInfo(),
                    'device-id': KeyInfo(),
                    'name': KeyInfo(),
                    'numbers': KeyInfo(),
                    'ports': KeyInfo(),
                    'serial-number': KeyInfo(),
                    'speed': KeyInfo(),
                    'usb-version': KeyInfo(),
                    'vendor': KeyInfo(),
                    'vendor-id': KeyInfo(),
                },
            )),
            ('7.20', '>=', 'Not supported anymore in version 7.20'),
        ],
    ),

    ('system', 'resource', 'usb', 'settings'): APIData(
        versioned=[
            ('7.15', '>=', VersionedAPIData(
                fixed_entries=True,
                single_value=True,
                fully_understood=True,
                fields={
                    'authorization': KeyInfo(),
                },
            )),
            ('7.20', '>=', 'Not supported anymore in version 7.20'),
        ],
    ),

    ('system', 'routerboard', 'mode-button'): APIData(
        versioned=[
            ('7.15', '>=', VersionedAPIData(
                fixed_entries=True,
                single_value=True,
                fully_understood=True,
                fields={
                    'enabled': KeyInfo(),
                    'hold-time': KeyInfo(),
                    'on-event': KeyInfo(),
                },
            )),
        ],
    ),

    ('system', 'routerboard', 'reset-button'): APIData(
        versioned=[
            ('7.15', '>=', VersionedAPIData(
                fixed_entries=True,
                single_value=True,
                fully_understood=True,
                fields={
                    'enabled': KeyInfo(),
                    'hold-time': KeyInfo(),
                    'on-event': KeyInfo(),
                },
            )),
        ],
    ),

    ('system', 'routerboard', 'settings'): APIData(
        unversioned=VersionedAPIData(
            fixed_entries=True,
            single_value=True,
            fully_understood=True,
            versioned_fields=[
                ([('7.15', '>=')], 'boot-os', KeyInfo(default='router-os')),
                ([('7.15', '>=')], 'cpu-mode', KeyInfo()),
                ([('7.15', '>=')], 'disable-pci', KeyInfo()),
                ([('7.15', '>=')], 'etherboot-port', KeyInfo()),
                ([('7.15', '>=')], 'gpio-function', KeyInfo()),
                ([('7.15', '>=')], 'init-delay', KeyInfo()),
                ([('7.15', '<')], 'memory-frequency', KeyInfo()),
                ([('7.15', '>=')], 'regulatory-domain-ce', KeyInfo()),
            ],
            fields={
                'auto-upgrade': KeyInfo(default=False),
                'baud-rate': KeyInfo(default=115200),
                'boot-delay': KeyInfo(default='2s'),
                'boot-device': KeyInfo(default='nand-if-fail-then-ethernet'),
                'boot-protocol': KeyInfo(default='bootp'),
                'cpu-frequency': KeyInfo(),
                'enable-jumper-reset': KeyInfo(default=True),
                'enter-setup-on': KeyInfo(),  # default seems to differ per device but documentation say it's 'delete-key' not that it depends on model
                'force-backup-booter': KeyInfo(default=False),
                'preboot-etherboot': KeyInfo(default='disabled'),
                'preboot-etherboot-server': KeyInfo(default='any'),
                'protected-routerboot': KeyInfo(default='disabled'),
                'reformat-hold-button': KeyInfo(default='20s'),
                'reformat-hold-button-max': KeyInfo(default='10m'),
                'silent-boot': KeyInfo(default=False),
            },
        ),
    ),

    ('system', 'routerboard', 'usb'): APIData(
        versioned=[
            ('7.15', '>=', VersionedAPIData(
                fixed_entries=True,
                single_value=True,
                fully_understood=True,
                fields={
                    'type': KeyInfo(),
                    'usb-mode': KeyInfo(),
                },
            )),
        ],
    ),

    ('system', 'routerboard', 'wps-button'): APIData(
        versioned=[
            ('7.15', '>=', VersionedAPIData(
                fixed_entries=True,
                single_value=True,
                fully_understood=True,
                fields={
                    'enabled': KeyInfo(),
                    'hold-time': KeyInfo(),
                    'on-event': KeyInfo(),
                },
            )),
        ],
    ),

    ('system', 'scheduler'): APIData(
        unversioned=VersionedAPIData(
            primary_keys=('name',),
            fully_understood=True,
            # versioned_fields=[
            #     ([('7.15', '>=')], 'copy-from', KeyInfo(write_only=True)),
            # ],
            fields={
                'comment': KeyInfo(can_disable=True, remove_value=''),
                'disabled': KeyInfo(default=False),
                'interval': KeyInfo(default='0s'),
                'name': KeyInfo(),
                'on-event': KeyInfo(default=''),
                'policy': KeyInfo(default='ftp,reboot,read,write,policy,test,password,sniff,sensitive,romon'),
                'start-date': KeyInfo(),
                'start-time': KeyInfo(),
            },
        ),
    ),

    ('system', 'script'): APIData(
        unversioned=VersionedAPIData(
            primary_keys=('name',),
            fully_understood=True,
            # versioned_fields=[
            #     ([('7.15', '>=')], 'copy-from', KeyInfo(write_only=True)),
            # ],
            fields={
                'comment': KeyInfo(can_disable=True, remove_value=''),
                'dont-require-permissions': KeyInfo(default=False),
                'name': KeyInfo(),
                'owner': KeyInfo(),
                'policy': KeyInfo(default='ftp,reboot,read,write,policy,test,password,sniff,sensitive,romon'),
                'source': KeyInfo(default=''),
            },
        ),
    ),

    ('system', 'script', 'environment'): APIData(
        versioned=[
            ('7.15', '>=', VersionedAPIData(
                fully_understood=True,
                has_identifier=True,
                # fixed_entries=True,
                # primary_keys=('numbers',),
                fields={
                    'comment': KeyInfo(),
                    'numbers': KeyInfo(),
                    'value': KeyInfo(),
                },
            )),
        ],
    ),

    ('system', 'script', 'job'): APIData(
        versioned=[
            ('7.15', '>=', VersionedAPIData(
                fully_understood=True,
                has_identifier=True,
                # fixed_entries=True,
                # primary_keys=('numbers',),
                fields={
                    'comment': KeyInfo(),
                    'numbers': KeyInfo(),
                    'started': KeyInfo(),
                    'type': KeyInfo(),
                },
            )),
        ],
    ),

    ('system', 'swos'): APIData(
        versioned=[
            ('7.15', '>=', VersionedAPIData(
                fixed_entries=True,
                single_value=True,
                fully_understood=True,
                fields={
                    'address-acquisition-mode': KeyInfo(),
                    'allow-from': KeyInfo(),
                    'allow-from-ports': KeyInfo(),
                    'allow-from-vlan': KeyInfo(),
                    'identity': KeyInfo(),
                    'static-ip-address': KeyInfo(),
                },
            )),
        ],
    ),

    ('system', 'upgrade'): APIData(
        versioned=[
            ('7.15', '>=', VersionedAPIData(
                fully_understood=True,
                has_identifier=True,
                # fixed_entries=True,
                # primary_keys=('numbers',),
                fields={
                    'download': KeyInfo(),
                    'numbers': KeyInfo(),
                },
            )),
            ('7.17', '>=', 'Not supported anymore in version 7.17'),
        ],
    ),

    ('system', 'upgrade', 'mirror'): APIData(
        versioned=[
            ('7.17', '<', VersionedAPIData(
                fixed_entries=True,
                single_value=True,
                fully_understood=True,
                versioned_fields=[
                    ([('7.15', '>=')], 'password', KeyInfo()),
                ],
                fields={
                    'check-interval': KeyInfo(default='1d'),
                    'enabled': KeyInfo(default=False),
                    'primary-server': KeyInfo(default='0.0.0.0'),
                    'secondary-server': KeyInfo(default='0.0.0.0'),
                    'user': KeyInfo(default=''),
                },
            )),
            ('7.17', '>=', 'Not supported anymore in version 7.17'),
        ],
    ),

    ('system', 'upgrade', 'upgrade-package-source'): APIData(
        versioned=[
            ('7.15', '>=', VersionedAPIData(
                fully_understood=True,
                fields={
                    'address': KeyInfo(),
                    # 'copy-from': KeyInfo(write_only=True),
                    'user': KeyInfo(),
                },
            )),
            ('7.17', '>=', 'Not supported anymore in version 7.17'),
        ],
    ),

    ('system', 'ups'): APIData(
        unversioned=VersionedAPIData(
            primary_keys=('name',),
            fully_understood=True,
            # versioned_fields=[
            #     ([('7.15', '>=')], 'copy-from', KeyInfo(write_only=True)),
            # ],
            fields={
                'alarm-setting': KeyInfo(default='immediate'),
                'check-capabilities': KeyInfo(can_disable=True, remove_value=True),
                'comment': KeyInfo(can_disable=True, remove_value=''),
                'disabled': KeyInfo(default=True),
                'min-runtime': KeyInfo(default='never'),
                'name': KeyInfo(),
                'offline-time': KeyInfo(default='0s'),
                'port': KeyInfo(required=True),
            },
        ),
    ),

    ('system', 'watchdog'): APIData(
        unversioned=VersionedAPIData(
            fixed_entries=True,
            single_value=True,
            fully_understood=True,
            fields={
                'auto-send-supout': KeyInfo(default=False),
                'automatic-supout': KeyInfo(default=True),
                'ping-start-after-boot': KeyInfo(default='5m'),
                'ping-timeout': KeyInfo(default='1m'),
                'send-email-from': KeyInfo(default='none'),
                'send-email-to': KeyInfo(default='none'),
                'send-smtp-server': KeyInfo(default='none'),
                'watch-address': KeyInfo(default='none'),
                'watchdog-timer': KeyInfo(default=True),
            },
        ),
    ),

    ('task',): APIData(
        versioned=[
            ('7.15', '>=', VersionedAPIData(
                fully_understood=True,
                fields={
                    'append': KeyInfo(can_disable=True),
                    # 'copy-from': KeyInfo(write_only=True),
                    'file-name': KeyInfo(),
                    'max-lines': KeyInfo(),
                    'max-size': KeyInfo(),
                    'no-header-paging': KeyInfo(can_disable=True),
                    'save-interval': KeyInfo(),
                    'save-timestamp': KeyInfo(can_disable=True),
                    'source': KeyInfo(),
                    'switch-to': KeyInfo(can_disable=True),
                },
            )),
        ],
    ),

    ('tool', 'bandwidth-server'): APIData(
        unversioned=VersionedAPIData(
            fixed_entries=True,
            single_value=True,
            fully_understood=True,
            versioned_fields=[
                ([('7.18', '>=')], 'allowed-addresses4', KeyInfo()),
                ([('7.18', '>=')], 'allowed-addresses6', KeyInfo()),
            ],
            fields={
                'allocate-udp-ports-from': KeyInfo(default=2000),
                'authenticate': KeyInfo(default=True),
                'enabled': KeyInfo(default=True),
                'max-sessions': KeyInfo(default=100),
            },
        ),
    ),

    ('tool', 'calea'): APIData(
        versioned=[
            ('7.15', '>=', VersionedAPIData(
                fully_understood=True,
                fields={
                    'action': KeyInfo(),
                    'case-id': KeyInfo(),
                    'case-name': KeyInfo(),
                    'comment': KeyInfo(),
                    # 'copy-from': KeyInfo(write_only=True),
                    'disabled': KeyInfo(),
                    'file-root': KeyInfo(),
                    'intercept-ip': KeyInfo(),
                    'intercept-port': KeyInfo(),
                    'limited-file-hash-method': KeyInfo(),
                    'limited-file-stop-interval': KeyInfo(),
                    'pcap-file-hash-method': KeyInfo(),
                    'pcap-file-stop-count': KeyInfo(),
                    'pcap-file-stop-interval': KeyInfo(),
                    'pcap-file-stop-size': KeyInfo(),
                },
            )),
        ],
    ),

    ('tool', 'e-mail'): APIData(
        versioned=[
            ('7.12', '>=', VersionedAPIData(
                fixed_entries=True,
                single_value=True,
                fully_understood=True,
                versioned_fields=[
                    ([('7.21', '>=')], 'certificate-verification', KeyInfo()),
                    ([('7.15', '>=')], 'vrf', KeyInfo()),
                ],
                fields={
                    'from': KeyInfo(default='<>'),
                    'password': KeyInfo(default=''),
                    'port': KeyInfo(default=25),
                    'server': KeyInfo(default='0.0.0.0'),
                    'start-tls': KeyInfo(default=False),
                    'tls': KeyInfo(default=False),
                    'user': KeyInfo(default=''),
                    'vfr': KeyInfo(default=''),
                },
            )),
            ('7.12', '<', VersionedAPIData(
                fixed_entries=True,
                single_value=True,
                fully_understood=True,
                fields={
                    'address': KeyInfo(default='0.0.0.0'),
                    'from': KeyInfo(default='<>'),
                    'password': KeyInfo(default=''),
                    'port': KeyInfo(default=25),
                    'start-tls': KeyInfo(default=False),
                    'tls': KeyInfo(default=False),
                    'user': KeyInfo(default=''),
                    'vfr': KeyInfo(default=''),
                },
            )),
        ],
    ),

    ('tool', 'graphing'): APIData(
        unversioned=VersionedAPIData(
            fixed_entries=True,
            single_value=True,
            fully_understood=True,
            fields={
                'page-refresh': KeyInfo(default=300),
                'store-every': KeyInfo(default='5min'),
            },
        ),
    ),

    ('tool', 'graphing', 'interface'): APIData(
        versioned=[
            ('7', '>=', VersionedAPIData(
                fully_understood=True,
                # versioned_fields=[
                #     ([('7.15', '>=')], 'copy-from', KeyInfo(write_only=True)),
                # ],
                fields={
                    'allow-address': KeyInfo(default='0.0.0.0/0'),
                    'comment': KeyInfo(can_disable=True, remove_value=''),
                    'disabled': KeyInfo(default=False),
                    'interface': KeyInfo(default='all'),
                    'store-on-disk': KeyInfo(default=True),
                },
            )),
        ],
    ),

    ('tool', 'graphing', 'queue'): APIData(
        versioned=[
            ('7.15', '>=', VersionedAPIData(
                fully_understood=True,
                fields={
                    'allow-address': KeyInfo(),
                    'allow-target': KeyInfo(),
                    'comment': KeyInfo(),
                    # 'copy-from': KeyInfo(write_only=True),
                    'disabled': KeyInfo(),
                    'simple-queue': KeyInfo(),
                    'store-on-disk': KeyInfo(),
                },
            )),
        ],
    ),

    ('tool', 'graphing', 'resource'): APIData(
        versioned=[
            ('7', '>=', VersionedAPIData(
                fully_understood=True,
                # versioned_fields=[
                #     ([('7.15', '>=')], 'copy-from', KeyInfo(write_only=True)),
                # ],
                fields={
                    'allow-address': KeyInfo(default='0.0.0.0/0'),
                    'comment': KeyInfo(can_disable=True, remove_value=''),
                    'disabled': KeyInfo(default=False),
                    'store-on-disk': KeyInfo(default=True),
                },
            )),
        ],
    ),

    ('tool', 'mac-server'): APIData(
        unversioned=VersionedAPIData(
            fixed_entries=True,
            single_value=True,
            fully_understood=True,
            fields={
                'allowed-interface-list': KeyInfo(),
            },
        ),
    ),

    ('tool', 'mac-server', 'mac-winbox'): APIData(
        unversioned=VersionedAPIData(
            fixed_entries=True,
            single_value=True,
            fully_understood=True,
            fields={
                'allowed-interface-list': KeyInfo(),
            },
        ),
    ),

    ('tool', 'mac-server', 'ping'): APIData(
        unversioned=VersionedAPIData(
            fixed_entries=True,
            single_value=True,
            fully_understood=True,
            fields={
                'enabled': KeyInfo(default=True),
            },
        ),
    ),

    ('tool', 'mac-server', 'sessions'): APIData(
        versioned=[
            ('7.15', '>=', VersionedAPIData(
                fully_understood=True,
                has_identifier=True,
                # fixed_entries=True,
                # primary_keys=('numbers',),
                fields={
                    'interface': KeyInfo(),
                    'numbers': KeyInfo(),
                    'src-address': KeyInfo(),
                    'uptime': KeyInfo(),
                },
            )),
        ],
    ),

    ('tool', 'netwatch'): APIData(
        versioned=[
            ('7', '>=', VersionedAPIData(
                fully_understood=True,
                versioned_fields=[
                    ([('7.16', '>=')], 'accept-icmp-time-exceeded', KeyInfo(can_disable=True, default=False)),
                    # ([('7.15', '>=')], 'copy-from', KeyInfo(write_only=True)),
                    ([('7.16', '>=')], 'dns-server', KeyInfo(can_disable=True)),
                    ([('7.20', '>=')], 'early-failure-detection', KeyInfo(can_disable=True)),
                    ([('7.20', '>=')], 'early-success-detection', KeyInfo(can_disable=True)),
                    ([('7.17', '>=')], 'ignore-initial-down', KeyInfo(can_disable=True)),
                    ([('7.17', '>=')], 'ignore-initial-up', KeyInfo(can_disable=True)),
                    ([('7.16', '>=')], 'record-type', KeyInfo(can_disable=True)),
                    ([('7.16', '>=')], 'ttl', KeyInfo(can_disable=True, default=255)),
                ],
                fields={
                    'certificate': KeyInfo(can_disable=True),
                    'check-certificate': KeyInfo(can_disable=True),
                    'comment': KeyInfo(),
                    'disabled': KeyInfo(default=False),
                    'down-script': KeyInfo(can_disable=True),
                    'host': KeyInfo(required=True),
                    'http-codes': KeyInfo(can_disable=True),
                    'interval': KeyInfo(can_disable=True),
                    'name': KeyInfo(),
                    'packet-count': KeyInfo(can_disable=True),
                    'packet-interval': KeyInfo(can_disable=True),
                    'packet-size': KeyInfo(can_disable=True),
                    'port': KeyInfo(can_disable=True),
                    'src-address': KeyInfo(can_disable=True),
                    'start-delay': KeyInfo(can_disable=True),
                    'startup-delay': KeyInfo(can_disable=True),
                    'test-script': KeyInfo(can_disable=True),
                    'thr-avg': KeyInfo(can_disable=True),
                    'thr-http-time': KeyInfo(can_disable=True),
                    'thr-jitter': KeyInfo(can_disable=True),
                    'thr-loss-count': KeyInfo(can_disable=True),
                    'thr-loss-percent': KeyInfo(can_disable=True),
                    'thr-max': KeyInfo(can_disable=True),
                    'thr-stdev': KeyInfo(can_disable=True),
                    'thr-tcp-conn-time': KeyInfo(can_disable=True),
                    'timeout': KeyInfo(can_disable=True),
                    'type': KeyInfo(default='simple'),
                    'up-script': KeyInfo(can_disable=True),
                },
            )),
        ],
    ),

    ('tool', 'romon'): APIData(
        unversioned=VersionedAPIData(
            fixed_entries=True,
            single_value=True,
            fully_understood=True,
            fields={
                'enabled': KeyInfo(default=False),
                'id': KeyInfo(default='00:00:00:00:00:00'),
                'secrets': KeyInfo(default=''),
            },
        ),
    ),

    ('tool', 'romon', 'port'): APIData(
        unversioned=VersionedAPIData(
            fully_understood=True,
            versioned_fields=[
                ([('7.15', '>=')], 'comment', KeyInfo()),
                # ([('7.15', '>=')], 'copy-from', KeyInfo(write_only=True)),
            ],
            fields={
                'cost': KeyInfo(),
                'disabled': KeyInfo(),
                'forbid': KeyInfo(),
                'interface': KeyInfo(),
                'secrets': KeyInfo(),
            },
        ),
    ),

    ('tool', 'sms'): APIData(
        unversioned=VersionedAPIData(
            fixed_entries=True,
            single_value=True,
            fully_understood=True,
            versioned_fields=[
                ([('7.15', '<')], 'auto-erase', KeyInfo(default=False)),
                ([('7.16', '>=')], 'polling', KeyInfo()),
                ([('7.20', '>=')], 'remove-sent-sms-after-send', KeyInfo()),
                ([('7.15', '>=')], 'sms-storage', KeyInfo()),
            ],
            fields={
                'allowed-number': KeyInfo(default=''),
                'channel': KeyInfo(default=0),
                'port': KeyInfo(default='none'),
                'receive-enabled': KeyInfo(default=False),
                'secret': KeyInfo(default=''),
                'sim-pin': KeyInfo(default=''),
            },
        ),
    ),

    ('tool', 'sniffer'): APIData(
        unversioned=VersionedAPIData(
            fixed_entries=True,
            single_value=True,
            fully_understood=True,
            versioned_fields=[
                ([('7.15', '>=')], 'filter-dst-ip-address', KeyInfo()),
                ([('7.15', '>=')], 'filter-dst-ipv6-address', KeyInfo()),
                ([('7.15', '>=')], 'filter-dst-mac-address', KeyInfo()),
                ([('7.15', '>=')], 'filter-dst-port', KeyInfo()),
                ([('7.15', '>=')], 'filter-src-ip-address', KeyInfo()),
                ([('7.15', '>=')], 'filter-src-ipv6-address', KeyInfo()),
                ([('7.15', '>=')], 'filter-src-mac-address', KeyInfo()),
                ([('7.15', '>=')], 'filter-src-port', KeyInfo()),
                ([('7.15', '>=')], 'filter-vlan', KeyInfo()),
                ([('7.19', '>=')], 'max-packet-size', KeyInfo()),
                ([('7.15', '>=')], 'quick-rows', KeyInfo()),
                ([('7.15', '>=')], 'quick-show-frame', KeyInfo()),
            ],
            fields={
                'file-limit': KeyInfo(default='1000KiB'),
                'file-name': KeyInfo(default=''),
                'filter-cpu': KeyInfo(default=''),
                'filter-direction': KeyInfo(default='any'),
                'filter-interface': KeyInfo(default=''),
                'filter-ip-address': KeyInfo(default=''),
                'filter-ip-protocol': KeyInfo(default=''),
                'filter-ipv6-address': KeyInfo(default=''),
                'filter-mac-address': KeyInfo(default=''),
                'filter-mac-protocol': KeyInfo(default=''),
                'filter-operator-between-entries': KeyInfo(default='or'),
                'filter-port': KeyInfo(default=''),
                'filter-size': KeyInfo(default=''),
                'filter-stream': KeyInfo(default=False),
                'memory-limit': KeyInfo(default='100KiB'),
                'memory-scroll': KeyInfo(default=True),
                'only-headers': KeyInfo(default=False),
                'streaming-enabled': KeyInfo(default=False),
                'streaming-server': KeyInfo(default='0.0.0.0:37008'),
            },
        ),
    ),

    ('tool', 'traffic-generator'): APIData(
        unversioned=VersionedAPIData(
            fixed_entries=True,
            single_value=True,
            fully_understood=True,
            fields={
                'latency-distribution-max': KeyInfo(default='100us'),
                'measure-out-of-order': KeyInfo(default=True),
                'stats-samples-to-keep': KeyInfo(default=100),
                'test-id': KeyInfo(default=0),
            },
        ),
    ),

    ('tool', 'traffic-generator', 'packet-template'): APIData(
        versioned=[
            ('7.15', '>=', VersionedAPIData(
                fully_understood=True,
                fields={
                    'comment': KeyInfo(),
                    'compute-checksum-from-offset': KeyInfo(),
                    # 'copy-from': KeyInfo(write_only=True),
                    'data': KeyInfo(),
                    'data-byte': KeyInfo(),
                    'header-stack': KeyInfo(),
                    'interface': KeyInfo(can_disable=True),
                    'ip-dscp': KeyInfo(can_disable=True),
                    'ip-dst': KeyInfo(can_disable=True),
                    'ip-frag-off': KeyInfo(can_disable=True),
                    'ip-gateway': KeyInfo(can_disable=True),
                    'ip-id': KeyInfo(can_disable=True),
                    'ip-protocol': KeyInfo(can_disable=True),
                    'ip-src': KeyInfo(can_disable=True),
                    'ip-ttl': KeyInfo(can_disable=True),
                    'ipv6-dst': KeyInfo(can_disable=True),
                    'ipv6-flow-label': KeyInfo(can_disable=True),
                    'ipv6-gateway': KeyInfo(can_disable=True),
                    'ipv6-hop-limit': KeyInfo(can_disable=True),
                    'ipv6-next-header': KeyInfo(can_disable=True),
                    'ipv6-src': KeyInfo(can_disable=True),
                    'ipv6-traffic-class': KeyInfo(can_disable=True),
                    'mac-dst': KeyInfo(can_disable=True),
                    'mac-protocol': KeyInfo(can_disable=True),
                    'mac-src': KeyInfo(can_disable=True),
                    'name': KeyInfo(),
                    'port': KeyInfo(can_disable=True),
                    'random-byte-offsets-and-masks': KeyInfo(),
                    'random-ranges': KeyInfo(),
                    'raw-header': KeyInfo(can_disable=True),
                    'special-footer': KeyInfo(),
                    'tcp-ack': KeyInfo(can_disable=True),
                    'tcp-data-offset': KeyInfo(can_disable=True),
                    'tcp-dst-port': KeyInfo(can_disable=True),
                    'tcp-flags': KeyInfo(can_disable=True),
                    'tcp-src-port': KeyInfo(can_disable=True),
                    'tcp-syn': KeyInfo(can_disable=True),
                    'tcp-urgent-pointer': KeyInfo(can_disable=True),
                    'tcp-window-size': KeyInfo(can_disable=True),
                    'udp-checksum': KeyInfo(can_disable=True),
                    'udp-dst-port': KeyInfo(can_disable=True),
                    'udp-src-port': KeyInfo(can_disable=True),
                    'vlan-id': KeyInfo(can_disable=True),
                    'vlan-priority': KeyInfo(can_disable=True),
                    'vlan-protocol': KeyInfo(can_disable=True),
                },
            )),
        ],
    ),

    ('tool', 'traffic-generator', 'port'): APIData(
        versioned=[
            ('7.15', '>=', VersionedAPIData(
                fully_understood=True,
                fields={
                    # 'copy-from': KeyInfo(write_only=True),
                    'disabled': KeyInfo(),
                    'interface': KeyInfo(),
                    'name': KeyInfo(),
                },
            )),
        ],
    ),

    ('tool', 'traffic-generator', 'raw-packet-template'): APIData(
        versioned=[
            ('7.15', '>=', VersionedAPIData(
                fully_understood=True,
                fields={
                    'comment': KeyInfo(),
                    'compute-checksum-from-offset': KeyInfo(),
                    # 'copy-from': KeyInfo(write_only=True),
                    'data': KeyInfo(),
                    'data-byte': KeyInfo(),
                    'header': KeyInfo(),
                    'ip-header-offset': KeyInfo(),
                    'ipv6-header-offset': KeyInfo(),
                    'name': KeyInfo(),
                    'port': KeyInfo(can_disable=True),
                    'random-byte-offsets-and-masks': KeyInfo(),
                    'random-ranges': KeyInfo(),
                    'special-footer': KeyInfo(),
                    'tcp-header-offset': KeyInfo(),
                    'udp-compute-checksum': KeyInfo(),
                    'udp-header-offset': KeyInfo(),
                },
            )),
        ],
    ),

    ('tool', 'traffic-generator', 'stream'): APIData(
        versioned=[
            ('7.15', '>=', VersionedAPIData(
                fully_understood=True,
                fields={
                    # 'copy-from': KeyInfo(write_only=True),
                    'cpu-core': KeyInfo(),
                    'disabled': KeyInfo(),
                    'id': KeyInfo(),
                    'mbps': KeyInfo(),
                    'name': KeyInfo(),
                    'packet-count': KeyInfo(),
                    'packet-size': KeyInfo(),
                    'port': KeyInfo(can_disable=True),
                    'pps': KeyInfo(),
                    'tx-template': KeyInfo(),
                },
            )),
        ],
    ),

    ('tool', 'traffic-monitor'): APIData(
        versioned=[
            ('7.15', '>=', VersionedAPIData(
                fully_understood=True,
                fields={
                    'comment': KeyInfo(),
                    # 'copy-from': KeyInfo(write_only=True),
                    'disabled': KeyInfo(),
                    'interface': KeyInfo(),
                    'name': KeyInfo(),
                    'on-event': KeyInfo(),
                    'threshold': KeyInfo(),
                    'traffic': KeyInfo(),
                    'trigger': KeyInfo(),
                },
            )),
        ],
    ),

    ('tr069-client',): APIData(
        versioned=[
            ('7.15', '>=', VersionedAPIData(
                fixed_entries=True,
                single_value=True,
                fully_understood=True,
                fields={
                    'acs-url': KeyInfo(),
                    'check-certificate': KeyInfo(),
                    'client-certificate': KeyInfo(),
                    'connection-request-password': KeyInfo(),
                    'connection-request-port': KeyInfo(),
                    'connection-request-username': KeyInfo(),
                    'enabled': KeyInfo(),
                    'password': KeyInfo(),
                    'periodic-inform-enabled': KeyInfo(),
                    'periodic-inform-interval': KeyInfo(),
                    'provisioning-code': KeyInfo(),
                    'username': KeyInfo(),
                },
            )),
        ],
    ),

    ('user',): APIData(
        unversioned=VersionedAPIData(
            primary_keys=('name',),
            fully_understood=True,
            versioned_fields=[
                # ([('7.15', '>=')], 'copy-from', KeyInfo(write_only=True)),
                ([('7.16', '>=')], 'inactivity-policy', KeyInfo()),
                ([('7.16', '>=')], 'inactivity-timeout', KeyInfo()),
            ],
            fields={
                'address': KeyInfo(),
                'comment': KeyInfo(can_disable=True, remove_value=''),
                'disabled': KeyInfo(default=False),
                'expired': KeyInfo(read_only=True),
                'group': KeyInfo(),
                'last-logged-in': KeyInfo(read_only=True),
                'name': KeyInfo(),
                'password': KeyInfo(write_only=True),
            },
        ),
    ),

    ('user', 'aaa'): APIData(
        unversioned=VersionedAPIData(
            fixed_entries=True,
            single_value=True,
            fully_understood=True,
            fields={
                'accounting': KeyInfo(default=True),
                'default-group': KeyInfo(default='read'),
                'exclude-groups': KeyInfo(default=''),
                'interim-update': KeyInfo(default='0s'),
                'use-radius': KeyInfo(default=False),
            },
        ),
    ),

    ('user', 'group'): APIData(
        unversioned=VersionedAPIData(
            primary_keys=('name',),
            fully_understood=True,
            # versioned_fields=[
            #     ([('7.15', '>=')], 'copy-from', KeyInfo(write_only=True)),
            # ],
            fields={
                'comment': KeyInfo(can_disable=True, remove_value=''),
                'name': KeyInfo(),
                'policy': KeyInfo(),
                'skin': KeyInfo(default='default'),
            },
        ),
    ),

    ('user', 'settings'): APIData(
        unversioned=VersionedAPIData(
            fixed_entries=True,
            single_value=True,
            fully_understood=True,
            fields={
                'minimum-categories': KeyInfo(),
                'minimum-password-length': KeyInfo(),
            },
        ),
    ),

    ('user', 'ssh-keys'): APIData(
        versioned=[
            ('7.15', '>=', VersionedAPIData(
                fully_understood=True,
                fields={
                    'comment': KeyInfo(),
                    # 'copy-from': KeyInfo(write_only=True),
                    'key': KeyInfo(),
                    'user': KeyInfo(),
                },
            )),
        ],
    ),

    ('user-manager',): APIData(
        versioned=[
            ('7.15', '>=', VersionedAPIData(
                fixed_entries=True,
                single_value=True,
                fully_understood=True,
                versioned_fields=[
                    ([('7.21', '>=')], 'radsec-certificate', KeyInfo()),
                ],
                fields={
                    'accounting-port': KeyInfo(),
                    'authentication-port': KeyInfo(),
                    'certificate': KeyInfo(),
                    'enabled': KeyInfo(),
                    'require-message-auth': KeyInfo(),
                    'use-profiles': KeyInfo(),
                },
            )),
        ],
    ),

    ('user-manager', 'advanced'): APIData(
        versioned=[
            ('7.15', '>=', VersionedAPIData(
                fixed_entries=True,
                single_value=True,
                fully_understood=True,
                fields={
                    'paypal-allow': KeyInfo(),
                    'paypal-currency': KeyInfo(),
                    'paypal-password': KeyInfo(),
                    'paypal-signature': KeyInfo(),
                    'paypal-use-sandbox': KeyInfo(),
                    'paypal-user': KeyInfo(),
                    'web-private-password': KeyInfo(),
                    'web-private-username': KeyInfo(),
                },
            )),
        ],
    ),

    ('user-manager', 'attribute'): APIData(
        versioned=[
            ('7.15', '>=', VersionedAPIData(
                fully_understood=True,
                fields={
                    # 'copy-from': KeyInfo(write_only=True),
                    'name': KeyInfo(),
                    'packet-types': KeyInfo(),
                    'type-id': KeyInfo(),
                    'value-type': KeyInfo(),
                    'vendor-id': KeyInfo(),
                },
            )),
        ],
    ),

    ('user-manager', 'database'): APIData(
        versioned=[
            ('7.15', '>=', VersionedAPIData(
                fixed_entries=True,
                single_value=True,
                fully_understood=True,
                fields={
                    'db-path': KeyInfo(),
                },
            )),
        ],
    ),

    ('user-manager', 'limitation'): APIData(
        versioned=[
            ('7.15', '>=', VersionedAPIData(
                fully_understood=True,
                fields={
                    'comment': KeyInfo(),
                    # 'copy-from': KeyInfo(write_only=True),
                    'download-limit': KeyInfo(),
                    'name': KeyInfo(),
                    'rate-limit-burst-rx': KeyInfo(),
                    'rate-limit-burst-threshold-rx': KeyInfo(),
                    'rate-limit-burst-threshold-tx': KeyInfo(),
                    'rate-limit-burst-time-rx': KeyInfo(),
                    'rate-limit-burst-time-tx': KeyInfo(),
                    'rate-limit-burst-tx': KeyInfo(),
                    'rate-limit-min-rx': KeyInfo(),
                    'rate-limit-min-tx': KeyInfo(),
                    'rate-limit-priority': KeyInfo(),
                    'rate-limit-rx': KeyInfo(),
                    'rate-limit-tx': KeyInfo(),
                    'reset-counters-interval': KeyInfo(),
                    'reset-counters-start-time': KeyInfo(),
                    'transfer-limit': KeyInfo(),
                    'upload-limit': KeyInfo(),
                    'uptime-limit': KeyInfo(),
                },
            )),
        ],
    ),

    ('user-manager', 'payment'): APIData(
        versioned=[
            ('7.15', '>=', VersionedAPIData(
                fully_understood=True,
                fields={
                    # 'copy-from': KeyInfo(write_only=True),
                    'currency': KeyInfo(),
                    'method': KeyInfo(),
                    'price': KeyInfo(),
                    'profile': KeyInfo(),
                    'trans-end': KeyInfo(),
                    'trans-start': KeyInfo(),
                    'trans-status': KeyInfo(),
                    'user': KeyInfo(),
                    'user-message': KeyInfo(),
                },
            )),
        ],
    ),

    ('user-manager', 'profile'): APIData(
        versioned=[
            ('7.15', '>=', VersionedAPIData(
                fully_understood=True,
                fields={
                    'comment': KeyInfo(),
                    # 'copy-from': KeyInfo(write_only=True),
                    'name': KeyInfo(),
                    'name-for-users': KeyInfo(),
                    'override-shared-users': KeyInfo(),
                    'price': KeyInfo(),
                    'starts-when': KeyInfo(),
                    'validity': KeyInfo(),
                },
            )),
        ],
    ),

    ('user-manager', 'profile-limitation'): APIData(
        versioned=[
            ('7.15', '>=', VersionedAPIData(
                fully_understood=True,
                fields={
                    'comment': KeyInfo(),
                    # 'copy-from': KeyInfo(write_only=True),
                    'from-time': KeyInfo(),
                    'limitation': KeyInfo(),
                    'profile': KeyInfo(),
                    'till-time': KeyInfo(),
                    'weekdays': KeyInfo(),
                },
            )),
        ],
    ),

    ('user-manager', 'router'): APIData(
        versioned=[
            ('7.15', '>=', VersionedAPIData(
                fully_understood=True,
                versioned_fields=[
                    ([('7.21', '>=')], 'protocol', KeyInfo()),
                ],
                fields={
                    'address': KeyInfo(),
                    'coa-port': KeyInfo(),
                    'comment': KeyInfo(),
                    # 'copy-from': KeyInfo(write_only=True),
                    'disabled': KeyInfo(),
                    'name': KeyInfo(),
                    'shared-secret': KeyInfo(),
                },
            )),
        ],
    ),

    ('user-manager', 'user'): APIData(
        versioned=[
            ('7.15', '>=', VersionedAPIData(
                fully_understood=True,
                fields={
                    'attributes': KeyInfo(),
                    'caller-id': KeyInfo(),
                    'comment': KeyInfo(),
                    # 'copy-from': KeyInfo(write_only=True),
                    'disabled': KeyInfo(),
                    'group': KeyInfo(),
                    'name': KeyInfo(),
                    'otp-secret': KeyInfo(),
                    'password': KeyInfo(),
                    'shared-users': KeyInfo(),
                },
            )),
        ],
    ),

    ('user-manager', 'user', 'group'): APIData(
        versioned=[
            ('7.15', '>=', VersionedAPIData(
                fully_understood=True,
                fields={
                    'attributes': KeyInfo(),
                    'comment': KeyInfo(),
                    # 'copy-from': KeyInfo(write_only=True),
                    'inner-auths': KeyInfo(),
                    'name': KeyInfo(),
                    'outer-auths': KeyInfo(),
                },
            )),
        ],
    ),

    ('user-manager', 'user-profile'): APIData(
        versioned=[
            ('7.15', '>=', VersionedAPIData(
                fully_understood=True,
                fields={
                    # 'copy-from': KeyInfo(write_only=True),
                    'profile': KeyInfo(),
                    'user': KeyInfo(),
                },
            )),
        ],
    ),

    ('zerotier',): APIData(
        versioned=[
            ('7.15', '>=', VersionedAPIData(
                fully_understood=True,
                fields={
                    'comment': KeyInfo(),
                    # 'copy-from': KeyInfo(write_only=True),
                    'disabled': KeyInfo(),
                    'identity': KeyInfo(),
                    'interfaces': KeyInfo(),
                    'name': KeyInfo(),
                    'port': KeyInfo(),
                    'route-distance': KeyInfo(),
                },
            )),
        ],
    ),

    ('zerotier', 'controller'): APIData(
        versioned=[
            ('7.15', '>=', VersionedAPIData(
                fully_understood=True,
                fields={
                    'broadcast': KeyInfo(),
                    'comment': KeyInfo(),
                    # 'copy-from': KeyInfo(write_only=True),
                    'disabled': KeyInfo(),
                    'instance': KeyInfo(),
                    'ip-range': KeyInfo(),
                    'ip6-6plane': KeyInfo(),
                    'ip6-range': KeyInfo(),
                    'ip6-rfc4193': KeyInfo(),
                    'mtu': KeyInfo(),
                    'multicast-limit': KeyInfo(),
                    'name': KeyInfo(),
                    'network': KeyInfo(),
                    'private': KeyInfo(),
                    'routes': KeyInfo(),
                },
            )),
        ],
    ),

    ('zerotier', 'controller', 'member'): APIData(
        versioned=[
            ('7.15', '>=', VersionedAPIData(
                fully_understood=True,
                fields={
                    'authorized': KeyInfo(),
                    'bridge': KeyInfo(),
                    'comment': KeyInfo(),
                    # 'copy-from': KeyInfo(write_only=True),
                    'disabled': KeyInfo(),
                    'ip-address': KeyInfo(),
                    'name': KeyInfo(),
                    'network': KeyInfo(),
                    'zt-address': KeyInfo(),
                },
            )),
        ],
    ),

    ('zerotier', 'interface'): APIData(
        versioned=[
            ('7.15', '>=', VersionedAPIData(
                fully_understood=True,
                fields={
                    'allow-default': KeyInfo(),
                    'allow-global': KeyInfo(),
                    'allow-managed': KeyInfo(),
                    'arp-timeout': KeyInfo(),
                    'comment': KeyInfo(),
                    # 'copy-from': KeyInfo(write_only=True),
                    'disable-running-check': KeyInfo(),
                    'disabled': KeyInfo(),
                    'instance': KeyInfo(),
                    'name': KeyInfo(),
                    'network': KeyInfo(),
                },
            )),
        ],
    ),

}
