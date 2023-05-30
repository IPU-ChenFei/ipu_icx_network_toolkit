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
from enum import Enum
from dtaf_core.lib.dtaf_constants import OperatingSystems
from dtaf_core.lib.registry import MetaRegistry


@six.add_metaclass(MetaRegistry)
class TXT(object):
    """TXT constants"""

    TXT_REG_PUBLIC_BASE = 0xFED30000
    TXT_REG_PRIVATE_BASE = 0xFED20000

    TXT_CAPABLE_OS = [OperatingSystems.LINUX, OperatingSystems.ESXI]

    # From Patsburg PCH C-Spec 27.5.3 (Table for Decode BB LTR/LTW Cycles)
    TXT_REG_OFFSETS = dict(
        LT_STS=0x0000,
        LT_ESTS=0x0008,
        LT_EXISTS=0x0010,
        LT_JOINS=0x0020,
        LT_CRASH=0x0030,
        LT_SPAD=0x00A0,
        LT_DID=0x0110,
        LT_FITSTATUS=0x0340,
        ACM_ERROR=0x0328,
        LT_E2STS=0x08F0,
        SECRETS_PRIV=0x08E8
    )

    TXT_TRUSTED_REGISTER_VALUES = dict(LT_STS=0x0001C091, LT_ESTS=0x00000000)
    TXT_UNTRUSTED_REGISTER_VALUES = dict(LT_JOINS=0x00000000)
    LT_E2STS_EXP = 0x00000006
    LT_E2STS_RESET_EXP = 0x0000000E

    LT_CRASH = "LT Crash"
    LT_ESTS = "LT ESTS"
    LT_E2STS = "LT E2STS :"
    LT_STS = "LT_STS"

    LT_MSR_IA32_FEATURE_CONTROL_0x3A = "MSR IA32_FEATURE_CONTROL (0x3A)"
    LT_FED30308_HEAP_BASE = "FED30300 - HEAP BASE"
    LT_FED30308_HEAP_SIZE = "FED30308 - HEAP SIZE"
    LT_FED30270_SINIT_BASE_ADDRESS = "FED30270 - SINIT Base Address"
    LT_SINIT_MEM_ADDRESS = "[63:12]Sinit Mem Address..."
    LT_FED30278_SINIT_SIZE = "FED30278 - SINIT size"
    LT_FED30810_LT_PCH_DID_VID = "FED30810 LT PCH DIDVID"
    LT_FED30110_LT_DID_VID = "FED30110 - LT DID/VID"
    LT_CPU_ID = "CPU ID:"
    LT_FED300A0S_LT_SPAD_DONE = "FED300A0S - LT SPAD Done"
    LT_FED30010_LT_EXISTS = "FED30010 - LT EXISTS"
    LT_FED30020_LT_JOINS = "FED30020 - LT JOINS"

    ACM_SIG_REG = "0xff880000p"
    ACM_ERROR_REG = "0xfed30328p"
    LT_CRASH_ERROR_REG = "0xfed30030p"
    TPM_ESTABLISH_BIT = "0xfed40000p"

    TXT_ENABLE_KNOB_STRING = "ProcessorLtsxEnable=1,ProcessorVmxEnable=1,ProcessorSmxEnable=1,LockChipset=1," + \
                             "VTdSupport=1,InterruptRemap=1,"

    MSR_PKG_C6_RESIDENCY = 0x3F9
    TPM_LEGACY = "TPM1_2"
    TPM2 = "TPM2"
    class Fuses(object):
        CORE_CONFIG_BASE = "uncore0.pcu_cr_core_configuration_0."
        CAPID_CONFIG_BASE = "uncore0.pcu_cr_capid0_cfg."
        SMX_DISABLE_FUSE = CORE_CONFIG_BASE + "smx_dis"
        LTSX_ENABLE_FUSE = CORE_CONFIG_BASE + "lt_sx_en"
        PROD_PART_FUSE = CORE_CONFIG_BASE + "production_part"
        VMX_DISABLE_FUSE = CORE_CONFIG_BASE + "vmx_dis"
        LT_PRODUCTION_FUSE = CAPID_CONFIG_BASE + "lt_production"
        DEFAULT_EXPECTED_FUSES = {
            SMX_DISABLE_FUSE: 0,
            LTSX_ENABLE_FUSE: 1,
            PROD_PART_FUSE: 0,
            VMX_DISABLE_FUSE: 0,
            LT_PRODUCTION_FUSE: 1
        }

    class SvBios(object):
        TXT_ENABLE = "ProcessorLtsxEnable="
        VMX_ENABLE = "ProcessorVmxEnable="
        SMX_ENABLE = "ProcessorSmxEnable="
        LOCK_CHIPSET = "LockChipset="
        VTD_ENABLE = "VTdSupport="
        INTERRUPT_REMAP = "InterruptRemap="
        MSR_LOCK_ENABLE = "ProcessorMsrLockControl="


