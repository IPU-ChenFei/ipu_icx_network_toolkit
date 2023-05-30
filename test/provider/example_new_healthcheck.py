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
import os
import shutil
from xml.etree import ElementTree
import six
if six.PY2:
    from pathlib import Path
if six.PY3:
    from pathlib2 import Path

from dtaf_core.lib.base_test_case import BaseTestCase
from dtaf_core.lib.dtaf_constants import Framework
from dtaf_core.providers.provider_factory import ProviderFactory
from dtaf_core.providers.sut_os_provider import SutOsProvider
from dtaf_core.providers.silicon_debug_provider import SiliconDebugProvider
from dtaf_core.providers.silicon_reg_provider import SiliconRegProvider

from src.lib.common_content_lib import CommonContentLib
from src.lib.dtaf_content_constants import ProviderXmlConfigs
from src.power_management.lib.reset_base_test import ResetBaseTest


class ExampleNewHealthCheck(BaseTestCase):

    def __init__(self, test_log, arguments, cfg_opts):
        super(ExampleNewHealthCheck, self).__init__(test_log, arguments, cfg_opts)
        self._cfg = cfg_opts
        sut_os_cfg = cfg_opts.find(SutOsProvider.DEFAULT_CONFIG_PATH)
        self._os = ProviderFactory.create(sut_os_cfg, test_log)  # type: SutOsProvider

        self._common_content_lib = CommonContentLib(test_log, self._os, cfg_opts)

        self.sdp = None  # type:  SiliconDebugProvider
        self.sv = None  # type:  SiliconRegProvider
        self.x = None

    def initialize_sdp_sv_objects(self):
        # initialize sdp, if not already initialized
        if self.sdp is None:
            si_cfg = ElementTree.fromstring(ProviderXmlConfigs.SDP_XML_CONFIG)
            self.sdp = ProviderFactory.create(si_cfg, self._log)  # type: SiliconDebugProvider
        if self.sv is None:
            cpu = self._common_content_lib.get_platform_family()
            pch = self._common_content_lib.get_pch_family()
            sv_cfg = ElementTree.fromstring(ProviderXmlConfigs.PYTHON_SV_XML_CONFIG.format(cpu, pch))
            self.sv = ProviderFactory.create(sv_cfg, self._log)  # type: SiliconRegProvider
        # initialize sv, if not already initialized

    def get_new_healthcheck(self):
        # try:
        self.initialize_sdp_sv_objects()
        self.sv.refresh()
        x = None
        sockets = self.sv.get_sockets()
        for i in range(0, len(sockets)):
            try:
                log_file_name = "abc.txt"
                # self.sdp.start_log(upi_log_file)
                self.sdp.start_log(log_file_name,"a")
                sockets[i].uncore.punit.mc_status.show()
                self.sdp.stop_log()
            except Exception as e:
                self._log.info("exception: %s"%str(e))
        with open(log_file_name,"r") as f:
            lines = f.readlines()
            for l in lines:
                if l[0] in ["\r","\n"]:
                    continue
                if l.split(":")[0].strip() != "0x00000000":
                    f.close()
                    return False,l
        f.close()
        return True,None
            # self.sdp.stop_log()

        # except Exception as ex:
        #     self._log.error("Failed to collect axon logs due to exception: '{}'.".format(ex))

    def execute(self):
        self.get_new_healthcheck()
        return True


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if ExampleNewHealthCheck.main() else Framework.TEST_RESULT_FAIL)
