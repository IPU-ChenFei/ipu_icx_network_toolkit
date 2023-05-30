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
import six
from collections import OrderedDict
from enum import Enum

from dtaf_core.lib.registry import MetaRegistry
from dtaf_core.lib.private.cl_utils.adapter import data_types


@six.add_metaclass(MetaRegistry)
class TDX:
    """TDX constants"""

    class QemuCommands(object):
        SHUTDOWN = "system_powerdown"
        RESET = "system_reset"
        PAUSE = "stop"
        RESUME = "cont"
        STOP_EMULATION = "q"

    class TimeConstants(object):
        HOUR_IN_SECONDS = 3600
        MINUTE_IN_SECONDS = 60
        DAY_IN_SECONDS = 86400

    # label from content_configuration.xml file to use AC cycle instead of graceful reset
    AC_RESET = "AC_RESET"
    RESET_KNOBS = "RESET_KNOBS"

    # Number of attempts to boot a VM from content configuration file
    NUM_VM_BOOT_ATTEMPTS = "NUM_VM_BOOT_ATTEMPTS"

    # TDVM OSes
    TDVMOS = ["RHEL", "Ubuntu", "CentOS", "Windows"]

    # Linux TDVM configurations from content configuration file
    TDVF_PATH = "TDVF_PATH"
    TD_GUEST_IMAGE_DIR = "TD_GUEST_IMAGE_DIR"
    TD_GUEST_IMAGE_PATH_HOST = "TD_GUEST_IMAGE_PATH_HOST"
    TD_GUEST_IMAGE_PATH = "TD_GUEST_IMAGE_PATH_SUT"
    TD_GUEST_KERNEL = "TD_GUEST_KERNEL"
    TD_GUEST_CORES = "TD_GUEST_CORES"
    TD_GUEST_MEM = "TD_GUEST_MEM"
    NUMBER_OF_VMS = "NUMBER_OF_VMS"
    TELNET_RANGE_START = "TELNET_RANGE_START"
    SSH_RANGE_START = "SSH_RANGE_START"
    TD_GUEST_USER = "TD_GUEST_USER"
    TD_GUEST_USER_PWD = "TD_GUEST_USER_PWD"
    TD_GUEST_SERIAL_PATH = "TD_GUEST_SERIAL_PATH"
    TCP_RANGE_START = "TCP_RANGE_START"
    VM_BOOT_TIMEOUT = "VM_BOOT_TIMEOUT"
    VM_OS = "VM_OS"
    SEAM_MODULE_PATH_HOST = "SEAM_MODULE_PATH_HOST"
    SEAM_LOADER_UPDATE_PATH = "SEAM_LOADER_UPDATE_PATH"
    CMCI_MORPHING_ENABLE = "CMCI_MORPHING_ENABLE"
    DIRECTORY_MODE = "DIRECTORY_MODE_ENABLE"
    LM_MODE = "LM_MODE"
    INTEL_NEXT_KERNEL = "INTEL_NEXT_KERNEL"
    SMX_ENABLE = "SMX_ENABLED"
    DAM_ENABLE = "DAM_ENABLED"
    BIOS_SEAM_ENABLE = "BIOS_SEAMLDR_ENABLE"
    MEM_INTEGRITY_MODE = "MEM_INTEGRITY_MODE"
    CYCLING = "cycling"
    WARM_CYCLES = "warm_reboot_cycles"
    COLD_CYCLES = "cold_reboot_cycles"
    AC_CYCLES = "ac_reboot_cycles"
    IPMI_CYCLES = "ipmi_cycles"
    REDFISH_CYCLES = "redfish_cycles"
    TDX_DISABLE_ENABLE_CYCLES = "tdx_disable_cycle"
    TD_GUEST_REBOOT_CYCLES = "td_guest_reboot_cycles"
    TDX_SGX_HYDRA_TEST_TIME = "tdx_sgx_hydra_test_time"
    TD_GUEST_IMAGE_PATH_SUT_UBUNTU = "TD_GUEST_IMAGE_PATH_SUT_UBUNTU"
    LEGACY_GUEST_IMAGE_PATH_SUT_UBUNTU = "LEGACY_GUEST_IMAGE_PATH_SUT_UBUNTU"

    # Linux attestation constants
    ATTESTATION_STACK = "TDX_ATTESTATION_STACK_LOCATION"
    # password removed for security reason
    SBX_API_KEY = "SBX_API_KEY"
    E2E_SCRIPT_LOCATION = "E2E_SCRIPT_LOCATION"
    ATTESTATION_WARM_CYCLES = "attestation_warm_reboot_cycles"
    PCCS_PWD = "PCCS_PWD"

    # Windows guest configurations
    WINDOWS_GUEST_NAME = "WINDOWS_GUEST_NAME"
    LEGACY_VM_IMAGE_PATH_SUT = "LEGACY_VM_IMAGE_PATH_SUT"
    VM_TEMPLATE_NAME = "LegacyVMTemplate1"
    TD_GUEST_TEMPLATE_NAME = "TDTemplate"
    TD_GUEST_NAME = "TD{}-{}"  # VM name == TD + key - OS#, ex. TD1 - windows, TD3 - centos
    VM_GUEST_NAME = "VM{}-{}"  # VM name == VM + key #, ex. VM1 - windows, VM3 - centos
    TD_GUEST_NAME_FIRST_TWO = "TD"
    VM_GUEST_NAME_FIRST_TWO = "VM"
    TD_GUEST_IMAGE_MTC_SETUP_ENABLED = "TD_GUEST_IMAGE_MTC_SETUP_ENABLED"
    TD_GUEST_IMAGE_ENABLE_ETHERNET_ADAPTER = "TD_GUEST_IMAGE_ENABLE_ETHERNET_ADAPTER"
    TD_GUEST_VHD_GENERATION = "TD_GUEST_VHD_GENERATION"
    VM_TOOLS_BASE_LOC = "VM_TOOLS_BASE_LOC"

    # TDVM - Linux specific host settings
    NUMA_START_RANGE = "NUMA_START_RANGE"
    NUMA_INCREMENT_VALUE = "NUMA_INCREMENT_VALUE"
    INTEL_NEXT = "INTEL_NEXT_KERNEL"
    TDX_DMESG_STRINGS = ["TDX initialized", "Successfully initialized TDX module"]
    TDX_HOST_KERNEL_ARGS = ["console=ttyS0,115200", "tdx_host=on", "intel_iommu=on,sm_on", "numa_balancing=disable"]


    # TDVM - VM specific parameters
    NUMA_RANGE_DICT_LABEL = "numa_range"
    RUN_SCRIPT_PATH_DICT_LABEL = "run_script_path"
    SSH_PORT_DICT_LABEL = "ssh_port"
    TELNET_PORT_DICT_LABEL = "telnet_port"
    TCP_PORT_DICT_LABEL = "tcp_port"
    CID_LABEL = "cid_label"

    # BIOS directories
    EDKII_MENU_DIR = "EDKII Menu"
    SOCKET_CONFIG_DIR = "Socket Configuration"
    PROC_CONFIG_DIR = "Processor Configuration"
    PLAT_CONFIG_DIR = "Platform Configuration"
    MISC_CONFIG_DIR = "Miscellaneous Configuration"
    MEM_CONFIG_DIR = "Memory Configuration"
    MEM_RAS_CONFIG_DIR = "Memory RAS Configuration"
    COMMON_REF_CONFIG_DIR = "Common RefCode Configuration"

    # Automation directories for Linux
    TD_GUEST_IMAGE_PATH_LINUX = "/tdx/tdvm/images"
    TD_GUEST_LOG_PATH_LINUX = "/tdx/tdvm/logs"
    TDX_HOME_DIR = "/tdx/"
    YUM_REQUIRED_PACKAGES = "nc telnet numactl expect tdvf socat"
    YUM_OPTIONAL_PACKAGES = "epel-release msr-tools"
    ZIPPED_TDVM_FILES = "tdvm-logs.zip"
    SEAM_MODULE_PATH = "/tdx/seam/"
    SEAM_FW_PATH = "/boot/efi/EFI/TDX/"
    SEAMLDR_FILE = "*SEAMLDR.bin"
    SO_FILE = "*.so"
    SO_SIGSTRUCT_FILE = "*.so.sigstruct"

    class SeamLoaderFiles:  # ESP partition files
        SEAMLDR_NAME = "TDX-SEAM_SEAMLDR.bin"
        SO_SIGSTRUCT_NAME = "TDX-SEAM.so.sigstruct"
        SO_NAME = "TDX-SEAM.so"
        SEAM_FW_PATH = "/boot/efi/EFI/TDX/"

    class LibSeamLoaderFiles:  # installed package copies binaries in this format to this location
        SEAMLDR_NAME = "np-seamldr.acm"
        SO_SIGSTRUCT_NAME = "libtdx.so.sigstruct"
        SO_NAME = "libtdx.so"
        SEAM_FW_PATH = "/usr/lib/firmware/intel-seam/"

    # Linux commands
    REPLACE_SEAM_CMD = "dracut --force"
    IPMI_POWER_CYCLE = "ipmitool power cycle"
    POWER_BUTTON_SHUTDOWN_SET_CMD = "gsettings set org.gnome.settings-daemon.plugins.power power-button-action " \
                                    "interactive"
    POWER_BUTTON_SUSPEND_SET_CMD = "gsettings set org.gnome.settings-daemon.plugins.power power-button-action " \
                                   "suspend"
    DMIDECODE_GET_BIOS_VERSION = "dmidecode -s bios-version"
    DISABLE_LOGIN_TIMER_CMD = "gsettings set org.gnome.SessionManager logout-prompt false"
    ROOT_AUTOMATIC_LOGIN_VALUE = ["AutomaticLogin=root", "AutomaticLoginEnable=True"]
    ROOT_UNLOCK_SESSIONS_CMD = "loginctl unlock-sessions"

    # BIOS knob labels
    VMX_KNOB_LABEL = 'VMX'
    TME_KNOB_LABEL = 'Memory Encryption \\(TME\\)'
    TMEMT_KNOB_LABEL = 'Total Memory Encryption'
    MAX_KEYS_LABEL = 'Key stock amount'
    TDX_KNOB_LABEL = 'Trust Domain Extension'
    SGX_KNOB_LABEL = 'SW Guard Extensions \\(SGX\\)'
    MIRROR_MODE_LABEL = 'Mirror Mode'
    KEY_SPLIT_LABEL = 'TME-MT/TDX key split'
    NUMA_LABEL = 'Numa'
    UMA_BASED_CLUSTERING_KNOB = 'UMA-Based Clustering'

    # Options
    PARTIAL_MIRROR_MODE_OPTION = 'Partial Mirror Mode'
    FULL_MIRROR_MODE_OPTION = 'Full Mirror Mode'
    UMA_CLUSTER_HEMI_OPTION = 'Hemisphere (2-clusters)'
    UMA_CLUSTER_QUAD_OPTION = 'Quadrant   (4-clusters)'

    # stress test commands
    STRESSNG_CPU_CMD = "stress-ng --matrix 0 -t {}s -v --log-file "
    STRESSNG_MEMORY_CMD = "stress-ng --class memory --seq 0 -v --log-file "
    MPRIME_CMD = "mprime -t > "
    DISKSPD_CMD = "diskspd -c100M -t4 -Sh -d{} -w50 -L testfile > "
    NTTTCP_CLIENT_CMD = "ntttcp -s {}"
    NTTTCP_CLIENT_CMD_TIME = " -t {} -V > "
    NTTTCP_SERVER_CMD = "ntttcp -r"
    IPERF_SERVER_CMD = "iperf3 -i 10 -s"
    IPERF_CLIENT_CMD = "iperf3 -i 10 -w 400K -c {}"
    IPERF_CLIENT_CMD_TIME = " -t {} > "

    STRESSNG_COMPLETED_SUCCESSFULLY = ["metrics-check: all stressor metrics validated and sane", "successful run "
                                                                                                 "completed in"]

    class BiosKnobFiles(object):
        BIOS_CONFIG_FILE_TDX_DISABLE = "collateral/tdx_dis_reference_knobs.cfg"
        BIOS_CONFIG_FILE_VMX_ENABLE = "collateral/vmx_en_reference_knobs.cfg"
        BIOS_CONFIG_FILE_VMX_DISABLE = "collateral/vmx_dis_reference_knobs.cfg"
        BIOS_CONFIG_FILE_TMEMT_ENABLE = "collateral/tmemt_en_reference_knobs.cfg"
        BIOS_CONFIG_FILE_TMEMT_DISABLE = "collateral/tmemt_dis_reference_knobs.cfg"
        BIOS_CONFIG_FILE_TME_ENABLE = "../mktme/enable_tme/tme_enable_knob.cfg"
        BIOS_CONFIG_FILE_TME_DISABLE = "../mktme/enable_tme/tme_disable_knob.cfg"
        BIOS_CONFIG_FILE_TDX_ENABLE_ONLY = "collateral/tdx_only_en_reference_knobs.cfg"
        BIOS_CONFIG_FILE_TDX_DISABLE_ONLY = "collateral/tdx_only_dis_reference_knobs.cfg"
        BIOS_CONFIG_FILE_SPLIT_KEYS = "collateral/split_keys_knobs.cfg"
        BIOS_CONFIG_FILE_DIR_MODE_ENABLE = "collateral/dirmode_en_reference_knobs.cfg"
        BIOS_CONFIG_FILE_DIR_MODE_DISABLE = "collateral/dirmode_dis_reference_knobs.cfg"
        BIOS_CONFIG_FILE_TME_BYPASS = "collateral/tme_bypass_en.cfg"
        BIOS_CONFIG_FILE_CMCI_MORPHING_ENABLE = "collateral/cmci_morphing_en.cfg"
        BIOS_CONFIG_FILE_CMCI_MORPHING_DISABLE = "collateral/cmci_morphing_dis.cfg"
        BIOS_CONFIG_FILE_TWO_LM_ENABLE = "collateral/two_lm_en.cfg"
        BIOS_CONFIG_FILE_ONE_LM_ENABLE = "collateral/one_lm_en.cfg"
        BIOS_CONFIG_FILE_SMX_ENABLE = "collateral/smx_en_reference_knobs.cfg"
        BIOS_CONFIG_FILE_SGX_PRM_KNOB_SIZE = "collateral/sgx_prm_size.cfg"
        BIOS_CONFIG_FILE_SMX_DISABLE = "collateral/smx_dis_reference_knobs.cfg"
        BIOS_CONFIG_FILE_DAM_ENABLE = "collateral/dam_en_reference_knobs.cfg"
        BIOS_CONFIG_FILE_DAM_DISABLE = "collateral/dam_dis_reference_knobs.cfg"
        BIOS_CONFIG_FILE_BIOS_SEAM_ENABLE = "collateral/bios_seam_ldr_en_reference_knobs.cfg"
        BIOS_CONFIG_FILE_BIOS_SEAM_DISABLE = "collateral/bios_seam_ldr_dis_reference_knobs.cfg"
        BIOS_CONFIG_FILE_BIOS_MEM_INTEGRITY_ENABLE = "collateral/mem_integrity_en_reference_knobs.cfg"
        BIOS_CONFIG_FILE_BIOS_MEM_INTEGRITY_DISABLE = "collateral/mem_integrity_dis_reference_knobs.cfg"

    KNOBS = {f"{DIRECTORY_MODE}_True": BiosKnobFiles.BIOS_CONFIG_FILE_DIR_MODE_ENABLE,
             f"{DIRECTORY_MODE}_False": BiosKnobFiles.BIOS_CONFIG_FILE_DIR_MODE_DISABLE,
             f"{CMCI_MORPHING_ENABLE}_True": BiosKnobFiles.BIOS_CONFIG_FILE_CMCI_MORPHING_ENABLE,
             f"{CMCI_MORPHING_ENABLE}_False": BiosKnobFiles.BIOS_CONFIG_FILE_CMCI_MORPHING_DISABLE,
             f"{DAM_ENABLE}_True": BiosKnobFiles.BIOS_CONFIG_FILE_DAM_ENABLE,
             f"{DAM_ENABLE}_False": BiosKnobFiles.BIOS_CONFIG_FILE_DAM_DISABLE,
             f"{SMX_ENABLE}_True": BiosKnobFiles.BIOS_CONFIG_FILE_SMX_ENABLE,
             f"{SMX_ENABLE}_False": BiosKnobFiles.BIOS_CONFIG_FILE_SMX_DISABLE,
             f"{LM_MODE}_1LM": BiosKnobFiles.BIOS_CONFIG_FILE_ONE_LM_ENABLE,
             f"{LM_MODE}_2LM": BiosKnobFiles.BIOS_CONFIG_FILE_TWO_LM_ENABLE,
             f"{BIOS_SEAM_ENABLE}_True": BiosKnobFiles.BIOS_CONFIG_FILE_BIOS_SEAM_ENABLE,
             f"{BIOS_SEAM_ENABLE}_False": BiosKnobFiles.BIOS_CONFIG_FILE_BIOS_SEAM_DISABLE,
             f"{MEM_INTEGRITY_MODE}_CI": BiosKnobFiles.BIOS_CONFIG_FILE_BIOS_MEM_INTEGRITY_ENABLE,
             f"{MEM_INTEGRITY_MODE}_LI": BiosKnobFiles.BIOS_CONFIG_FILE_BIOS_MEM_INTEGRITY_DISABLE
             }

    CUSTOMIZABLE_KNOBS = [DIRECTORY_MODE, CMCI_MORPHING_ENABLE,
                          LM_MODE, DAM_ENABLE, SMX_ENABLE, BIOS_SEAM_ENABLE, MEM_INTEGRITY_MODE]

    # pmutils constants
    class PmUtilsCmds(object):
        PMUTILS_CSTATE_HARASSER = "pmutil_bin -S 1 -t {} -y 10 -cstate_harass=1"
        PMUTILS_RAPL_HARASSER = "pmutil_bin -S 0 -t {} -y 0.01 -socket_rapl_harass=1"
        PMUTILS_UNCORE_HARASSER = "pmutil_bin -t {} -y 10 -uncore_harass"
        PMUTILS_TURBO_HARASSER = "pmutil_bin -t {} -y 10 -turbo_harass"
        PMUTILS_PSTATE_HARASSER = "pmutil_bin -S 1 -t {} -y 10 -pstate_harass=1"

    # stress test names
    class WorkloadToolNames(object):
        DISKSPD = "diskspd"
        MPRIME = "mprime"
        STRESSNG = "stress-ng"
        NTTTCP = "ntttcp"
        IPERF = "iperf3"
        STRESSAPPTEST = "stressapptest"
        MLC_INTERNAL = "mlc_internal"
        SHA512SUM = "sha512sum"

    """Error collectors used for Fisher RAS testing."""
    LINUX_ERROR_COLLECTORS = ["mcelog"]

    class SncRegisterValues(object):
        """Registers for SNC and UMA testing."""
        REGISTER_PATH = "uncore.m2iosf0.snc_config"
        NUM_SNC_CLUSTERS_FIELD = "num_snc_clu"

        # fields and expected values for SNC4
        SNC_FOUR_FIELDS = {NUM_SNC_CLUSTERS_FIELD: 0x3,
                           "snc_ind_en": 0x1,
                           "full_snc_en": 0x0}

        # fields and expected values for SNC2
        SNC_TWO_FIELDS = {NUM_SNC_CLUSTERS_FIELD: 0x1,
                          "snc_ind_en": 0x1,
                          "full_snc_en": 0x1}

        # fields and expected values for UMA
        UMA_EN_FIELDS = {NUM_SNC_CLUSTERS_FIELD: 0x0,
                         "snc_ind_en": 0x1,
                         "full_snc_en": 0x0}

    # BIOS menu trees
    PROC_BIOS_PATH = OrderedDict([(EDKII_MENU_DIR, data_types.BIOS_UI_DIR_TYPE),
                                  (SOCKET_CONFIG_DIR, data_types.BIOS_UI_DIR_TYPE),
                                  (PROC_CONFIG_DIR, data_types.BIOS_UI_DIR_TYPE)])

    MISC_BIOS_PATH = OrderedDict([(EDKII_MENU_DIR, data_types.BIOS_UI_DIR_TYPE),
                                  (PLAT_CONFIG_DIR, data_types.BIOS_UI_DIR_TYPE),
                                  (MISC_CONFIG_DIR, data_types.BIOS_UI_DIR_TYPE)])

    RAS_BIOS_PATH = OrderedDict([(EDKII_MENU_DIR, data_types.BIOS_UI_DIR_TYPE),
                                 (SOCKET_CONFIG_DIR, data_types.BIOS_UI_DIR_TYPE),
                                 (MEM_CONFIG_DIR, data_types.BIOS_UI_DIR_TYPE),
                                 (MEM_RAS_CONFIG_DIR, data_types.BIOS_UI_DIR_TYPE)])

    COMMON_REF_CONFIG_PATH = OrderedDict([(EDKII_MENU_DIR, data_types.BIOS_UI_DIR_TYPE),
                                          (SOCKET_CONFIG_DIR, data_types.BIOS_UI_DIR_TYPE),
                                          (COMMON_REF_CONFIG_DIR, data_types.BIOS_UI_DIR_TYPE)])

    # failure messages when installing yum packages
    PACKAGE_INSTALL_FAIL_PHRASES = ["error", "no space left on device"]

    PYTHON_FAILURE_MESSAGES = ["python: command not found", "'python' is not recognized as an internal or external "
                                                            "command'", "no such file or directory"]

    class AttestationServer(Enum):
        SBX = "SBX"
        LIV = "LIV"
        PRX = "PRX"


