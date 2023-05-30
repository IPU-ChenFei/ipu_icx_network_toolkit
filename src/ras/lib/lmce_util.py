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

import time


class LmceUtil(object):
    """
    Lmce Util class, provides below functionality

    """

    def __init__(self, os, log, sdp, csp, common_content_lib, content_config):
        self._os = os
        self._log = log
        self._sdp = sdp
        self._csp = csp
        self._common_content_lib = common_content_lib
        self._common_content_config = content_config
        self._itp_halt_time = content_config.itp_halt_time_in_sec()
        self._ei = self._csp.get_cscripts_utils().get_ei_obj()

    def is_lmce_enabled(self):
        """
            Check the following register bits to see if LMCE is set correctly
                msr 0x3a  bit20 is set
                msr 0x4d0  bit0 is set
                msr 0x179  bit27 is set

            :return: true if lmce is set correctly in registers, false otherwise
            """

        try:
            self._log.info("Halting system ...")
            self._sdp.halt()
            time.sleep(float(self._itp_halt_time))
            check1bit20 = self._sdp.msr_read(0x3a)
            bit20 = self._common_content_lib.get_bits(check1bit20, 20)
            check2bit0 = self._sdp.msr_read(0x4d0)
            bit0 = self._common_content_lib.get_bits(check2bit0, 0)
            check3bit27 = self._sdp.msr_read(0x179)
            bit27 = self._common_content_lib.get_bits(check3bit27, 27)
            time.sleep(float(self._itp_halt_time))
            if bit20 and bit0 and bit27:
                self._log.info("msr 0x3a, 0x4d0 and 0x179 have expected values")
                ret_val = True
            else:
                self._log.info("msr data= %x, %x, %x  had unexpected values", check1bit20, check2bit0, check3bit27)
                ret_val = False
        except Exception as ex:
            log_error = "An exception occurred:\n{}".format(str(ex))
            self._log.error(log_error)
            raise ex
        finally:
            self._sdp.go()
        return ret_val

    def verify_lmce_is_enabled(self):
        """
        This Method is Used to Verify Whether Lmce is Successfully Enabled or not

        :return:
        :raise: RuntimeError if Lmce is not Enabled
        """
        try:
            self._log.info("Verifying whether Lmce is Enabled or Not ...")
            result = self.is_lmce_enabled()
            if result:
                self._log.info("Lmce is Enabled as Expected ...")
            else:
                log_error = "Lmce is Not Enabled"
                self._log.error(log_error)
                raise RuntimeError(log_error)
        except Exception as ex:
            log_error = "An exception occurred:\n{}".format(str(ex))
            self._log.error(log_error)
            raise ex

        return result

    def lmce_detect(self):
        """
        This Method is Used to Verify IA32_MCG_STATUS (LMCE MSR 0x17A)

        :return:
        :raise: RuntimeError if itp command fails to execute.
        """
        try:
            ret_val = False
            self._sdp.halt()
            check1bit3 = self._sdp.msr_read(0x17A)
            bit3 = self._common_content_lib.get_bits(check1bit3, 3)
            self._log.info("Verify IA32_MCG_STATUS (LMCE MSR 0x17A) Thiis indicates to the OS that the error "
                           "logged was NOT broadcast")
            if bit3:
                ret_val = True
                self._log.info("LMCE Detected.Error logged was NOT broadcast (localized)")

        except Exception as ex:
            log_error = "An exception occurred:\n{}".format(str(ex))
            self._log.error(log_error)
            raise ex
        finally:
            self._sdp.go()
        return ret_val

    def execute_lmce(self, ac_power=None):
        """
        This Method is Used to enject the error and verify the lmce is detected or not.

        :param ac_power
        :return:
        :raise: RuntimeError if itp command fails to execute.
        """
        try:
            ret_val = False
            self._log.info("Halting the System")
            self._sdp.halt()
            time.sleep(float(self._itp_halt_time))
            self._log.info("Injecting Memory Poison Error")
            self._ei.injectMemError(0x212345000, errType="uce")
            time.sleep(15)
            if self.lmce_detect():
                self._log.info("Halting the system")
                self._sdp.halt()
                time.sleep(float(self._itp_halt_time))
                self._log.info("Making Machine break = 0")
                self._sdp.itp.cv.machinecheckbreak = 0
                time.sleep(float(self._itp_halt_time))
                self._log.info("Issuing command for reset")
                #  pulse power good is not stable on EGS. So, replacing graceful AC ON OFF
                self._common_content_lib.perform_graceful_ac_off_on(ac_power=ac_power)
                self._os.wait_for_os(self._common_content_config.get_reboot_timeout())
                ret_val = True
            else:
                self._log.error("Lmce is disable")
                ret_val = False

        except Exception as ex:
            log_error = "An exception occurred:\n{}".format(str(ex))
            self._log.error(log_error)
            raise ex
        finally:
            self._sdp.go()
        return ret_val
