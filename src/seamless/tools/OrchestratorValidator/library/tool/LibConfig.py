#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
INTEL CONFIDENTIAL
Copyright 2017-2020 Intel Corporation.
This software and the related documents are Intel copyrighted materials, and
your use of them is governed by the express license under which they were
provided to you (License).Unless the License provides otherwise, you may not
use, modify, copy, publish, distribute, disclose or transmit this software or
the related documents without Intel's prior written permission.

This software and the related documents are provided as is, with no express or
implied warranties, other than those that are expressly stated in the License.
"""

from enum import Enum


class LibConfig:
    class ToolType(Enum):
        Unknown = None
        Ibst = 'IBST'
        Fit = 'FIT'

    configurationTag = 'configuration'
    settingsTag = None
    layoutTag = "layout"
    decompositionTag = "decomposition"
    overridesTag = None
    defaultPaddingValue = None
    rootTag = None
    runFrom = None
    maxBufferSize = None
    pathSeparator = "/"
    schemaPath = None
    appDir = None
    isGui = False
    isDecompose = False
    isFullDecomposition = False
    isVerbose = False
    enableRegions = 'enable_regions'
    exitCode = 0
    allowEmptyConfiguration = False
    isOrchestrator = False
    isAccessCheckSkipped = False
    isDirAclSet = False
    saveLog = False
    generateOutput: bool = None
    '''
    generateOutput - if it's None then we use default behaviour. Setting True / False is a way of communication that
    some part of the tool explicitly says that output is not needed or that it is needed.
    (e.g. ImportManifestFunction / VerifyManifestFunction)
    '''
    skipSchemaValidation = False
    toolType: ToolType = ToolType.Unknown
    legacyMap = False
