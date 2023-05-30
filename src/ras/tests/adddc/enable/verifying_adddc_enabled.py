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
from dtaf_core.lib.dtaf_constants import ProductFamilies
from dtaf_core.providers.provider_factory import ProviderFactory

from src.ras.tests.adddc.adddc_common import AdddcCommon


class VerifyingAdddcEnabled(AdddcCommon):
    """
        Glasgow_id : 58467
        This test verifies if BIOS is enabling ADDDC

    """
    BIOS_CONFIG_FILE = "../adddc_enabled_bios_knobs.cfg"

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Creates a new VerifyAdddcEnable object

        :param test_log: Used for debug and info messages
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        """
        super(VerifyingAdddcEnabled, self).__init__(test_log, arguments, cfg_opts, self.BIOS_CONFIG_FILE)

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
        super(VerifyingAdddcEnabled, self).prepare()

    def execute(self):
        """
        This Method is used to execute the method verifying_whether_ADDDC_is_enabled to verify if ADDDC is successfully
        enabled or not.

        :return:
        """
        cscripts_obj = ProviderFactory.create(self.sil_cfg, self._log)
        sdp_obj = ProviderFactory.create(self.sdp_cfg, self._log)
        try:
            sdp_obj.halt()
            addc_enabled_result = []
            dimm_info_obj = cscripts_obj.get_dimminfo_object()
            sockets = cscripts_obj.get_sockets()
            for socket in sockets:
                if cscripts_obj.silicon_cpu_family in self._common_content_lib.SILICON_14NM_FAMILY:
                    addc_enabled = dimm_info_obj.isADDDCEnabled(socket)
                elif cscripts_obj.silicon_cpu_family == ProductFamilies.SPR:
                    addc_enabled = dimm_info_obj.get_adddc_status(socket)
                else:
                    addc_enabled = dimm_info_obj.get_adddc_status(socket)

                addc_enabled_result.append(addc_enabled)

            self._log.info("The adddc_enabled value= '{}'".format(str(all(addc_enabled_result))))

        except Exception as ex:
            raise ex

        finally:
            sdp_obj.go()
        return all(addc_enabled_result)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if VerifyingAdddcEnabled.main() else Framework.TEST_RESULT_FAIL)
