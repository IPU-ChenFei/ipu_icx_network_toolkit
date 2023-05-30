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

from dtaf_core.lib.dtaf_constants import ProductFamilies
import enum


class ExecutionEnv(object):
    """Execution environment for commands"""
    OS = "os"
    UEFI = "uefi"
    ITP = "itp"


class WindowsDiskBusType:
    """
    Defines the windows storage type constants
    """
    BUS_TYPE_UNKNOWN = 0
    BUS_TYPE_SCSI = 1
    BUS_TYPE_ATAPI = 2
    BUS_TYPE_ATA = 3
    BUS_TYPE_1394 = 4
    BUS_TYPE_SSA = 5
    BUS_TYPE_FIBRE_CHANNEL = 6
    BUS_TYPE_USB = 7
    BUS_TYPE_RAID = 8
    BUS_TYPE_iSCSI = 9
    BUS_TYPE_SAS = 10
    BUS_TYPE_SATA = 11
    BUS_TYPE_SD = 12
    BUS_TYPE_MMC = 13
    BUS_TYPE_SPACES = 16
    BUS_TYPE_NVME = 17


class PowerManagementConstants:
    """
        Defines the power management type constants
    """
    SYSTEM_IDLE_TIME_12_HRS = 43200
    SYSTEM_IDLE_TIME_24_HRS = 86400
    SYSTEM_IDLE_TIME_1_HR = 3600
    WAIT_TIME = 600
    SLEEP_TIMEOUT_NEVER = 0
    BLANK_SCREEN_TIMEOUT = 0


class TimeConstants:
    """
    Defines the time constants
    """
    ONE_SEC = 1
    TEN_SEC = 10
    TWENTY_SEC = 20
    THIRTY_SEC = 30
    FOURTY_SEC = 40
    FIFTY_SEC = 50
    ONE_MIN_IN_SEC = 60
    FIVE_MIN_IN_SEC = 300
    TEN_MIN_IN_SEC = 600
    FIFTEEN_IN_SEC = 900
    ONE_HOUR_IN_SEC = 3600
    TWO_HOUR_IN_SEC = 7200
    FOUR_HOURS_IN_SEC = 14400
    EIGHT_HOURS_IN_SEC = 28800
    SIX_HOURS_IN_SEC = 21600
    TEN_HOURS_IN_SEC = 36000
    TWELVE_HOURS_IN_SEC = 43200
    FORTY_EIGHT_HOURS = 172800


class BootScriptConstants:
    """
        Defines the constants for boot script execution
    """
    # please add SILICON family with stepping which requires boot script to below dict
    SILICON_REQUIRES_BOOTSCRIPT = {ProductFamilies.SPR: ['A0', 'A1']}

    POWER_OFF_PATTERN = "Waiting up to 15.00 seconds to reach break: power_off"
    POWER_ON_PATTERN = "Waiting up to 15.00 seconds to reach break: power_on"
    BOOTSCRIPT_LOG_FILE_NAME = "boot_script.log"
    POWER_OFF_ON_TRIGGER_WAIT_TIME = 100
    BOOT_SCRIPT_PASS_SCORE_1800 = "BOOTSCRIPT SCORE IS: 1800 (Bucket: WARM_CPU_RESET_BREAK)"
    BOOT_SCRIPT_PASS_SCORE_2200 = "BOOTSCRIPT SCORE IS: 2200 (Bucket: BREAKS_DONE)"
    BOOT_SCRIPT_PASSED = "BOOTSCRIPT PASSED: THERE WERE NO ERRORS IN BOOTSCRIPT EXECUTION"
    BOOT_SCRIPT_NOT_REQUIRED = "Bootscript not required for this target."


class ProviderXmlConfigs:
    """
    Defines the provider config constants
    """
    PYTHON_SV_XML_CONFIG = """<?xml version="1.0" encoding="UTF-8"?>
            <silicon_reg>
                <driver>
                    <pythonsv>
                        <unlocker>C:\PushUtil\PushUtil.exe</unlocker>
                        <debugger_interface_type>IPC</debugger_interface_type>
                        <silicon>
                            <cpu_family>{}</cpu_family>
                            <pch_family>{}</pch_family>
                        </silicon>
                        <components>
                            <component>pch</component>
                            <component>socket</component>
                        </components>
                    </pythonsv>
                </driver>
            </silicon_reg>
            """

    SDP_XML_CONFIG = """<?xml version="1.0" encoding="UTF-8"?>
                        <silicon_debug>
                            <driver>
                                <xdp type="IPC" />
                            </driver>
                        </silicon_debug>
                        """

    SUT_OS_XML_CONFIG = """<?xml version="1.0" encoding="UTF-8"?>
            <sut_os name="{}" subtype="{}" version="{}" kernel="{}">
                <shutdown_delay>5.0</shutdown_delay>
                <driver>
                    <ssh>
                        <credentials user="{}" password="{}"/>
                        <ipv4>{}</ipv4>
                    </ssh>
                </driver>
            </sut_os>
            """

    LOG_XML_CONFIG = """<?xml version="1.0" encoding="UTF-8"?> 
        <core>
            <log path="{}\\" />
        </core>
        """


class BonnieTool(object):
    """
    This method is to define the BonnieTool Constant
    """
    FIND_FOLDER_NAME = "bonnie++"
    BONNIE_SUT_FOLDER_NAME = "bonnie_stress_tool"
    BONNIE_HOST_FOLDER_NAME = "bonnie++.zip"
    BONNIE_HOST_FOLDER_PATH = "/root/'%s'" % BONNIE_SUT_FOLDER_NAME
    FIND_INSTALL_PATH = "find $(pwd) -type d -name '%s'" % FIND_FOLDER_NAME


class CommonConstants:
    HTTP_PROXY = HTTPS_PROXY = "http://proxy-chain.intel.com:911"


