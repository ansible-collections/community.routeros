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
      - RouterOS api port. If I(tls) is set, port will apply to TLS/SSL connection.
      - Defaults are C(8728) for the HTTP API, and C(8729) for the HTTPS API.
    type: int
  validate_certs:
    description:
      - Set to C(false) to skip validation of TLS certificates.
      - See also I(validate_cert_hostname). Only used when I(tls=true).
      - B(Note:) instead of simply deactivating certificate validations to "make things work",
        please consider creating your own CA certificate and using it to sign certificates used
        for your router. You can tell the module about your CA certificate with the I(ca_path)
        option.
    type: bool
    default: true
    version_added: 1.2.0
  validate_cert_hostname:
    description:
      - Set to C(true) to validate hostnames in certificates.
      - See also I(validate_certs). Only used when I(tls=true) and I(validate_certs=true).
    type: bool
    default: false
    version_added: 1.2.0
  ca_path:
    description:
      - PEM formatted file that contains a CA certificate to be used for certificate validation.
      - See also I(validate_cert_hostname). Only used when I(tls=true) and I(validate_certs=true).
    type: path
    version_added: 1.2.0
  encoding:
    description:
      - Use the specified encoding when communicating with the RouterOS device.
      - Default is C(ASCII). Note that C(UTF-8) requires librouteros 3.2.1 or newer.
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
