#!/usr/bin/env python
from src.lib.common_content_lib import CommonContentLib
from dtaf_core.lib.base_test_case import BaseTestCase
from dtaf_core.providers.sut_os_provider import SutOsProvider
from dtaf_core.providers.provider_factory import ProviderFactory
# from src.seamless.tests.bmc.functional.SEAM_BMC_0001_BasicCheck import SEAM_BMC_0001_BasicCheck
# from src.seamless.tests.bmc.functional.SEAM_BMC_0003_send_sps_update_capsule import SEAM_BMC_0003_send_sps_update_capsule
# from src.seamless.lib.seamless_common import SeamlessBaseTest
from dtaf_core.lib import log_utils
from dtaf_core.lib.dtaf_constants import Framework
import platform
from multiprocessing import Process
import multiprocessing
import logging
from src.seamless.tools.CrossProductOrchestrator.App.Utils.Process import SeamLessProcess
import time
import sys


class example:

    def __init__(self):
        pass

    def create_object(self):

        exec_os = platform.system()
        try:
            cfg_file_default = Framework.CFG_FILE_PATH[exec_os]
        except KeyError:
            print("Error - execution OS " + str(exec_os) + " not supported!")
            raise RuntimeError("Error - execution OS " + str(exec_os) + " not supported!")
        arguments = BaseTestCase.parse_arguments(None, cfg_file_default)

        # Add user-specified arguments
        # BaseTestCase.add_arguments()

        print(arguments.cfg_file)
        config_parameters = BaseTestCase.parse_config_file(arguments)

        test_log = log_utils.create_logger("example", False,
                                           config_parameters)

        sut_os_cfg = config_parameters.find(SutOsProvider.DEFAULT_CONFIG_PATH)
        os_obj = ProviderFactory.create(sut_os_cfg, test_log)

        obj_common = CommonContentLib(test_log, os_obj, config_parameters)
        return obj_common






if __name__ == '__main__':
    obj = example()
    actual_callable = obj.create_object()
    process = Process(target=actual_callable.clear_all_os_error_logs)
    process.start()
    process.join()