class TXTSKX(TXT):

    class Fuses(object):
        CORE_CONFIG_BASE = "uncore0.pcu_cr_core_configuration_0."
        CAPID_CONFIG_BASE = "uncore0.pcu_cr_capid0_cfg."
        SMX_DISABLE_FUSE = CORE_CONFIG_BASE + "smx_dis"
        LTSX_ENABLE_FUSE = CORE_CONFIG_BASE + "lt_sx_en"
        PROD_PART_FUSE = CORE_CONFIG_BASE + "production_part"
        VMX_DISABLE_FUSE = CORE_CONFIG_BASE + "vmx_dis"
        LT_PRODUCTION_FUSE = CAPID_CONFIG_BASE + "lt_production"
        DEFAULT_EXPECTED_FUSES = {
            SMX_DISABLE_FUSE: 0,
            LTSX_ENABLE_FUSE: 1,
            PROD_PART_FUSE: 0,
            VMX_DISABLE_FUSE: 0,
            LT_PRODUCTION_FUSE: 1
        }


class TXTCLX(TXT):

    CSCRIPT_SOCKET0_UNCORE_PCU_RESOLVED_CORES_CMD_STR = "csp.socket0.uncore0.pcu_cr_resolved_cores_cfg"
    CSCRIPT_SOCKET1_UNCORE_PCU_RESOLVED_CORES_CMD_STR = "csp.socket1.uncore0.pcu_cr_resolved_cores_cfg"

    class Fuses(object):
        CORE_CONFIG_BASE = "uncore0.pcu_cr_core_configuration_0."
        CAPID_CONFIG_BASE = "uncore0.pcu_cr_capid0_cfg."
        SMX_DISABLE_FUSE = CORE_CONFIG_BASE + "smx_dis"
        LTSX_ENABLE_FUSE = CORE_CONFIG_BASE + "lt_sx_en"
        PROD_PART_FUSE = CORE_CONFIG_BASE + "production_part"
        VMX_DISABLE_FUSE = CORE_CONFIG_BASE + "vmx_dis"
        LT_PRODUCTION_FUSE = CAPID_CONFIG_BASE + "lt_production"
        DEFAULT_EXPECTED_FUSES = {
            SMX_DISABLE_FUSE: 0,
            LTSX_ENABLE_FUSE: 1,
            PROD_PART_FUSE: 0,
            VMX_DISABLE_FUSE: 0,
            LT_PRODUCTION_FUSE: 1
        }


class TXTICX(TXT):

    class Fuses(object):
        CORE_CONFIG_BASE = "uncore.punit.core_configuration_0."
        CAPID_CONFIG_BASE = "uncore.punit.capid0_cfg"
        SMX_DISABLE_FUSE = CORE_CONFIG_BASE + "smx_dis"
        LTSX_ENABLE_FUSE = CORE_CONFIG_BASE + "lt_sx_en"
        PROD_PART_FUSE = CORE_CONFIG_BASE + "production_part"
        VMX_DISABLE_FUSE = CORE_CONFIG_BASE + "vmx_dis"
        LT_PRODUCTION_FUSE = CAPID_CONFIG_BASE + "lt_production"
        DEFAULT_EXPECTED_FUSES = {
            SMX_DISABLE_FUSE: 0,
            LTSX_ENABLE_FUSE: 1,
            PROD_PART_FUSE: 0,
            VMX_DISABLE_FUSE: 0,
            LT_PRODUCTION_FUSE: 0  # Will change to 1 around ES2
        }


class Tboot(object):
    """Tboot-related constants"""
    # Tboot OS constants
    LINK_TO_CLONE_LATEST_TBOOT = "http://hg.code.sf.net/p/tboot/code"
    TBOOT_FOLDER = "tboot"
    TBOOT_GZ_FILE = "tboot.gz"
    TBOOT_DESTINATION_FOLDER = "tboot-code"
    TBOOT_LINUX_TBOOT_POSTFIX = "_linux_tboot"

    class Log(object):
        """Tboot log strings"""
        TBOOT_TXT_ERRORCODE = "TBOOT: TXT.ERRORCODE:"
        TBOOT_TXT_ESTS = "TBOOT: TXT.ESTS:"
        TBOOT_TXT_E2STS = "TBOOT: TXT.E2STS:"
        TBOOT_IA32_FEATURE_CONTROL_MSR = "TBOOT: IA32_FEATURE_CONTROL_MSR:"
        TBOOT_TXT_HEAP_BASE = "TBOOT: TXT.HEAP.BASE:"
        TBOOT_TXT_HEAP_SIZE = "TBOOT: TXT.HEAP.SIZE:"
        TBOOT_TXT_SINIT_BASE = "TBOOT: TXT.SINIT.BASE:"
        TBOOT_TXT_SINIT_SIZE = "TBOOT: TXT.SINIT.SIZE:"
        TBOOT_CHIPSET_IDS = "TBOOT: chipset ids:"
        TBOOT_CPU_ID = "TBOOT: processor family/model/stepping:"


