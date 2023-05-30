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

from importlib import import_module
from abc import ABCMeta
from six import add_metaclass

from dtaf_core.lib.dtaf_constants import OperatingSystems

from src.provider.base_provider import BaseProvider
from src.lib.common_content_lib import CommonContentLib
from src.lib.content_configuration import ContentConfiguration


@add_metaclass(ABCMeta)
class MSRReaderProvider(BaseProvider):
    """Provides MSR Reader information"""

    def __init__(self, log, cfg_opts, os_obj, sdp=None):
        """
        Create a new MSR Provider object.

        :param log: Logger object to use for output messages
        :param cfg_opts: xml.etree.ElementTree.Element of configuration
        options for execution environment
        :param os_obj: os object
        :param sdp: SiliconDebugProvider
        """
        super(MSRReaderProvider, self).__init__(log, cfg_opts, os_obj)
        self._log = log
        self._cfg_opts = cfg_opts
        self._os = os_obj
        self._sut_os = self._os.os_type
        self._common_content_lib = CommonContentLib(log, os_obj, cfg_opts)
        self._common_content_configuration = ContentConfiguration(self._log)
        self.execution_timeout = self._common_content_configuration.get_command_timeout()
        if sdp:
            self.sdp = sdp

    @staticmethod
    def factory(log, cfg_opts, os_obj, sdp=None):
        """
        To create a factory object based on the configuration xml file.

        :return: object
        """

        package = r"src.provider.msr_reader_provider"
        if sdp:
            mod_name = "ITPProvider"
        else:
            if OperatingSystems.WINDOWS == os_obj.os_type:
                mod_name = "WindowsMSRProvider"
            elif OperatingSystems.LINUX == os_obj.os_type:
                mod_name = "LinuxMSRProvider"
            else:
                raise NotImplementedError("Test is not implemented for %s" % os_obj.os_type)
        mod = import_module(package, mod_name)
        aclass = getattr(mod, mod_name)
        return aclass(log, cfg_opts, os_obj, sdp)


class ITPProvider(MSRReaderProvider):

    def __init__(self, log, cfg_opts, os_obj, sdp):
        """
        Create a new Windows ITP Provider object.

        :param log: Logger object to use for output messages
        :param cfg_opts: xml.etree.ElementTree.Element of configuration
        :param os_obj: os object
        :param sdp: SiliconDebugProvider
        """
        super(ITPProvider, self).__init__(log, cfg_opts, os_obj, sdp)

    def get_msr_value(self, msr_cmd_value):
        """This method get msr value"""
        msr_value = ""
        try:
            self._log.debug("Halt CPU devices")
            self.sdp.halt()
            msr_value = hex(self.sdp.msr_read(msr_cmd_value, squash=True))
        except Exception as e:
            self._log.error("Unknown exception while verifying SGX")
        finally:
            self.sdp.go()

        self._log.info("Actual MSR value :%s", msr_value)

        return msr_value


class WindowsMSRProvider(MSRReaderProvider):
    """Windows MSR provider"""

    def __init__(self, log, cfg_opts, os_obj, sdp):
        """
        Create a new Windows SGX Provider object.

        :param log: Logger object to use for output messages
        :param cfg_opts: xml.etree.ElementTree.Element of configuration
        :param os_obj: os object
        :param sdp: SiliconDebugProvider
        """
        super(WindowsMSRProvider, self).__init__(log, cfg_opts, os_obj, sdp)

    def get_msr_value(self):
        """This method get msr value"""
        raise NotImplementedError

class LinuxMSRProvider(MSRReaderProvider):
    """Linux MSR provider object"""

    def __init__(self, log, cfg_opts, os_obj, sdp):
        super(LinuxMSRProvider, self).__init__(log, cfg_opts, os_obj, sdp)

    def get_msr_value(self):
        """This method get msr value"""
        raise NotImplementedError
