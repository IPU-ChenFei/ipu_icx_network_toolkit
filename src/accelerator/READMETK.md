1.On Host: 

    a.	copy all tools to host C:\BKCPkg\domains\accelerator
    .bashrc
    20.11.3.zip
    auto-poc.zip
    cpuid
    idxd-config-accel-config-v3.4.6.4.zip
    idxd_ktest-master.zip
    kernel-spr-bkc-pc-devel-6.13-0.el8.x86_64.rpm
    kernel-spr-bkc-pc-modules-internal-6.13-0.el8.x86_64.rpm
    mega.conf
    mlc_v3.9a.tgz
    msr-tools-1.3-17.el8.x86_64.rpm
    openssl-OpenSSL_1_1_1-stable.zip
    OVMF.fd
    p95v303b6.linux64.tar.gz
    pnpwls-master.zip
    PTU_V2.2.zip
    QAT_Engine-0.6.12.zip
    qat20.l.0.9.0-00023_1.zip
    qat_app_q4_21-release.zip
    qatzip.sh
    QAT_Linux_OpenSSL_Speed_Test_Script.sh
    QAT_Linux_OpenSSL_Speed_Test_Script_Asymmetric.sh
    QAT_Linux_OpenSSL_Speed_Test_Script_Symmetric.sh
    release_ver_7.5.2.zip
    sample_code.tar.gz
    socwatch_chrome_linux_INTERNAL_v2021.2_x86_64.tar.gz
    accel-random-config-and-test-main.zip
    src.zip
    stressapptest-master.zip
    mega_script.py
    ppexpect.py
    prime95.py
    sgx_sdk.py
    socwatch.py
    dlb_vmw_0.8.0.28.zip
    iadx_vmw_int_rel_bin_0.2.0.15.zip
    qat-2.1.0.29.zip
    
    b.modify tools, drivers, common configs in host C;\Autoamtion\tkconfig\ folder.
        C:\Automation\tkconfig\sut_tool\platform(egs,bhs)_sut_tool.ini
        C:\Automation\tkconfig\sut\sut.ini
        C:\Automation\tkconfig\system_configuration.ini

    c. pip install pyVmomi in host

2.On SUT: 

    a.  do SUT setup
    copy https://github.com/intel-innersource/frameworks.automation.dtaf.content.egs.dtaf-content-egs/tree/main_toolkit/src/collaterals/setup/sut/linux/os_initial_linux.sh file to SUT
    #dos2unix os_initial_linux.sh
    #sh os_initial_linux.sh 

    b.	Install old cryptography tool
    #python -m pip install --upgrade pip --proxy=http://child-prc.intel.com:913
    # python -m pip install --upgrade paramiko --proxy=http://child-prc.intel.com:913
    # pip uninstall -y cryptography # uninstall 37.0.0
    # pip install cryptography==36.0.2


    c.	For VM TCD , Download the guest image file corresponding to the current BKC version from the BKC release email, and set password: password
    Such as : “EagleStream SapphireRapids BKC Release Announcement 2022 WW21 - BKC#56”, CentOS 8 Stream 5.15 v6 and kernel version is 5.15.0-spr.bkc.pc.6.13.0.x86_64
    Guest image link:  https://ubit-artifactory-or.intel.com/artifactory/linuxmvpstacks-or-local/linux-stack-bkc/2022ww19/internal-images/spr-bkc-pc-centos-stream-8-coreserver-6.13.0.img.xz
    # dnf update --allowerasing --nobest
    # dnf install qemu-kvm -y –-allowerasing
    #mkdir -p /home/BKCPkg/domains/accelerator/imgs
    #cd /home/BKCPkg/domains/accelerator/imgs/
    #wget https://ubit-artifactory-or.intel.com/artifactory/linuxmvpstacks-or-local/linux-stack-bkc/2022ww19/internal-images/spr-bkc-pc-centos-stream-8-coreserver-6.13.0.img.xz
    #xz -d spr-bkc-pc-centos-stream-8-coreserver-6.13.0.img.xz
    #\mv spr-bkc-pc-centos-stream-8-coreserver-6.13.0.img centos.img
    #copy OVMF.fd  to /home/
    #run below command and change vm password to password with command: passwd
    
    CentOS 5.12:
    qemu-system-x86_64 -name centos_bhs_2 -accel kvm -m 20240 -smp 4 -net nic,model=virtio -nic user,hostfwd=tcp::2222-:22 -bios /home/OVMF.fd -drive file=/home/BKCPkg/domains/accelerator/imgs/centos.img,format=raw -monitor pty -cpu host -machine q35 -nographic
    CentOS 5.15:
    /usr/libexec/qemu-kvm -name centos_bhs_2 -accel kvm -m 20240 -smp 4 -net nic,model=virtio -nic user,hostfwd=tcp::2222-:22 -bios /home/OVMF.fd -drive file=/home/BKCPkg/domains/accelerator/imgs/centos.img,format=raw -monitor pty -cpu host -machine q35 -nographic
    
    #passwd: password

#\cp centos.img centos.qcow2     