class TpmIndices(object):
    """Enum for TPM indices"""
    PO = "PO"
    PS = "PS"
    AUX = "AUX"
    SGX = "SGX"


class ArtifactoryToolPaths(Enum):
    """Path to Artifactory tools."""
    TPM2PROVTOOLS = "TPM2ProvfilesCBnT.zip"
    SERVER_SECURITY_TOOLS = "ServerSecurityToolkit.zip"


class Tpm2ToolCmds(object):
    """Dict of indices to TPM2 Prov tool commands"""
    PROV_CMDS = {"PO": "Tpm2PoProv.nsh",
                 "SGX": "Tpm2SgxiProv.nsh",
                 "PS": "Tpm2TxtProv.nsh",
                 "AUX": "Tpm2_CBnT_Prov.nsh"}
    CLEAR_OWNERSHIP = "TPM2ClearOwnership.nsh"
    PCR_GEN = "ServerPCRDumpTPM2.efi"
    CLEAR_INDEX = {"PO": "Tpm2ProvTool.efi"}

class LCPPolicyElements(object):
    """Policy Element types for launch control policies"""
    PCONF = "pconf"
    MLE = "mle"
    MLE_LEGACY = "mle_legacy"


class Tpm2LcpCommands:
    CREATE_ELEMENT = "lcp2_crtpolelt"
    CREATE_LIST = "lcp2_crtpollist"
    CREATE_POLICY = "lcp2_crtpol"
    MLE_HASH = "lcp2_mlehash"

class Tpm12LcpCommands:
    CREATE_ELEMENT = "lcp_crtpolelt"
    CREATE_LIST = "lcp_crtpollist"
    CREATE_POLICY = "lcp_crtpol"
    MLE_HASH = "lcp_mlehash"

class Tpm2KeySignatures:
    RSA3072 = "3072"
    RSA2048 = "2048"


class LCPPolicyElements(object):
    """Policy Element types for launch control policies"""
    PCONF = "pconf"
    MLE = "mle"
    MLE_LEGACY = "mle_legacy"


class Tpm2LcpCommands:
    CREATE_ELEMENT = "lcp2_crtpolelt"
    CREATE_LIST = "lcp2_crtpollist"
    CREATE_POLICY = "lcp2_crtpol"
    MLE_HASH = "lcp2_mlehash"


class Tpm2KeySignatures:
    RSA3072 = "3072"
    RSA2048 = "2048"


class Tpm2Drive(object):
    """
       Constants for accessing TPM2 collateral from the UEFI shell.

       TPM2 provisioning makes  use of the UEFI shell. This requires a flash drive to be attached to the SUT with
       the following structure:
       / drive root
         |_ TxtBtgInfo.efi
         |_ ServerTXTINFO.efi
         |_ getsec64.efi
         |_ tpm2_automation
           |- TPM2 Tools
             |- TPM2ProvFiles
                |- ExamplePO_Sha256.iDef
                |- ExamplePsSha256.iDef
                |- ExampleSgxSha256.iDef
                |- Tpm2PoProv.nsh
                |- Tpm2TxtProv.nsh
                |- Tpm2SgxiProv.nsh
                |- Other files included in Tpm2ProvFiles package
    """
    TPM2_FOLDER = "tpm2_automation/"
    TPM2_TOOLS_FOLDER = '"Tpm2 Tools"/'
    TPM2_PROVISIONING_FOLDER = "Tpm2ProvFiles/"
    TPM2_PCR_FOLDER = "TPM PCR/"

class Tpm12Drive(object):
    """
       Constants for accessing TPM 1.2 collateral from the UEFI shell.

       TPM 1.2 provisioning makes  use of the UEFI shell. This requires a flash drive to be attached to the SUT with
       the following structure:
       / drive root
         |_ ServerTPMTool
           |- Executable
             |- DefaultTPMProvisionNPW-Unlocked.nsh
             |- Other files included in Executable folder
    """
    TPM12_FOLDER = "ServerTPMTool/"
    TPM12_EXEC_FOLDER = "Executable/"


class FitTableLabels(object):
    """Enum for FIT table labels"""
    KEY_MANIFEST = "__KEYM__"
    BOOT_POLICY_MANIFEST = "__ACBP__"
    ACM_HEADER = "0x00010002"
