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


class OobAltAcCyclingMultipleFeatures(SDSiBaseTestCase):
    """
    Verify that a system can perform AC power cycles without errors. Platform maintains initial configuration settings
    and Soft Sku provisioning, and system does not fail with any errors.
    """
    AC_CYCLE_COUNT = 1000

    def get_phoenix_id(self) -> int:
        """Get the Phoenix ID of the test
        
        Returns:
            int: Phoenix ID of the test, return 0 if a TCD has not been created yet.
        """
        return 22012935895

    def prepare(self) -> None:
        """Test preparation/setup """
        self.xmlcli_tool.load_bios_defaults()
        self.sdsi_feature_lib.set_sgx_default_knobs()
        self.sdsi_agent.verify_agent()
        self.sdsi_agent.erase_provisioning()
        self.cycling_tool.perform_ac_cycle()
        self.sdsi_agent.validate_default_registry_values()

    def execute(self) -> None:
        """
        Verify that a system can perform DC system reset cycles including OS boot and shutdown without errors.
        Platform maintains initial configuration settings and Soft Sku provisioning, and system does not fail with any
        unexpected error conditions.
        """
        # Verify the status of the default device lists and SGX functionality
        self._log.info("Verify expected default DSA devices are enumerated.")
        self.sdsi_feature_lib.verify_dsa_device_count(self.sdsi_agent.num_sockets)
        self.sdsi_feature_lib.set_and_validate_prm_size(FeatureNames.BASE.value)
        self.sdsi_feature_lib.set_and_validate_prm_size(FeatureNames.SG40.value, False)

        # Install multiple feature bundle capability [SG40, DSA4].
        active_features = []
        for socket in range(self.sdsi_agent.num_sockets):
            active_features.append(self.sdsi_agent.apply_lac_by_name(socket, [FeatureNames.DLB4.value,
                                                                              FeatureNames.SG40.value]))
        self.cycling_tool.perform_ac_cycle()
        self.sdsi_feature_lib.set_and_validate_prm_size(FeatureNames.SG40.value)

        for cycle in range(self.AC_CYCLE_COUNT):
            # Alternate between mctp and wire for oob agent read commands
            if cycle % 2 == 0:
                self.sdsi_agent.swap_to_out_of_band_mctp()
            else:
                self.sdsi_agent.swap_to_out_of_band_wire()

            self._log.info(f'Performing warm cycle #{cycle}, then validating expected provisioning.')
            self.cycling_tool.perform_os_cycle()
            for socket in range(self.sdsi_agent.num_sockets):
                self.sdsi_agent.validate_active_feature_set(socket, active_features[socket])
            # Verify devices are enumerated as expected from the bundle.
            self._log.info("Verify expected DSA devices are enumerated.")
            self.sdsi_feature_lib.verify_dsa_device_count(self.sdsi_agent.num_sockets * 4)

if __name__ == "__main__":
    sys.exit(not OobAltAcCyclingMultipleFeatures.run())
