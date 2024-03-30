# Community RouterOS Release Notes

**Topics**
- <a href="#v2-13-0">v2\.13\.0</a>
  - <a href="#release-summary">Release Summary</a>
  - <a href="#minor-changes">Minor Changes</a>
  - <a href="#bugfixes">Bugfixes</a>
- <a href="#v2-12-0">v2\.12\.0</a>
  - <a href="#release-summary-1">Release Summary</a>
  - <a href="#minor-changes-1">Minor Changes</a>
- <a href="#v2-11-0">v2\.11\.0</a>
  - <a href="#release-summary-2">Release Summary</a>
  - <a href="#minor-changes-2">Minor Changes</a>
- <a href="#v2-10-0">v2\.10\.0</a>
  - <a href="#release-summary-3">Release Summary</a>
  - <a href="#minor-changes-3">Minor Changes</a>
  - <a href="#bugfixes-1">Bugfixes</a>
- <a href="#v2-9-0">v2\.9\.0</a>
  - <a href="#release-summary-4">Release Summary</a>
  - <a href="#minor-changes-4">Minor Changes</a>
  - <a href="#bugfixes-2">Bugfixes</a>
- <a href="#v2-8-3">v2\.8\.3</a>
  - <a href="#release-summary-5">Release Summary</a>
  - <a href="#known-issues">Known Issues</a>
- <a href="#v2-8-2">v2\.8\.2</a>
  - <a href="#release-summary-6">Release Summary</a>
  - <a href="#bugfixes-3">Bugfixes</a>
- <a href="#v2-8-1">v2\.8\.1</a>
  - <a href="#release-summary-7">Release Summary</a>
  - <a href="#bugfixes-4">Bugfixes</a>
- <a href="#v2-8-0">v2\.8\.0</a>
  - <a href="#release-summary-8">Release Summary</a>
  - <a href="#minor-changes-5">Minor Changes</a>
  - <a href="#bugfixes-5">Bugfixes</a>
- <a href="#v2-7-0">v2\.7\.0</a>
  - <a href="#release-summary-9">Release Summary</a>
  - <a href="#minor-changes-6">Minor Changes</a>
  - <a href="#bugfixes-6">Bugfixes</a>
- <a href="#v2-6-0">v2\.6\.0</a>
  - <a href="#release-summary-10">Release Summary</a>
  - <a href="#minor-changes-7">Minor Changes</a>
  - <a href="#bugfixes-7">Bugfixes</a>
- <a href="#v2-5-0">v2\.5\.0</a>
  - <a href="#release-summary-11">Release Summary</a>
  - <a href="#minor-changes-8">Minor Changes</a>
  - <a href="#bugfixes-8">Bugfixes</a>
- <a href="#v2-4-0">v2\.4\.0</a>
  - <a href="#release-summary-12">Release Summary</a>
  - <a href="#minor-changes-9">Minor Changes</a>
  - <a href="#bugfixes-9">Bugfixes</a>
  - <a href="#known-issues-1">Known Issues</a>
- <a href="#v2-3-1">v2\.3\.1</a>
  - <a href="#release-summary-13">Release Summary</a>
  - <a href="#known-issues-2">Known Issues</a>
- <a href="#v2-3-0">v2\.3\.0</a>
  - <a href="#release-summary-14">Release Summary</a>
  - <a href="#minor-changes-10">Minor Changes</a>
  - <a href="#bugfixes-10">Bugfixes</a>
- <a href="#v2-2-1">v2\.2\.1</a>
  - <a href="#release-summary-15">Release Summary</a>
  - <a href="#bugfixes-11">Bugfixes</a>
- <a href="#v2-2-0">v2\.2\.0</a>
  - <a href="#release-summary-16">Release Summary</a>
  - <a href="#minor-changes-11">Minor Changes</a>
  - <a href="#bugfixes-12">Bugfixes</a>
  - <a href="#new-modules">New Modules</a>
- <a href="#v2-1-0">v2\.1\.0</a>
  - <a href="#release-summary-17">Release Summary</a>
  - <a href="#minor-changes-12">Minor Changes</a>
  - <a href="#bugfixes-13">Bugfixes</a>
  - <a href="#new-modules-1">New Modules</a>
- <a href="#v2-0-0">v2\.0\.0</a>
  - <a href="#release-summary-18">Release Summary</a>
  - <a href="#minor-changes-13">Minor Changes</a>
  - <a href="#breaking-changes--porting-guide">Breaking Changes / Porting Guide</a>
  - <a href="#bugfixes-14">Bugfixes</a>
  - <a href="#new-plugins">New Plugins</a>
    - <a href="#filter">Filter</a>
- <a href="#v1-2-0">v1\.2\.0</a>
  - <a href="#release-summary-19">Release Summary</a>
  - <a href="#minor-changes-14">Minor Changes</a>
  - <a href="#bugfixes-15">Bugfixes</a>
- <a href="#v1-1-0">v1\.1\.0</a>
  - <a href="#release-summary-20">Release Summary</a>
  - <a href="#minor-changes-15">Minor Changes</a>
- <a href="#v1-0-1">v1\.0\.1</a>
  - <a href="#release-summary-21">Release Summary</a>
  - <a href="#bugfixes-16">Bugfixes</a>
- <a href="#v1-0-0">v1\.0\.0</a>
  - <a href="#release-summary-22">Release Summary</a>
  - <a href="#bugfixes-17">Bugfixes</a>
- <a href="#v0-1-1">v0\.1\.1</a>
  - <a href="#release-summary-23">Release Summary</a>
  - <a href="#bugfixes-18">Bugfixes</a>
- <a href="#v0-1-0">v0\.1\.0</a>
  - <a href="#release-summary-24">Release Summary</a>
  - <a href="#minor-changes-16">Minor Changes</a>

<a id="v2-13-0"></a>
## v2\.13\.0

<a id="release-summary"></a>
### Release Summary

Bugfix and feature release\.

<a id="minor-changes"></a>
### Minor Changes

