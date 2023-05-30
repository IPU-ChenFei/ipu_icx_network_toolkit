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

from dtaf_core.lib.base_test_case import BaseTestCase
from dtaf_core.lib.dtaf_constants import ProductFamilies
from dtaf_core.providers.ac_power import AcPowerControlProvider
from dtaf_core.providers.bios_provider import BiosProvider
from dtaf_core.providers.provider_factory import ProviderFactory
from dtaf_core.providers.silicon_reg_provider import SiliconRegProvider
from dtaf_core.providers.sut_os_provider import SutOsProvider

from src.lib.bios_util import BiosUtil
from src.lib.common_content_lib import CommonContentLib
from src.lib.content_configuration import ContentConfiguration


class DemandScrubCommon(BaseTestCase):
    """
    This Class is Used as Common Class For all the Demand Scrub Functionality Test Cases
    """
    PICKLE_FILE_NAME = "objects.pkl"

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create an instance of sut os provider, BiosProvider, SiliconDebugProvider, SiliconRegProvider
         BIOS util and Config util,

        :param test_log: Log object
        :param arguments: None
        :param cfg_opts: Configuration Object of provider
        """
        super(
            DemandScrubCommon,
            self).__init__(
            test_log,
            arguments,
            cfg_opts)

        self._cfg = cfg_opts

        sut_os_cfg = cfg_opts.find(SutOsProvider.DEFAULT_CONFIG_PATH)
        self._os = ProviderFactory.create(sut_os_cfg, test_log)  # type: SutOsProvider

        bios_cfg = cfg_opts.find(BiosProvider.DEFAULT_CONFIG_PATH)
        self._bios = ProviderFactory.create(bios_cfg, test_log)  # type: BiosProvider

        ac_cfg = cfg_opts.find(AcPowerControlProvider.DEFAULT_CONFIG_PATH)
        self._ac = ProviderFactory.create(ac_cfg, test_log)  # type: AcPowerControlProvider

        self._common_content_lib = CommonContentLib(self._log, self._os, self._cfg)

        self._bios_util = BiosUtil(cfg_opts, bios_config_file=None, bios_obj=self._bios, log=self._log,
                                   common_content_lib=self._common_content_lib)

        self.sil_cfg = cfg_opts.find(SiliconRegProvider.DEFAULT_CONFIG_PATH)
        self._si_reg = None

        self._common_content_configuration = ContentConfiguration(self._log)

        self._reboot_timeout = self._common_content_configuration.get_reboot_timeout()

        self._platform = self._common_content_lib.get_platform_family()
        self._pch = self._common_content_lib.get_pch_family()
        self._log_path = self._common_content_lib.get_log_file_dir()

        self.queue = None

    def verify_if_demand_scrub_enabled(self):
        """
        This Function Verifies whether Demand Scrub is enabled or Not

        :return: True is demand scrub is enabled else False
        """
        try:
            if self._platform == ProductFamilies.SPR:
                return self._common_content_lib.execute_pythonsv_function(self.verify_demand_scrub_using_sv)

            # verify using cscripts
            self._si_reg = ProviderFactory.create(self.sil_cfg, self._log)  # type: SiliconRegProvider
            self._log.info("Executing CScripts get_xnm_memicals_utils_object...")
            muObj = self._si_reg.get_xnm_memicals_utils_object()
            pop_ch_list = muObj.getPopChList(socket=0)
            self._log.info("Number of pop_mc_list='{}'".format(len(pop_ch_list)))

            for popMc in pop_ch_list:
                if self._si_reg.silicon_cpu_family in self._common_content_lib.SILICON_14NM_FAMILY:
                    if popMc.sktObj.uncore0.readregister("imc%d_m2mem_defeatures0" % popMc.mc).demandscrubwrdis:
                        self._log.error("Demand scrub is Not Enabled for mc{}".format(popMc.mc))
                        return False
                    else:
                        self._log.info("Demand scrub is Enabled Successfully for mc{}".format(popMc.mc))
                else:
                    # for 10nm like ICX
                    if popMc.regs.sysfeatures0.srubwr.read() == 1:
                        self._log.error("Demand scrub is Not Enabled for mc{}".format(popMc.mc))
                        return False
                    else:
                        self._log.info("Demand scrub is Enabled Successfully for mc{}".format(popMc.mc))

        except Exception as ex:
            self._log.error("Unable to verify whether Demand Scrub is Enabled or Not due to exception '{}'"
                            .format(str(ex)))
            raise ex

        return True

    @staticmethod
    def verify_demand_scrub_using_sv(pythonsv, log):
        """
        Verified if demand scrub is enabled using python sv commands
        :param: pythonsv - pythonsv object
        :param: log - log object

        :return: True if demand scrub is enabled rlse False
        """
        demand_scrub = False
        try:
            mc_utils = pythonsv.get_mc_utils_obj()
            if mc_utils.is_demand_scrub_enabled():
                log.info("Demand scrub is Enabled for all mc controllers...")
                demand_scrub = True
            else:
                log.error("Demand scrub is not Enabled for one or more mc controllers...")
                demand_scrub = False
        except Exception as ex:
            log_error = "Unable to verify whether Demand Scrub is Enabled or Not due to exception '{}'".format(str(ex))
            log.error(log_error)
            raise RuntimeError(log_error)
        finally:
            return demand_scrub
