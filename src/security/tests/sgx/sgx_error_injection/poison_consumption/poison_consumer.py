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

from abc import abstractmethod
from argparse import Namespace
from typing import Pattern, Union, List
import xml.etree.ElementTree as ET
import os
import re
from pathlib import Path

from src.lib import content_exceptions
from src.security.tests.sgx.sgx_error_injection.sgx_error_injection import SgxErrorInjectionBaseTest

EMCA_EN_BIOS_CFG_FILE: str = os.path.join(Path(__file__).parent.resolve(), "emca_en_bios.cfg")
EMCA_DIS_BIOS_CFG_FILE: str = os.path.join(Path(__file__).parent.resolve(), "emca_dis_bios.cfg")
VIRAL_EN_BIOS_CFG_FILE: str = os.path.join(Path(__file__).parent.resolve(), "viral_en_bios.cfg")
VIRAL_DIS_BIOS_CFG_FILE: str = os.path.join(Path(__file__).parent.resolve(), "viral_dis_bios.cfg")

class PoisonConsumer(SgxErrorInjectionBaseTest):
    """Base class for SGX tests Poison error injection tests"""

    def __init__(self, test_log: str, arguments: Union[Namespace, None], cfg_opts: ET.ElementTree):
        add_bios_cfg: List[str] = []

        if self.is_emca_en():
            add_bios_cfg.append(EMCA_EN_BIOS_CFG_FILE)
        else:
            add_bios_cfg.append(EMCA_DIS_BIOS_CFG_FILE)

        if self.is_viral_en():
            add_bios_cfg.append(VIRAL_EN_BIOS_CFG_FILE)
        else:
            add_bios_cfg.append(VIRAL_DIS_BIOS_CFG_FILE)

        super(PoisonConsumer, self).__init__(test_log, arguments, cfg_opts, add_bios_cfg=add_bios_cfg)

    def execute(self) -> bool:
        inj_addr: int = self.sgx_phys_addr + 32*1024*1024

        self.run_semt(timeout=None)
        self.unlock_injectors()

        self._log.info(f"Injecting error into address 0x{hex(inj_addr)}")
        self.uncorrectable_error(phys_addr=inj_addr)

        self._log.info("Verifying Error Injection")
        self.uncorrectable_error_verify()
        self._log.info("Error Injection Successful")

        return self.verify()

    @abstractmethod
    def verify(self) -> bool:
        """Test-specific verification.
        :returns: True if test completed successfully."""
        raise NotImplementedError

    @abstractmethod
    def is_viral_en(self) -> bool:
        """Viral Status should be enabled in BIOS
        :returns: True if viral status should be enabled"""
        raise NotImplementedError

    @abstractmethod
    def is_emca_en(self) -> bool:
        """EMCA CMCI-SMI Morphing should be enabled in BIOS
        :returns: True if EMCA CMCI-SMI Morphing should be enabled"""
        raise NotImplementedError
