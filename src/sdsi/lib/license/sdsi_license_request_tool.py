#!/usr/bin/env python
#################################################################################
# INTEL CONFIDENTIAL
# Copyright Intel Corporation All Rights Reserved.
#
# The source code contained or described herein and all documents related to
# the source code ("Material") are owned by Intel Corporation or its suppliers
# or licensors. Title to the Material remains with Intel Corporation or its
# suppliers and licensors. The Material may contain trade secrets and proprietary
# and confidential information of Intel Corporation and its suppliers and
# licensors, and is protected by worldwide copyright and trade secret laws and
# treaty provisions. No part of the Material may be used, copied, reproduced,
# modified, published, uploaded, posted, transmitted, distributed, or disclosed
# in any way without Intel's prior express written permission.
#
# No license under any patent, copyright, trade secret or other intellectual
# property right is granted to or conferred upon you by disclosure or delivery
# of the Materials, either expressly, by implication, inducement, estoppel or
# otherwise. Any license under such intellectual property rights must be express
# and approved by Intel in writing.
#################################################################################
"""Provides an interface to interact with the SDSi API to request SDSi Licenses

    Typical usage example:
        self._sdsi_license_tool = SDSiLicenseTool(api_key, self._log.info, self._log.error) if api_key else None
        order_id = self._sdsi_license_tool.create_order([self.get_cpu_hw_asset_id(socket)], feature_list)
        lac_path = self._sdsi_license_tool.install_license_package(order_id)[0]
"""
import base64
import json
import os
import shutil
import time
import zipfile
from typing import Callable, List

import requests

import src.sdsi.lib.sdsi_exceptions as SDSiExceptions


