#import time
#from src.lib.toolkit.auto_api import *
#from sys import exit
#from src.lib.toolkit.steps_lib.prepare.boot_to import boot_to
#from src.mev.lib.mev import MEV, MEVOp
#from src.mev.lib.utility import get_bdf
from src.network.lib import *

CASE_DESC = [
    # TODO
    'case name here',
    # list the name of those cases which are expected to be executed before this case
    '<dependencies: if any>'
]


def test_steps(sut, my_os):
    # type: (SUT, GenericOS) -> None
    mev = MEV(sut)
    try:
        boot_to(sut, sut.default_os)

        MEVOp.lce_common_prepare_step(mev)

        Case.step("get pci device (LAN CPF/NVME PF/NVME CPF) info")
        _, stdout, _ = sut.execute_shell_cmd('lspci -vt | egrep "1453|1457|1458"', 30)
        Case.expect('check mev device info for 1453/1457/1458',
                    '1453' in stdout and '1457' in stdout and '1458' in stdout)

        Case.step('Uninstall the nvme drive and install  vfio-pci')
        sut.execute_shell_cmd('modprobe -r nvme', 30)
        return_code, _, _ = sut.execute_shell_cmd('modprobe vfio-pci', 30)
        Case.expect('return value is 0', return_code == 0)

        Case.step('Write LAN CPF, NVME PF, NVME CPF into the vfio-pci driver')
        sut.execute_shell_cmd('echo 8086 1453 > /sys/bus/pci/drivers/vfio-pci/new_id', 30)
        sut.execute_shell_cmd('echo 8086 1457 > /sys/bus/pci/drivers/vfio-pci/new_id', 30)
        sut.execute_shell_cmd('echo 8086 1458 > /sys/bus/pci/drivers/vfio-pci/new_id', 30)

        Case.step('Get LAN CPF is bdf')
        lan_bdf = get_bdf(sut.execute_shell_cmd, 1453, 0)
        Case.step('Get LAN CPF IOMMU group of device')
        _, iommu_group, _ = sut.execute_shell_cmd(
            f'echo $(basename $(readlink /sys/bus/pci/devices/{lan_bdf}/iommu_group))', 30)
        iommu_group = iommu_group.strip('\n')
        Case.step(r'Autoload application shall be executed with mev\_nvme\_static\_ints.conf file')
        return_code, _, _ = sut.execute_shell_cmd(
            f"/usr/bin/nvme_cpf_autoload -a {lan_bdf} -g {iommu_group} < "
            f"/usr/share/nvme-cpf/autoload/mev_nvme_static_ints.conf", 30)
        Case.expect('return value is 0', return_code == 0)

        Case.step('Create an empty sh file')
        return_code, _, _ = sut.execute_shell_cmd('touch autoload.sh', 30, cwd='/root')
        Case.expect('return value is 0', return_code == 0)

        # Step10 - Enable hugepages in the OS
        Case.step('Enable hugepages in the OS')
        sut.execute_shell_cmd('mkdir -p /dev/hugepages1G_2M', 30)
        return_code, stdout, _ = sut.execute_shell_cmd('sysctl -p', 30)
        if 'vm.nr_hugepages=2048' not in stdout and 'vm.hugetlb_shm_group=36' not in stdout:
            return_code, stdout, stderr = sut.execute_shell_cmd('echo "vm.nr_hugepages=2048" >> /etc/sysctl.conf', 30)
            Case.expect('return value is 0', return_code == 0)
            return_code, _, _ = sut.execute_shell_cmd('echo "vm.hugetlb_shm_group=36" >> /etc/sysctl.conf', 30)
            Case.expect('return value is 0', return_code == 0)
        _, stdout, _ = sut.execute_shell_cmd('cat /etc/fstab', 30)
        if "nodev /dev/hugepages1G_2M hugetlbfs pagesize=2M 0 0" not in stdout:
            return_code, stdout, stderr = sut.execute_shell_cmd(
                'echo "nodev /dev/hugepages1G_2M hugetlbfs pagesize=2M 0 0" >> /etc/fstab', 30)
            Case.expect('return value is 0', return_code == 0)
        sut.execute_shell_cmd('mount -a', 30)

        # Step11 - Create a VM with huge pages enabled
        Case.step('Create a VM with huge pages enabled')
        mev.create_vms(vm_num=1, mem_sz=2048, cpu_num=2, hugepage=True)

        Case.step('run stress test')
        vm0 = mev.vm_list[0]
        mev.pass_vf_traffic(vm0)
        nvme_bdf_pf = get_bdf(sut.execute_shell_cmd, 1457, 0)
        nvme_bdf_cpf = get_bdf(sut.execute_shell_cmd, 1458, 0)
        LCE_SAMPLES = ['dma_sample 0', 'dma_sample 1', 'dma_sample 2',
                       'dc_stateless_sample_snappy', 'dc_stateless_sample_zstd', 'cy_algchaining_sample']

        Case.step('load lce related drivers')
        mev.execute_acc_cmd('modprobe qat_lce_cpfxx', timeout=60)
        sut.execute_shell_cmd('modprobe qat_lce_common', timeout=60)
        sut.execute_shell_cmd('modprobe qat_lce_apfxx', timeout=60)

        start_time = time.time()
        while time.time() - start_time < 43200:
            Case.expect('ping to DHCP client successfully.', MEVOp.ping_to_dhcp(vm0, mode='ipv4'))
            time.sleep(10)
            return_code, stdout, stderr = sut.execute_shell_cmd(
                'export AUTOLOAD_SCRIPT=\"/root/autoload.sh\" && export MEV_NVME_DEVICE_MODE=\"HW\" && '
                f'./nvme_cpf_integration_test -l 3 --gtest_filter=it_base.it_admin_flow_polling -p {nvme_bdf_pf} -c {nvme_bdf_cpf}'
                ' | grep -i "[  PASSED  ]"', 60, cwd='/usr/libexec/')
            Case.expect('Check running value is "[  PASSED  ] 1 test."', '[  PASSED  ] 1 test.' in stdout)
            for cmd in LCE_SAMPLES:
                return_code, _, _ = sut.execute_shell_cmd(cmd, timeout=60)
                Case.expect('return value is 0', return_code == 0)
                time.sleep(10)

        Case.step("Clear autoload.sh file")
        return_code, _, _ = sut.execute_shell_cmd('rm -f autoload.sh ', 30, cwd='/root')
        Case.expect('return value is 0', return_code == 0)

    except Exception as e:
        raise e
    finally:
        MEVOp.clean_up(mev)


def clean_up(sut):
    pass


def test_main():

    # ParameterParser parses all the embed parameters
    # --help to see all allowed parameters
    user_parameters = ParameterParser.parse_embeded_parameters()
    # add your parameter parsers with list user_parameters

    # if you would like to hardcode to disable clearcmos
    # ParameterParser.bypass_clearcmos = True

    # if commandline provide sut description file by --sut <json file>
    #       generate sut instance from given json file
    #       if multiple files have been provided in command line, only the 1st will take effect for get_default_sut
    #       to get multiple sut, call function get_sut_list instead
    # otherwise
    #       default sut configure file will be loaded
    #       which is defined in basic.config.DEFAULT_SUT_CONFIG_FILE
    sut = get_default_sut()
    my_os = OperationSystem[OS.get_os_family(sut.default_os)]

    try:
        Case.start(sut, CASE_DESC)
        test_steps(sut, my_os)

    except Exception as e:
        Result.get_exception(e, str(traceback.format_exc()))
    finally:
        Case.end()
        clean_up(sut)


if __name__ == '__main__':
    test_main()
    exit(Result.returncode)
