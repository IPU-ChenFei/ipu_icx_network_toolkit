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
from typing import List
import sys

from src.lib import content_exceptions
from sgx_error_injection import SgxErrorInjectionBaseTest
from dtaf_core.lib.dtaf_constants import Framework


class CorrectableErrorEpcMetadata(SgxErrorInjectionBaseTest):
    """
    Test ID: 22012584885
    Correctable single-bit error injection in EPC memory holding Xucode/metadata
    Pre-reqs: SGX compatible platform/OS
    """
    TEST_CASE_ID: List[str] = ["22012584885",
                               "Correctable single-bit error injection in EPC memory holding Xucode/metadata"]

    def execute(self) -> bool:
        inj_addr: int = self.sgx_phys_addr+32*1024*1024

        self.unlock_injectors()

        self._log.info("Injecting error to address 0x{}".format(hex(inj_addr)))
        self.correctable_error(phys_addr=inj_addr)
        self.run_semt(timeout=None)
        self.correctable_error_verify()

        return True

    def cleanup(self, return_status) -> None:
        try:
            self.os.execute("pkill semt", timeout=60)
        except:
            """If this fails, it's likely because semt has already stopped."""
            pass

        super(CorrectableErrorEpcMetadata, self).cleanup(return_status)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if CorrectableErrorEpcMetadata.main() else
             Framework.TEST_RESULT_FAIL)