* api\_info\, api\_modify \- make path <code>user group</code> modifiable and add <code>comment</code> attribute \([https\://github\.com/ansible\-collections/community\.routeros/issues/256](https\://github\.com/ansible\-collections/community\.routeros/issues/256)\, [https\://github\.com/ansible\-collections/community\.routeros/pull/257](https\://github\.com/ansible\-collections/community\.routeros/pull/257)\)\.
* api\_modify\, api\_info \- add support for the <code>ip vrf</code> path in RouterOS 7  \([https\://github\.com/ansible\-collections/community\.routeros/pull/259](https\://github\.com/ansible\-collections/community\.routeros/pull/259)\)

<a id="bugfixes"></a>
### Bugfixes

* facts \- fix date not getting removed for idempotent config export \([https\://github\.com/ansible\-collections/community\.routeros/pull/262](https\://github\.com/ansible\-collections/community\.routeros/pull/262)\)\.

<a id="v2-12-0"></a>
## v2\.12\.0

<a id="release-summary-1"></a>
### Release Summary

Feature release\.

<a id="minor-changes-1"></a>
### Minor Changes

* api\_info\, api\_modify \- add <code>interface ovpn\-client</code> path \([https\://github\.com/ansible\-collections/community\.routeros/issues/242](https\://github\.com/ansible\-collections/community\.routeros/issues/242)\, [https\://github\.com/ansible\-collections/community\.routeros/pull/244](https\://github\.com/ansible\-collections/community\.routeros/pull/244)\)\.
* api\_info\, api\_modify \- add <code>radius</code> path \([https\://github\.com/ansible\-collections/community\.routeros/issues/241](https\://github\.com/ansible\-collections/community\.routeros/issues/241)\, [https\://github\.com/ansible\-collections/community\.routeros/pull/245](https\://github\.com/ansible\-collections/community\.routeros/pull/245)\)\.
* api\_info\, api\_modify \- add <code>routing rule</code> path \([https\://github\.com/ansible\-collections/community\.routeros/issues/162](https\://github\.com/ansible\-collections/community\.routeros/issues/162)\, [https\://github\.com/ansible\-collections/community\.routeros/pull/246](https\://github\.com/ansible\-collections/community\.routeros/pull/246)\)\.
* api\_info\, api\_modify \- add missing path <code>routing bgp template</code> \([https\://github\.com/ansible\-collections/community\.routeros/pull/243](https\://github\.com/ansible\-collections/community\.routeros/pull/243)\)\.
* api\_info\, api\_modify \- add support for the <code>tx\-power</code> attribute in <code>interface wireless</code> \([https\://github\.com/ansible\-collections/community\.routeros/pull/239](https\://github\.com/ansible\-collections/community\.routeros/pull/239)\)\.
* api\_info\, api\_modify \- removed <code>host</code> primary key in <code>tool netwatch</code> path \([https\://github\.com/ansible\-collections/community\.routeros/pull/248](https\://github\.com/ansible\-collections/community\.routeros/pull/248)\)\.
* api\_modify\, api\_info \- added support for <code>interface wifiwave2</code> \([https\://github\.com/ansible\-collections/community\.routeros/pull/226](https\://github\.com/ansible\-collections/community\.routeros/pull/226)\)\.

<a id="v2-11-0"></a>
## v2\.11\.0

<a id="release-summary-2"></a>
### Release Summary

Feature and bugfix release\.

<a id="minor-changes-2"></a>
### Minor Changes

* api\_info\, api\_modify \- add missing DoH parameters <code>doh\-max\-concurrent\-queries</code>\, <code>doh\-max\-server\-connections</code>\, and <code>doh\-timeout</code> to the <code>ip dns</code> path \([https\://github\.com/ansible\-collections/community\.routeros/issues/230](https\://github\.com/ansible\-collections/community\.routeros/issues/230)\, [https\://github\.com/ansible\-collections/community\.routeros/pull/235](https\://github\.com/ansible\-collections/community\.routeros/pull/235)\)
* api\_info\, api\_modify \- add missing parameters <code>address\-list</code>\, <code>address\-list\-timeout</code>\, <code>randomise\-ports</code>\, and <code>realm</code> to subpaths of the <code>ip firewall</code> path \([https\://github\.com/ansible\-collections/community\.routeros/issues/236](https\://github\.com/ansible\-collections/community\.routeros/issues/236)\, [https\://github\.com/ansible\-collections/community\.routeros/pull/237](https\://github\.com/ansible\-collections/community\.routeros/pull/237)\)\.
* api\_info\, api\_modify \- mark the <code>interface wireless</code> parameter <code>running</code> as read\-only \([https\://github\.com/ansible\-collections/community\.routeros/pull/233](https\://github\.com/ansible\-collections/community\.routeros/pull/233)\)\.
* api\_info\, api\_modify \- set the default value to <code>false</code> for the  <code>disabled</code> parameter in some more paths where it can be seen in the documentation \([https\://github\.com/ansible\-collections/community\.routeros/pull/237](https\://github\.com/ansible\-collections/community\.routeros/pull/237)\)\.
* api\_modify \- add missing <code>comment</code> attribute to <code>/routing id</code> \([https\://github\.com/ansible\-collections/community\.routeros/pull/234](https\://github\.com/ansible\-collections/community\.routeros/pull/234)\)\.
* api\_modify \- add missing attributes to the <code>routing bgp connection</code> path \([https\://github\.com/ansible\-collections/community\.routeros/pull/234](https\://github\.com/ansible\-collections/community\.routeros/pull/234)\)\.
* api\_modify \- add versioning to the <code>/tool e\-mail</code> path \(RouterOS 7\.12 release\) \([https\://github\.com/ansible\-collections/community\.routeros/pull/234](https\://github\.com/ansible\-collections/community\.routeros/pull/234)\)\.
* api\_modify \- make <code>/ip traffic\-flow target</code> a multiple value attribute \([https\://github\.com/ansible\-collections/community\.routeros/pull/234](https\://github\.com/ansible\-collections/community\.routeros/pull/234)\)\.

<a id="v2-10-0"></a>
## v2\.10\.0

<a id="release-summary-3"></a>
### Release Summary

Bugfix and feature release\.

<a id="minor-changes-3"></a>
### Minor Changes

* api\_info \- add new <code>include\_read\_only</code> option to select behavior for read\-only values\. By default these are not returned \([https\://github\.com/ansible\-collections/community\.routeros/pull/213](https\://github\.com/ansible\-collections/community\.routeros/pull/213)\)\.
* api\_info\, api\_modify \- add support for <code>address\-list</code> and <code>match\-subdomain</code> introduced by RouterOS 7\.7 in the <code>ip dns static</code> path \([https\://github\.com/ansible\-collections/community\.routeros/pull/197](https\://github\.com/ansible\-collections/community\.routeros/pull/197)\)\.
* api\_info\, api\_modify \- add support for <code>user</code>\, <code>time</code> and <code>gmt\-offset</code> under the <code>system clock</code> path \([https\://github\.com/ansible\-collections/community\.routeros/pull/210](https\://github\.com/ansible\-collections/community\.routeros/pull/210)\)\.
* api\_info\, api\_modify \- add support for the <code>interface ppp\-client</code> path \([https\://github\.com/ansible\-collections/community\.routeros/pull/199](https\://github\.com/ansible\-collections/community\.routeros/pull/199)\)\.
* api\_info\, api\_modify \- add support for the <code>interface wireless</code> path \([https\://github\.com/ansible\-collections/community\.routeros/pull/195](https\://github\.com/ansible\-collections/community\.routeros/pull/195)\)\.
* api\_info\, api\_modify \- add support for the <code>iot modbus</code> path \([https\://github\.com/ansible\-collections/community\.routeros/pull/205](https\://github\.com/ansible\-collections/community\.routeros/pull/205)\)\.
* api\_info\, api\_modify \- add support for the <code>ip dhcp\-server option</code> and <code>ip dhcp\-server option sets</code> paths \([https\://github\.com/ansible\-collections/community\.routeros/pull/223](https\://github\.com/ansible\-collections/community\.routeros/pull/223)\)\.
* api\_info\, api\_modify \- add support for the <code>ip upnp interfaces</code>\, <code>tool graphing interface</code>\, <code>tool graphing resource</code> paths \([https\://github\.com/ansible\-collections/community\.routeros/pull/227](https\://github\.com/ansible\-collections/community\.routeros/pull/227)\)\.
* api\_info\, api\_modify \- add support for the <code>ipv6 firewall nat</code> path \([https\://github\.com/ansible\-collections/community\.routeros/pull/204](https\://github\.com/ansible\-collections/community\.routeros/pull/204)\)\.
* api\_info\, api\_modify \- add support for the <code>mode</code> property in <code>ip neighbor discovery\-settings</code> introduced in RouterOS 7\.7 \([https\://github\.com/ansible\-collections/community\.routeros/pull/198](https\://github\.com/ansible\-collections/community\.routeros/pull/198)\)\.
* api\_info\, api\_modify \- add support for the <code>port remote\-access</code> path \([https\://github\.com/ansible\-collections/community\.routeros/pull/224](https\://github\.com/ansible\-collections/community\.routeros/pull/224)\)\.
* api\_info\, api\_modify \- add support for the <code>routing filter rule</code> and <code>routing filter select\-rule</code> paths \([https\://github\.com/ansible\-collections/community\.routeros/pull/200](https\://github\.com/ansible\-collections/community\.routeros/pull/200)\)\.
* api\_info\, api\_modify \- add support for the <code>routing table</code> path in RouterOS 7 \([https\://github\.com/ansible\-collections/community\.routeros/pull/215](https\://github\.com/ansible\-collections/community\.routeros/pull/215)\)\.
* api\_info\, api\_modify \- add support for the <code>tool netwatch</code> path in RouterOS 7 \([https\://github\.com/ansible\-collections/community\.routeros/pull/216](https\://github\.com/ansible\-collections/community\.routeros/pull/216)\)\.
* api\_info\, api\_modify \- add support for the <code>user settings</code> path \([https\://github\.com/ansible\-collections/community\.routeros/pull/201](https\://github\.com/ansible\-collections/community\.routeros/pull/201)\)\.
* api\_info\, api\_modify \- add support for the <code>user</code> path \([https\://github\.com/ansible\-collections/community\.routeros/pull/211](https\://github\.com/ansible\-collections/community\.routeros/pull/211)\)\.
* api\_info\, api\_modify \- finalize fields for the <code>interface wireless security\-profiles</code> path and enable it \([https\://github\.com/ansible\-collections/community\.routeros/pull/203](https\://github\.com/ansible\-collections/community\.routeros/pull/203)\)\.
* api\_info\, api\_modify \- finalize fields for the <code>ppp profile</code> path and enable it \([https\://github\.com/ansible\-collections/community\.routeros/pull/217](https\://github\.com/ansible\-collections/community\.routeros/pull/217)\)\.
* api\_modify \- add new <code>handle\_read\_only</code> and <code>handle\_write\_only</code> options to handle the module\'s behavior for read\-only and write\-only fields \([https\://github\.com/ansible\-collections/community\.routeros/pull/213](https\://github\.com/ansible\-collections/community\.routeros/pull/213)\)\.
* api\_modify\, api\_info \- support API paths <code>routing id</code>\, <code>routing bgp connection</code> \([https\://github\.com/ansible\-collections/community\.routeros/pull/220](https\://github\.com/ansible\-collections/community\.routeros/pull/220)\)\.

<a id="bugfixes-1"></a>
### Bugfixes

* api\_info\, api\_modify \- in the <code>snmp</code> path\, ensure that <code>engine\-id\-suffix</code> is only available on RouterOS 7\.10\+\, and that <code>engine\-id</code> is read\-only on RouterOS 7\.10\+ \([https\://github\.com/ansible\-collections/community\.routeros/issues/208](https\://github\.com/ansible\-collections/community\.routeros/issues/208)\, [https\://github\.com/ansible\-collections/community\.routeros/pull/218](https\://github\.com/ansible\-collections/community\.routeros/pull/218)\)\.

<a id="v2-9-0"></a>
## v2\.9\.0

<a id="release-summary-4"></a>
### Release Summary

Bugfix and feature release\.

<a id="minor-changes-4"></a>
### Minor Changes

* api\_info\, api\_modify \- add path <code>caps\-man channel</code> and enable path <code>caps\-man manager interface</code> \([https\://github\.com/ansible\-collections/community\.routeros/issues/193](https\://github\.com/ansible\-collections/community\.routeros/issues/193)\, [https\://github\.com/ansible\-collections/community\.routeros/pull/194](https\://github\.com/ansible\-collections/community\.routeros/pull/194)\)\.
* api\_info\, api\_modify \- add path <code>ip traffic\-flow target</code> \([https\://github\.com/ansible\-collections/community\.routeros/issues/191](https\://github\.com/ansible\-collections/community\.routeros/issues/191)\, [https\://github\.com/ansible\-collections/community\.routeros/pull/192](https\://github\.com/ansible\-collections/community\.routeros/pull/192)\)\.

<a id="bugfixes-2"></a>
### Bugfixes

* api\_modify\, api\_info \- add missing parameter <code>engine\-id\-suffix</code> for the <code>snmp</code> path \([https\://github\.com/ansible\-collections/community\.routeros/issues/189](https\://github\.com/ansible\-collections/community\.routeros/issues/189)\, [https\://github\.com/ansible\-collections/community\.routeros/pull/190](https\://github\.com/ansible\-collections/community\.routeros/pull/190)\)\.

<a id="v2-8-3"></a>
## v2\.8\.3

<a id="release-summary-5"></a>
### Release Summary

Maintenance release with updated documentation\.

From this version on\, community\.routeros is using the new [Ansible semantic markup](https\://docs\.ansible\.com/ansible/devel/dev\_guide/developing\_modules\_documenting\.html\#semantic\-markup\-within\-module\-documentation)
in its documentation\. If you look at documentation with the ansible\-doc CLI tool
from ansible\-core before 2\.15\, please note that it does not render the markup
correctly\. You should be still able to read it in most cases\, but you need
ansible\-core 2\.15 or later to see it as it is intended\. Alternatively you can
look at [the devel docsite](https\://docs\.ansible\.com/ansible/devel/collections/community/routeros/)
for the rendered HTML version of the documentation of the latest release\.

<a id="known-issues"></a>
### Known Issues

* Ansible markup will show up in raw form on ansible\-doc text output for ansible\-core before 2\.15\. If you have trouble deciphering the documentation markup\, please upgrade to ansible\-core 2\.15 \(or newer\)\, or read the HTML documentation on [https\://docs\.ansible\.com/ansible/devel/collections/community/routeros/](https\://docs\.ansible\.com/ansible/devel/collections/community/routeros/)\.

<a id="v2-8-2"></a>
## v2\.8\.2

<a id="release-summary-6"></a>
### Release Summary

Bugfix release\.

<a id="bugfixes-3"></a>
### Bugfixes

* api\_modify\, api\_info \- add missing parameter <code>tls</code> for the <code>tool e\-mail</code> path \([https\://github\.com/ansible\-collections/community\.routeros/issues/179](https\://github\.com/ansible\-collections/community\.routeros/issues/179)\, [https\://github\.com/ansible\-collections/community\.routeros/pull/180](https\://github\.com/ansible\-collections/community\.routeros/pull/180)\)\.

<a id="v2-8-1"></a>
## v2\.8\.1

<a id="release-summary-7"></a>
### Release Summary

Bugfix release\.

<a id="bugfixes-4"></a>
### Bugfixes

* facts \- do not crash in CLI output preprocessing in unexpected situations during line unwrapping \([https\://github\.com/ansible\-collections/community\.routeros/issues/170](https\://github\.com/ansible\-collections/community\.routeros/issues/170)\, [https\://github\.com/ansible\-collections/community\.routeros/pull/177](https\://github\.com/ansible\-collections/community\.routeros/pull/177)\)\.

<a id="v2-8-0"></a>
## v2\.8\.0

<a id="release-summary-8"></a>
### Release Summary

Bugfix and feature release\.

<a id="minor-changes-5"></a>
### Minor Changes

* api\_modify \- adapt data for API paths <code>ip dhcp\-server network</code> \([https\://github\.com/ansible\-collections/community\.routeros/pull/156](https\://github\.com/ansible\-collections/community\.routeros/pull/156)\)\.
* api\_modify \- add support for API path <code>snmp community</code> \([https\://github\.com/ansible\-collections/community\.routeros/pull/159](https\://github\.com/ansible\-collections/community\.routeros/pull/159)\)\.
* api\_modify \- add support for <code>trap\-interfaces</code> in API path <code>snmp</code> \([https\://github\.com/ansible\-collections/community\.routeros/pull/159](https\://github\.com/ansible\-collections/community\.routeros/pull/159)\)\.
* api\_modify \- add support to disable IPv6 in API paths <code>ipv6 settings</code> \([https\://github\.com/ansible\-collections/community\.routeros/pull/158](https\://github\.com/ansible\-collections/community\.routeros/pull/158)\)\.
* api\_modify \- support API paths <code>ip firewall layer7\-protocol</code> \([https\://github\.com/ansible\-collections/community\.routeros/pull/153](https\://github\.com/ansible\-collections/community\.routeros/pull/153)\)\.
* command \- workaround for extra characters in stdout in RouterOS versions between 6\.49 and 7\.1\.5 \([https\://github\.com/ansible\-collections/community\.routeros/issues/62](https\://github\.com/ansible\-collections/community\.routeros/issues/62)\, [https\://github\.com/ansible\-collections/community\.routeros/pull/161](https\://github\.com/ansible\-collections/community\.routeros/pull/161)\)\.

<a id="bugfixes-5"></a>
### Bugfixes

* api\_info\, api\_modify \- fix default and remove behavior for <code>dhcp\-options</code> in path <code>ip dhcp\-client</code> \([https\://github\.com/ansible\-collections/community\.routeros/issues/148](https\://github\.com/ansible\-collections/community\.routeros/issues/148)\, [https\://github\.com/ansible\-collections/community\.routeros/pull/154](https\://github\.com/ansible\-collections/community\.routeros/pull/154)\)\.
* api\_modify \- fix handling of disabled keys on creation \([https\://github\.com/ansible\-collections/community\.routeros/pull/154](https\://github\.com/ansible\-collections/community\.routeros/pull/154)\)\.
* various plugins and modules \- remove unnecessary imports \([https\://github\.com/ansible\-collections/community\.routeros/pull/149](https\://github\.com/ansible\-collections/community\.routeros/pull/149)\)\.

<a id="v2-7-0"></a>
## v2\.7\.0

<a id="release-summary-9"></a>
### Release Summary

Bugfix and feature release\.

<a id="minor-changes-6"></a>
### Minor Changes

* api\_modify\, api\_info \- support API paths <code>ip arp</code>\, <code>ip firewall raw</code>\, <code>ipv6 firewall raw</code> \([https\://github\.com/ansible\-collections/community\.routeros/pull/144](https\://github\.com/ansible\-collections/community\.routeros/pull/144)\)\.

<a id="bugfixes-6"></a>
### Bugfixes

* api\_modify\, api\_info \- defaults corrected for fields in <code>interface wireguard peers</code> API path \([https\://github\.com/ansible\-collections/community\.routeros/pull/144](https\://github\.com/ansible\-collections/community\.routeros/pull/144)\)\.

<a id="v2-6-0"></a>
## v2\.6\.0

<a id="release-summary-10"></a>
### Release Summary

Regular bugfix and feature release\.

<a id="minor-changes-7"></a>
### Minor Changes

* api\_modify\, api\_info \- add field <code>regexp</code> to <code>ip dns static</code> \([https\://github\.com/ansible\-collections/community\.routeros/issues/141](https\://github\.com/ansible\-collections/community\.routeros/issues/141)\)\.
* api\_modify\, api\_info \- support API paths <code>interface wireguard</code>\, <code>interface wireguard peers</code> \([https\://github\.com/ansible\-collections/community\.routeros/pull/143](https\://github\.com/ansible\-collections/community\.routeros/pull/143)\)\.

<a id="bugfixes-7"></a>
### Bugfixes

* api\_modify \- do not use <code>name</code> as a unique key in <code>ip dns static</code> \([https\://github\.com/ansible\-collections/community\.routeros/issues/141](https\://github\.com/ansible\-collections/community\.routeros/issues/141)\)\.
* api\_modify\, api\_info \- do not crash if router contains <code>regexp</code> DNS entries in <code>ip dns static</code> \([https\://github\.com/ansible\-collections/community\.routeros/issues/141](https\://github\.com/ansible\-collections/community\.routeros/issues/141)\)\.

<a id="v2-5-0"></a>
## v2\.5\.0

<a id="release-summary-11"></a>
### Release Summary

Feature and bugfix release\.

<a id="minor-changes-8"></a>
### Minor Changes

* api\_info\, api\_modify \- support API paths <code>interface ethernet poe</code>\, <code>interface gre6</code>\, <code>interface vrrp</code> and also support all previously missing fields of entries in <code>ip dhcp\-server</code> \([https\://github\.com/ansible\-collections/community\.routeros/pull/137](https\://github\.com/ansible\-collections/community\.routeros/pull/137)\)\.

<a id="bugfixes-8"></a>
### Bugfixes

* api\_modify \- <code>address\-pool</code> field of entries in API path <code>ip dhcp\-server</code> is not required anymore \([https\://github\.com/ansible\-collections/community\.routeros/pull/137](https\://github\.com/ansible\-collections/community\.routeros/pull/137)\)\.

<a id="v2-4-0"></a>
## v2\.4\.0

<a id="release-summary-12"></a>
### Release Summary

Feature release improving the <code>api\*</code> modules\.

<a id="minor-changes-9"></a>
### Minor Changes

* api\* modules \- Add new option <code>force\_no\_cert</code> to connect with ADH ciphers \([https\://github\.com/ansible\-collections/community\.routeros/pull/124](https\://github\.com/ansible\-collections/community\.routeros/pull/124)\)\.
* api\_info \- new parameter <code>include\_builtin</code> which allows to include \"builtin\" entries that are automatically generated by ROS and cannot be modified by the user \([https\://github\.com/ansible\-collections/community\.routeros/pull/130](https\://github\.com/ansible\-collections/community\.routeros/pull/130)\)\.
* api\_modify\, api\_info \- support API paths \- <code>interface bonding</code>\, <code>interface bridge mlag</code>\, <code>ipv6 firewall mangle</code>\, <code>ipv6 nd</code>\, <code>system scheduler</code>\, <code>system script</code>\, <code>system ups</code> \([https\://github\.com/ansible\-collections/community\.routeros/pull/133](https\://github\.com/ansible\-collections/community\.routeros/pull/133)\)\.
* api\_modify\, api\_info \- support API paths <code>caps\-man access\-list</code>\, <code>caps\-man configuration</code>\, <code>caps\-man datapath</code>\, <code>caps\-man manager</code>\, <code>caps\-man provisioning</code>\, <code>caps\-man security</code> \([https\://github\.com/ansible\-collections/community\.routeros/pull/126](https\://github\.com/ansible\-collections/community\.routeros/pull/126)\)\.
* api\_modify\, api\_info \- support API paths <code>interface list</code> and <code>interface list member</code> \([https\://github\.com/ansible\-collections/community\.routeros/pull/120](https\://github\.com/ansible\-collections/community\.routeros/pull/120)\)\.
* api\_modify\, api\_info \- support API paths <code>interface pppoe\-client</code>\, <code>interface vlan</code>\, <code>interface bridge</code>\, <code>interface bridge vlan</code> \([https\://github\.com/ansible\-collections/community\.routeros/pull/125](https\://github\.com/ansible\-collections/community\.routeros/pull/125)\)\.
* api\_modify\, api\_info \- support API paths <code>ip ipsec identity</code>\, <code>ip ipsec peer</code>\, <code>ip ipsec policy</code>\, <code>ip ipsec profile</code>\, <code>ip ipsec proposal</code> \([https\://github\.com/ansible\-collections/community\.routeros/pull/129](https\://github\.com/ansible\-collections/community\.routeros/pull/129)\)\.
* api\_modify\, api\_info \- support API paths <code>ip route</code> and <code>ip route vrf</code> \([https\://github\.com/ansible\-collections/community\.routeros/pull/123](https\://github\.com/ansible\-collections/community\.routeros/pull/123)\)\.
* api\_modify\, api\_info \- support API paths <code>ipv6 address</code>\, <code>ipv6 dhcp\-server</code>\, <code>ipv6 dhcp\-server option</code>\, <code>ipv6 route</code>\, <code>queue tree</code>\, <code>routing ospf area</code>\, <code>routing ospf area range</code>\, <code>routing ospf instance</code>\, <code>routing ospf interface\-template</code>\, <code>routing pimsm instance</code>\, <code>routing pimsm interface\-template</code> \([https\://github\.com/ansible\-collections/community\.routeros/pull/131](https\://github\.com/ansible\-collections/community\.routeros/pull/131)\)\.
* api\_modify\, api\_info \- support API paths <code>system logging</code>\, <code>system logging action</code> \([https\://github\.com/ansible\-collections/community\.routeros/pull/127](https\://github\.com/ansible\-collections/community\.routeros/pull/127)\)\.
* api\_modify\, api\_info \- support field <code>hw\-offload</code> for path <code>ip firewall filter</code> \([https\://github\.com/ansible\-collections/community\.routeros/pull/121](https\://github\.com/ansible\-collections/community\.routeros/pull/121)\)\.
* api\_modify\, api\_info \- support fields <code>address\-list</code>\, <code>address\-list\-timeout</code>\, <code>connection\-bytes</code>\, <code>connection\-limit</code>\, <code>connection\-mark</code>\, <code>connection\-rate</code>\, <code>connection\-type</code>\, <code>content</code>\, <code>disabled</code>\, <code>dscp</code>\, <code>dst\-address\-list</code>\, <code>dst\-address\-type</code>\, <code>dst\-limit</code>\, <code>fragment</code>\, <code>hotspot</code>\, <code>icmp\-options</code>\, <code>in\-bridge\-port</code>\, <code>in\-bridge\-port\-list</code>\, <code>ingress\-priority</code>\, <code>ipsec\-policy</code>\, <code>ipv4\-options</code>\, <code>jump\-target</code>\, <code>layer7\-protocol</code>\, <code>limit</code>\, <code>log</code>\, <code>log\-prefix</code>\, <code>nth</code>\, <code>out\-bridge\-port</code>\, <code>out\-bridge\-port\-list</code>\, <code>packet\-mark</code>\, <code>packet\-size</code>\, <code>per\-connection\-classifier</code>\, <code>port</code>\, <code>priority</code>\, <code>psd</code>\, <code>random</code>\, <code>realm</code>\, <code>routing\-mark</code>\, <code>same\-not\-by\-dst</code>\, <code>src\-address</code>\, <code>src\-address\-list</code>\, <code>src\-address\-type</code>\, <code>src\-mac\-address</code>\, <code>src\-port</code>\, <code>tcp\-mss</code>\, <code>time</code>\, <code>tls\-host</code>\, <code>ttl</code> in <code>ip firewall nat</code> path \([https\://github\.com/ansible\-collections/community\.routeros/pull/133](https\://github\.com/ansible\-collections/community\.routeros/pull/133)\)\.
* api\_modify\, api\_info \- support fields <code>combo\-mode</code>\, <code>comment</code>\, <code>fec\-mode</code>\, <code>mdix\-enable</code>\, <code>poe\-out</code>\, <code>poe\-priority</code>\, <code>poe\-voltage</code>\, <code>power\-cycle\-interval</code>\, <code>power\-cycle\-ping\-address</code>\, <code>power\-cycle\-ping\-enabled</code>\, <code>power\-cycle\-ping\-timeout</code> for path <code>interface ethernet</code> \([https\://github\.com/ansible\-collections/community\.routeros/pull/121](https\://github\.com/ansible\-collections/community\.routeros/pull/121)\)\.
* api\_modify\, api\_info \- support fields <code>jump\-target</code>\, <code>reject\-with</code> in <code>ip firewall filter</code> API path\, field <code>comment</code> in <code>ip firwall address\-list</code> API path\, field <code>jump\-target</code> in <code>ip firewall mangle</code> API path\, field <code>comment</code> in <code>ipv6 firewall address\-list</code> API path\, fields <code>jump\-target</code>\, <code>reject\-with</code> in <code>ipv6 firewall filter</code> API path \([https\://github\.com/ansible\-collections/community\.routeros/pull/133](https\://github\.com/ansible\-collections/community\.routeros/pull/133)\)\.
* api\_modify\, api\_info \- support for API fields that can be disabled and have default value at the same time\, support API paths <code>interface gre</code>\, <code>interface eoip</code> \([https\://github\.com/ansible\-collections/community\.routeros/pull/128](https\://github\.com/ansible\-collections/community\.routeros/pull/128)\)\.
* api\_modify\, api\_info \- support for fields <code>blackhole</code>\, <code>pref\-src</code>\, <code>routing\-table</code>\, <code>suppress\-hw\-offload</code>\, <code>type</code>\, <code>vrf\-interface</code> in <code>ip route</code> path \([https\://github\.com/ansible\-collections/community\.routeros/pull/131](https\://github\.com/ansible\-collections/community\.routeros/pull/131)\)\.
* api\_modify\, api\_info \- support paths <code>system ntp client servers</code> and <code>system ntp server</code> available in ROS7\, as well as new fields <code>servers</code>\, <code>mode</code>\, and <code>vrf</code> for <code>system ntp client</code> \([https\://github\.com/ansible\-collections/community\.routeros/pull/122](https\://github\.com/ansible\-collections/community\.routeros/pull/122)\)\.

<a id="bugfixes-9"></a>
### Bugfixes

* api\_modify \- <code>ip route</code> entry can be defined without the need of <code>gateway</code> field\, which is correct for unreachable/blackhole type of routes \([https\://github\.com/ansible\-collections/community\.routeros/pull/131](https\://github\.com/ansible\-collections/community\.routeros/pull/131)\)\.
* api\_modify \- <code>queue interface</code> path works now \([https\://github\.com/ansible\-collections/community\.routeros/pull/131](https\://github\.com/ansible\-collections/community\.routeros/pull/131)\)\.
* api\_modify\, api\_info \- removed wrong field <code>dynamic</code> from API path <code>ipv6 firewall address\-list</code> \([https\://github\.com/ansible\-collections/community\.routeros/pull/133](https\://github\.com/ansible\-collections/community\.routeros/pull/133)\)\.
* api\_modify\, api\_info \- the default of the field <code>ingress\-filtering</code> in <code>interface bridge port</code> is now <code>true</code>\, which is the default in ROS \([https\://github\.com/ansible\-collections/community\.routeros/pull/125](https\://github\.com/ansible\-collections/community\.routeros/pull/125)\)\.
* command\, facts \- commands do not timeout in safe mode anymore \([https\://github\.com/ansible\-collections/community\.routeros/pull/134](https\://github\.com/ansible\-collections/community\.routeros/pull/134)\)\.

<a id="known-issues-1"></a>
### Known Issues

* api\_modify \- when limits for entries in <code>queue tree</code> are defined as human readable \- for example <code>25M</code> \-\, the configuration will be correctly set in ROS\, but the module will indicate the item is changed on every run even when there was no change done\. This is caused by the ROS API which returns the number in bytes \- for example <code>25000000</code> \(which is inconsistent with the CLI behavior\)\. In order to mitigate that\, the limits have to be defined in bytes \(those will still appear as human readable in the ROS CLI\) \([https\://github\.com/ansible\-collections/community\.routeros/pull/131](https\://github\.com/ansible\-collections/community\.routeros/pull/131)\)\.
* api\_modify\, api\_info \- <code>routing ospf area</code>\, <code>routing ospf area range</code>\, <code>routing ospf instance</code>\, <code>routing ospf interface\-template</code> paths are not fully implemented for ROS6 due to the significant changes between ROS6 and ROS7 \([https\://github\.com/ansible\-collections/community\.routeros/pull/131](https\://github\.com/ansible\-collections/community\.routeros/pull/131)\)\.

<a id="v2-3-1"></a>
## v2\.3\.1

<a id="release-summary-13"></a>
### Release Summary

Maintenance release with improved documentation\.

<a id="known-issues-2"></a>
### Known Issues

* The <code>community\.routeros\.command</code> module claims to support check mode\. Since it cannot judge whether the commands executed modify state or not\, this behavior is incorrect\. Since this potentially breaks existing playbooks\, we will not change this behavior until community\.routeros 3\.0\.0\.

<a id="v2-3-0"></a>
## v2\.3\.0

<a id="release-summary-14"></a>
### Release Summary

Feature and bugfix release\.

<a id="minor-changes-10"></a>
### Minor Changes

* The collection repository conforms to the [REUSE specification](https\://reuse\.software/spec/) except for the changelog fragments \([https\://github\.com/ansible\-collections/community\.routeros/pull/108](https\://github\.com/ansible\-collections/community\.routeros/pull/108)\)\.
* api\* modules \- added <code>timeout</code> parameter \([https\://github\.com/ansible\-collections/community\.routeros/pull/109](https\://github\.com/ansible\-collections/community\.routeros/pull/109)\)\.
* api\_modify\, api\_info \- support API path <code>ip firewall mangle</code> \([https\://github\.com/ansible\-collections/community\.routeros/pull/110](https\://github\.com/ansible\-collections/community\.routeros/pull/110)\)\.

<a id="bugfixes-10"></a>
### Bugfixes

* api\_modify\, api\_info \- make API path <code>ip dhcp\-server</code> support <code>script</code>\, and <code>ip firewall nat</code> support <code>in\-interface</code> and <code>in\-interface\-list</code> \([https\://github\.com/ansible\-collections/community\.routeros/pull/110](https\://github\.com/ansible\-collections/community\.routeros/pull/110)\)\.

<a id="v2-2-1"></a>
## v2\.2\.1

<a id="release-summary-15"></a>
### Release Summary

Bugfix release\.

<a id="bugfixes-11"></a>
### Bugfixes

* api\_modify\, api\_info \- make API path <code>ip dhcp\-server lease</code> support <code>server\=all</code> \([https\://github\.com/ansible\-collections/community\.routeros/issues/104](https\://github\.com/ansible\-collections/community\.routeros/issues/104)\, [https\://github\.com/ansible\-collections/community\.routeros/pull/107](https\://github\.com/ansible\-collections/community\.routeros/pull/107)\)\.
* api\_modify\, api\_info \- make API path <code>ip dhcp\-server network</code> support missing options <code>boot\-file\-name</code>\, <code>dhcp\-option\-set</code>\, <code>dns\-none</code>\, <code>domain</code>\, and <code>next\-server</code> \([https\://github\.com/ansible\-collections/community\.routeros/issues/104](https\://github\.com/ansible\-collections/community\.routeros/issues/104)\, [https\://github\.com/ansible\-collections/community\.routeros/pull/106](https\://github\.com/ansible\-collections/community\.routeros/pull/106)\)\.

<a id="v2-2-0"></a>
## v2\.2\.0

<a id="release-summary-16"></a>
### Release Summary

New feature release\.

<a id="minor-changes-11"></a>
### Minor Changes

* All software licenses are now in the <code>LICENSES/</code> directory of the collection root\. Moreover\, <code>SPDX\-License\-Identifier\:</code> is used to declare the applicable license for every file that is not automatically generated \([https\://github\.com/ansible\-collections/community\.routeros/pull/101](https\://github\.com/ansible\-collections/community\.routeros/pull/101)\)\.

<a id="bugfixes-12"></a>
### Bugfixes

* Include <code>LICENSES/BSD\-2\-Clause\.txt</code> file for the <code>routeros</code> module utils \([https\://github\.com/ansible\-collections/community\.routeros/pull/101](https\://github\.com/ansible\-collections/community\.routeros/pull/101)\)\.

<a id="new-modules"></a>
### New Modules

* api\_info \- Retrieve information from API
* api\_modify \- Modify data at paths with API

<a id="v2-1-0"></a>
## v2\.1\.0

<a id="release-summary-17"></a>
### Release Summary

Feature and bugfix release with new modules\.

<a id="minor-changes-12"></a>
### Minor Changes

* Added a <code>community\.routeros\.api</code> module defaults group\. Use with <code>group/community\.routeros\.api</code> to provide options for all API\-based modules \([https\://github\.com/ansible\-collections/community\.routeros/pull/89](https\://github\.com/ansible\-collections/community\.routeros/pull/89)\)\.
* Prepare collection for inclusion in an Execution Environment by declaring its dependencies \([https\://github\.com/ansible\-collections/community\.routeros/pull/83](https\://github\.com/ansible\-collections/community\.routeros/pull/83)\)\.
* api \- add new option <code>extended query</code> more complex queries against RouterOS API \([https\://github\.com/ansible\-collections/community\.routeros/pull/63](https\://github\.com/ansible\-collections/community\.routeros/pull/63)\)\.
* api \- update <code>query</code> to accept symbolic parameters \([https\://github\.com/ansible\-collections/community\.routeros/pull/63](https\://github\.com/ansible\-collections/community\.routeros/pull/63)\)\.
* api\* modules \- allow to set an encoding other than the default ASCII for communicating with the API \([https\://github\.com/ansible\-collections/community\.routeros/pull/95](https\://github\.com/ansible\-collections/community\.routeros/pull/95)\)\.

<a id="bugfixes-13"></a>
### Bugfixes

* query \- fix query function check for <code>\.id</code> vs\. <code>id</code> arguments to not conflict with routeros arguments like <code>identity</code> \([https\://github\.com/ansible\-collections/community\.routeros/pull/68](https\://github\.com/ansible\-collections/community\.routeros/pull/68)\, [https\://github\.com/ansible\-collections/community\.routeros/issues/67](https\://github\.com/ansible\-collections/community\.routeros/issues/67)\)\.
* quoting and unquoting filter plugins\, api module \- handle the escape sequence <code>\\\_</code> correctly as escaping a space and not an underscore \([https\://github\.com/ansible\-collections/community\.routeros/pull/89](https\://github\.com/ansible\-collections/community\.routeros/pull/89)\)\.

<a id="new-modules-1"></a>
### New Modules

* api\_facts \- Collect facts from remote devices running MikroTik RouterOS using the API
* api\_find\_and\_modify \- Find and modify information using the API

<a id="v2-0-0"></a>
## v2\.0\.0

<a id="release-summary-18"></a>
### Release Summary

A new major release with breaking changes in the behavior of <code>community\.routeros\.api</code> and <code>community\.routeros\.command</code>\.

<a id="minor-changes-13"></a>
### Minor Changes

* api \- make validation of <code>WHERE</code> for <code>query</code> more strict \([https\://github\.com/ansible\-collections/community\.routeros/pull/53](https\://github\.com/ansible\-collections/community\.routeros/pull/53)\)\.
* command \- the <code>commands</code> and <code>wait\_for</code> options now convert the list elements to strings \([https\://github\.com/ansible\-collections/community\.routeros/pull/55](https\://github\.com/ansible\-collections/community\.routeros/pull/55)\)\.
* facts \- the <code>gather\_subset</code> option now converts the list elements to strings \([https\://github\.com/ansible\-collections/community\.routeros/pull/55](https\://github\.com/ansible\-collections/community\.routeros/pull/55)\)\.

<a id="breaking-changes--porting-guide"></a>
### Breaking Changes / Porting Guide

* api \- due to a programming error\, the module never failed on errors\. This has now been fixed\. If you are relying on the module not failing in case of idempotent commands \(resulting in errors like <code>failure\: already have such address</code>\)\, you need to adjust your roles/playbooks\. We suggest to use <code>failed\_when</code> to accept failure in specific circumstances\, for example <code>failed\_when\: \"\'failure\: already have \' in result\.msg\[0\]\"</code> \([https\://github\.com/ansible\-collections/community\.routeros/pull/39](https\://github\.com/ansible\-collections/community\.routeros/pull/39)\)\.
* api \- splitting commands no longer uses a naive split by whitespace\, but a more RouterOS CLI compatible splitting algorithm \([https\://github\.com/ansible\-collections/community\.routeros/pull/45](https\://github\.com/ansible\-collections/community\.routeros/pull/45)\)\.
* command \- the module now always indicates that a change happens\. If this is not correct\, please use <code>changed\_when</code> to determine the correct changed status for a task \([https\://github\.com/ansible\-collections/community\.routeros/pull/50](https\://github\.com/ansible\-collections/community\.routeros/pull/50)\)\.

<a id="bugfixes-14"></a>
### Bugfixes

* api \- improve splitting of <code>WHERE</code> queries \([https\://github\.com/ansible\-collections/community\.routeros/pull/47](https\://github\.com/ansible\-collections/community\.routeros/pull/47)\)\.
* api \- when converting result lists to dictionaries\, no longer removes second <code>\=</code> and text following that if present \([https\://github\.com/ansible\-collections/community\.routeros/pull/47](https\://github\.com/ansible\-collections/community\.routeros/pull/47)\)\.
* routeros cliconf plugin \- adjust function signature that was modified in Ansible after creation of this plugin \([https\://github\.com/ansible\-collections/community\.routeros/pull/43](https\://github\.com/ansible\-collections/community\.routeros/pull/43)\)\.

<a id="new-plugins"></a>
### New Plugins

<a id="filter"></a>
#### Filter

* join \- Join a list of arguments to a command
* list\_to\_dict \- Convert a list of arguments to a list of dictionary
* quote\_argument \- Quote an argument
* quote\_argument\_value \- Quote an argument value
* split \- Split a command into arguments

<a id="v1-2-0"></a>
## v1\.2\.0

<a id="release-summary-19"></a>
### Release Summary

Bugfix and feature release\.

<a id="minor-changes-14"></a>
### Minor Changes

* Avoid internal ansible\-core module\_utils in favor of equivalent public API available since at least Ansible 2\.9 \([https\://github\.com/ansible\-collections/community\.routeros/pull/38](https\://github\.com/ansible\-collections/community\.routeros/pull/38)\)\.
* api \- add options <code>validate\_certs</code> \(default value <code>true</code>\)\, <code>validate\_cert\_hostname</code> \(default value <code>false</code>\)\, and <code>ca\_path</code> to control certificate validation \([https\://github\.com/ansible\-collections/community\.routeros/pull/37](https\://github\.com/ansible\-collections/community\.routeros/pull/37)\)\.
* api \- rename option <code>ssl</code> to <code>tls</code>\, and keep the old name as an alias \([https\://github\.com/ansible\-collections/community\.routeros/pull/37](https\://github\.com/ansible\-collections/community\.routeros/pull/37)\)\.
* fact \- add fact <code>ansible\_net\_config\_nonverbose</code> to get idempotent config \(no date\, no verbose\) \([https\://github\.com/ansible\-collections/community\.routeros/pull/23](https\://github\.com/ansible\-collections/community\.routeros/pull/23)\)\.

<a id="bugfixes-15"></a>
### Bugfixes

* api \- when using TLS/SSL\, remove explicit cipher configuration to insecure values\, which also makes it impossible to connect to newer RouterOS versions \([https\://github\.com/ansible\-collections/community\.routeros/pull/34](https\://github\.com/ansible\-collections/community\.routeros/pull/34)\)\.

<a id="v1-1-0"></a>
## v1\.1\.0

<a id="release-summary-20"></a>
### Release Summary

This release allow dashes in usernames for SSH\-based modules\.

<a id="minor-changes-15"></a>
### Minor Changes

* command \- added support for a dash \(<code>\-</code>\) in username \([https\://github\.com/ansible\-collections/community\.routeros/pull/18](https\://github\.com/ansible\-collections/community\.routeros/pull/18)\)\.
* facts \- added support for a dash \(<code>\-</code>\) in username \([https\://github\.com/ansible\-collections/community\.routeros/pull/18](https\://github\.com/ansible\-collections/community\.routeros/pull/18)\)\.

<a id="v1-0-1"></a>
## v1\.0\.1

<a id="release-summary-21"></a>
### Release Summary

Maintenance release with a bugfix for <code>api</code>\.

<a id="bugfixes-16"></a>
### Bugfixes

* api \- remove <code>id to \.id</code> as default requirement which conflicts with RouterOS <code>id</code> configuration parameter \([https\://github\.com/ansible\-collections/community\.routeros/pull/15](https\://github\.com/ansible\-collections/community\.routeros/pull/15)\)\.

<a id="v1-0-0"></a>
## v1\.0\.0

<a id="release-summary-22"></a>
### Release Summary

This is the first production \(non\-prerelease\) release of <code>community\.routeros</code>\.

<a id="bugfixes-17"></a>
### Bugfixes

* routeros terminal plugin \- allow slashes in hostnames for terminal detection\. Without this\, slashes in hostnames will result in connection timeouts \([https\://github\.com/ansible\-collections/community\.network/pull/138](https\://github\.com/ansible\-collections/community\.network/pull/138)\)\.

<a id="v0-1-1"></a>
## v0\.1\.1

<a id="release-summary-23"></a>
### Release Summary

Small improvements and bugfixes over the initial release\.

<a id="bugfixes-18"></a>
### Bugfixes

* api \- fix crash when the <code>ssl</code> parameter is used \([https\://github\.com/ansible\-collections/community\.routeros/pull/3](https\://github\.com/ansible\-collections/community\.routeros/pull/3)\)\.

<a id="v0-1-0"></a>
## v0\.1\.0

<a id="release-summary-24"></a>
### Release Summary

The <code>community\.routeros</code> continues the work on the Ansible RouterOS modules from their state in <code>community\.network</code> 1\.2\.0\. The changes listed here are thus relative to the modules <code>community\.network\.routeros\_\*</code>\.

<a id="minor-changes-16"></a>
### Minor Changes

* facts \- now also collecting data about BGP and OSPF \([https\://github\.com/ansible\-collections/community\.network/pull/101](https\://github\.com/ansible\-collections/community\.network/pull/101)\)\.
* facts \- set configuration export on to verbose\, for full configuration export \([https\://github\.com/ansible\-collections/community\.network/pull/104](https\://github\.com/ansible\-collections/community\.network/pull/104)\)\.
