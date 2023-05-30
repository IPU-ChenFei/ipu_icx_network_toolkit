
For TC ID: G44055-EGS_PV_184 - M-2-SATA-Stability and Stress- FIO
		16013670882 - M2 NVME-Stability and Stress- FIO(CENTOS)
		16013670865 - M2 VME-Stability and Stress- FIO(RHEL)

 1. connect M.2 SATA/ M.2 NVME Device
 2. execute the command lsscsi in SUT and find the Drive that is connected 
	ex: dev/sda, /dev/sdb, /dev/sdc, /dev/sdd,  /dev/nvme0n1
 3. Update the file_name tag to update drive name in content configuration file
		ex: /dev/sdd /dev/nvme0n1
	<fio>
		<!-- FIO app test tool configuration -->
		<fio_runtime>600</fio_runtime> <!-- give time in seconds -->
		<!-- Give any one required operation among these read, write, randread, randwrite -->
		<read_write_operation>read</read_write_operation>
		<!-- Give ssd details in below format : seperated. Ignore OS SSD -->
		<file_name> /dev/sdd</file_name>
		<!-- Give expected bandwidth value -->
		<expected_bandwidth>0</expected_bandwidth>
	</fio>
 4. Run the test case now.