class SDSiLicenseTool:
    """License wrapper class which provides functions for interacting with the SDSi license requesting API."""

    ORDER_TEMPLATE: dict = {
                        "customer": {
                            "soldTo": {
                                "customerIdType": "CMF_ID",
                                "customerId": "9999999999"
                            },
                            "shipTo": {
                                "customerIdType": "CMF_ID",
                                "customerId": "9999999999"
                            }
                        },
                        "productsOrdered": [],
                        "hardwareAssets": {
                            "assetIdType": "PPIN",
                            "assetIds": []
                        }
                    }
    PROXIES: dict = {'http': 'child-prc.intel.com:913',
                     'https': 'child-prc.intel.com:913'}
    ORDER_URL: str = 'https://api.sdsi-prx.intel.com/v3/orders'
    INSTALL_URL: str = 'https://api.sdsi-prx.intel.com/v3/license-activation-codes/package?orderId={}'

    def __init__(self, api_key: str, info_log: Callable[[str], None] = print, error_log: Callable[[str], None] = print)\
            -> None:
        """Initialize the license request tool.

        Args:
            api_key: The API key for the SDSi API.
            info_log: The function used to log INFO level messages.
            error_log: The function used to log ERROR level messages.
        """
        self.request_header: dict = {'accept': 'application/json',
                                     'X-Api-Key': api_key,
                                     'Content-Type': 'application/json'}
        self._status_header: dict = {'accept': 'application/json',
                                     'X-Api-Key': api_key}
        self._install_header: dict = {'accept': 'application/zip',
                                      'X-Api-Key': api_key}
        self._log_info = info_log
        self._log_error = error_log

    def create_order(self, hw_ids: List[str], product_ids: List[str]) -> str:
        """Send an order request to the API

        Args:
            hw_ids: list of str PPINS of the CPUs to request products for. Ex: ['2272C3CAFAEA6754', '22730A4AE08A5138']
            product_ids: list of str product names to request. Ex: ['SGX512', 'IAA4', 'DSA4']

        Return:
            str: The order id.

        Raises:
            LicenseOrderError: If the order request recieves an error code response from the API.
        """
        # Fill request template with products and hardware ids
        self._log_info(f"Creating Order - requested PPINS: {hw_ids}, requested products: {product_ids}.")
        request = self.ORDER_TEMPLATE
        products = [{'productRef': {'productIdType': 'SHORT_NAME', 'productId': pid}} for pid in product_ids]
        request['hardwareAssets']['assetIds'] = hw_ids
        request['productsOrdered'] = products

        # Send request to API
        self._log_info("Sending Order Request.")
        res = requests.post(self.ORDER_URL, json=request, proxies=self.PROXIES, headers=self.request_header)
        if res.status_code >= 300:
            error_msg = f"Invalid request: {res.json()['error']['message']}"
            self._log_error(error_msg)
            raise SDSiExceptions.LicenseOrderError(error_msg)

        self._log_info(f"Submitted order: {res.json()['uuid']}")
        return res.json()['uuid']

    def _check_order(self, order_id: str) -> bool:
        """Check the status of an order.

        Args:
            order_id: The id of the order to check the status of.

        Return:
            bool: True if the order is fulfilled. False if not.

        Raises:
            LicenseOrderError: If the API response is an error code, or the order has failed to fulfill.
        """
        # Send order status request
        self._log_info(f"Checking order status for order: {order_id}.")
        res = requests.get(self.ORDER_URL + '/' + order_id, proxies=self.PROXIES, headers=self._status_header)
        if res.status_code >= 300:
            error_msg = f"Invalid request: {res.json()['error']['message']}"
            self._log_error(error_msg)
            raise SDSiExceptions.LicenseOrderError(error_msg)
        if res.json()['status'] == "ERROR":
            error_msg = f"Invalid request: {json.dumps(res.json()['errors'], indent=4)}"
            self._log_error(error_msg)
            raise SDSiExceptions.LicenseOrderError(error_msg)

        # Parse order status from response
        self._log_info(f"Order status: {res.json()['status']}")
        self._log_info(f"Order processing: {res.json()['processingStage']}")
        return res.json()['status'] == 'FULFILLED' and res.json()['processingStage'] == 'COMPLETE'

    def install_license_package(self, order_id: str, install_directory: str = os.getcwd()) -> List[str]:
        """Install a license response for a corresponding order. A file will be created at the given directory
        containing the LAC. The function will verify the order is fulfilled before sending an installation request.

        Args:
            order_id: The id of the order to install license response.
            install_directory: the directory to install the LACs

        Return:
            List[str]: a list of the paths of the newly installed LACs

        Raises:
            LicenseInstallationError: If the API response code for installation is an error code.
        """
        # Wait for order to be fulfilled
        for _attempt in range(10):
            if self._check_order(order_id): break
            self._log_info("Order not ready, waiting...")
            time.sleep(10)

        # Send license installation request
        self._log_info(f"Sending installation request for order {order_id}.")
        res = requests.get(self.INSTALL_URL.format(order_id), proxies=self.PROXIES, headers=self._install_header)
        if res.status_code >= 300:
            error_msg = f"Installation response failure: {res.json()['error']['message']}"
            self._log_error(error_msg)
            raise SDSiExceptions.LicenseInstallationError(error_msg)

        # Download licenses from downloaded zip folder
        self._log_info("Downloading license package as zip folder and extract contents.")
        zip_name = order_id + '.zip'
        with open(zip_name, 'wb') as zip_file:
            [zip_file.write(chunk) for chunk in res.iter_content(chunk_size=512)]
        with open(zip_name, 'rb') as zip_file:
            extract = zipfile.ZipFile(zip_file)
            [extract.extract(name, order_id) for name in extract.namelist()]
        os.remove(zip_name)

        # Rename LACs to give details about their contents
        self._log_info("Creating LAC files from json packages...")
        lac_directories = []
        for json_name in extract.namelist():
            with open(os.path.join(order_id, json_name)) as lac_file:
                lac = json.load(lac_file)
                for cap in lac['licenseActivationCode']['capabilityActivationPayloads']:
                    lac_name = lac['licenseActivationCode']['hardwareId']['value']
                    lac_name += '_key_id_1_rev_' + str(lac['licenseActivationCode']['revision'])
                    for activated_license in cap['capabilityActivationPayloadMetadata']['activatedLicenses']:
                        lac_name += '_' + activated_license['licensedProduct']['productShortName']
                    lac_name += '.json'
            lac_directories.append(os.path.join(install_directory, lac_name))
            shutil.move(os.path.join(order_id, json_name), lac_directories[-1])
        os.rmdir(order_id)

        self._log_info(f"Installation complete for order {order_id}.")
        return lac_directories

    def _create_binary_from_lac(self, lac_directory: str, bin_directory: str = os.getcwd()) -> None:
        """Create a binary CAP file from an LAC at the given path. The binary will have the same base name as the LAC.

        Args:
            lac_directory: The path to the LAC to create a binary from.
            bin_directory: the directory to create the new binary file.
        """

        with open(lac_directory) as lac_file:
            json_name = os.path.basename(lac_file.name)
            bin_name = json_name.replace('.json', '.bin')
            self._log_info(f"Creating Binary file from json package: {json_name}.")
            with open(os.path.join(bin_directory, bin_name), 'wb') as cap_file:
                cap = json.load(lac_file)['licenseActivationCode']['capabilityActivationPayloads'][0]
                cap_file.write(base64.b64decode(cap['capabilityActivationPayloadValue']))
            self._log_info(f"Binary CAP file created: {bin_name}.")

    def create_license_set(self, hw_ids: List[str], product_ids: List[List[str]]) -> None:
        """Create a license set by installing a list of products for the given PPINs.
        All LACs/binaries wil be placed in a single set folder, given an automatically generated sequential name.

        Args:
            hw_ids: PPINS of the CPUs to request the features for. Ex: ['2272C3CAFAEA6754', '22730A4AE08A5138']
            product_ids: Features to request. Each list item will be a CAP.
                         Ex: [['BASE'], ['SGX512'], ['BASE'], ['IAA4', 'DSA4']]

        Raises:
            LicenseOrderError: If all license ordering fails.
            LicenseInstallationError: If all license installation fails.
        """
        # Generate set name
        set_number = 1
        while os.path.lexists(os.path.join(os.getcwd(), "Set_" + str(set_number))):
            set_number += 1
        set_name = "Set_" + str(set_number)
        set_dir = os.path.join(os.getcwd(), set_name)
        self._log_info(f"Ordering and Installing {set_name}.")

        # Order all licenses.
        order_list = []
        for product_list in product_ids:
            try:
                order_id = self.create_order(hw_ids, product_list)
                order_list.append(order_id)
            except SDSiExceptions.LicenseOrderError:
                self._log_error(f'Failed to order {order_list} for HWIDS {hw_ids}.')

        if not order_list:
            os.rmdir(set_dir)
            error_msg = 'Failed to order licenses.'
            self._log_error(error_msg)
            raise SDSiExceptions.LicenseOrderError(error_msg)

        # Install license packages from orders
        os.mkdir(os.path.join(os.getcwd(), set_name), 0o777)
        os.mkdir(os.path.join(os.getcwd(), set_name, 'json'), 0o777)
        os.mkdir(os.path.join(os.getcwd(), set_name, 'bin'), 0o777)
        for order_id in order_list:
            try:
                for installed_lac in self.install_license_package(order_id, os.path.join(set_dir, 'json')):
                    self._create_binary_from_lac(installed_lac, os.path.join(set_dir, 'bin'))
            except (SDSiExceptions.LicenseOrderError, SDSiExceptions.LicenseInstallationError):
                self._log_error(f'Failed to install order {order_id}.')

        if not os.listdir(set_dir):
            os.rmdir(set_dir)
            error_msg = 'Failed to install licenses.'
            self._log_error(error_msg)
            raise SDSiExceptions.LicenseInstallationError(error_msg)

        self._log_info(f"Created {set_name}.")
