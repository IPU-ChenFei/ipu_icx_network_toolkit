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
import sys

from src.sdsi.lib.license.sdsi_license_names import FeatureNames
from src.sdsi.lib.sdsi_base_test_case import SDSiBaseTestCase


class IbProvisionDifferentRevsMixed(SDSiBaseTestCase):
    """
    With SoftSKU, Platform POR is not changing to support asymmetric configuration of multiple CPUs in the same system.
    Platform still would require all sockets to be consistently upgraded from a SoftSKU perspective.
    """

    def get_phoenix_id(self) -> int:
        """Get the Phoenix ID of the test
        
        Returns:
            int: Phoenix ID of the test, return 0 if a TCD has not been created yet.
        """
        return 0

    def prepare(self) -> None:
        """Test preparation/setup """
        self.xmlcli_tool.load_bios_defaults()
        self.sdsi_feature_lib.set_iaa_driver_default_knobs()
        self.sdsi_feature_lib.set_sgx_default_knobs()
        self.sdsi_agent.verify_agent()
        self.sdsi_agent.erase_provisioning()
        self.cycling_tool.perform_ac_cycle()
        self.sdsi_agent.validate_default_registry_values()

    def execute(self) -> None:
        """
        Verify RTB license will restore orignal platform functionality prior to the application of SSKU Licenses.
        """
        # Verify the status of the default device lists and PrmSize.
        self._log.info("Verify expected default DLB devices are enumerated.")
        self.sdsi_feature_lib.verify_dlb_device_count(self.sdsi_agent.num_sockets)
        self._log.info("Verify expected default IAA devices are enumerated.")
        self.sdsi_feature_lib.verify_iaa_device_count(self.sdsi_agent.num_sockets)
        self._log.info('Verify expected SGX functionality.')
        self.sdsi_feature_lib.set_and_validate_prm_size(FeatureNames.BASE.value)
        self.sdsi_feature_lib.set_and_validate_prm_size(FeatureNames.SG40.value, False)

        # Install different features on different sockets [SG40], [IAA4].
        socket_0_features = self.sdsi_agent.apply_lac_by_name(0, [FeatureNames.SG40.value])
        socket_1_features = self.sdsi_agent.apply_lac_by_name(1, [FeatureNames.IAA4.value])
        self.cycling_tool.perform_ac_cycle()
        self.sdsi_agent.validate_active_feature_set(0, socket_0_features)
        self.sdsi_agent.validate_active_feature_set(1, socket_1_features)

        # Verify the status of the device lists and PrmSize after provisioning.
        self._log.info("Verify expected DLB devices are enumerated.")
        self.sdsi_feature_lib.verify_dlb_device_count(self.sdsi_agent.num_sockets)
        self._log.info("Verify expected IAA devices are enumerated.")
        self.sdsi_feature_lib.verify_iaa_device_count(self.sdsi_agent.num_sockets + 3)
        self._log.info('Verify expected SGX functionality.')
        self.sdsi_feature_lib.set_and_validate_prm_size(FeatureNames.BASE.value)
        self.sdsi_feature_lib.set_and_validate_prm_size(FeatureNames.SG40.value, False)

        # Install different features on different sockets [DLB4], [SG40].
        socket_0_features = self.sdsi_agent.apply_lac_by_name(0, [FeatureNames.DLB4.value])
        socket_1_features = self.sdsi_agent.apply_lac_by_name(1, [FeatureNames.SG40.value])
        self.cycling_tool.perform_ac_cycle()
        self.sdsi_agent.validate_active_feature_set(0, socket_0_features)
        self.sdsi_agent.validate_active_feature_set(1, socket_1_features)

        # Verify the status of the device lists and PrmSize after provisioning.
        self._log.info("Verify expected DLB devices are enumerated.")
        self.sdsi_feature_lib.verify_iaa_device_count(self.sdsi_agent.num_sockets + 3)
        self._log.info("Verify expected IAA devices are enumerated.")
        self.sdsi_feature_lib.verify_iaa_device_count(self.sdsi_agent.num_sockets + 3)
        self._log.info('Verify expected SGX functionality.')
        self.sdsi_feature_lib.set_and_validate_prm_size(FeatureNames.SG40.value)

        # Install different features on different sockets [BASE], [DLB4].
        self.sdsi_agent.apply_lac_by_name(0, [FeatureNames.BASE.value])
        socket_1_features = self.sdsi_agent.apply_lac_by_name(1, [FeatureNames.DLB4.value])
        self.cycling_tool.perform_ac_cycle()
        self.sdsi_agent.validate_active_feature_set(1, socket_1_features)

        # Verify the status of the device lists and PrmSize after provisioning.
        self._log.info("Verify expected DLB devices are enumerated.")
        self.sdsi_feature_lib.verify_iaa_device_count(self.sdsi_agent.num_sockets + 3)
        self._log.info("Verify expected IAA devices are enumerated.")
        self.sdsi_feature_lib.verify_iaa_device_count(self.sdsi_agent.num_sockets + 3)
        self._log.info('Verify expected SGX functionality.')
        self.sdsi_feature_lib.set_and_validate_prm_size(FeatureNames.BASE.value)
        self.sdsi_feature_lib.set_and_validate_prm_size(FeatureNames.SG40.value, False)

        # Install different features on different sockets [IAA4], [BASE].
        socket_0_features = self.sdsi_agent.apply_lac_by_name(0, [FeatureNames.IAA4.value])
        self.sdsi_agent.apply_lac_by_name(1, [FeatureNames.BASE.value])
        self.cycling_tool.perform_ac_cycle()
        self.sdsi_agent.validate_active_feature_set(0, socket_0_features)

        # Verify the status of the device lists and PrmSize after provisioning.
        self._log.info("Verify expected DLB devices are enumerated.")
        self.sdsi_feature_lib.verify_dlb_device_count(self.sdsi_agent.num_sockets)
        self._log.info("Verify expected IAA devices are enumerated.")
        self.sdsi_feature_lib.verify_iaa_device_count(self.sdsi_agent.num_sockets + 3)
        self._log.info('Verify expected SGX functionality.')
        self.sdsi_feature_lib.set_and_validate_prm_size(FeatureNames.BASE.value)
        self.sdsi_feature_lib.set_and_validate_prm_size(FeatureNames.SG40.value, False)

if __name__ == "__main__":
    sys.exit(not IbProvisionDifferentRevsMixed.run())