class TDXSPR(TDX):
    """SPR specific registers and constants."""

    class RegisterConstants(object):
        MSR_TME_CAPABILITIES = 0x981
        MSR_TME_ACTIVATE = 0x982
        MSR_SEAMRR_BASE = 0x1400
        MSR_SEAMRR_MASK = 0x1401
        MSR_TME_KEYID_PARTITIONING = 0x87
        MTTR_CAPABILITIES = 0xfe
        MSR_MCHECK_ERROR = 0xa0
        UCODE_SIGNING = 0x8b
        DAM_REGISTER = 0x503

    class MSRTMECapabilitiesBits(object):
        MAX_KEYS_START = 36
        MAX_KEYS_END = 50
        MAX_KEYID_START = 32
        MAX_KEYID_END = 35
        TME_ENCRYPTION_BYPASS_SUPPORTED = 31
        PLAT_INTEGRITY_SUPPORTED = 1

    class MSRTMEActivateBits(object):
        KEYID_BITS_TDX_START = 36
        KEYID_BITS_TDX_END = 39
        KEYID_BITS_MKTME_START = 32
        KEYID_BITS_MKTME_END = 35
        HARDWARE_ENCRYPTION_ENABLE = 1
        TME_ENCRYPTION_BYPASS_ENABLE = 31
        MEM_INTEGRITY_ENABLED = 49

    class SEAMRRBASEBits(object):
        CONFIGURED_BIT = 3
        BASE_ADDRESS_START = 25
        BASE_ADDRESS_END = 51

    class MSRTMEKeyPartitioning(object):
        MSR_TME_KEYS_END = 31
        MSR_TME_KEYS_START = 0
        MSR_TDX_KEYS_START = 32
        MSR_TDX_KEYS_END = 63

    class MTTRCapabilitiesBits(object):
        TDX_ENUMERATION = 15

    class SEAMRRMaskBits(object):
        SEAMRR_ACTIVE = 11
        SEAMRR_LOCKED = 10
        MASK_ADDRESS_START = 25
        MASK_ADDRESS_END = 51

    class MCHECKErrorMsrValues(object):
        NO_TDX_KEYS = 0xF46F
        LT_AGENT_NOT_SET = 0xf553
        LT_PLAT_NOT_SET = 0x1381

    class UcodeSigningMsrBit(object):
        UCODE_PROD_BIT = 63

    class DAMMsrBit(object):
        DAM_CLEARED = 1

    TXT_TRUSTED_REGISTER_VALUES = dict(LT_STS=0x00018091, LT_ESTS=0x00000000)

    MAX_KEYS = 127  # 128 max - 1 key for TME = 127

    # Mapping number of TDX keys to XmlCli BIOS knob index
    KEY_IDX = {0: 0x0, 64: 0x1, 96: 0x2, 112: 0x3, 120: 0x4, 124: 0x5, 126: 0x6}

    # How many TDX key ID bits to assign to TDX if there are no keys assigned and TDX BIOS knobs are enabled
    DEFAULT_TDX_KEYS = 64
    PRMRR_BASE_MSRS = [0x2a0, 0x2a1, 0x2a2, 0x2a3, 0x2a4, 0x2a5, 0x2a6, 0x2a7]

    PRM_KNOB_VALUES = {
        "128M": 0x8000000,
        "256M": 0x10000000,
        "512M": 0x20000000,
        "1G": 0x40000000,
        "2G": 0x80000000,
        "4G": 0x100000000,
        "8G": 0x200000000,
        "16G": 0x400000000,
        "32G": 0x800000000,
        "64G": 0x1000000000,
        "128G": 0x2000000000,
        "256G": 0x4000000000,
        "512G": 0x8000000000
    }


class TDXEMR(TDXSPR):
    """EMR specific registers and constants."""

    # TODO: No EMR specific values yet, should inherit values from SPR unless specifically overridden
    pass


class TDXGNR(TDXSPR):
    """GNR specific registers and constants."""

    MAX_KEYS = 2047  # 2048 max - 1 key for TME = 2047

    # TODO: update key splits for 2048 key max
    # Mapping number of TDX keys to XmlCli BIOS knob index
    KEY_IDX = {0: 0x0, 64: 0x1, 96: 0x2, 112: 0x3, 120: 0x4, 124: 0x5, 126: 0x6}

    # How many TDX key ID bits to assign to TDX if there are no keys assigned and TDX BIOS knobs are enabled
    DEFAULT_TDX_KEYS = 64
