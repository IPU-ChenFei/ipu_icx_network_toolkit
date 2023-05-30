###phoenix ID: 16013537636 - U.2_NVME-Passthrough_Link_Speed_Checks_CENTOS
			   16013616262 - DV-NVME-Passthrough_Link_Speed_Checks_RHEL

Pre-requisite:
    RHEL installed.
MCIO Slot which is needed to Test.
For example if we need to test "mcio_s0_pxp4_pcieg_port0" slot and "mcio_s0_pxp4_pcieg_port1" then we should keep these slot under "select_slot" tag seprerated by comma, eg: below:
    <select_slot>mcio_s0_pxp4_pcieg_port0,mcio_s0_pxp4_pcieg_port1</select_slot>

Now fill the details of Populated slot:
<pcie_device_population>
    <SPR>
        <!-- MCIO Socket -0 -->
        <mcio_s0_pxp4_pcieg_port0>
            <Pcie_Device_Name>U.2</Pcie_Device_Name>
            <pcie_device_speed_in_gt_sec>16</pcie_device_speed_in_gt_sec>
            <pcie_device_width>x4</pcie_device_width>
        </mcio_s0_pxp4_pcieg_port0>
        <mcio_s0_pxp4_pcieg_port1>
            <Pcie_Device_Name>U.2</Pcie_Device_Name>
            <pcie_device_speed_in_gt_sec>16</pcie_device_speed_in_gt_sec>
            <pcie_device_width>x4</pcie_device_width>
        </mcio_s0_pxp4_pcieg_port1>
        <mcio_s0_pxp4_pcieg_port2>
            <Pcie_Device_Name>U.2</Pcie_Device_Name>
            <pcie_device_speed_in_gt_sec>16</pcie_device_speed_in_gt_sec>
            <pcie_device_width>x4</pcie_device_width>
        </mcio_s0_pxp4_pcieg_port2>
        <mcio_s0_pxp4_pcieg_port3>
            <Pcie_Device_Name>U.2</Pcie_Device_Name>
            <pcie_device_speed_in_gt_sec>16</pcie_device_speed_in_gt_sec>
            <pcie_device_width>x4</pcie_device_width>
        </mcio_s0_pxp4_pcieg_port3>
        <mcio_s0_pxp5_pcieg_port0>
            <Pcie_Device_Name>U.2</Pcie_Device_Name>
            <pcie_device_speed_in_gt_sec>16</pcie_device_speed_in_gt_sec>
            <pcie_device_width>x4</pcie_device_width>
        </mcio_s0_pxp5_pcieg_port0>
        <mcio_s0_pxp5_pcieg_port1>
            <Pcie_Device_Name>U.2</Pcie_Device_Name>
            <pcie_device_speed_in_gt_sec>16</pcie_device_speed_in_gt_sec>
            <pcie_device_width>x4</pcie_device_width>
        </mcio_s0_pxp5_pcieg_port1>
        <mcio_s0_pxp5_pcieg_port2>
            <Pcie_Device_Name>U.2</Pcie_Device_Name>
            <pcie_device_speed_in_gt_sec>16</pcie_device_speed_in_gt_sec>
            <pcie_device_width>x4</pcie_device_width>
        </mcio_s0_pxp5_pcieg_port2>
        <mcio_s0_pxp5_pcieg_port3>
            <Pcie_Device_Name>U.2</Pcie_Device_Name>
            <pcie_device_speed_in_gt_sec>16</pcie_device_speed_in_gt_sec>
            <pcie_device_width>x4</pcie_device_width>
        </mcio_s0_pxp5_pcieg_port3>
        <!-- MCIO Socket 1 -->
        <mcio_s1_pxp4_pcieg_port0>
            <Pcie_Device_Name>U.2</Pcie_Device_Name>
            <pcie_device_speed_in_gt_sec>16</pcie_device_speed_in_gt_sec>
            <pcie_device_width>x4</pcie_device_width>
        </mcio_s1_pxp4_pcieg_port0>
        <mcio_s1_pxp4_pcieg_port1>
            <Pcie_Device_Name>U.2</Pcie_Device_Name>
            <pcie_device_speed_in_gt_sec>16</pcie_device_speed_in_gt_sec>
            <pcie_device_width>x4</pcie_device_width>
        </mcio_s1_pxp4_pcieg_port1>
        <mcio_s1_pxp4_pcieg_port2>
            <Pcie_Device_Name>U.2</Pcie_Device_Name>
            <pcie_device_speed_in_gt_sec>16</pcie_device_speed_in_gt_sec>
            <pcie_device_width>x4</pcie_device_width>
        </mcio_s1_pxp4_pcieg_port2>
        <mcio_s1_pxp4_pcieg_port3>
            <Pcie_Device_Name>U.2</Pcie_Device_Name>
            <pcie_device_speed_in_gt_sec>16</pcie_device_speed_in_gt_sec>
            <pcie_device_width>x4</pcie_device_width>
        </mcio_s1_pxp4_pcieg_port3>
        <mcio_s1_pxp5_pcieg_port0>
            <Pcie_Device_Name>U.2</Pcie_Device_Name>
            <pcie_device_speed_in_gt_sec>16</pcie_device_speed_in_gt_sec>
            <pcie_device_width>x4</pcie_device_width>
        </mcio_s1_pxp5_pcieg_port0>
        <mcio_s1_pxp5_pcieg_port1>
            <Pcie_Device_Name>U.2</Pcie_Device_Name>
            <pcie_device_speed_in_gt_sec>16</pcie_device_speed_in_gt_sec>
            <pcie_device_width>x4</pcie_device_width>
        </mcio_s1_pxp5_pcieg_port1>
        <mcio_s1_pxp5_pcieg_port2>
            <Pcie_Device_Name>U.2</Pcie_Device_Name>
            <pcie_device_speed_in_gt_sec>16</pcie_device_speed_in_gt_sec>
            <pcie_device_width>x4</pcie_device_width>
        </mcio_s1_pxp5_pcieg_port2>
        <mcio_s1_pxp5_pcieg_port3>
            <Pcie_Device_Name>U.2</Pcie_Device_Name>
            <pcie_device_speed_in_gt_sec>16</pcie_device_speed_in_gt_sec>
            <pcie_device_width>x4</pcie_device_width>
        </mcio_s1_pxp5_pcieg_port3>
    </SPR>
</pcie_device_population>

Run the test case now.
