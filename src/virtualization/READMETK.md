1.1 Linux VT -- Host: 

    a. Install following python modules:
	invoke-1.3.0-py3-none-any.whl
	pathlib2-2.3.7.post1-py2.py3-none-any.whl
	fabric-2.5.0-py2.py3-none-any.whl
	cryptography-3.1.1-cp36-cp36m-win_amd64.whl
    pyOpenSSL-0.15-py2.py3-none-any.whl
	pyvmomi-6.5-py2.py3-none-any.whl
	six-1.12.0-py2.py3-none-any.whl
    paramiko-2.6.0-py2.py3-none-any.whl
	dtaf_core-1.35.0-py2.py3-none-any.whl

1.2 Linux VT -- SUT: 

    a.  do SUT setup
    copy https://github.com/intel-innersource/frameworks.automation.dtaf.content.egs.dtaf-content-egs/tree/main_toolkit/src/collaterals/setup/sut/linux/os_initial_linux.sh file to SUT
    #dos2unix os_initial_linux.sh
    #sh os_initial_linux.sh 
	#dos2unix env_ini_debug.sh & sh env_ini_debug.sh
	#dos2unix env_ini_inband.sh & sh env_ini_inband.sh

    b.	python preparation
    #python -m pip install --upgrade pip --proxy=http://child-prc.intel.com:913
    #pip install paramiko-2.6.0-py2.py3-none-any.whl
	#python -m pip install scp

    c.	Install rpms
    #yum install -y qemu-kvm
    #yum install -y libvirt
    #systemctl enable libvirtd
    #systemctl start libvirtd
    #yum install -y python3-libvirt
    #yum install -y virt-install

    d.	Prepare relevant dirs/files:
	/home/BKCPkg/domains/virtualization/auto-poc                 #from \\ccr\ec\proj\DPG\PV\test_case_tool\virtualization\auto-poc
	/home/BKCPkg/domains/virtualization/imgs/                    #from \\ccr\ec\proj\DPG\PV\test_case_tool\virtualization\linux\imgs
	/home/BKCPkg/domains/virtualization/imgs/rhel0.qcow
	/home/BKCPkg/domains/virtualization/imgs/windows0.qcow
	/home/BKCPkg/domains/virtualization/imgs/cent0.img
	/home/BKCPkg/domains/virtualization/virtualization_inband    #from repo src/virtualization/lib/virtualization_inband
	/home/BKCPkg/domains/virtualization/vt_sut_linux_tools       #from repo src\virtualization\vt_sut_linux_tools

2.1 VMWare VT -- Host: 
    
    # Automated execution setup environment
    a. Install following python modules:
	invoke-1.3.0-py3-none-any.whl
	pathlib2-2.3.7.post1-py2.py3-none-any.whl
	fabric-2.5.0-py2.py3-none-any.whl
	cryptography-3.1.1-cp36-cp36m-win_amd64.whl
    	pyOpenSSL-0.15-py2.py3-none-any.whl
	pyvmomi-6.5-py2.py3-none-any.whl
	six-1.12.0-py2.py3-none-any.whl
    	paramiko-2.6.0-py2.py3-none-any.whl
	dtaf_core-1.35.0-py2.py3-none-any.whl

    b. copy all api script to host C:\frameworks.automation.dtaf.content.egs.dtaf-content-egs\src\virtualization
	ssh_basic.py
	cmd_both_run.py
	cmd_check_utils.py
	cmd_quick_run.py
	file_manager.py


2.2 VMWare VT -- SUT: 
    # Automated execution setup environment
    a.copy all api script/tools to Sut /vmfs/volumes/datastore1/
	①/vmfs/volumes/datastore1/BKCPkg/domains/vt_hls/apiscripts:
	Check_VM_Working
	Create_VM_Script
	Get_Vmip
	Modify_csockets
	Modify_csockets.zip
	Passth_device
	Reserve_GMem
	Save_all_ip
	Select_pci_bn.sh
	Vm_Power_Management
	python_api
	reboot_esxi.sh
	stressapptest-master.zip
	check_ballon.sh

	②/vmfs/volumes/datastore1/BKCPkg/domains/vt_tools:
	INT_bootbank_iads_0.10.0-1OEMINCOMPAT.800.0.0.53620472.vib
	INT_bootbank_qat_2.1.0.37-1OEMINCOMPAT.800.0.0.53620472.vib
	SPR_VT_RANDOM_CONFIG_PATH_L
	Source_Centos
	Source_Rhel
	Source_Win
	Source_WinVMware2
	VMW-esx-8.0.0-Intel-qat-2.1.0.37-1OEM.800.0.0.53620472.zip
	dlb_ext_rel_bin_0.9.3.51-7.0.2-17630552.tar.gz
	iads_ext_rel_bin_0.10.0.45-8.0.0-53620472-dvx.tar
	qat2.0_ext_rel_bin_2.1.0.37-8.0.0-53620472-dvx.zip
	intel-nvme-vmd-en_2.0.0.1146-1OEM.700.1.0.15843807_16259168-package.zip
	vmware-storcli.vib
	VMW_bootbank_net-community_1.2.7.0-1vmw.700.1.0.15843807.vib
	Ntttcp.exe
	ethr.exe

3.1 Win VT -- Host: 
    # Automated execution setup environment
    a. Install following python modules:
	invoke-1.3.0-py3-none-any.whl
	pathlib2-2.3.7.post1-py2.py3-none-any.whl
	fabric-2.5.0-py2.py3-none-any.whl
	cryptography-3.1.1-cp36-cp36m-win_amd64.whl
    	pyOpenSSL-0.15-py2.py3-none-any.whl
	pyvmomi-6.5-py2.py3-none-any.whl
	six-1.12.0-py2.py3-none-any.whl
    	paramiko-2.6.0-py2.py3-none-any.whl
	dtaf_core-1.35.0-py2.py3-none-any.whl


3.2 Win VT -- SUT: 
    a. copy all api script/tools to Sut 
	①C:\BKCPkg\domains\vt_hls\apiscripts:
	Ethr_test.ps1
	Ntttcp_test.ps1
	Open_port.ps1

	②C:\BKCPkg\domains\vt_tools:
	Ntttcp.exe
	ethr.exe
	MLNX_WinOF2-2_80_50000_All_x64.exe
	iometer-1.1.0-win64.x86_64-bin.zip
	fio-3.9-x64.msi
