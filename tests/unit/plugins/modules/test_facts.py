# Copyright (c) Ansible Project
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from ansible_collections.community.internal_test_tools.tests.unit.compat.mock import patch
from ansible_collections.community.internal_test_tools.tests.unit.plugins.modules.utils import set_module_args

from ansible_collections.community.routeros.plugins.modules import facts
from .routeros_module import TestRouterosModule, load_fixture


class TestRouterosFactsModule(TestRouterosModule):

    module = facts

    def setUp(self):
        super(TestRouterosFactsModule, self).setUp()
        self.mock_run_commands = patch('ansible_collections.community.routeros.plugins.modules.facts.run_commands')
        self.run_commands = self.mock_run_commands.start()

    def tearDown(self):
        super(TestRouterosFactsModule, self).tearDown()
        self.mock_run_commands.stop()

    def load_fixtures(self, commands=None):
        def load_from_file(*args, **kwargs):
            module = args
            commands = kwargs['commands']
            output = list()

            for command in commands:
                filename = str(command).split(' | ', 1)[0].replace(' ', '_')
                output.append(load_fixture('facts%s' % filename))
            return output

        self.run_commands.side_effect = load_from_file

    def test_facts_default(self):
        with set_module_args(dict(gather_subset='default')):
            result = self.execute_module()
        self.assertEqual(
            result['ansible_facts']['ansible_net_hostname'], 'MikroTik'
        )
        self.assertEqual(
            result['ansible_facts']['ansible_net_version'], '6.42.5 (stable)'
        )
        self.assertEqual(
            result['ansible_facts']['ansible_net_model'], 'RouterBOARD 3011UiAS'
        )
        self.assertEqual(
            result['ansible_facts']['ansible_net_serialnum'], '1234567890'
        )
        self.assertEqual(
            result['ansible_facts']['ansible_net_arch'], 'x86'
        )
        self.assertEqual(
            result['ansible_facts']['ansible_net_uptime'], '3h28m52s'
        )

    def test_facts_hardware(self):
        with set_module_args(dict(gather_subset='hardware')):
            result = self.execute_module()
        self.assertEqual(
            result['ansible_facts']['ansible_net_spacefree_mb'], 64921.6
        )
        self.assertEqual(
            result['ansible_facts']['ansible_net_spacetotal_mb'], 65024.0
        )
        self.assertEqual(
            result['ansible_facts']['ansible_net_memfree_mb'], 988.3
        )
        self.assertEqual(
            result['ansible_facts']['ansible_net_memtotal_mb'], 1010.8
        )

    def test_facts_config(self):
        with set_module_args(dict(gather_subset='config')):
            result = self.execute_module()
        self.assertIsInstance(
            result['ansible_facts']['ansible_net_config'], str
        )

        self.assertIsInstance(
            result['ansible_facts']['ansible_net_config_nonverbose'], str
        )

    def test_facts_interfaces(self):
        with set_module_args(dict(gather_subset='interfaces')):
            result = self.execute_module()
        self.assertIn(
            result['ansible_facts']['ansible_net_all_ipv4_addresses'][0], ['10.37.129.3', '10.37.0.0', '192.168.88.1']
        )
        self.assertEqual(
            result['ansible_facts']['ansible_net_all_ipv6_addresses'], ['fe80::21c:42ff:fe36:5290']
        )
        self.assertEqual(
            result['ansible_facts']['ansible_net_all_ipv6_addresses'][0],
            result['ansible_facts']['ansible_net_interfaces']['ether1']['ipv6'][0]['address']
        )
        self.assertEqual(
            len(result['ansible_facts']['ansible_net_interfaces'].keys()), 11
        )
        self.assertEqual(
            len(result['ansible_facts']['ansible_net_neighbors']), 4
        )

    def test_facts_interfaces_no_ipv6(self):
        fixture = load_fixture(
            'facts/ipv6_address_print_detail_without-paging_no-ipv6'
        )
        interfaces = self.module.Interfaces(module=self.module)
        addresses = interfaces.parse_detail(data=fixture)
        result = interfaces.populate_addresses(data=addresses, family='ipv6')

        self.assertEqual(result, None)

    def test_facts_routing(self):
        with set_module_args(dict(gather_subset='routing')):
            result = self.execute_module()
        self.assertIn(
            result['ansible_facts']['ansible_net_bgp_peer']['iBGP_BRAS.TYRMA']['name'], ['iBGP_BRAS.TYRMA']
        )
        self.assertIn(
            result['ansible_facts']['ansible_net_bgp_peer']['iBGP_BRAS.TYRMA']['instance'], ['MAIN_AS_STARKDV']
        )
        self.assertIn(
            result['ansible_facts']['ansible_net_bgp_peer']['iBGP_BRAS.TYRMA']['remote-address'], ['10.10.100.1']
        )
        self.assertIn(
            result['ansible_facts']['ansible_net_bgp_peer']['iBGP_BRAS.TYRMA']['remote-as'], ['64520']
        )
        self.assertIn(
            result['ansible_facts']['ansible_net_bgp_peer']['iBGP_BRAS.TYRMA']['nexthop-choice'], ['default']
        )
        self.assertIn(
            result['ansible_facts']['ansible_net_bgp_peer']['iBGP_BRAS.TYRMA']['multihop'], ['no']
        )
        self.assertIn(
            result['ansible_facts']['ansible_net_bgp_peer']['iBGP_BRAS.TYRMA']['route-reflect'], ['yes']
        )
        self.assertIn(
            result['ansible_facts']['ansible_net_bgp_peer']['iBGP_BRAS.TYRMA']['hold-time'], ['3m']
        )
        self.assertIn(
            result['ansible_facts']['ansible_net_bgp_peer']['iBGP_BRAS.TYRMA']['ttl'], ['default']
        )
        self.assertIn(
            result['ansible_facts']['ansible_net_bgp_peer']['iBGP_BRAS.TYRMA']['address-families'], ['ip']
        )
        self.assertIn(
            result['ansible_facts']['ansible_net_bgp_peer']['iBGP_BRAS.TYRMA']['update-source'], ['LAN_KHV']
        )
        self.assertIn(
            result['ansible_facts']['ansible_net_bgp_peer']['iBGP_BRAS.TYRMA']['default-originate'], ['never']
        )
        self.assertIn(
            result['ansible_facts']['ansible_net_bgp_peer']['iBGP_BRAS.TYRMA']['remove-private-as'], ['no']
        )
        self.assertIn(
            result['ansible_facts']['ansible_net_bgp_peer']['iBGP_BRAS.TYRMA']['as-override'], ['no']
        )
        self.assertIn(
            result['ansible_facts']['ansible_net_bgp_peer']['iBGP_BRAS.TYRMA']['passive'], ['no']
        )
        self.assertIn(
            result['ansible_facts']['ansible_net_bgp_peer']['iBGP_BRAS.TYRMA']['use-bfd'], ['yes']
        )
        self.assertIn(
            result['ansible_facts']['ansible_net_bgp_vpnv4_route']['GRE_TYRMA']['route-distinguisher'], ['64520:666']
        )
        self.assertIn(
            result['ansible_facts']['ansible_net_bgp_vpnv4_route']['GRE_TYRMA']['dst-address'], ['10.10.66.8/30']
        )
        self.assertIn(
            result['ansible_facts']['ansible_net_bgp_vpnv4_route']['GRE_TYRMA']['gateway'], ['10.10.100.1']
        )
        self.assertIn(
            result['ansible_facts']['ansible_net_bgp_vpnv4_route']['GRE_TYRMA']['interface'], ['GRE_TYRMA']
        )
        self.assertIn(
            result['ansible_facts']['ansible_net_bgp_vpnv4_route']['GRE_TYRMA']['in-label'], ['6136']
        )
        self.assertIn(
            result['ansible_facts']['ansible_net_bgp_vpnv4_route']['GRE_TYRMA']['out-label'], ['6136']
        )
        self.assertIn(
            result['ansible_facts']['ansible_net_bgp_vpnv4_route']['GRE_TYRMA']['bgp-local-pref'], ['100']
        )
        self.assertIn(
            result['ansible_facts']['ansible_net_bgp_vpnv4_route']['GRE_TYRMA']['bgp-origin'], ['incomplete']
        )
        self.assertIn(
            result['ansible_facts']['ansible_net_bgp_vpnv4_route']['GRE_TYRMA']['bgp-ext-communities'], ['RT:64520:666']
        )
        self.assertIn(
            result['ansible_facts']['ansible_net_bgp_instance']['default']['name'], ['default']
        )
        self.assertIn(
            result['ansible_facts']['ansible_net_bgp_instance']['default']['as'], ['65530']
        )
        self.assertIn(
            result['ansible_facts']['ansible_net_bgp_instance']['default']['router-id'], ['0.0.0.0']
        )
        self.assertIn(
            result['ansible_facts']['ansible_net_bgp_instance']['default']['redistribute-connected'], ['no']
        )
        self.assertIn(
            result['ansible_facts']['ansible_net_bgp_instance']['default']['redistribute-static'], ['no']
        )
        self.assertIn(
            result['ansible_facts']['ansible_net_bgp_instance']['default']['redistribute-rip'], ['no']
        )
        self.assertIn(
            result['ansible_facts']['ansible_net_bgp_instance']['default']['redistribute-ospf'], ['no']
        )
        self.assertIn(
            result['ansible_facts']['ansible_net_bgp_instance']['default']['redistribute-other-bgp'], ['no']
        )
        self.assertIn(
            result['ansible_facts']['ansible_net_bgp_instance']['default']['client-to-client-reflection'], ['yes']
        )
        self.assertIn(
            result['ansible_facts']['ansible_net_bgp_instance']['default']['ignore-as-path-len'], ['no']
        )
        self.assertIn(
            result['ansible_facts']['ansible_net_route']['altegro']['dst-address'], ['10.10.66.0/30']
        )
        self.assertIn(
            result['ansible_facts']['ansible_net_route']['altegro']['pref-src'], ['10.10.66.1']
        )
        self.assertIn(
            result['ansible_facts']['ansible_net_route']['altegro']['gateway'], ['bridge1']
        )
        self.assertIn(
            result['ansible_facts']['ansible_net_route']['altegro']['gateway-status'], ['bridge1']
        )
        self.assertIn(
            result['ansible_facts']['ansible_net_route']['altegro']['distance'], ['0']
        )
        self.assertIn(
            result['ansible_facts']['ansible_net_route']['altegro']['scope'], ['10']
        )
        self.assertIn(
            result['ansible_facts']['ansible_net_route']['altegro']['routing-mark'], ['altegro']
        )
        self.assertIn(
            result['ansible_facts']['ansible_net_ospf_instance']['default']['name'], ['default']
        )
        self.assertIn(
            result['ansible_facts']['ansible_net_ospf_instance']['default']['router-id'], ['10.10.50.1']
        )
        self.assertIn(
            result['ansible_facts']['ansible_net_ospf_instance']['default']['distribute-default'], ['never']
        )
        self.assertIn(
            result['ansible_facts']['ansible_net_ospf_instance']['default']['redistribute-connected'], ['no']
        )
        self.assertIn(
            result['ansible_facts']['ansible_net_ospf_instance']['default']['redistribute-static'], ['no']
        )
        self.assertIn(
            result['ansible_facts']['ansible_net_ospf_instance']['default']['redistribute-rip'], ['no']
        )
        self.assertIn(
            result['ansible_facts']['ansible_net_ospf_instance']['default']['redistribute-bgp'], ['no']
        )
        self.assertIn(
            result['ansible_facts']['ansible_net_ospf_instance']['default']['redistribute-other-ospf'], ['no']
        )
        self.assertIn(
            result['ansible_facts']['ansible_net_ospf_instance']['default']['metric-default'], ['1']
        )
        self.assertIn(
            result['ansible_facts']['ansible_net_ospf_instance']['default']['metric-connected'], ['20']
        )
        self.assertIn(
            result['ansible_facts']['ansible_net_ospf_instance']['default']['metric-static'], ['20']
        )
        self.assertIn(
            result['ansible_facts']['ansible_net_ospf_instance']['default']['metric-rip'], ['20']
        )
        self.assertIn(
            result['ansible_facts']['ansible_net_ospf_instance']['default']['metric-bgp'], ['auto']
        )
        self.assertIn(
            result['ansible_facts']['ansible_net_ospf_instance']['default']['metric-other-ospf'], ['auto']
        )
        self.assertIn(
            result['ansible_facts']['ansible_net_ospf_instance']['default']['in-filter'], ['ospf-in']
        )
        self.assertIn(
            result['ansible_facts']['ansible_net_ospf_instance']['default']['out-filter'], ['ospf-out']
        )
        self.assertIn(
            result['ansible_facts']['ansible_net_ospf_neighbor']['default']['instance'], ['default']
        )
        self.assertIn(
            result['ansible_facts']['ansible_net_ospf_neighbor']['default']['router-id'], ['10.10.100.1']
        )
        self.assertIn(
            result['ansible_facts']['ansible_net_ospf_neighbor']['default']['address'], ['10.10.1.2']
        )
        self.assertIn(
            result['ansible_facts']['ansible_net_ospf_neighbor']['default']['interface'], ['GRE_TYRMA']
        )
        self.assertIn(
            result['ansible_facts']['ansible_net_ospf_neighbor']['default']['priority'], ['1']
        )
        self.assertIn(
            result['ansible_facts']['ansible_net_ospf_neighbor']['default']['dr-address'], ['0.0.0.0']
        )
        self.assertIn(
            result['ansible_facts']['ansible_net_ospf_neighbor']['default']['backup-dr-address'], ['0.0.0.0']
        )
        self.assertIn(
            result['ansible_facts']['ansible_net_ospf_neighbor']['default']['state'], ['Full']
        )
        self.assertIn(
            result['ansible_facts']['ansible_net_ospf_neighbor']['default']['state-changes'], ['15']
        )
        self.assertIn(
            result['ansible_facts']['ansible_net_ospf_neighbor']['default']['ls-retransmits'], ['0']
        )
        self.assertIn(
            result['ansible_facts']['ansible_net_ospf_neighbor']['default']['ls-requests'], ['0']
        )
        self.assertIn(
            result['ansible_facts']['ansible_net_ospf_neighbor']['default']['db-summaries'], ['0']
        )
        self.assertIn(
            result['ansible_facts']['ansible_net_ospf_neighbor']['default']['adjacency'], ['6h8m46s']
        )
