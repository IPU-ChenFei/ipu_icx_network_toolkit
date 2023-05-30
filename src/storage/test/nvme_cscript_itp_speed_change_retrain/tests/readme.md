### G56609 - G56609 - NVMe_M.2_PCIe_CScripts_ITP_T5_Speed Change Retrain - Gen 1, 2, 3


Pre requisite:
	M.2 NVME conected.
	Linux RHEL Installed.
1. open terminal in SUT type below command:

	 lspci| grep 'Non-Volatile'
	 
2. find bus id from above command ouput bdf value
		ex: 03:00.0 Non-Volatile memory Controller
		03 is busid
3. update the bus tag with bus id in src/configuration/content_configuration.xml 
	<pcie_device_population>
            <SPR>
                <pcie_m_2>
                    <bus>03</bus>
                </pcie_m_2>
			</SPR>
	</pcie_device_population>

		
4. Run the test case now.
