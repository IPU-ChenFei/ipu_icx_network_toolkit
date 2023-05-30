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


class AdddcUtil(object):
    """
    AdddcUtil Util class, provides below functionality
    1. Check adddc enabled
    """

    def __init__(self, log, csp, sdp, common_content_lib):
        self._log = log
        self._csp = csp
        self._sdp = sdp
        self._common_content_lib = common_content_lib
        self._product = self._csp.silicon_cpu_family

    def is_adddc_enabled(self, socket=None, mc=None):
        """
        Returns True if ADDDC is enabled.  False otherwise.

        :param socket  Socket object or integer
        :param mc:  Memory controller integer or None for all populated
        :param ch:  Channel integer or None for all populated
        :param log:  Logger object
        """
        adddc_enabled = False

        try:
            self._sdp.halt()
            self._log.info("Getting mc list from xnmMemicalsUtils object from CScripts...")
            mu_obj = self._csp.get_xnm_memicals_utils_object()
            if self._product in self._common_content_lib.SILICON_14NM_FAMILY:
                pop_ch_list = mu_obj.getPopChList(socket=socket, mc=mc)
            else:
                pop_ch_list = mu_obj.get_pop_ch_list(socket=socket, mc=mc)

            sys_burst_length = None
            # In order to be a little more robust, pass ddrt == true,
            # then deal with it within the loop
            for pop_ch in pop_ch_list:
                self._log.debug("Iterating through channel list and checking the burst length and if burst length "
                                "is 1 then ADDDC is enabled")
                # TODO: move this ddr and ddr5 definitions to DTAF_Core
                if not any(x in pop_ch.dimm_dict for x in ["ddr4", "ddr5"]):
                    continue

                # MR0 A0:A1 Burst Length
                burst_length = pop_ch.regs.tcmr2shadow.scratch.read() & 0x3
                if burst_length == 1:
                    adddc_enabled = True
                # Checking ADDDC is enabled or not
                if sys_burst_length is None:
                    sys_burst_length = burst_length
                elif sys_burst_length != burst_length:
                    self._log.error("ADDDC enabled inconsistently across multiple channels! "
                                    "Cannot give a boolean result!")
                    raise RuntimeError("ADDDC enable set inconsistently across multiple channels! "
                                       "Cannot give a boolean result!")

                self._log.debug(" ADDDC_enabled: %s" % adddc_enabled)
        except Exception as ex:
            log_error = "Exception occurred while checking adddc is enabled: '{}'".format(ex)
            self._log.error(log_error)
            raise ex
        finally:
            self._sdp.go()

        return adddc_enabled
