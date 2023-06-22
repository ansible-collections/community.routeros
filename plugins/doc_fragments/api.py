# -*- coding: utf-8 -*-

# Copyright (c) 2020, Nikolay Dachev <nikolay@dachev.info>
# GNU General Public License v3.0+ https://www.gnu.org/licenses/gpl-3.0.txt
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type


class ModuleDocFragment(object):

    DOCUMENTATION = r'''
options:
  hostname:
    description:
      - RouterOS hostname API.
    required: true
    type: str
  username:
    description:
      - RouterOS login user.
    required: true
    type: str
  password:
    description:
      - RouterOS user password.
    required: true
    type: str
  timeout:
    description:
      - Timeout for the request.
    type: int
    default: 10
    version_added: 2.3.0
  tls:
    description:
      - If is set TLS will be used for RouterOS API connection.
    required: false
    type: bool
    default: false
    aliases:
      - ssl
  port:
    description:
      - RouterOS api port. If O(tls) is set, port will apply to TLS/SSL connection.
      - Defaults are V(8728) for the HTTP API, and V(8729) for the HTTPS API.
    type: int
  force_no_cert:
    description:
      - Set to V(true) to connect without a certificate when O(tls=true).
      - See also O(validate_certs).
      - B(Note:) this forces the use of anonymous Diffie-Hellman (ADH) ciphers. The protocol is susceptible
        to Man-in-the-Middle attacks, because the keys used in the exchange are not authenticated.
        Instead of simply connecting without a certificate to "make things work" have a look at
        O(validate_certs) and O(ca_path).
    type: bool
    default: false
    version_added: 2.4.0
  validate_certs:
    description:
      - Set to V(false) to skip validation of TLS certificates.
      - See also O(validate_cert_hostname). Only used when O(tls=true).
      - B(Note:) instead of simply deactivating certificate validations to "make things work",
        please consider creating your own CA certificate and using it to sign certificates used
        for your router. You can tell the module about your CA certificate with the O(ca_path)
        option.
    type: bool
    default: true
    version_added: 1.2.0
  validate_cert_hostname:
    description:
      - Set to V(true) to validate hostnames in certificates.
      - See also O(validate_certs). Only used when O(tls=true) and O(validate_certs=true).
    type: bool
    default: false
    version_added: 1.2.0
  ca_path:
    description:
      - PEM formatted file that contains a CA certificate to be used for certificate validation.
      - See also O(validate_cert_hostname). Only used when O(tls=true) and O(validate_certs=true).
    type: path
    version_added: 1.2.0
  encoding:
    description:
      - Use the specified encoding when communicating with the RouterOS device.
      - Default is V(ASCII). Note that V(UTF-8) requires librouteros 3.2.1 or newer.
    type: str
    default: ASCII
    version_added: 2.1.0
requirements:
  - librouteros
  - Python >= 3.6 (for librouteros)
seealso:
  - ref: ansible_collections.community.routeros.docsite.api-guide
    description: How to connect to RouterOS devices with the RouterOS API
'''