class Mprime95ToolConstant(object):
    MPRIME95_LINUX_SCRIPT_FILE = r"mprime_linux.py"
    MPRIME_TOOL_NAME = r'mprime'
    MPRIME_LOG_FILE = r'mprime_linux_output.txt'
    REGEX_FOR_UNEXPECTED_EXPECTS = r'unexpected expects:(.*)'
    REGEX_FOR_SUCCESSFULL_EXPECTS = r'Successful tests:(.*)'
    FIO_TOOL_NAME = r"fio"
    STRESS_APP_TEST = r"stressapptest"
    STRESS_APP_LOG = r"stress.log"


class SolarHwpConstants:
    """
    Solar HWP native constants
    """
    SOLAR_SUT_FOLDER_NAME = "solar_tool"
    SOLAR_HOST_FOLDER_NAME = "Solar.tar.gz"
    SOLAR_SETUP = "./SolarSetup.sh"
    SOLAR_OUT = "./Solar.out /i"
    SOLAR_WINDOWS_COMMAND = "Solar.exe /cfg {}"


class ChannelConfigConstant:
    """ Class that holds Channel configuration constants"""

    CHANNEL_CONFIG_1 = "1-0-1-0-1-0-1-0"
    CHANNEL_CONFIG_2 = "1-1-1-1-1-1-1-1"
    CHANNEL_CONFIG_3 = "2-1-2-1-2-1-2-1"
    CHANNEL_CONFIG_4 = "2-2-2-2-2-2-2-2"
    CHANNEL_CONFIG_5 = "0-2-0-2-0-2-0-2"
    CHANNEL_CONFIG_6 = "0-0-0-0-0-0-0-0"
    CHANNEL_CONFIG_7 = "1-0-0-0-0-0-0-0"


class VssMode:
    """ This class holds the mode information of VSS"""

    MEMORY_MODE = "memory mode"  # memory mode
    MIXED_MODE_1LM = "mixed mode 1LM"  # 1LM
    MIXED_MODE_2LM = "mixed mode 2LM"  # 2LM
    ILVSS_MODE = "texec"
    IWVSS_MODE = "ctc.exe"


class SncConstants:
    """ This class holds the SNC based cluster constants"""

    SNC2_CLUSTER = 2
    SNC4_CLUSTER = 4


class UmaConstants:
    """ This class holds the UMA based cluster constants"""

    UMA2_CLUSTER = 2
    UMA4_CLUSTER = 4


class SlotConfigConstant:
    """
    Class that holds Slot configuration constants.
    Channels -   A  -  B  -  C  -  D  -  E  -  F  -  G  -  H
    Slots    - A1-A2-B1-B2-C1-C2-D1-D2-E1-E2-F1-F2-G1-G2-H1-H2
    """

    SLOT_CONFIG_8_by_1 = "DDR-CR-DDR-0-DDR-0-DDR-0-DDR-0-DDR-0-DDR-0-DDR-0"
    SLOT_CONFIG_8_by_4 = "DDR-CR-DDR-0-DDR-CR-DDR-0-DDR-CR-DDR-0-DDR-CR-DDR-0"
    SLOT_CONFIG_8_by_8 = "DDR-CR-DDR-CR-DDR-CR-DDR-CR-DDR-CR-DDR-CR-DDR-CR-DDR-CR"
    SLOT_CONFIG_4_by_4 = "CR-0-DDR-0-CR-0-DDR-0-CR-0-DDR-0-CR-0-DDR-0"
    CR_DDR_REFERENCE = ["8_plus_1", "8_plus_4", "8_plus_8", "4_plus_4"]


class AcpicaToolConstants:
    """
    Class that holds the ACPICA Tool constants
    """
    acpica_tar_file_name = "acpica-unix.tar.gz"
    acpic_folder_name = "acpica-unix-20200717"
    acpic_tool_name = "acpica-unix"


class PcieAttribute(object):
    VENDOR_ID = "vendor_id"
    DEVICE_ID = "device_id"
    DEVICE_CLASS = "device_class"
    DEVICE_DRIVER = "device_driver"
    LINKCAP_SPEED = "linkcap_speed"
    LINKCAP_WIDTH = "linkcap_width"
    LINKSTATUS_WIDTH = "linkstatus_width"
    LINKSTATUS_SPEED = "linkstatus_speed"
    CLASS_GUID = "ClassGuid"
    DRIVER_VERSION = "DriverVersion"
    DEVICE_NAME = "DeviceName"
    FULL_DEVICE_ID = "DeviceId"


class IntelPcieDeviceId(object):
    CPU_ROOT_DEVICES = {ProductFamilies.ICX: 'a194', ProductFamilies.SPR: '1bbd'}
    PCH_ROOT_DEVICES = {ProductFamilies.ICX: 'a195', ProductFamilies.SPR: '1bbf'}
    ME_DEVICE_ID = {ProductFamilies.ICX: 'a1ba', ProductFamilies.SPR: '1be0'}
    AHCI_DEVICE_ID = {ProductFamilies.ICX: 'a1d2', ProductFamilies.SPR: '1bcd'}
    XHCI_DEVICE_ID = {ProductFamilies.ICX: 'a1af', ProductFamilies.SPR: '1bcd'}
    SMBUS_DEVICE_ID = {ProductFamilies.ICX: 'a1a3', ProductFamilies.SPR: '1bc9'}
    SATA_DEVICE_ID = {ProductFamilies.ICX: 'a182', ProductFamilies.SPR: '1ba2'}
    LPC_ESPI_DEVICE_ID = {ProductFamilies.ICX: 'a1c1', ProductFamilies.SPR: '1b81'}
    SPI_DEVICE_ID = {ProductFamilies.ICX: 'a1a4', ProductFamilies.SPR: '1bca'}
    ETHERNET_DEVICE_ID = {ProductFamilies.ICX: '1533', ProductFamilies.SPR: '15f2'}
    PCIE_NVME_M2_DEVICE_ID = {ProductFamilies.ICX: '0a54', ProductFamilies.SPR: '0a54'}

    PCIE_LINK_SPEED_WIDTH_DICT = {
        ProductFamilies.ICX: {'1533': {'linkcap_speed': '2.5GT/s', 'linkcap_width': 'x1',
                                       'device_driver': 'igb'},  # Ethernet
                              'a194': {'linkcap_speed': '8GT/s', 'linkcap_width': 'x1',
                                       'device_driver': 'pcieport'},  # cpu root
                              'a195': {'linkcap_speed': '8GT/s', 'linkcap_width': 'x1',
                                       'device_driver': 'pcieport'},  # pch root

                              'a182': {'device_driver': 'ahci'},  # usb
                              '0a54': {'linkcap_speed': '8GT/s', 'linkcap_width': 'x4'}
                              },
        ProductFamilies.SPR: {'15f2': {'linkcap_speed': '5GT/s', 'linkcap_width': 'x1',
                                       'device_driver': 'igc'},
                              '1bbd': {'linkcap_speed': '8GT/s', 'linkcap_width': 'x1',
                                       'device_driver': 'pcieport'},
                              'abbe': {'linkcap_speed': '8GT/s', 'linkcap_width': 'x1',
                                       'device_driver': 'pcieport'},
                              'aba2': {'device_driver': 'ahci'},
                              '0a54': {'linkcap_speed': '8GT/s', 'linkcap_width': 'x4'}
                              }
    }


