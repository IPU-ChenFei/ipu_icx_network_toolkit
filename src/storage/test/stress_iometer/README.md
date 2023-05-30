To Generate IOMeter Configuartion File Refer Below Link

Links : "https://wiki.ith.intel.com/pages/viewpage.action?spaceKey=itecOpenStack&title=How+to+run+disk+performance+test"

- After selecting the required options in this above link.
- Click Save button and save configfile.icf locally to the required path.

Testcase : H80015-PI_Storage_StressIO_NVMe_PCH_VMD_W.

Hardware Required:
M.2 Nvme card should be connected and windows OS should be installed in M.2

Content_configuration Update:

<pcie_m_2>
        <Pcie_Device_Name>PCIe NVMe M.2</Pcie_Device_Name>
        <pcie_device_speed_in_gt_sec>8</pcie_device_speed_in_gt_sec>
        <pcie_device_width>x2</pcie_device_width>
        <bus>04</bus>
</pcie_m_2>

In above Content_configuration update bus value will differ when both Slot c and m.2 are occupied.
We need to update bus value accordingly.
