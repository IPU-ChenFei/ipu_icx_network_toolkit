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

from typing import List, Pattern
import sys
import re

from poison_consumer import PoisonConsumer

from dtaf_core.lib.dtaf_constants import Framework
from src.lib import content_exceptions


EMCA_EN_VERIFY_STR: List[str] = [r"Logging Uncorrected Error to WHEA", r"\[Mca\]Find uncorrected error at CPU [0-9]+",
                                 r"\[Mca\]Sending OS notification via MCE", r"\[Mca\]Successfully notify OS"]
EMCA_EN_VERIFY_PAT: List[Pattern] = [re.compile(s) for s in EMCA_EN_VERIFY_STR]


class SgxInitDcuEcmaViralEn(PoisonConsumer):
    """
    Test ID: 18015104902
    Poison Consumed on SGX init by DCU (eMCA  + Viral enabled)
    Test Pre-requisites: SGX enabled CPU
    """

    TEST_CASE_ID: List[str] = ["18015104902", "Poison Consumed on SGX init by DCU (eMCA  + Viral enabled)"]

    def is_emca_en(self) -> bool:
        return True

    def is_viral_en(self) -> bool:
        return True

    def verify(self) -> bool:
        """Checks that the test completed successfully
        :returns: True if test was successful
        :raises content_exceptions.TestFail: If test fails"""

        self._log.info("Checking that SGX is disabled")
        if self.sgx.is_sgx_enabled():
            raise content_exceptions.TestFail("SGX still enabled")

        self._log.info("Checking serial logs")
        with open(self.serial_log_path, "r") as serial_log_file:
            serial_log: str = serial_log_file.read()

            for p in EMCA_EN_VERIFY_PAT:
                if not p.findall(serial_log):
                    raise content_exceptions.TestFail(f"Could not find pattern {p.pattern} in serial log")

        self._log.info("Checking that SGX was re-enabled")
        self.sgx.check_sgx_enable()

        return True


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if SgxInitDcuEcmaViralEn.main() else Framework.TEST_RESULT_FAIL)