class RDTConstants(object):
    """
    This class holds the RDT Constants:
    """
    RDT_STRESS_CONSTANTS = {"STRESS_DIR": "STRESS", "STRESS_TAR_FILE": "stress-1.0.4.tar.gz"}
    RDT_STREAM_CONSTANTS = {"STREAM_DIR": "STREAM", "STREAM_LINUX_FILE": "stream_rdt.zip"}
    RDT_FOLDER = "RDT"
    RDT_MEMTESTER_CONSTANTS = {"MEMTESTER_DIR": "MEMTESTER", "MEMTESTER_TAR_FILE": "memtester-4.5.0.tar.gz"}
    DEFAULT_COS_MASK_VAL = {ProductFamilies.ICX: '0xfff', ProductFamilies.SPR: '0x7fff'}
    RDT_MBL_STR = 'MBL[MB/s]'
    RDT_MBR_STR = 'MBR[MB/s]'
    RDT_CORE_STR = 'Core'


class PcieDeviceClassConstants(object):
    PCIE_USB = "USB controller"
    PCIE_USB_WINDOWS = "USB Controller"
    PCIE_SMBUS = "SMBus"
    PCIE_ETHERNET_CONTROLLER = "Ethernet controller"
    PCIE_SPI = "Serial bus controller"
    PCIE_SPI_WINDOWS = "SERIAL_BUS_CTLR, OTHER"
    PCIE_SATA_CONTROLLER = "SATA controller"
    PCIE_ME = "Communication controller"
    PCIE_LPC_ESPI = "ISA bridge"
    PCIE_LPC_ESPI_WINDOWS = "BRIDGE_DEV, ISA"
    PCIE_BRIDGE = "PCI bridge"
    PCIE_BRIDGE_WINDOWS = "BRIDGE_DEV"


class PcieLinuxDriverNameConstant(object):
    KERNEL_DRIVER_PCIE_PORT = "pcieport"
    KERNEL_DRIVER_I801_SMBUS = 'i801_smbus'
    KERNEL_DRIVER_AHCI = "ahci"
    KERNEL_DRIVER_XHCI = "xhci_hcd"
    KERNEL_DRIVER_ME = "mei_me"
    KERNEL_DRIVER_NIC = "e1000e"
    KERNEL_DRIVER_ETHERNET = "igb"


class NumberFormats:
    """
    NumberFormats names
    """

    BINARY = "binary"
    DECIMAL = "decimal"
    HEXADECIMAL = "hexadecimal"


class LinuxCyclingToolConstant:
    CYCLING_SCRIPTS_FILE_NAME = "cycling_linux.py"
    CYCLING_SUT_FOLDER_NAME = "cycling_tools"
    CYCLING_HOST_FOLDER_NAME = "LinuxCycling.zip"
    CYCLING_TOOL_SUT_FOLDER_NAME = "LinuxCycling"
    FIND_INSTALL_PATH = "find $(pwd) -type d -name '%s'" % CYCLING_TOOL_SUT_FOLDER_NAME
    CYCLING_HOST_FOLDER_PATH = "/root/'%s'" % CYCLING_SUT_FOLDER_NAME
    LOG_DIR = "/var/log/cycling/"


class PcieCyclingConstant:
    PING_HOST = "ping -c 4 {}"
    PING_WIN_HOST = "ping -n 4 {}"
    VALIDATE_PINGING = "4 received"
    VALIDATE_WIN_PINGING = "Received = 4"
    CAT_COMMAND = "cat {}"
    TEST_FILE = "test.txt"
    TEST_STRING = 'Testing on SATA'
    ECHO_COMMAND = "echo '{}' > {}".format(TEST_STRING, TEST_FILE)
    USB_TEST_STRING = 'Testing on USB'
    ECHO_COMMAND_USB = "echo '{}' > {}".format(USB_TEST_STRING, TEST_FILE)
    REMOVE_FILE = "rm -f {}".format(TEST_FILE)
    UNMOUNT_COMMAND = "umount {}"


class OsLogVerificationConstant:
    DUT_STRESS_FILE_NAME = "stress.log"
    DUT_RAS_TOOLS_FILE_NAME = "ras_tools"
    DUT_MESSAGES_FILE_NAME = "messages"
    DUT_MESSAGES_PATH = "/var/log/" + DUT_MESSAGES_FILE_NAME

    DUT_JOURNALCTL_FILE_NAME = "journalctl"
    DUT_JOURNALCTL_NO_PROMPT = DUT_JOURNALCTL_FILE_NAME + " --no-pager"

    DUT_DMESG_FILE_NAME = "dmesg"
    LINUX_BIN_LOCATION = "/usr/bin"
    CMD_TO_GREP_MCE_ERROR = 'abrt-cli list | grep -i "mce"'


