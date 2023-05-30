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
"""Module containing sdsi-specific exceptions to be raised when tests errors occur.

    Typical usage example:
        import src.sdsi.lib.sdsi_exceptions as SDSiExceptions
        if write_result.cmd_failed():
            error = write_result.stderr.strip()
            raise SDSiExceptions.ProvisioningError(error)
"""

class InstallerError(RuntimeError):
    """Raise for errors related to the sdsi installer setup"""

class AgentSetupError(RuntimeError):
    """Raise for errors related to the SDSi Agent setup"""

class MissingCapError(RuntimeError):
    """Raise when capability activation payloads are missing from the SUT"""

class MissingLicenseKeyError(RuntimeError):
    """Raise when license keys are missing from the SUT"""

class MissingEraseKeyError(RuntimeError):
    """Raise when erase keys are missing from the SUT"""

class ProvisioningError(RuntimeError):
    """Raise when CAP provisioning fails"""

class NegativeProvisioningError(RuntimeError):
    """Raise when CAP provisioning succeeds when it should fail"""

class CapRevisionError(RuntimeError):
    """Raise when CAP provisioning fails due to incorrect revisions"""

class LicenseKeyError(RuntimeError):
    """Raise for errors related to SDSi license key"""

class EraseProvisioningError(RuntimeError):
    """Raise when erase provisioning fails"""

class InstallerReadError(RuntimeError):
    """Raise when SDSi read command fails"""

class AgentReadError(RuntimeError):
    """Raise when SDSi Agent read command fails"""

class LicenseKeyFailCountError(RuntimeError):
    """Raise when license key failure counter is invalid value"""

class CapFailCountError(RuntimeError):
    """Raise when Cap failure counter is invalid value"""

class AvailableUpdatesError(RuntimeError):
    """Raise when ssku available updates value is invalid value"""

class DeviceError(RuntimeError):
    """Raise when enumerated devices are not matching expected enumeration"""

class DriverError(RuntimeError):
    """Raise when Drivers do not behave as neccessary for test"""

class SGXError(RuntimeError):
    """Raise when SGX functionality does not behave as intended"""

class LicenseOrderError(RuntimeError):
    """Raise when license order provides failure response code."""

class LicenseInstallationError(RuntimeError):
    """Raise when license fails to install from API."""
