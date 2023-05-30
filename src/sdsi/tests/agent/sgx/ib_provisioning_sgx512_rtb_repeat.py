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


class IbProvisioningSgx512RTBRepeat(SDSiBaseTestCase):
    """
    This test case is specific to SGX 512GB EPC functionality.  Enables a 512GB SGX Enclave Size.
    The return to base operation reduces the available SGX enclave size to default.
    """

    def get_phoenix_id(self) -> int:
        """Get the Phoenix ID of the test
        
        Returns:
            int: Phoenix ID of the test, return 0 if a TCD has not been created yet.
        """
        return 22015383737

    def prepare(self) -> None:
        """Test preparation/setup """
        self.xmlcli_tool.load_bios_defaults()
        set_knobs = self.sdsi_feature_lib.set_sgx_default_knobs()
        self.sdsi_agent.verify_agent()
        self.sdsi_agent.erase_provisioning()
        self.cycling_tool.perform_ac_cycle()
        self.xmlcli_tool.verify_bios_knobs(set_knobs)
        self.sdsi_agent.validate_default_registry_values()

    def execute(self) -> None:
        """
        This test case is specific to SGX 512GB EPC functionality.  Enables a 512GB SGX Enclave Size.
        The return to base operation reduces the available SGX enclave size to default.
        """
        # Verify base functionality of SGX
        self.sdsi_feature_lib.set_and_validate_prm_size(FeatureNames.BASE.value)
        self.sdsi_feature_lib.set_and_validate_prm_size(FeatureNames.SG40.value, False)

        for _repeat in range(2):
            # Provision SG40 License on CPU
            active_features = []
            for socket in range(self.sdsi_agent.num_sockets):
                active_features.append(self.sdsi_agent.apply_lac_by_name(socket, [FeatureNames.SG40.value]))
            self.cycling_tool.perform_ac_cycle()
            for socket in range(self.sdsi_agent.num_sockets):
                self.sdsi_agent.validate_active_feature_set(socket, active_features[socket])
        
            # Verify SG40 functionality on provisioned CPU
            self.sdsi_feature_lib.set_and_validate_prm_size(FeatureNames.SG40.value)
        
            # Provision RTB License on CPU
            for socket in range(self.sdsi_agent.num_sockets):
                self.sdsi_agent.apply_lac_by_name(socket, [FeatureNames.BASE.value])
            self.cycling_tool.perform_ac_cycle()
        
            # Verify base functionality of SGX
            self.sdsi_feature_lib.set_and_validate_prm_size(FeatureNames.BASE.value)
            self.sdsi_feature_lib.set_and_validate_prm_size(FeatureNames.SG40.value, False)

if __name__ == "__main__":
    sys.exit(not IbProvisioningSgx512RTBRepeat.run())
