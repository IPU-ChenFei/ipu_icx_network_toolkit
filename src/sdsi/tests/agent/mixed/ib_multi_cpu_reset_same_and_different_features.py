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


class IbMultiCpuResetSameAndDifferentFeatures(SDSiBaseTestCase):
    """
    On a multi-CPU socket system being upgraded, force a platform reset after the first CPU socket is upgraded but prior
    to the second socket upgrade, resulting in a mis-matched configuration state.
    """

    def get_phoenix_id(self) -> int:
        """Get the Phoenix ID of the test
        
        Returns:
            int: Phoenix ID of the test, return 0 if a TCD has not been created yet.
        """
        return 22012931472

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
        Verify common features in a multi-feature bundle license that upgrade features applied
        initially in a multi-feature bundle will provision upgraded functionality that suspersedes the original bundle.
        """
        # Verify the status of the default device lists.
        self._log.info("Verify expected default DLB devices are enumerated.")
        self.sdsi_feature_lib.verify_dlb_device_count(self.sdsi_agent.num_sockets)
        self._log.info("Verify expected default DSA devices are enumerated.")
        self.sdsi_feature_lib.verify_dsa_device_count(self.sdsi_agent.num_sockets)
        # Verify base functionality of SGX
        self.sdsi_feature_lib.set_and_validate_prm_size(FeatureNames.BASE.value)
        self.sdsi_feature_lib.set_and_validate_prm_size(FeatureNames.SG40.value, False)

        # Provision DSA4 on socket 0 and validate provisioning.
        active_features = self.sdsi_agent.apply_lac_by_name(0, [FeatureNames.DSA4.value])
        self.cycling_tool.perform_ac_cycle()
        self.sdsi_agent.validate_active_feature_set(0, active_features)
        # Verify devices are enumerated as expected from the provisioning
        self._log.info("Verify expected DLB devices are enumerated.")
        self.sdsi_feature_lib.verify_dlb_device_count(self.sdsi_agent.num_sockets)
        self._log.info("Verify expected DSA devices are enumerated.")
        self.sdsi_feature_lib.verify_dsa_device_count(self.sdsi_agent.num_sockets + 3)
        # Verify functionality of SGX
        self.sdsi_feature_lib.set_and_validate_prm_size(FeatureNames.SG40.value, False)

        # Provision DLB4 on socket 1 and validate provisioning.
        active_features = self.sdsi_agent.apply_lac_by_name(1, [FeatureNames.DLB4.value])
        self.cycling_tool.perform_ac_cycle()
        self.sdsi_agent.validate_active_feature_set(1, active_features)
        # Verify devices are enumerated as expected from the provisioning
        self._log.info("Verify expected DLB devices are enumerated.")
        self.sdsi_feature_lib.verify_dlb_device_count(self.sdsi_agent.num_sockets + 3)
        self._log.info("Verify expected DSA devices are enumerated.")
        self.sdsi_feature_lib.verify_dsa_device_count(self.sdsi_agent.num_sockets + 3)
        # Verify functionality of SGX
        self.sdsi_feature_lib.set_and_validate_prm_size(FeatureNames.SG40.value, False)

        # Provision SG40 on socket 0 and validate provisioning.
        active_features = self.sdsi_agent.apply_lac_by_name(0, [FeatureNames.SG40.value])
        self.cycling_tool.perform_ac_cycle()
        self.sdsi_agent.validate_active_feature_set(0, active_features)
        # Verify devices are enumerated as expected from the provisioning
        self._log.info("Verify expected DLB devices are enumerated.")
        self.sdsi_feature_lib.verify_dlb_device_count(self.sdsi_agent.num_sockets + 3)
        self._log.info("Verify expected DSA devices are enumerated.")
        self.sdsi_feature_lib.verify_dsa_device_count(self.sdsi_agent.num_sockets + 3)
        # Verify functionality of SGX
        self.sdsi_feature_lib.set_and_validate_prm_size(FeatureNames.SG40.value, False)

        # Provision SG40 on socket 1 and validate provisioning.
        active_features = self.sdsi_agent.apply_lac_by_name(1, [FeatureNames.SG40.value])
        self.cycling_tool.perform_ac_cycle()
        self.sdsi_agent.validate_active_feature_set(1, active_features)
        # Verify devices are enumerated as expected from the provisioning
        self._log.info("Verify expected DLB devices are enumerated.")
        self.sdsi_feature_lib.verify_dlb_device_count(self.sdsi_agent.num_sockets + 3)
        self._log.info("Verify expected DSA devices are enumerated.")
        self.sdsi_feature_lib.verify_dsa_device_count(self.sdsi_agent.num_sockets + 3)
        # Verify functionality of SGX
        self.sdsi_feature_lib.set_and_validate_prm_size(FeatureNames.SG40.value)

        # Provision DLB4 on socket 0 and validate provisioning.
        active_features = self.sdsi_agent.apply_lac_by_name(0, [FeatureNames.DLB4.value])
        self.cycling_tool.perform_ac_cycle()
        self.sdsi_agent.validate_active_feature_set(0, active_features)
        # Verify devices are enumerated as expected from the provisioning
        self._log.info("Verify expected DLB devices are enumerated.")
        self.sdsi_feature_lib.verify_dlb_device_count(self.sdsi_agent.num_sockets * 4)
        self._log.info("Verify expected DSA devices are enumerated.")
        self.sdsi_feature_lib.verify_dsa_device_count(self.sdsi_agent.num_sockets + 3)
        # Verify functionality of SGX
        self.sdsi_feature_lib.set_and_validate_prm_size(FeatureNames.SG40.value)

        # Provision DSA4 on socket 1 and validate provisioning.
        active_features = self.sdsi_agent.apply_lac_by_name(1, [FeatureNames.DSA4.value])
        self.cycling_tool.perform_ac_cycle()
        self.sdsi_agent.validate_active_feature_set(1, active_features)
        # Verify devices are enumerated as expected from the provisioning
        self._log.info("Verify expected DLB devices are enumerated.")
        self.sdsi_feature_lib.verify_dlb_device_count(self.sdsi_agent.num_sockets * 4)
        self._log.info("Verify expected DSA devices are enumerated.")
        self.sdsi_feature_lib.verify_dsa_device_count(self.sdsi_agent.num_sockets * 4)
        # Verify functionality of SGX
        self.sdsi_feature_lib.set_and_validate_prm_size(FeatureNames.SG40.value)

        # Provision BASE on socket 0 and validate provisioning.
        self.sdsi_agent.apply_lac_by_name(0, [FeatureNames.BASE.value])
        self.cycling_tool.perform_ac_cycle()
        # Verify devices are enumerated as expected from the provisioning
        self._log.info("Verify expected DLB devices are enumerated.")
        self.sdsi_feature_lib.verify_dlb_device_count(self.sdsi_agent.num_sockets + 3)
        self._log.info("Verify expected DSA devices are enumerated.")
        self.sdsi_feature_lib.verify_dsa_device_count(self.sdsi_agent.num_sockets + 3)
        # Verify functionality of SGX
        self.sdsi_feature_lib.set_and_validate_prm_size(FeatureNames.SG40.value, False)

        # Provision BASE on socket 1 and validate provisioning.
        self.sdsi_agent.apply_lac_by_name(1, [FeatureNames.BASE.value])
        self.cycling_tool.perform_ac_cycle()
        # Verify devices are enumerated as expected from the provisioning
        self._log.info("Verify expected DLB devices are enumerated.")
        self.sdsi_feature_lib.verify_dlb_device_count(self.sdsi_agent.num_sockets)
        self._log.info("Verify expected DSA devices are enumerated.")
        self.sdsi_feature_lib.verify_dsa_device_count(self.sdsi_agent.num_sockets)
        # Verify functionality of SGX
        self.sdsi_feature_lib.set_and_validate_prm_size(FeatureNames.SG40.value, False)

if __name__ == "__main__":
    sys.exit(not IbMultiCpuResetSameAndDifferentFeatures.run())