class WindowsMemrwToolConstant:
    MEMRW_FOLDER_NAME = "memrw_tool"
    HOST_ZIP_FILE_NAME = "memrw.zip"
    MEMRW_CMD_TO_GET_PCIE_INFO = "memrw64.exe -a"
    CYCLING_HOST_FOLDER_NAME = "WinCycle.exe"
    CYCLING_SCRIPT_FILE_NAME = "cycling_windows.py"
    CYCLING_LOG_DIR = "C:\Cycling\Logs"
    TERMINATE_CYCLING_APP = "WinCycle.exe --disable"
    CMD_FOR_SUT_HOME_PATH = "echo %HOMEDRIVE%%HOMEPATH%"


class TurboStatConstants:
    """This class holds the TurboStat tool constants"""
    TURBOSTAT_TOOL_NAME = "turbostat.tar.gz"
    TURBOSTAT_TOOL_FOLDER_NAME = "turbostat"
    COMPLETE_TURBOSTAT_TOOL_PATH = "/turbo_stat/usr/bin"
    TURBOSTAT_LOG_FILE_NAME = r"turbostat_data.txt"
    TURBOSTAT_CMD_LINUX = "./turbostat -i 1 >{}"

class BurnInConstants:
    """This class holds the BurnIn tool constants"""
    BIT_EXE_FILE_NAME_WINDOWS = "bit.exe"
    BURNIN_TEST_CMD_WINDOWS = BIT_EXE_FILE_NAME_WINDOWS + " /c {} /d {} /r"
    BURNIN_BIT_LOG = "BiTLog2.log"
    BURNIN_BIT_LOG_NEW = "BiTLog2_{}.log"
    BURNIN_BIT_LOG_VM = "BiTLog2_{}.log"
    #BURNIN_LOG_PATH_WIN =r'C:\Automation\burner\'
    BURNIN_BIT_LOG_VM_WIN = "BIT_log_*.log"
    BURNIN_TEST_FAIL_CMD = "TEST RUN FAILED"
    BURNIN_TEST_THRESHOLD_TIMEOUT = 60
    BIT_INSTALLED_PATH_WINDOWS = r"C:\Burnintest"
    BIT_INSTALL_COMMAND_WINDOWS = r"C:\Burnintest\bitpro.exe /VERYSILENT /DIR={}".format(BIT_INSTALLED_PATH_WINDOWS)
    BIT_KEY_WINDOWS = "key.dat"
    BIT_KEY_WINDOWS_VM = "SN*"

    BURNIN_TEST_CMD_LINUX = "./bit_cmd_line_x64 -B -D %d -C %s -d"
    BURNIN_TEST_CMD_LINUX_VM = "./bit_cmd_line_x64 -B -D {} -C {} -d"
    BURNIN_LOCAL_DEBUG_LOG = "bit_debug_log.log"
    BURNIN_TEST_DEBUG_LOG = "debug.log"
    BURNIN_TEST_DEBUG_LOG_VM = "debug_{}.log"
    BURNIN_TEST_START_MATCH = " Parent PID "
    BURNIN_TEST_END_MATCH = "###################### STOP_TEST_DEBUG_FINISHES ######################"


class IntelSsdDcToolConstants:
    """This class holds the Intel SSD Data Center tool constants"""
    INTEL_SSD_DC_TOOL_64 = "Intel SSD Data Center Tool x64 "
    INTEL_SSD_DC_TOOL_32 = "Intel SSD Data Center Tool Win32 "


class LttsmToolConstant(object):
    LTSSM_TOOL_HOST_FILE_NAME_LINUX = "LTSSMtool.zip"
    LTSSM_TOOL_SUT_FOLDER_NAME_LINUX = "lttsm_tool"
    LTSSM_TOOL_HOST_FILE_NAME_WINDOWS = "LTSSMtool.zip"
    LTSSM_TOOL_SUT_FOLDER_NAME_WINDOWS = "lttsm_tool"


class DriverCycleToolConstant(object):
    DRIVER_CYCLE_TOOL_HOST_FILE_NAME = "DriverCycleWin.zip"
    DRIVER_CYCLE_TOOL_SUT_FOLDER_NAME = "driver_cycle"
    DRIVER_TOOL_NAME_LINUX = "drivercycle.sh"


class CcbPackageConstants:
    HOST_FOLDER_NAME = "ccb_package.zip"
    SUT_FOLDER_NAME = "ccb_package"
    WHL_PACKAGE_FOLDER_NAME = "whl_package"


class FrequencyConstants:
    """This class holds the Frequency Constants"""
    FREQUENCY_4800 = '4800'
    FREQUENCY_3200 = '3200'
    FREQUENCY_2800 = '2800'


class LinPackToolConstant:
    MKLB_FILE_NAME = "l_mklb_p_11.3.3.011.tgz"
    MPI_FILE_NAME = "l_mpi_2018.1.163.tgz"
    SUT_MPI_FOLDER_NAME = "l_mpi_2018.1.163"
    HOST_FOLDER_NAME = "linpack_mpi.zip"
    SUT_FOLDER_NAME = "linkpack"
    COMMAND_TO_INSTALL = "./install.sh --INSTALL_MODE=NONRPM -s silent.cfg"
    path_to_change_config_file = \
        "/l_mklb_p_11.3.3.011/benchmarks_11.3.3/linux/mkl/benchmarks/mp_linpack/bin_intel/intel64"


class VROCConstants:
    """This class holds the VROC tool constants"""
    ZIP_EXTENSION = ".zip"
    DIR_CMD = "dir *{} | FINDSTR vroc{}".format(ZIP_EXTENSION, ZIP_EXTENSION)
    SETUP_FILE_WHERE_CMD = "where /R C:\\vroc SetupVROC.exe"
    SETUP_CMD = "SetupVROC.exe -s"
    VERIFY_VROC_CMD = "PowerShell Get-WmiObject -Class Win32_Product"
    TOOL_NAME = "Intel(R) Virtual RAID on CPU"
    MAKE_CMD = "mkdir {} && tar xf {} -C {}"
    INSTALL_FOLDER_PATH = r"C:\vroc\Install"


