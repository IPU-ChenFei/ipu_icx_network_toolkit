import re
import time
import os as os
import pandas as pd
import socket
import sys
import struct
from datetime import datetime
from dtaf_core.lib.dtaf_constants import Framework, ProductFamilies
from dtaf_core.providers.sut_os_provider import SutOsProvider
from src.lib.common_content_lib import CommonContentLib
import src.lib.content_exceptions as content_exceptions
from dtaf_core.providers.silicon_debug_provider import SiliconDebugProvider
from dtaf_core.providers.silicon_reg_provider import SiliconRegProvider
from dtaf_core.lib.dtaf_constants import OperatingSystems
from src.lib.content_configuration import ContentConfiguration
from dtaf_core.providers.provider_factory import ProviderFactory



class HsioBaseTelemetry:
    """
    This class is for base telemetry .This class would be the base class for PCIe/CXl/UPI telemetry. This class creates pythonsv/cscripts objects.
    """
    PCIE_DEVICES_PRE_DICT = {}
    PCIE_DEVICES_POST_DICT = {}
    PCIE_ENDPOINT_LTSSM_STATES_DICT={}
    _DEVICE_SPEED_IN_GT_SEC_TO_PCIE_GEN_DICT = {"2.5": "Gen1", "5": "Gen2", "8": "Gen3", "16": "Gen4", "32": "Gen5"}
    REG_PROVIDER_CSCRIPTS = "CscriptsSiliconRegProvider"
    REG_PROVIDER_PYTHONSV = "PythonsvSiliconRegProvider"
    REGEX_CMD_FOR_PYTHONSV_PORT = r"Port.*"
    REGEX_CMD_FOR_SOCKET = r"SOCKET{}"
    SLS_LOGFILE_NAME = "pcie_sls.log"
    SOCKET = "SOCKET{}"

    def __init__(self, log, sut_os, cfg_opts):
        self._log = log
        self._os = sut_os
        self._cfg = cfg_opts
        self._common_content_configuration = ContentConfiguration(self._log)
        self.si_dbg_cfg = cfg_opts.find(SiliconDebugProvider.DEFAULT_CONFIG_PATH)
        self.sil_cfg = cfg_opts.find(SiliconRegProvider.DEFAULT_CONFIG_PATH)
        self._sdp = ProviderFactory.create(self.si_dbg_cfg, self._log)
        self._reg_provider = ProviderFactory.create(self.sil_cfg, self._log)
        self._common_content_lib = CommonContentLib(self._log, self._os, self._cfg)
        self.log_dir = self._common_content_lib.get_log_file_dir()
        self.TELEMETRY_OUTPUT_CSV_DEST_PATH = self._common_content_configuration.get_io_telemetry_csv_path()
        self.TELEMETRY_UPI_OUTPUT_CSV_DEST_PATH = self._common_content_configuration.get_upi_telemetry_csv_path()
        self._cmd_time_out = self._common_content_configuration.get_command_timeout()
        self.reg_provider_class = type(self._reg_provider).__name__
        self.pcie_sls_log_file = os.path.join(self.log_dir, self.SLS_LOGFILE_NAME)
        if self.reg_provider_class == self.REG_PROVIDER_CSCRIPTS:
            if self._reg_provider.silicon_cpu_family == ProductFamilies.GNR:
                # See HSD https://hsdes.intel.com/appstore/article/#/22015048844
                self._log.info("get_pci_obj missing from get_cscripts_utils in cscripts GNR - Telemetry class instantiation failed")
                return
            self._sv = self._reg_provider.get_cscripts_utils().getSVComponent()
            self.pci = self._reg_provider.get_cscripts_utils().get_pci_obj()
            self.pcie_ltssm_obj = self._reg_provider.get_cscripts_utils().get_pcie_obj()
            self.pcicfg = self.pci.config

        elif self.reg_provider_class == self.REG_PROVIDER_PYTHONSV:
            self._sv = self._reg_provider._sv
            import svtools.itp2baseaccess as base
            self.base_obj = base.baseaccess()
            self.pcicfg = self.base_obj.pcicfg
            self.pcie_ltssm_obj = self._reg_provider.get_ltssm_object()
        else:
            raise content_exceptions.TestSetupError("Failed to create cscripts/pythonsv object, please check system config")

    def get_dtaf_host_current_datetime(self):
        """
        This method gives the datetime
        :param None
        :return:  test_datetime It gives the datetime when the test is triggerred.
        """
        try:
            test_datetime = datetime.now()
            test_datetime = test_datetime.strftime("%d/%m/%Y %H:%M:%S")
        except:
            self._log.error(" Datetime Error ")
            test_datetime = "NA"
        return  test_datetime

    def get_dtaf_host(self):
        """
        This method gives dtaf hostname
        :param None
        :returns:  It returns the host name of the system where DTAF is running.
        """
        try:
            dtaf_host_name = socket.gethostname()

        except:
            self._log.error("Socket Library Not Found")
            dtaf_host_name = "NA"
            test_datetime = "NA"
        return dtaf_host_name
