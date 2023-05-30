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

from dtaf_core.lib.dtaf_constants import Framework
from dtaf_core.lib.base_test_case import BaseTestCase
from dtaf_core.providers.provider_factory import ProviderFactory
from dtaf_core.providers.sut_os_provider import SutOsProvider

from src.lib.common_content_lib import CommonContentLib
from src.lib.content_configuration import ContentConfiguration
from src.lib.content_artifactory_utils import ContentArtifactoryUtils
from src.lib.install_collateral import InstallCollateral


class ArtifactoryTest(BaseTestCase):
    """
    Class to test Install Collateral Method.
    """

    def __init__(self, test_log, arguments, cfg_opts):

        super(ArtifactoryTest, self).__init__(test_log, arguments, cfg_opts)

        sut_os_cfg = cfg_opts.find(SutOsProvider.DEFAULT_CONFIG_PATH)
        self._os = ProviderFactory.create(sut_os_cfg, test_log)  # type: SutOsProvider

        self._common_content_lib = CommonContentLib(self._log, self._os, cfg_opts)
        self._common_content_configuration = ContentConfiguration(self._log)
        self._command_timeout = self._common_content_configuration.get_command_timeout()
        self._obj1 = ContentArtifactoryUtils(self._log, self._os, self._common_content_lib, cfg_opts)
        self._install_collateral = InstallCollateral(self._log, self._os, cfg_opts)

    def prepare(self):
        """
        To check whether the host is alive or not.
        """
        if not self._os.is_alive():
            self._log.error("System is not alive")
            raise RuntimeError("OS is not alive")

    def execute(self):  # type: () -> bool
        """
        Function to test one of the mlc functionalities.
        1. Get latency information
        # You can use a class scope constant to assign the log name on your preference.
        # You can use a function scope variable if class variable is not necessary.
        :return: path of the host folder.
        """
        # Windows
        # self._install_collateral.install_prime95() #passed
        # self._install_collateral.install_selviewer()#passed
        # self._install_collateral.install_mem_rebooter()#passed
        # self._install_collateral.install_platform_cycler()# passed
        # self._install_collateral.install_fio() #passed
        # self._install_collateral.install_burnintest() #passed
        # self._install_collateral.install_itp_xmlcli() #passed
        # self._install_collateral.copy_scp_go_to_sut() #passed
        # self._install_collateral.install_socwatch_windows() #passed
        # self._install_collateral.install_driver_cycle() #passed
        # self._install_collateral.install_ltssm_tool() #passed
        # self._install_collateral.install_ccbsdk_in_sut() #passed
        # self._install_collateral.install_ccbhwapi_in_sut() #worked  but failed due to other reason
        #self._install_collateral.copy_sgx_hydra_windows() #passed

        # Tested and Verified -Linux
        self._install_collateral.install_qat()
        self._install_collateral.install_dpdk()
        # self._install_collateral.install_aer_inject_tool()  #  -- Passed
        # self._install_collateral.install_prime95(app_details=True)  # -- Passed
        # self._install_collateral.install_stressng()  # -- Passed
        # self._install_collateral.install_pmutility()  # did not understand this method So, skipping.
        # self._install_collateral.install_iperf()  # -- Passed
        # # self._install_collateral.install_selviewer()  # Not Implemented for Linux
        # self._install_collateral.install_platform_cycler() #--Passed
        # self._install_collateral.install_mlc()  #--Passed
        #self._install_collateral.install_linux_ras_tools()  #--Passed
        # self._install_collateral.install_ntttcp()  #--Passed
        # self._install_collateral.install_disk_spd()  #--Passed
        # self._install_collateral.install_stream_tool() #--Passed
        # self._install_collateral.copy_mcelog_conf_to_sut()  #--Passed
        # self._install_collateral.install_dcpmm_platform_cycler()  #Passed
        # self._install_collateral.install_stream_zip_file()  #--Passed
        # self._install_collateral.install_burnintest() #---Passed
        # # #  self._install_collateral.install_dpdk() #-- not required bcoz tool won't be available in collateral
        self._install_collateral.install_itp_xmlcli()  #--Passed
        # #  self._install_collateral.install_rdt() # Not required as Tool is not available in Collateral
        # # self._install_collateral.copy_smartctl_exe_file_to_sut()  # On windows Need to test
        self._install_collateral.install_turbo_stat_tool_linux()  #--Passed
        self._install_collateral.install_socwatch()  #--Passed
        self._install_collateral.copy_scp_go_to_sut()  #--Passed
        self._install_collateral.install_cpuid()  #--Passed
        self._install_collateral.install_bonnie_to_sut()  #--Passed
        self._install_collateral.install_stress_tool_to_sut()  #--Passed
        self._install_collateral.install_fio_linux()  #--Passed
        self._install_collateral.install_acpica_tool_linux()   #--Passed
        # self._install_collateral.install_ptu("ptu", "unified_server_ptu.tar.gz")  #--Passed

        # self._install_collateral.install_burnin_linux() # passes
        # self._install_collateral.install_perthread_sh_file()
        # self._install_collateral.install_run_stream()  # passed
        # self._install_collateral.install_ltssm_tool()  #passed
        # self._install_collateral.install_driver_cycle()  # passed
        # self._install_collateral.copy_semt_files_to_sut()  # passed
        # self._install_collateral.install_msr_tools_linux()  # passed
        # self._install_collateral.install_linpack_mpi()  #passed
        # # self._install_collateral.install_dynamo_tool_linux() # Not required test
        # self._install_collateral.install_crunch_tool()
        #self._install_collateral.copy_and_install_hydra_tool()
        self._install_collateral.install_pcm_tool()
        self._install_collateral.install_ioport()
        self._install_collateral.copy_and_execute_tolerant_script()
        self._install_collateral.install_run_stream()
      #  self._install_collateral.install_socwatch()


        return True


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if ArtifactoryTest.main() else Framework.TEST_RESULT_FAIL)
