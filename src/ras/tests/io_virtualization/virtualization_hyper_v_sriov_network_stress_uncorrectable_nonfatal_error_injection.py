#!/usr/bin/env python
##########################################################################
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
##########################################################################
import sys
import os
import time

from dtaf_core.lib.dtaf_constants import OperatingSystems, Framework
from dtaf_core.providers.provider_factory import ProviderFactory

from src.lib.dtaf_content_constants import ErrorTypeAttribute
from src.lib.dtaf_content_constants import SeverityAttribute
from src.lib.os_lib import WindowsCommonLib
from src.provider.vm_provider import VMs
from src.ras.tests.io_virtualization.virtualization_hyper_v_sriov_network_stress_correctable_error_injection import VirtualizationHyperVSriovStressCorrectableErrorInjection
from src.provider.stressapp_provider import StressAppTestProvider
from src.lib import content_exceptions


class VirtualizationHyperVSriovStressUnCorrectableNonFatalErrorInjection(VirtualizationHyperVSriovStressCorrectableErrorInjection):
    """
    Create and stress SR-IOV ports created in Hyper-V  and stress agianst other VMs or external clients to ensure stability of the SR-IOV ports.
    While the system is running inject errors throughout the duration (12 hrs) of the test to ensure system remains stable
    Glossgow: G69372
    """

    def __init__(
            self,
            test_log,
            arguments,
            cfg_opts
    ):
        """
        Create an instance of VirtualizationHyperVSriovStressCorrectableErrorInjection

        :param test_log: Log object
        :param arguments: None
        :param cfg_opts: Configuration Object of provider
        """
        super(VirtualizationHyperVSriovStressUnCorrectableNonFatalErrorInjection, self).__init__(test_log, arguments, cfg_opts)

    def prepare(self):  # type: () -> None
        """
        This method is to execute prepare.
        """
        set_registery_key = self._common_content_lib.execute_sut_cmd(
            'powershell reg add "HKLM\SYSTEM\CurrentControlSet\Control\PnP\PCI" /v "eDpcDisabled" /t REG_DWORD /d 1 /f',
            "Enable eDPCDisable register on SUT", self._command_timeout)
        self._log.info("setting eDpcDisabled register result \n{}".format(set_registery_key))
        self.perform_graceful_g3()
        query_registry_key = self._common_content_lib.execute_sut_cmd(
            'powershell reg query "HKLM\SYSTEM\CurrentControlSet\Control\PnP\PCI" /v "eDpcDisabled" /t REG_DWORD',
            "Query eDPCDisable register on SUT", self._command_timeout)
        self._log.info("Query eDpcDisabled register result \n{}".format(query_registry_key))
        if not "match(es) found" in query_registry_key:
            raise content_exceptions.TestFail("Fail to set the eDpcDisabled register on SUT")
        super(VirtualizationHyperVSriovStressUnCorrectableNonFatalErrorInjection, self).prepare()

    def execute(self, err_type=ErrorTypeAttribute.UNC_NON_FATAL, severity=SeverityAttribute.NON_FATAL):  # type: () -> bool
        """
        This method is to
        1. Create VM
        2. Verify VM
        3. add SRIOV supported network adapter to VM
        4. Configure static ip on VM and SUT
        5. Run iperf traffic across SUT and VM
        6. inject correctable error
        7. Verify iperf status on SUT and VM

        """
        super(VirtualizationHyperVSriovStressUnCorrectableNonFatalErrorInjection, self).execute(ERR_TYPE=ErrorTypeAttribute.UNC_NON_FATAL,
                                                                                                SEVERITY=SeverityAttribute.NON_FATAL)
        return True

    def cleanup(self, return_status):
        self._common_content_lib.execute_sut_cmd('powershell reg delete "HKLM\SYSTEM\CurrentControlSet\Control\PnP\PCI" /v "eDpcDisabled /f"',
                                                 "Delete eDpcDisabled on SUT", self._command_timeout)
        super(VirtualizationHyperVSriovStressUnCorrectableNonFatalErrorInjection, self).cleanup(return_status)

if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if VirtualizationHyperVSriovStressUnCorrectableNonFatalErrorInjection.main()
             else Framework.TEST_RESULT_FAIL)
