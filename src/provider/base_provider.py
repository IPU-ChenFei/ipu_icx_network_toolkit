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
from abc import ABCMeta, abstractmethod


@six.add_metaclass(ABCMeta)
class BaseProvider(object):
    """
    Abstract base class for Providers, classes that provide abstractions for external resources.
    """

    def __init__(self, log, cfg_opts, os_obj):
        """
        Create a new provider object.

        :param log: logging.Logger object to use to store debug output from this Provider.
        :param cfg_opts: Dictionary of configuration options provided by the ConfigFileParser.
        """
        self._log = log
        self._cfg = cfg_opts
        self._os = os_obj

    def __enter__(self):
        """
        Enter resource context for this provider.

        :return: Resource to use (usually self)
        """
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Exit resource context for this provider.

        :param exc_type: Exception type
        :param exc_val: Exception value
        :param exc_tb: Exception traceback
        :return: None
        """
        pass  # Note: DO NOT return a "True" value if you override this function. Otherwise, exceptions will be hidden!

    @staticmethod
    @abstractmethod
    def factory(log, cfg_opts, os_obj):
        """
        Return an instance of the provider based on the platform and configuration parameters.

        :param log: logging.Logger object to use for debug output
        :param cfg_opts: Dictionary of configuration options provided by the ConfigFileParser.
        :param os_obj: os object
        :return: Instance of this Provider object, which the test case can use.
        """
        raise NotImplementedError("All subclasses should override factory!")