class DynamoToolConstants:
    """
    Dynamo tool constants
    """
    DYNAMO_SUT_FOLDER_NAME = "dynamo"
    DYNAMO_HOST_FOLDER_NAME = "dynamo.tar"
    EXECUTE_DYNAMO_METER_CMD = "./dynamo -i {} -m {}"


class IOmeterToolConstants:
    """
    IOMeter tool constants
    """
    REG_CMD = "reg import iometer.reg"
    ADD_IOMETER_REG = "reg import execute_iometer.reg"
    EXECUTE_AUTOLOGON_REG = "reg import auto_logon.reg"
    ADD_AUTOLOGON_REG = ["Windows Registry Editor Version 5.00\n",
                         "[HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Winlogon\]\n",
                         '"AutoAdminLogon"="1"\n']
    EXECUTE_IOMETER_CMD = "IOmeter.exe /c {} /r result.csv"
    TASKFIND_CMD = "TASKLIST | FINDSTR /I {}"
    ZIP_FILE_NAME = "iometer_tool.zip"
    IOMETER_TOOL_FOLDER = "iometer_tool"
    ZIP_CMD = "Powershell Compress-Archive *.* {}"
    READ_ERROR = "Read Errors"
    WRITE_ERROR = "Write Errors"
    ERROR_LIMIT = 0
    FILE_NAME = "check_disk.txt"
    DEFAULT_USER = '"DefaultUserName"="{}"\n'
    DEFAULT_PASSWORD = '"DefaultPassword"="{}"\n'
    AUTO_LOGON_REG_FILE_NAME = "auto_logon.reg"


class RasPcieAer:
    """
    Ras Pcie Aer Constants
    """
    HOST_FOLDER_NAME = r"aer-inject-master.tar.gz"
    SUT_FOLDER_NAME = r"aer_inject"
    SUT_TOOL_FOLDER_NAME = r"aer-inject-master"
    RAS_UTILS_HOST_FOLDER_NAME = r"ras-utils-7.0-6.el7.x86_64.rpm"
    RAS_UTILS_SUT_FOLDER_NAME = r"ras-utils"
    INSTALL_RAS_UTILS = "yum install -y {}".format(RAS_UTILS_HOST_FOLDER_NAME)


class RasErrorType:
    CORRECTABLE = "correctable"
    FATAL = "fatal"
    NON_FATAL = "non fatal"
    MIXED_CORRECTABLE_NON_FATAL = "mixed corr nonfatal"
    MULTIPLE_CORRECTABLE_NON_FATAL = "multiple corr nonfatal"


class StressCrunchTool:
    HOST_FOLDER_NAME = r"crunch.tar.gz"
    SUT_FOLDER_NAME = r"crunch"


class StressLibquantumTool:
    HOST_FILE_NAME = r"libquantum.tar.gz"
    SUT_FOLDER_NAME = r"libquantum"


class StressMprimeTool:
    HOST_FILE_NAME = r"p95v298b6.linux64.tar.gz"
    SUT_FOLDER_NAME = r"mprime"
    PRIME_FILE_CONTENT = ["V24OptionsConverted=1", "WGUID_version=2", "StressTester=1",
                          "UsePrimenet=0", "MinTortureFFT=4", "MaxTortureFFT=8192",
                          "TortureMem=9216", "TortureTime=3", "TortureWeak=0"]
    REMOVE_PRIME_FILE = "rm -rf prime.txt"
    START_MPRIME_STRESS_ON_SUT_CMD = "./mprime -t prime.txt"
    CHECK_MPRIME_RUN_CMD = "ps -ef | grep mprime"
    STRING_TO_CHECK = "./mprime"


