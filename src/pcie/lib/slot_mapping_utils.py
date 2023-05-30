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

from src.lib.dtaf_content_constants import PcieSlotAttribute


class SlotMappingUtils:
    """
    This class is for pcie common util.
    """
    LRB = {
        PcieSlotAttribute.PCIE_SLOT_CSP_PATH:
            {
                ProductFamilies.SPR: "uncore.pi5.pxp1.pcieg{}.port0.cfg.secbus",
                ProductFamilies.EMR: "uncore.pi5.pxp1.pcieg{}.port0.cfg.secbus",
                ProductFamilies.GNR: "io0.uncore.pi5.pxp1.rp0.cfg.secbus"},
        PcieSlotAttribute.PCIE_SLOT_SOCKET: {
            ProductFamilies.SPR: 0,
            ProductFamilies.EMR: 0,
            ProductFamilies.GNR: 0
        }
    }

    LRT = {
        PcieSlotAttribute.PCIE_SLOT_CSP_PATH:
            {
                ProductFamilies.SPR: "uncore.pi5.pxp2.pcieg{}.port0.cfg.secbus",
                ProductFamilies.EMR: "uncore.pi5.pxp2.pcieg{}.port0.cfg.secbus",
                ProductFamilies.GNR: "io0.uncore.pi5.pxp2.rp0.cfg.secbus"},
        PcieSlotAttribute.PCIE_SLOT_SOCKET: {
            ProductFamilies.SPR: 0,
            ProductFamilies.EMR: 0,
            ProductFamilies.GNR: 0
        }
    }

    SLOT_B = {
        PcieSlotAttribute.PCIE_SLOT_CSP_PATH:
            {
                ProductFamilies.SPR: "uncore.pi5.pxp3.pcieg{}.port0.cfg.secbus",
                ProductFamilies.EMR: "uncore.pi5.pxp3.pcieg{}.port0.cfg.secbus",
                ProductFamilies.GNR: "io0.uncore.pi5.pxp3.rp0.cfg.secbus"},
        PcieSlotAttribute.PCIE_SLOT_SOCKET: {
            ProductFamilies.SPR: 0,
            ProductFamilies.EMR: 0,
            ProductFamilies.GNR: 0
        }
    }

    SLOT_D = {
        PcieSlotAttribute.PCIE_SLOT_CSP_PATH:
            {
                ProductFamilies.SPR: "uncore.pi5.pxp0.pcieg{}.port2.cfg.secbus",
                ProductFamilies.EMR: "uncore.pi5.pxp0.pcieg{}.port2.cfg.secbus",
                ProductFamilies.GNR: "io0.uncore.pi5.pxp0.rp0.cfg.secbus"},
        PcieSlotAttribute.PCIE_SLOT_SOCKET: {
            ProductFamilies.SPR: 1,
            ProductFamilies.EMR: 1,
            ProductFamilies.GNR: 1
        }
    }

    SLOT_E = {
        PcieSlotAttribute.PCIE_SLOT_CSP_PATH:
            {
                ProductFamilies.SPR: "uncore.pi5.pxp1.pcieg{}.port0.cfg.secbus",
                ProductFamilies.EMR: "uncore.pi5.pxp1.pcieg{}.port0.cfg.secbus",
                ProductFamilies.GNR: "io0.uncore.pi5.pxp1.rp0.cfg.secbus"},
        PcieSlotAttribute.PCIE_SLOT_SOCKET: {
            ProductFamilies.SPR: 1,
            ProductFamilies.EMR: 1,
            ProductFamilies.GNR: 1
        }
    }
    RRB = {
        PcieSlotAttribute.PCIE_SLOT_CSP_PATH:
            {
                ProductFamilies.SPR: "uncore.pi5.pxp3.pcieg{}.port0.cfg.secbus",
                ProductFamilies.EMR: "uncore.pi5.pxp3.pcieg{}.port0.cfg.secbus",
                ProductFamilies.GNR: "io0.uncore.pi5.pxp3.rp0.cfg.secbus"},
        PcieSlotAttribute.PCIE_SLOT_SOCKET: {
            ProductFamilies.SPR: 1,
            ProductFamilies.EMR: 1,
            ProductFamilies.GNR: 1
        }
    }
    RRT = {
        PcieSlotAttribute.PCIE_SLOT_CSP_PATH:
            {
                ProductFamilies.SPR: "uncore.pi5.pxp2.pcieg{}.port0.cfg.secbus",
                ProductFamilies.EMR: "uncore.pi5.pxp2.pcieg{}.port0.cfg.secbus",
                ProductFamilies.GNR: "io0.uncore.pi5.pxp2.rp0.cfg.secbus"},
        PcieSlotAttribute.PCIE_SLOT_SOCKET: {
            ProductFamilies.SPR: 1,
            ProductFamilies.EMR: 1,
            ProductFamilies.GNR: 1
        }
    }

    # PXP 4 and PXP 5
    S0_PXP4_P0 = {
        PcieSlotAttribute.PCIE_SLOT_CSP_PATH:
            {
                ProductFamilies.SPR: "uncore.pi5.pxp4.pcieg{}.port0.cfg.secbus",
                ProductFamilies.EMR: "uncore.pi5.pxp4.pcieg{}.port0.cfg.secbus",
                ProductFamilies.GNR: "io0.uncore.pi5.pxp4.rp0.cfg.secbus"},
        PcieSlotAttribute.PCIE_SLOT_SOCKET: {
            ProductFamilies.SPR: 0,
            ProductFamilies.EMR: 0,
            ProductFamilies.GNR: 0
        }
    }
    S0_PXP5_P0 = {
        PcieSlotAttribute.PCIE_SLOT_CSP_PATH:
            {
                ProductFamilies.SPR: "uncore.pi5.pxp5.pcieg{}.port0.cfg.secbus",
                ProductFamilies.EMR: "uncore.pi5.pxp5.pcieg{}.port0.cfg.secbus",
                ProductFamilies.GNR: "io0.uncore.pi5.pxp5.rp0.cfg.secbus"},
        PcieSlotAttribute.PCIE_SLOT_SOCKET: {
            ProductFamilies.SPR: 0,
            ProductFamilies.EMR: 0,
            ProductFamilies.GNR: 0
        }
    }
    S1_PXP4_P0 = {
        PcieSlotAttribute.PCIE_SLOT_CSP_PATH:
            {
                ProductFamilies.SPR: "uncore.pi5.pxp4.pcieg{}.port0.cfg.secbus",
                ProductFamilies.EMR: "uncore.pi5.pxp4.pcieg{}.port0.cfg.secbus",
                ProductFamilies.GNR: "io0.uncore.pi5.pxp4.rp0.cfg.secbus"},
        PcieSlotAttribute.PCIE_SLOT_SOCKET: {
            ProductFamilies.SPR: 1,
            ProductFamilies.EMR: 1,
            ProductFamilies.GNR: 1
        }
    }
    S1_PXP5_P0 = {
        PcieSlotAttribute.PCIE_SLOT_CSP_PATH:
            {
                ProductFamilies.SPR: "uncore.pi5.pxp5.pcieg{}.port0.cfg.secbus",
                ProductFamilies.EMR: "uncore.pi5.pxp5.pcieg{}.port0.cfg.secbus",
                ProductFamilies.GNR: "io0.uncore.pi5.pxp5.rp0.cfg.secbus"},
        PcieSlotAttribute.PCIE_SLOT_SOCKET: {
            ProductFamilies.SPR: 1,
            ProductFamilies.EMR: 1,
            ProductFamilies.GNR: 1
        }
    }

    # PXP 8, 9

    S0_PXP8_P0 = {
        PcieSlotAttribute.PCIE_SLOT_CSP_PATH:
            {
                ProductFamilies.GNR: "io1.uncore.pi5.pxp8.rp0.cfg.secbus",
            },
        PcieSlotAttribute.PCIE_SLOT_SOCKET: {
            ProductFamilies.GNR: 0
        }
    }
    S0_PXP9_P0 = {
        PcieSlotAttribute.PCIE_SLOT_CSP_PATH:
            {
                ProductFamilies.GNR: "io1.uncore.pi5.pxp9.rp0.cfg.secbus",
            },
        PcieSlotAttribute.PCIE_SLOT_SOCKET: {
            ProductFamilies.GNR: 0
        }
    }
    S1_PXP8_P0 = {
        PcieSlotAttribute.PCIE_SLOT_CSP_PATH:
            {
                ProductFamilies.GNR: "io1.uncore.pi5.pxp8.rp0.cfg.secbus",
            },
        PcieSlotAttribute.PCIE_SLOT_SOCKET: {
            ProductFamilies.GNR: 1
        }
    }
    S1_PXP9_P0 = {
        PcieSlotAttribute.PCIE_SLOT_CSP_PATH:
            {
                ProductFamilies.GNR: "io1.uncore.pi5.pxp9.rp0.cfg.secbus",
            },
        PcieSlotAttribute.PCIE_SLOT_SOCKET: {
            ProductFamilies.GNR: 1
        }
    }
    MCIO_S0_PXP4_P0 = {
        PcieSlotAttribute.PCIE_SLOT_CSP_PATH:
            {
                ProductFamilies.SPR: "uncore.pi5.pxp4.pcieg{}.port0.cfg.secbus",
                ProductFamilies.EMR: "uncore.pi5.pxp4.pcieg{}.port0.cfg.secbus",
            },
        PcieSlotAttribute.PCIE_SLOT_SOCKET: {
            ProductFamilies.SPR: 0,
            ProductFamilies.EMR: 0
        }
    }
    MCIO_S0_PXP4_P1 = {
        PcieSlotAttribute.PCIE_SLOT_CSP_PATH:
            {
                ProductFamilies.SPR: "uncore.pi5.pxp4.pcieg{}.port1.cfg.secbus",
                ProductFamilies.EMR: "uncore.pi5.pxp4.pcieg{}.port1.cfg.secbus",
            },
        PcieSlotAttribute.PCIE_SLOT_SOCKET: {
            ProductFamilies.SPR: 0,
            ProductFamilies.EMR: 0
        }
    }
    MCIO_S0_PXP4_P2 = {
        PcieSlotAttribute.PCIE_SLOT_CSP_PATH:
            {
                ProductFamilies.SPR: "uncore.pi5.pxp4.pcieg{}.port2.cfg.secbus",
                ProductFamilies.EMR: "uncore.pi5.pxp4.pcieg{}.port2.cfg.secbus",
            },
        PcieSlotAttribute.PCIE_SLOT_SOCKET: {
            ProductFamilies.SPR: 0,
            ProductFamilies.EMR: 0
        }
    }
    MCIO_S0_PXP4_P3 = {
        PcieSlotAttribute.PCIE_SLOT_CSP_PATH:
            {
                ProductFamilies.SPR: "uncore.pi5.pxp4.pcieg{}.port3.cfg.secbus",
                ProductFamilies.EMR: "uncore.pi5.pxp4.pcieg{}.port3.cfg.secbus",
            },
        PcieSlotAttribute.PCIE_SLOT_SOCKET: {
            ProductFamilies.SPR: 0,
            ProductFamilies.EMR: 0
        }
    }
    MCIO_S0_PXP5_P0 = {
        PcieSlotAttribute.PCIE_SLOT_CSP_PATH:
            {
                ProductFamilies.SPR: "uncore.pi5.pxp5.pcieg{}.port0.cfg.secbus",
                ProductFamilies.EMR: "uncore.pi5.pxp5.pcieg{}.port0.cfg.secbus",
            },
        PcieSlotAttribute.PCIE_SLOT_SOCKET: {
            ProductFamilies.SPR: 0,
            ProductFamilies.EMR: 0
        }
    }
    MCIO_S0_PXP5_P1 = {
        PcieSlotAttribute.PCIE_SLOT_CSP_PATH:
            {
                ProductFamilies.SPR: "uncore.pi5.pxp5.pcieg{}.port1.cfg.secbus",
                ProductFamilies.EMR: "uncore.pi5.pxp5.pcieg{}.port1.cfg.secbus",
            },
        PcieSlotAttribute.PCIE_SLOT_SOCKET: {
            ProductFamilies.SPR: 0,
            ProductFamilies.EMR: 0
        }
    }
    MCIO_S0_PXP5_P2 = {
        PcieSlotAttribute.PCIE_SLOT_CSP_PATH:
            {
                ProductFamilies.SPR: "uncore.pi5.pxp5.pcieg{}.port2.cfg.secbus",
                ProductFamilies.EMR: "uncore.pi5.pxp5.pcieg{}.port2.cfg.secbus",
            },
        PcieSlotAttribute.PCIE_SLOT_SOCKET: {
            ProductFamilies.SPR: 0,
            ProductFamilies.EMR: 0
        }
    }
    MCIO_S0_PXP5_P3 = {
        PcieSlotAttribute.PCIE_SLOT_CSP_PATH:
            {
                ProductFamilies.SPR: "uncore.pi5.pxp5.pcieg{}.port3.cfg.secbus",
                ProductFamilies.EMR: "uncore.pi5.pxp5.pcieg{}.port3.cfg.secbus",
            },
        PcieSlotAttribute.PCIE_SLOT_SOCKET: {
            ProductFamilies.SPR: 0,
            ProductFamilies.EMR: 0
        }
    }
    MCIO_S1_PXP4_P0 = {
        PcieSlotAttribute.PCIE_SLOT_CSP_PATH:
            {
                ProductFamilies.SPR: "uncore.pi5.pxp4.pcieg{}.port0.cfg.secbus",
                ProductFamilies.EMR: "uncore.pi5.pxp4.pcieg{}.port0.cfg.secbus",
            },
        PcieSlotAttribute.PCIE_SLOT_SOCKET: {
            ProductFamilies.SPR: 1,
            ProductFamilies.EMR: 1
        }
    }
    MCIO_S1_PXP4_P1 = {
        PcieSlotAttribute.PCIE_SLOT_CSP_PATH:
            {
                ProductFamilies.SPR: "uncore.pi5.pxp4.pcieg{}.port1.cfg.secbus",
                ProductFamilies.EMR: "uncore.pi5.pxp4.pcieg{}.port1.cfg.secbus",
            },
        PcieSlotAttribute.PCIE_SLOT_SOCKET: {
            ProductFamilies.SPR: 1,
            ProductFamilies.EMR: 1
        }
    }
    MCIO_S1_PXP4_P2 = {
        PcieSlotAttribute.PCIE_SLOT_CSP_PATH:
            {
                ProductFamilies.SPR: "uncore.pi5.pxp4.pcieg{}.port2.cfg.secbus",
                ProductFamilies.EMR: "uncore.pi5.pxp4.pcieg{}.port2.cfg.secbus",
            },
        PcieSlotAttribute.PCIE_SLOT_SOCKET: {
            ProductFamilies.SPR: 1,
            ProductFamilies.EMR: 1
        }
    }
    MCIO_S1_PXP4_P3 = {
        PcieSlotAttribute.PCIE_SLOT_CSP_PATH:
            {
                ProductFamilies.SPR: "uncore.pi5.pxp4.pcieg{}.port3.cfg.secbus",
                ProductFamilies.EMR: "uncore.pi5.pxp4.pcieg{}.port3.cfg.secbus",
            },
        PcieSlotAttribute.PCIE_SLOT_SOCKET: {
            ProductFamilies.SPR: 1,
            ProductFamilies.EMR: 1
        }
    }
    MCIO_S1_PXP5_P0 = {
        PcieSlotAttribute.PCIE_SLOT_CSP_PATH:
            {
                ProductFamilies.SPR: "uncore.pi5.pxp5.pcieg{}.port0.cfg.secbus",
                ProductFamilies.EMR: "uncore.pi5.pxp5.pcieg{}.port0.cfg.secbus",
            },
        PcieSlotAttribute.PCIE_SLOT_SOCKET: {
            ProductFamilies.SPR: 1,
            ProductFamilies.EMR: 1
        }
    }
    MCIO_S1_PXP5_P1 = {
        PcieSlotAttribute.PCIE_SLOT_CSP_PATH:
            {
                ProductFamilies.SPR: "uncore.pi5.pxp5.pcieg{}.port1.cfg.secbus",
                ProductFamilies.EMR: "uncore.pi5.pxp5.pcieg{}.port1.cfg.secbus",
            },
        PcieSlotAttribute.PCIE_SLOT_SOCKET: {
            ProductFamilies.SPR: 1,
            ProductFamilies.EMR: 1
        }
    }
    MCIO_S1_PXP5_P2 = {
        PcieSlotAttribute.PCIE_SLOT_CSP_PATH:
            {
                ProductFamilies.SPR: "uncore.pi5.pxp5.pcieg{}.port2.cfg.secbus",
                ProductFamilies.EMR: "uncore.pi5.pxp5.pcieg{}.port2.cfg.secbus",
            },
        PcieSlotAttribute.PCIE_SLOT_SOCKET: {
            ProductFamilies.SPR: 1,
            ProductFamilies.EMR: 1
        }
    }
    MCIO_S1_PXP5_P3 = {
        PcieSlotAttribute.PCIE_SLOT_CSP_PATH:
            {
                ProductFamilies.SPR: "uncore.pi5.pxp5.pcieg{}.port3.cfg.secbus",
                ProductFamilies.EMR: "uncore.pi5.pxp5.pcieg{}.port3.cfg.secbus",
            },
        PcieSlotAttribute.PCIE_SLOT_SOCKET: {
            ProductFamilies.SPR: 1,
            ProductFamilies.EMR: 1
        }
    }
    SLOT_E_BIFURCATION_P0 = {
        PcieSlotAttribute.PCIE_SLOT_CSP_PATH:
            {
                ProductFamilies.SPR: "uncore.pi5.pxp1.pcieg{}.port0.cfg.secbus",
                ProductFamilies.EMR: "uncore.pi5.pxp1.pcieg{}.port0.cfg.secbus",
            },
        PcieSlotAttribute.PCIE_SLOT_SOCKET: {
            ProductFamilies.SPR: 1,
            ProductFamilies.EMR: 1
        }
    }
    SLOT_E_BIFURCATION_P1 = {
        PcieSlotAttribute.PCIE_SLOT_CSP_PATH:
            {
                ProductFamilies.SPR: "uncore.pi5.pxp1.pcieg{}.port1.cfg.secbus",
                ProductFamilies.EMR: "uncore.pi5.pxp1.pcieg{}.port1.cfg.secbus",
            },
        PcieSlotAttribute.PCIE_SLOT_SOCKET: {
            ProductFamilies.SPR: 1,
            ProductFamilies.EMR: 1
        }
    }
    SLOT_E_BIFURCATION_P2 = {
        PcieSlotAttribute.PCIE_SLOT_CSP_PATH:
            {
                ProductFamilies.SPR: "uncore.pi5.pxp1.pcieg{}.port2.cfg.secbus",
                ProductFamilies.EMR: "uncore.pi5.pxp1.pcieg{}.port2.cfg.secbus",
            },
        PcieSlotAttribute.PCIE_SLOT_SOCKET: {
            ProductFamilies.SPR: 1,
            ProductFamilies.EMR: 1
        }
    }
    SLOT_E_BIFURCATION_P3 = {
        PcieSlotAttribute.PCIE_SLOT_CSP_PATH:
            {
                ProductFamilies.SPR: "uncore.pi5.pxp1.pcieg{}.port3.cfg.secbus",
                ProductFamilies.EMR: "uncore.pi5.pxp1.pcieg{}.port3.cfg.secbus",
            },
        PcieSlotAttribute.PCIE_SLOT_SOCKET: {
            ProductFamilies.SPR: 1,
            ProductFamilies.EMR: 1
        }
    }
    SLOT_B_BIFURCATION_P0 = {
        PcieSlotAttribute.PCIE_SLOT_CSP_PATH:
            {
                ProductFamilies.SPR: "uncore.pi5.pxp3.pcieg{}.port0.cfg.secbus",
                ProductFamilies.EMR: "uncore.pi5.pxp3.pcieg{}.port0.cfg.secbus",
            },
        PcieSlotAttribute.PCIE_SLOT_SOCKET: {
            ProductFamilies.SPR: 0,
            ProductFamilies.EMR: 0
        }
    }
    SLOT_B_BIFURCATION_P1 = {
        PcieSlotAttribute.PCIE_SLOT_CSP_PATH:
            {
                ProductFamilies.SPR: "uncore.pi5.pxp3.pcieg{}.port1.cfg.secbus",
                ProductFamilies.EMR: "uncore.pi5.pxp3.pcieg{}.port1.cfg.secbus",
            },
        PcieSlotAttribute.PCIE_SLOT_SOCKET: {
            ProductFamilies.SPR: 0,
            ProductFamilies.EMR: 0
        }
    }
    SLOT_B_BIFURCATION_P2 = {
        PcieSlotAttribute.PCIE_SLOT_CSP_PATH:
            {
                ProductFamilies.SPR: "uncore.pi5.pxp3.pcieg{}.port2.cfg.secbus",
                ProductFamilies.EMR: "uncore.pi5.pxp3.pcieg{}.port2.cfg.secbus",
            },
        PcieSlotAttribute.PCIE_SLOT_SOCKET: {
            ProductFamilies.SPR: 0,
            ProductFamilies.EMR: 0
        }
    }
    SLOT_B_BIFURCATION_P3 = {
        PcieSlotAttribute.PCIE_SLOT_CSP_PATH:
            {
                ProductFamilies.SPR: "uncore.pi5.pxp3.pcieg{}.port3.cfg.secbus",
                ProductFamilies.EMR: "uncore.pi5.pxp3.pcieg{}.port3.cfg.secbus",
            },
        PcieSlotAttribute.PCIE_SLOT_SOCKET: {
            ProductFamilies.SPR: 0,
            ProductFamilies.EMR: 0
        }
    }
    PCIE_SLOT_MAPPING_WITH_BUS = {
        PcieSlotAttribute.LEFT_RISER_BOTTOM: LRB,
        PcieSlotAttribute.LEFT_RISER_TOP: LRT,
        PcieSlotAttribute.SLOT_B: SLOT_B,
        PcieSlotAttribute.SLOT_D: SLOT_D,
        PcieSlotAttribute.SLOT_E: SLOT_E,
        PcieSlotAttribute.RIGHT_RISER_BOTTOM: RRB,
        PcieSlotAttribute.RIGHT_RISER_TOP: RRT,
        PcieSlotAttribute.S0_PXP4_P0: S0_PXP4_P0,
        PcieSlotAttribute.S0_PXP5_P0: S0_PXP5_P0,
        PcieSlotAttribute.S1_PXP4_P0: S1_PXP4_P0,
        PcieSlotAttribute.S1_PXP5_P0: S1_PXP5_P0,
        PcieSlotAttribute.S1_PXP9_P0: S1_PXP9_P0,

        PcieSlotAttribute.MCIO_S0_PXP4_P0: MCIO_S0_PXP4_P0,
        PcieSlotAttribute.MCIO_S0_PXP4_P1: MCIO_S0_PXP4_P1,
        PcieSlotAttribute.MCIO_S0_PXP4_P2: MCIO_S0_PXP4_P2,
        PcieSlotAttribute.MCIO_S0_PXP4_P3: MCIO_S0_PXP4_P3,
        PcieSlotAttribute.MCIO_S0_PXP5_P0: MCIO_S0_PXP5_P0,
        PcieSlotAttribute.MCIO_S0_PXP5_P1: MCIO_S0_PXP5_P1,
        PcieSlotAttribute.MCIO_S0_PXP5_P2: MCIO_S0_PXP5_P2,
        PcieSlotAttribute.MCIO_S0_PXP5_P3: MCIO_S0_PXP5_P3,
        PcieSlotAttribute.MCIO_S1_PXP4_P0: MCIO_S1_PXP4_P0,
        PcieSlotAttribute.MCIO_S1_PXP4_P1: MCIO_S1_PXP4_P1,
        PcieSlotAttribute.MCIO_S1_PXP4_P2: MCIO_S1_PXP4_P2,
        PcieSlotAttribute.MCIO_S1_PXP4_P3: MCIO_S0_PXP4_P3,
        PcieSlotAttribute.MCIO_S1_PXP5_P0: MCIO_S1_PXP5_P0,
        PcieSlotAttribute.MCIO_S1_PXP5_P1: MCIO_S1_PXP5_P1,
        PcieSlotAttribute.MCIO_S1_PXP5_P2: MCIO_S1_PXP5_P2,
        PcieSlotAttribute.MCIO_S1_PXP5_P3: MCIO_S1_PXP5_P3,

        PcieSlotAttribute.SLOT_E_BIFURCATION_P0: SLOT_E_BIFURCATION_P0,
        PcieSlotAttribute.SLOT_E_BIFURCATION_P1: SLOT_E_BIFURCATION_P1,
        PcieSlotAttribute.SLOT_E_BIFURCATION_P2: SLOT_E_BIFURCATION_P2,
        PcieSlotAttribute.SLOT_E_BIFURCATION_P3: SLOT_E_BIFURCATION_P3,
        PcieSlotAttribute.SLOT_B_BIFURCATION_P3: SLOT_B_BIFURCATION_P3,
        PcieSlotAttribute.SLOT_B_BIFURCATION_P2: SLOT_B_BIFURCATION_P2,
        PcieSlotAttribute.SLOT_B_BIFURCATION_P1: SLOT_B_BIFURCATION_P1,
        PcieSlotAttribute.SLOT_B_BIFURCATION_P0: SLOT_B_BIFURCATION_P0
    }

    def __init__(self, log, os, cfg_opts):
        self._log = log
        self._os = os
        self._cfg = cfg_opts

    @staticmethod
    def get_slot_bus_mappping_dict():
        """
        This method is to
        """
        return SlotMappingUtils.PCIE_SLOT_MAPPING_WITH_BUS
