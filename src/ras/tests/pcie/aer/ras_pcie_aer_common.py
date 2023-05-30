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

import os

from dtaf_core.providers.provider_factory import ProviderFactory
from dtaf_core.providers.sut_os_provider import SutOsProvider
from dtaf_core.providers.bios_provider import BiosProvider
from dtaf_core.providers.silicon_reg_provider import SiliconRegProvider
from dtaf_core.providers.silicon_debug_provider import SiliconDebugProvider

from src.lib.bios_util import BiosUtil
from src.lib.common_content_lib import CommonContentLib
from src.lib.content_configuration import ContentConfiguration
from src.lib.content_base_test_case import ContentBaseTestCase
from src.lib.dtaf_content_constants import RasErrorType


class PcieAerCommon(ContentBaseTestCase):
    """
    Common base class for Ras Pcie Aer test cases
    """
    CORR_ERR_RECEIVED = r"Corrected error received:\s+[0-9]+:{}"
    UNC_NONFATAL_ERR_RECEIVED = r"Uncorrected \(Non-Fatal\) error received:\s+[0-9]+:{}"
    UNC_FATAL_ERR_RECEIVED = r"Uncorrected \(Fatal\) error received:\s+[0-9]+:{}"
    CORR_BAD_TLP_FILE_CONTENT = """AER
    COR_STATUS BAD_TLP 
    HEADER_LOG 0 1 2 3
    """
    UNC_FATAL_MALF_TLP_FILE_CONTENT = """AER
    UNCOR_STATUS MALF_TLP 
    HEADER_LOG 0 1 2 3
    """
    UNC_NONFATAL_COMP_ABORT_FILE_CONTENT = """AER 
    # PCI_ID [WWWW:]XX.YY.Z 
    UNCOR_STATUS COMP_ABORT 
    HEADER_LOG 0 1 2 3"""
    MIXED_CORR_BAD_TLP_UNC_NONFATAL_COMP_ABORT_FILE_CONTENT = """AER 
    # PCI_ID [WWWW:]XX.YY.Z 
    COR_STATUS BAD_TLP 
    UNCOR_STATUS COMP_ABORT 
    HEADER_LOG 0 1 2 3"""
    MULTIPLE_CORR_BAD_TLP_UNC_NONFATAL_COMP_ABORT_FILE_CONTENT = """AER 
    # PCI_ID [WWWW:]XX.YY.Z 
    COR_STATUS BAD_TLP 
    HEADER_LOG 0 1 2 3 
    # 
    AER 
    # PCI_ID [WWWW:]XX.YY.Z 
    UNCOR_STATUS COMP_ABORT 
    HEADER_LOG 4 5 6 7"""
    CREATE_AER_FILE_UNC_NONFATAL_COMP_ABORT = "echo \"{}\" > file".format(UNC_NONFATAL_COMP_ABORT_FILE_CONTENT)
    CREATE_AER_FILE_CORR_BAD_TLP = "echo \"{}\" > file".format(CORR_BAD_TLP_FILE_CONTENT)
    CREATE_AER_FILE_UNC_FATAL_MALF_TLP = "echo \"{}\" > file".format(UNC_FATAL_MALF_TLP_FILE_CONTENT)
    CREATE_AER_FILE_MIXED_CORR_BAD_TLP_UNC_NONFATAL_COMP_ABORT = "echo \"{}\" > file".format(
        MIXED_CORR_BAD_TLP_UNC_NONFATAL_COMP_ABORT_FILE_CONTENT)
    CREATE_AER_FILE_MULTIPLE_CORR_BAD_TLP_UNC_NONFATAL_COMP_ABORT = "echo \"{}\" > file".format(
        MULTIPLE_CORR_BAD_TLP_UNC_NONFATAL_COMP_ABORT_FILE_CONTENT)
    AER_INJECT_ERR_CMD = "./aer-inject --id={} file"
    CREATE_AER_FILE_DICT = {
        RasErrorType.CORRECTABLE: CREATE_AER_FILE_CORR_BAD_TLP,
        RasErrorType.FATAL: CREATE_AER_FILE_UNC_FATAL_MALF_TLP,
        RasErrorType.NON_FATAL: CREATE_AER_FILE_UNC_NONFATAL_COMP_ABORT,
        RasErrorType.MIXED_CORRECTABLE_NON_FATAL: CREATE_AER_FILE_MIXED_CORR_BAD_TLP_UNC_NONFATAL_COMP_ABORT,
        RasErrorType.MULTIPLE_CORRECTABLE_NON_FATAL: CREATE_AER_FILE_MULTIPLE_CORR_BAD_TLP_UNC_NONFATAL_COMP_ABORT
    }
    #  Correctable
    DMESG_BAD_TLP_CORR_ERR_SIG = ["BadTLP", "Corrected error received", "severity=Corrected"]
    JOURNALCTL_BAD_TLP_CORR_ERR_SIG = ["severity=Corrected"]

    #  FATAL
    DMESG_COMP_ABORT_UNC_FATAL_ERR_SIG = [r"Uncorrected \(Fatal\) error received", r"severity=Uncorrected \(Fatal\)",
                                          r"AER: device recovery successful"]
    JOURNALCTL_COMP_ABORT_UNC_FATAL_ERR_SIG = [r"severity=Uncorrected \(Fatal\)"]

    #  Non FATAL
    DMESG_COMP_ABORT_UNC_NONFATAL_ERR_SIG = [r"Uncorrected \(Non-Fatal\) error received",
                                             r"severity=Uncorrected \(Non-Fatal\)", r"CmpltAbrt",
                                             r"Header: 00000000 00000001 00000002 00000003",
                                             r"AER: device recovery successful"]
    JOURNALCTL_COMP_ABORT_UNC_NONFATAL_ERR_SIG = [r"Uncorrected \(Non-Fatal\) error received",
                                                  r"severity=Uncorrected \(Non-Fatal\)", r"CmpltAbrt"]

    #  Multiple
    DMESG_BAD_TLP_CORR_ABORT_UNC_NONFATAL_ERR_SIG = [r"severity=Corrected", "BadTLP",
                                                     r"Uncorrected \(Non-Fatal\) error received",
                                                     r"severity=Uncorrected \(Non-Fatal\)", r"CmpltAbrt",
                                                     r"TLP Header: 00000004 00000005 00000006 00000007",
                                                     r"AER: device recovery successful"]
    JOURNALCTL_BAD_TLP_CORR_ABORT_UNC_NONFATAL_ERR_SIG = [r"severity=Corrected", r"BadTLP",
                                                          r"severity=Uncorrected \(Non-Fatal\)",
                                                          r"CmpltAbrt",
                                                          r"TLP Header: 00000004 00000005 00000006 00000007"]

    #  MIXED
    DMESG_CORR_BAD_TLP_UNC_NONFATAL_COMP_ABORT_SIG = [r"Corrected error received", r"severity=Corrected", r"BadTLP",
                                                      r"Uncorrected \(Non-Fatal\) error received",
                                                      r"severity=Uncorrected \(Non-Fatal\)", r"CmpltAbrt",
                                                      r"AER: device recovery successful"]
    JOURNALCTL_CORR_BAD_TLP_UNC_NONFATAL_COMP_ABORT_SIGN = [r"Corrected error received", r"severity=Corrected",
                                                            r"BadTLP",
                                                            r"Uncorrected \(Non-Fatal\) error received",
                                                            r"severity=Uncorrected \(Non-Fatal\)", r"CmpltAbrt"]

    def __init__(self, test_log, arguments, cfg_opts, bios_config_file):
        """
        Creates a new Pcie Aer Common object

        :param test_log: Used for debug and info messages
        :param arguments: Used for ContentBaseTestCase
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        :param bios_config_file: Used for bios config file
        """
        bios_config_file = os.path.join(os.path.dirname(os.path.abspath(
            __file__)), bios_config_file)
        super(PcieAerCommon, self).__init__(test_log, arguments, cfg_opts, bios_config_file)
        self._aer_inject_tool_path = ""
        sil_cfg = cfg_opts.find(SiliconRegProvider.DEFAULT_CONFIG_PATH)
        self._cscripts = ProviderFactory.create(sil_cfg, test_log)  # type: SiliconRegProvider

    def prepare(self):
        # type: () -> None
        """
        1. Clear All Os Logs before Starting the Test Case
        2. Setting the bios knobs to its default mode.
        3. Setting the bios knobs as per the test case.
        4. Rebooting the SUT to apply the new bios settings.
        5. Verifying the bios knobs that are set.

        :return: None
        """
        super(PcieAerCommon, self).prepare()

    def create_aer_file(self, type_error, cmd_path):
        """
        This method is to create AER file.

        :param type_error
        :param cmd_path
        """
        self._log.info("Create the {} file to SUT".format(type_error))
        self._common_content_lib.execute_sut_cmd(sut_cmd=self.CREATE_AER_FILE_DICT[type_error], cmd_str="echo",
                                                 execute_timeout=self._command_timeout, cmd_path=cmd_path)

    def inject_aer_error(self, bdf_value, cmd_path=None):
        """
        This method is to inject AER Error.

        :param bdf_value
        :param cmd_path
        """
        self._log.info("Inject AER Error")
        try:
            self._common_content_lib.execute_sut_cmd(sut_cmd=self.AER_INJECT_ERR_CMD.format(bdf_value),
                                                     cmd_str=self.AER_INJECT_ERR_CMD.format(bdf_value),
                                                     execute_timeout=self._command_timeout,
                                                     cmd_path=cmd_path)
            self._log.info("Successfully injected the Error")
        except Exception as ex:
            self._log.error("Captured error during inject command execution with exception: {}".format(ex))
            pass