class PcieSlotAttribute:
    SLOT_NAME = "Slot_Name"
    PCIE_DEVICE_NAME = "Pcie_Device_Name"
    PCIE_DEVICE_SPEED_IN_GT_SEC = "pcie_device_speed_in_gt_sec"
    PCIE_DEVICE_WIDTH = "pcie_device_width"
    LEFT_RISER_BOTTOM = "left_riser_bottom"
    LEFT_RISER_TOP = "left_riser_top"
    SLOT_C = "slot_c"
    SLOT_M_2 = "pcie_m_2"
    PCIE_SLOT_CSP_PATH = "cscript_path"
    PCIE_SLOT_SOCKET = "socket"
    PORT_MAPPED_WITH_GEN_5 = "pcie_port_mapped_with_gen5"
    PORT_MAPPED_WITH_GEN_4 = "pcie_port_mapped_with_gen4"
    PORT_MAPPED_WITH_GEN = "pcie_port_mapped_with_gen{}"
    SLOT_B = "slot_b"
    SLOT_D = "slot_d"
    SLOT_E = "slot_e"
    RIGHT_RISER_BOTTOM = "right_riser_bottom"
    RIGHT_RISER_TOP = "right_riser_top"
    MCIO_S0_PXP4_P0 = "mcio_s0_pxp4_pcieg_port0"
    MCIO_S0_PXP4_P1 = "mcio_s0_pxp4_pcieg_port1"
    MCIO_S0_PXP4_P2 = "mcio_s0_pxp4_pcieg_port2"
    MCIO_S0_PXP4_P3 = "mcio_s0_pxp4_pcieg_port3"
    MCIO_S0_PXP5_P0 = "mcio_s0_pxp5_pcieg_port0"
    MCIO_S0_PXP5_P1 = "mcio_s0_pxp5_pcieg_port1"
    MCIO_S0_PXP5_P2 = "mcio_s0_pxp5_pcieg_port2"
    MCIO_S0_PXP5_P3 = "mcio_s0_pxp5_pcieg_port3"
    MCIO_S1_PXP4_P0 = "mcio_s1_pxp4_pcieg_port0"
    MCIO_S1_PXP4_P1 = "mcio_s1_pxp4_pcieg_port1"
    MCIO_S1_PXP4_P2 = "mcio_s1_pxp4_pcieg_port2"
    MCIO_S1_PXP4_P3 = "mcio_s1_pxp4_pcieg_port3"
    MCIO_S1_PXP5_P0 = "mcio_s1_pxp5_pcieg_port0"
    MCIO_S1_PXP5_P1 = "mcio_s1_pxp5_pcieg_port1"
    MCIO_S1_PXP5_P2 = "mcio_s1_pxp5_pcieg_port2"
    MCIO_S1_PXP5_P3 = "mcio_s1_pxp5_pcieg_port3"
    SLOT_E_BIFURCATION_P0 = "slot_e_bifurcation_port0"
    SLOT_E_BIFURCATION_P1 = "slot_e_bifurcation_port1"
    SLOT_E_BIFURCATION_P2 = "slot_e_bifurcation_port2"
    SLOT_E_BIFURCATION_P3 = "slot_e_bifurcation_port3"
    SLOT_B_BIFURCATION_P0 = "slot_b_bifurcation_port0"
    SLOT_B_BIFURCATION_P1 = "slot_b_bifurcation_port1"
    SLOT_B_BIFURCATION_P2 = "slot_b_bifurcation_port2"
    SLOT_B_BIFURCATION_P3 = "slot_b_bifurcation_port3"
    S0_PXP4_P0 = "s0_pxp4_p0"
    S0_PXP5_P0 = "s0_pxp5_p0"
    S0_PXP8_P0 = "s0_pxp8_p0"
    S0_PXP9_P0 = "s0_pxp9_p0"
    S1_PXP4_P0 = "s1_pxp4_p0"
    S1_PXP5_P0 = "s1_pxp5_p0"
    S1_PXP8_P0 = "s1_pxp8_p0"
    S1_PXP9_P0 = "s1_pxp9_p0"
    PCIE_ALL_SLOT = ["slot_c", "left_riser_bottom", "left_riser_top", "slot_b", "slot_d", "slot_e",
                     "right_riser_bottom", "right_riser_top", "mcio_s0_pxp4_pcieg_port0", "mcio_s0_pxp4_pcieg_port1",
                     "mcio_s0_pxp4_pcieg_port2", "mcio_s0_pxp4_pcieg_port3", "mcio_s0_pxp5_pcieg_port0",
                     "mcio_s0_pxp5_pcieg_port1", "mcio_s0_pxp5_pcieg_port2", "mcio_s0_pxp5_pcieg_port3",
                     "mcio_s1_pxp4_pcieg_port0", "mcio_s1_pxp4_pcieg_port1", "mcio_s1_pxp4_pcieg_port2",
                     "mcio_s1_pxp4_pcieg_port3", "mcio_s1_pxp5_pcieg_port0", "mcio_s1_pxp5_pcieg_port1",
                     "mcio_s1_pxp5_pcieg_port2", "mcio_s1_pxp5_pcieg_port3"]
    PCH_SLOT = ["slot_c", "nvme_m_2"]
    BIFURCATION_SLOTS = ["slot_e_bifurcation_port0", "slot_e_bifurcation_port1",
                         "slot_e_bifurcation_port2", "slot_e_bifurcation_port3",
                         "slot_b_bifurcation_port0", "slot_b_bifurcation_port1",
                         "slot_b_bifurcation_port2", "slot_b_bifurcation_port3"]
    BIFURCATION_SLOT_NAME = ["slot_e", "slot_b"]
    PCIE_SLOTS_LIST = ["slot_c", "left_riser_bottom", "left_riser_top", "slot_b", "slot_d", "slot_e",
                       "right_riser_bottom", "right_riser_top"]
    ALL_MCIO_SLOT = ["mcio_s0_pxp4_pcieg_port0", "mcio_s0_pxp4_pcieg_port1",
                     "mcio_s0_pxp4_pcieg_port2", "mcio_s0_pxp4_pcieg_port3", "mcio_s0_pxp5_pcieg_port0",
                     "mcio_s0_pxp5_pcieg_port1", "mcio_s0_pxp5_pcieg_port2", "mcio_s0_pxp5_pcieg_port3",
                     "mcio_s1_pxp4_pcieg_port0", "mcio_s1_pxp4_pcieg_port1", "mcio_s1_pxp4_pcieg_port2",
                     "mcio_s1_pxp4_pcieg_port3", "mcio_s1_pxp5_pcieg_port0", "mcio_s1_pxp5_pcieg_port1",
                     "mcio_s1_pxp5_pcieg_port2", "mcio_s1_pxp5_pcieg_port3"]


class PhysicalProviderConstants:
    PHY_SX_STATE = "SXSTATE"
    PHY_POST_CODE = "POSTCODE"


class PTUToolConstants:
    """
    PTU tool constants
    """
    UTILIZATION = "Util"
    C0 = "C0"
    C1 = "C1"
    C6 = "C6"
    SUT_DELETE_FILE = r'del C:\ptu\*.csv'
    ZERO = 0
    extension = r'ptumon.csv'
    STR_UTIL = 'columun_values_util'
    STR_C0 = "columun_values_c0"
    STR_C1 = "columun_values_c1"
    STR_C6 = "columun_values_c6"
    STR_C0_C1_SUM = "sum_c0_c1"


class SgxHydraToolConstants:
    HYDRA_TEST_DIR = "Hydra_tool"
    HYDRA_TOOL = "SGXHydra.zip"
    HYDRA_TOOL_WINDOWS = "SGXHydraEx-FIRST.zip"


class RootDirectoriesConstants:
    LINUX_ROOT_DIR = "/root/"


