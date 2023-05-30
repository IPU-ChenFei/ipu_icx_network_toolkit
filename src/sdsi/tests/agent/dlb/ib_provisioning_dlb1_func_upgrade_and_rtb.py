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


class IbDlb1FuncProvisionAndRTB(SDSiBaseTestCase):
    """
    Verify that DLB devices work only after applying the DLB1 licenses (except default devices)
    """

    def get_phoenix_id(self) -> int:
        """Get the Phoenix ID of the test
        
        Returns:
            int: Phoenix ID of the test, return 0 if a TCD has not been created yet.
        """
        return 22013944913

    def execute(self) -> None:
        """
        Verify that DLB devices work only after applying the DLB1 licenses (except default devices)
        """
        # Verify the status of the default DLB device lists.
        self._log.info("Verify expected default DLB devices are enumerated.")
        self.sdsi_feature_lib.verify_dlb_device_count(0)

        # Install DLB1 capability.
        active_features = []
        for socket in range(self.sdsi_agent.num_sockets):
            active_features.append(self.sdsi_agent.apply_lac_by_name(socket, [FeatureNames.DLB1.value]))
        self.cycling_tool.perform_ac_cycle()
        for socket in range(self.sdsi_agent.num_sockets):
            self.sdsi_agent.validate_active_feature_set(socket, active_features[socket])

        # Verify DLB1 devices are numerated.
        self._log.info("Verify DLB1 devices are enumerated after applying capability payload")
        self.sdsi_feature_lib.verify_dlb_device_count(self.sdsi_agent.num_sockets)

        # Apply RTB payload license
        for socket in range(self.sdsi_agent.num_sockets):
            self.sdsi_agent.apply_lac_by_name(socket, [FeatureNames.BASE.value])
        self.cycling_tool.perform_ac_cycle()

        # Verify the status of the default DLB device lists.
        self._log.info("Verify expected default DLB devices are enumerated.")
        self.sdsi_feature_lib.verify_dlb_device_count(0)

if __name__ == "__main__":
    sys.exit(not IbDlb1FuncProvisionAndRTB.run())
