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

from src.sdsi.tests.agent.certificate.ib_apply_signed_license_key_to_erase_certification import InBandEraseProvisioning


class OobEraseProvisioning(InBandEraseProvisioning):
    """
    Using SDSi Agent with OOB functionality, apply a License Erase Certification Key and verify
    the CPU provisioning information stored in NVRAM is deleted.
    """

    def get_phoenix_id(self) -> int:
        """Get the Phoenix ID of the test
        
        Returns:
            int: Phoenix ID of the test, return 0 if a TCD has not been created yet.
        """
        return 18014075585

    def prepare(self) -> None:
        """Perform preparation for test"""
        self.sdsi_agent.swap_to_out_of_band_mctp()
        super().prepare()

if __name__ == "__main__":
    sys.exit(not OobEraseProvisioning.run())