class InventoryConstants:
    SUT_INVENTORY_FILE_NAME = r"C:\Inventory\sut_inventory.cfg"


class CbntConstants:
    CURRENT_VERSION = "IFWI Current Version"


class SutInventoryConstants:
    """
    This Class is Used to declare SUT Inventory Configuration Constants
    """
    SUT_INVENTORY_FILE_NAME = r"C:\Inventory\sut_inventory.cfg"
    NVME = "nvme"
    SATA = "sata"
    SATA_RAID = "sata_raid"
    NON_RAID_SSD_NAME = "non_raid_ssd_name"
    SATA_RAID_SSD_NAME = "sata_raid_ssd_name"
    WINDOWS = "windows"
    RHEL = "rhel"
    CENTOS = "centos"
    ESXI = "esxi"
    BLANK = "blank"
    NVME_SSD_NAME_RHEL = "nvme_ssd_name_rhel"
    NVME_SSD_NAME_CENTOS = "nvme_ssd_name_centos"
    NVME_SSD_NAME_WINDOWSM = "nvme_ssd_name_windows"
    SATA_SSD_NAME_RHEL = "sata_ssd_name_rhel"
    SATA_SSD_NAME_CENTOS = "sata_ssd_name_centos"
    SATA_SSD_NAME_WINDOWS = "sata_ssd_name_windows"


class UefiTool:
    PCR_TOOL_DIR = "pcrdump64"
    PCR_DUMP_TOOL = "pcrdump64.zip"


class PcmToolConstants:
    """
        This Class is Used to declare SUT Inventory Configuration Constants
        """
    PCM_TOOL_ZIP_FILE = "ProcessorCounterMonitor.tar"


class SiliconDetails:
    """
    This class is used to get the silicon Constants
    """
    B0_silicon = "B0"
    C2_silicon = "C2"


class CRFileSystems:
    DAX = "dax"
    BLOCK = "block"


class IntelPostCodes:
    PC_E3 = "E3"
    PC_00 = "00"
    PC_4A = "4A"
    PC_02 = "02"
    PC_72 = "72"
    PC_22 = "22"
    PC_EE = "EE"


class DellPostCodes(object):
    PC_0 = "0"
    PC_1 = "1"  # System boot
    PC_7 = "7"
    PC_8 = "8"  # SMM Initialization
    PC_9 = "9"  # PCI bus enumeration & video initialization.
    PC_41 = "41"  # PCI configuration
    PC_55 = "55"  # Performing CSIOR
    PC_58 = "58"  # Preparing to bootPC
    PC_7F = "7F"  # Given control to OS.
    PC_7E = "7E"  # Giving control to UEFI aware OS


class HpePostCodes(object):
    PC_0 = "0"
    PC_1 = "1"
    PC_7 = "7"
    PC_8 = "8"  # SMM Initialization
    PC_9 = "9"  # PCI bus enumeration & video initialization.
    PC_41 = "41"  # PCI configuration
    PC_55 = "55"  # Performing CSIOR
    PC_58 = "58"  # Preparing to bootPC
    PC_7F = "7F"  # Given control to OS.
    PC_7E = "7E"  # Giving control to UEFI aware OS


class PcmMemoryConstants:
    """
        This Class is Used to declare PCM Memory Constants
        """
    PCM_TOOL_FILE = "pcm-memory.x"
    PCM_MEMORY = "PCMMemory"
    HEX_VALUES = [0x4, 0x6, 0x8, 0x2]  # Hex values for [4,6,8,2]


class PlatformType(object):
    """
    This class defines the platform type
    """
    REFERENCE = "reference"  # intel RVP
    DELL = "dell"
    HPE = "hpe"
    MSFT = "msft"


class PlatformEnvironment(object):
    """
    This class defines the platform environment
    """
    HARDWARE = "Hardware"
    SIMICS = "Simics"


class PowerStates:
    S0 = "S0"
    S3 = "S3"
    S5 = "S5"
    G3 = "G3"
    S1 = "S1"
    S4 = "S4"


class ResetStatus(object):
    SUCCESS = 0
    OS_NOT_ALIVE = 1
    PC_STUCK = 2
    DC_FAILURE = 3
    AC_FAILURE = 4
    STATE_CHANGE_FAILURE = 5


class HealthCheckFailures(object):
    DMI = "dmi"
    UPI = "upi"
    PCIE = "pcie"
    MCE = "mce"
    PC_STUCK = "pc_stuck"
    STATE_CHANGE = "state_change"
    BOOT_FAILURE = "boot_failure"
    DIMM_THERMAL = "dimm_thermal"
    CPU_THERMAL = "cpu_thermal"
    ANY = "any"
    OS_NOT_ALIVE = "os_not_alive"
    MEMORY_CHECK = "system_memory_check"
    CLOCK_HEALTH_CHECK = "clock_check_failure"


class PythonSvDump(object):
    MCA_DUMP = "mca_dump"
    MCU_DUMP = "mcu_dump"
    UPI_DUMP = "upi_dump"
    UPI_ERROR_DUMP = "upi_error_dump"
    S3M_DUMP = "s3m_dump"
    PMC_DUMP = "pmc_dump"
    PUNIT_DUMP = "punit_dump"
    PCU_DATA = "pcu_data"
    PMC_DEBUG = "pmc_debug"
    PMC_HISTO = "pmc_histo"
    EBC_STATE = "ebc_state"
    DDR_PHY_DUMP = "ddr_phy_dump"
    MEMSS_DUMP = "memss_dump"
    S3M_CFR_CHECK = "s3m_cfr_check"
    SUT_SOFT_HARD_HUNG = "sut_soft_hard_hung"


