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


class RasSmmCommon(object):
    """
    This Class is Used as Common Class For all the SMM Functionality Test Cases
    """

    def __init__(self, log, csp, sdp):
        self._log = log
        self._cscripts = csp
        self._sdp = sdp

    def smm_entry(self):
        self._log.info("Halting the System ...")
        self._sdp.halt()
        self._log.info("Entering the SMM Mode")
        self._sdp.itp.cv.smmentrybreak = 1
        self._log.info("Resuming the Threads ...")
        self._sdp.go()

    def smm_entry_for_masking_ieh(self):
        self._log.info("Halting the System ...")
        self._sdp.halt()
        self._log.info("Entering the SMM Mode")
        self._sdp.itp.cv.smmentrybreak = 1
        self._sdp.itp.threads[0].port(0xb2, 1)
        self._log.info("Resuming the Threads ...")
        self._sdp.go()

    def smm_exit(self):
        self._log.info("Halting the System ...")
        self._sdp.halt()
        self._log.info("Exiting the SMM Mode")
        self._sdp.itp.cv.smmentrybreak = 0
        self._log.info("Resuming the Threads ...")
        self._sdp.go()

    def enter_smm_mode(self):
        """
        This Function is for to set the SMM Mode enable
        """
        try:
            self._log.info("Halting the System")
            self._sdp.halt()
            self._log.info("Set SMM boot parameters then enable threads")
            self._sdp.itp.cv.initbreak = 0
            self._sdp.itp.cv.shutdownbreak = 0
            self._sdp.itp.cv.machinecheckbreak = 0
            self._sdp.itp.cv.breakall = 1
            self._log.info("Entering the SMM Mode")
            self._sdp.itp.cv.smmentrybreak = 1
            self._log.info("Resuming the Threads ...")
            self._sdp.itp.threads[0].port(0xb2, 1)
            self._sdp.go()
        except Exception as ex:
            log_error = "An exception occurred:\n{}".format(str(ex))
            self._log.error(log_error)
            raise ex

    def exit_smm_mode(self):
        """
        Halt threads, remove SMM boot parameters, enable threads

        :return:
        """
        self._sdp.halt()
        self._sdp.itp.cv.breakall = 1
        self._sdp.itp.cv.smmentrybreak = 0
        self._sdp.go()