class RasRunnerToolConstant(object):
    RUNNER_CMD_DICT = ["yes | cp /runner/install/binaries7.1/memrunner "
                       "/runner/bin/applications/memrunner_x64/memrunner ",
                       "yes | cp /runner/install/binaries7.1/threadrunner "
                       "/runner/bin/applications/threadrunner_x64/threadrunner ",
                       "yes | cp /runner/install/binaries7.1/librunner_python_x64.so "
                       "/runner/bin/scripts/librunner_python_x64.so ",
                       "yes | cp /runner/install/binaries7.1/xtest /runner/bin/applications/dgem/xtest ",
                       "yes | cp /runner/install/binaries7.1/xtestAVX2 /runner/bin/applications/dgem/xtestAVX2 ",
                       "yes | cp /runner/install/binaries7.1/stream /runner/bin/applications/stream/stream ",
                       "yes | cp /runner/install/binaries7.1/streamAVX2 /runner/bin/applications/stream/streamAVX2 ",
                       "yes | cp /runner/install/binaries7.1/stressapptest /runner/bin/applications/sat/stressapptest  ",
                       ]
    RUNNER_FOLDER_PATH = "cp -r /root/runner/6.0/* /runner"


class MemoryHealthCheck():
    SYSTEM_MEMORY_CHECK = "system_memory_check"
    CPU_CHECK = "cpu_check"
    DDR_FREQ_CHECK = "ddr_frequency_check"
    DISK_SPACE_CHECK = "disk_space_check"
    NUMA_SNC_CHECK = "numa_snc_check"
    RESET_CHECK = "reset_check"


class ErrorTypeAttribute():
    CORRECTABLE = "correctable"
    UNC_NON_FATAL = "unc_non_fatal"
    UNC_FATAL = "unc_fatal"
    CORRECTABLE_AER = "correctable_aer"
    UNC_NON_FATAL_EDPC_DISABLED = "unc_non_fatal_edpc_disabled"


class SeverityAttribute():
    FATAL = "fatal"
    NON_FATAL = "nonfatal"


class RaidConstants():
    RAID0 = "RAID0(Stripe)"
    RAID1 = "RAID1(Mirror)"
    RAID5 = "RAID5(Parity)"
    RAID10 = "RAID10(RAID1+0)"
    CREATE_VOLUME = "Create Volume"
    CREATE_RAID_VOLUME = "Create RAID Volume"
    DELETE_RAID_VOLUME = "Delete"
    SELECT_YES = "Yes"
    SELECT_X = "X"


class RasIoConstant():
    RasIoVirtualization = "ras/io_virtualization"


class PassThroughAttribute(enum.Enum):
    Network = "Network"
    NVMe = "NVMe"


class VmTypeAttribute(enum.Enum):
    RS_5 = "RS5"
    RHEL = "RHEL"


class MLCToolConstants(object):
    MLC_TOOL_NAME = "mlc"
    MLC_PEAK_INJECTION_BANDWIDTH_CMD = "./mlc --peak_injection_bandwidth -Z -t{}"


class StreamToolTypes(object):
    STREAM_TYPE_AVX3 = "avx3"


class StressAppTestConstants(object):
    STRESS_APP_TOOL_NAME = "stressapptest"
    STRESS_APP_TEST_COMMAND = "./stressapptest -s {} -M -m -W"


class SandstoneTestConstants(object):
    PROXY_CHAIN = "echo proxy=http://proxy-chain.intel.com:912 >> /etc/dnf/dnf.conf"
    DNF_UTILS = "dnf install -y dnf-utils"
    CONTAINERD_IO = "dnf install -y --allowerasing docker-ce docker-ce-cli containerd.io"
    IPMI_TOOL = "yum install -y OpenIPMI ipmitool"
    STOP_FIREWALL_SUT = "systemctl stop firewalld"
    DAEMON_RELOAD = "systemctl daemon-reload"
    ENABLE_DOCKER = "systemctl enable docker"
    START_DOCKER = "systemctl start docker"
    ROOT = "/root/sandstone_logs"

    PULL_SANDSTONE_REPO = "docker pull prt-registry.sova.intel.com/sandstone:{}"
    RUN_SANDSTONE_TEST = "docker run -i --privileged prt-registry.sova.intel.com/sandstone:{} -vv --beta -T 5m " \
                         "--disable=@locks_cross_cacheline > /root/sandstone_logs/sandstone_cycle{}.log"
    IPMI_TOOL_POWER_CYCLE = "ipmitool power cycle"
    IPMI_TOOL_POWER_RESET = "ipmitool power reset"


class CpuFanSpeedConstants(object):
    SET_FAN_SPEED_PWM_15_16 = ["echo {} > /sys/class/hwmon/hwmon0/pwm16",
                               "echo {} > /sys/class/hwmon/hwmon0/pwm15"]
    GET_FAN_SPEED_PWM_15_16 = ["cat /sys/class/hwmon/hwmon0/pwm16", "cat /sys/class/hwmon/hwmon0/pwm15"]
    FAN_SPEED_100_PERCENT = "255"


class XmlCliConstants(object):
    XMLCLI_LOG_FILE = "XmlCli.log"
    OUT_DIR = r"C:\Python36\Lib\site-packages\pysvtools\xmlcli\out"
    SEARCH_STRING = "Saving the output Binary file as"


class VmStressAttribute(object):
    IP = "ip"
    VM_OS_OBJ = "vm_os_obj"
    IPERF_SUT_PATH = "iperf_sut_path"
    LINUX_ETHERNET_INTERFACE_NAME = "eth1"
    WINDOWS_19 = "Windows_19"
    WINDOWS_16 = "Windows_16"
    LINUX = "Linux"
    VSWITCH_FOR_STATIC = "VS_For_Static"
    LINUX_IPERF_TEST_NAME = "iperf3"
    WINDOWS_IPERF_TEST_CMD = "iperf3.exe"


class DiskCheckConstant(object):
    FILE_NAME = "check_disk.txt"


class CvCliToolConstant(object):
    CV_CLI_LINUX_SCRIPT_FILE = r"cxl_cv_linux.py"
    CV_CLI_LOG_FILE = r'cv_cli_linux_output.txt'
    CV_CLI_TOOL_NAME = r'CXL_CV_CLI'
