from dtaf_core.lib.tklib.infra.bios.bios import BIOS_KNOB_SERIAL

'''
XMLCLi Definition
Variable name must end with '_xmlcli'
Variable value is a tuple which consist of bios knob name and bios knob value
'''
enable_smx_xmlcli = ('ProcessorSmxEnable', '0x1')
disable_smx_xmlcli = ('ProcessorSmxEnable', '0x0')
enable_txt_xmlcli = ('ProcessorLtsxEnable', '0x1')
disable_txt_xmlcli = ('ProcessorLtsxEnable', '0x0')

enable_MemoryFrequency4000_xmlcli = ('DdrFreqLimit', '0x19')
enable_MemoryFrequency4400_xmlcli = ('DdrFreqLimit', '0x1C')
enable_MemoryFrequency4800_xmlcli = ('DdrFreqLimit', '0x1D')

enable_vtd_xmlcli = ('VTdSupport', '0x1')
disable_vtd_xmlcli = ('VTdSupport', '0x0')
enable_vmx_xmlcli = ("ProcessorVmxEnable", "0x1")
disable_vmx_xmlcli = ("ProcessorVmxEnable", "0x0")
enable_X2apic_xmlcli = ('ProcessorX2apic', ' 0x1')
disable_X2apic_xmlcli = ('ProcessorX2apic', ' 0x0')
disable_UmaBasedCluster_xmlcli = ('UmaBasedClustering', '0x0')
enable_UmaBasedCluster_xmlcli = ('UmaBasedClustering', '0x2')
enable_Sgx_xmlcli = ('EnableSgx', '0x1')
disable_Sgx_xmlcli = ('EnableSgx', '0x0')
disable_PatrolScrub_xmlcli = ('PatrolScrub', '0x0')
enable_PatrolScrub_xmlcli = ('PatrolScrub', '0x1')
enable__PatrolScrub_POST_xmlcli = ('PatrolScrub', '0x2')
enable_Tme_xmlcli = ('EnableTme', '0x1')
disable_Tme_xmlcli = ('EnableTme', '0x0')
knob_setting_security_common_xmlcli = (*enable_smx_xmlcli, *enable_txt_xmlcli, *enable_vtd_xmlcli)
knob_setting_virtual_common_xmlcli = (*enable_vmx_xmlcli, *enable_vtd_xmlcli)

enable_wol_support_xmlcli = ('WakeOnLanSupport', '0x1')
enable_wol_s5_xmlcli = ('WakeOnLanS5', '0x1')
enable_wol_knob_setting_xmlcli = (*enable_wol_support_xmlcli, *enable_wol_s5_xmlcli)

disable_wol_support_xmlcli = ('WakeOnLanSupport', '0x0')
disable_wol_s5_xmlcli = ('WakeOnLanS5', '0x0')
disable_wol_knob_setting_xmlcli = (*disable_wol_support_xmlcli, *disable_wol_s5_xmlcli)

disable_SpeedStep_xmlcli = ('ProcessorEistEnable', '0x0')
disable_C6Enable_xmlcli = ('C6Enable', '0x0')
disable_SpeedStep_and_C6Enable_xmlcli = (*disable_SpeedStep_xmlcli, *disable_C6Enable_xmlcli)

enable_SpeedStep_xmlcli = ('ProcessorEistEnable', '0x1')
enable_C6Enable_xmlcli = ('C6Enable', '0x1')
enable_SpeedStep_and_C6Enable_xmlcli = (*enable_SpeedStep_xmlcli, *enable_C6Enable_xmlcli)

enable_PM_Turbo_mode_xmlcli = ('TurboMode', '0x1')
disable_PM_Turbo_mode_xmlcli = ('TurboMode', '0x0')

enable_PM_CState_auto_xmlcli = ('PackageCState', '0xFF')
enable_PM_CState_C0_C1_state_xmlcli = ('PackageCState', '0x0')

enable_PM_monitor_mwait_xmlcli = ('MonitorMWait', '0x1')
disable_PM_monitor_mwait_xmlcli = ('MonitorMWait', '0x0')

enable_PM_C6_report_xmlcli = ('C6Enable', '0x1')
disable_PM_C6_report_xmlcli = ('C6Enable', '0x0')

enable_processor_HWP_out_of_band_xmlcli = ('ProcessorHWPMEnable', '0x2')
disable_processor_HWP_out_of_band_xmlcli = ('ProcessorHWPMEnable', '0x0')

enable_ISS_xmlcli = ('DynamicIss', '0x1')
disable_ISS_xmlcli = ('DynamicIss', '0x0')

disable_snc_xmlci = ('SncEn', '0x0')
enable_snc2_xmlci = ('SncEn', '0x2')
enable_snc4_xmlci = ('SncEn', '0x4')

disable_UMA_Based_clustering_xmlci = ('UmaBasedClustering', '0x0')
enable_UMA_Based_clustering_hemi_xmlci = ('UmaBasedClustering', '0x2')
enable_UMA_Based_clustering_quad_xmlci = ('UmaBasedClustering', '0x4')

enable_dfx_rank_mask_xmlcli = ('dfxRankMaskEn', '0x1')
disable_dfx_rank_mask_xmlcli = ('dfxRankMaskEn', '0x0')

disable_socket0_mc0_ch0_xmlcli = ('dfxRankMask_0', '0x0')
disable_socket0_mc0_ch1_xmlcli = ('dfxRankMask_1', '0x0')
disable_socket0_mc1_ch0_xmlcli = ('dfxRankMask_3', '0x0')
disable_socket0_mc1_ch1_xmlcli = ('dfxRankMask_4', '0x0')
disable_socket0_mc2_ch0_xmlcli = ('dfxRankMask_6', '0x0')
disable_socket0_mc2_ch1_xmlcli = ('dfxRankMask_7', '0x0')
disable_socket0_mc3_ch0_xmlcli = ('dfxRankMask_9', '0x0')
disable_socket0_mc3_ch1_xmlcli = ('dfxRankMask_10', '0x0')
disable_socket1_mc0_ch0_xmlcli = ('dfxRankMask_12', '0x0')
disable_socket1_mc0_ch1_xmlcli = ('dfxRankMask_13', '0x0')
disable_socket1_mc1_ch0_xmlcli = ('dfxRankMask_15', '0x0')
disable_socket1_mc1_ch1_xmlcli = ('dfxRankMask_16', '0x0')
disable_socket1_mc2_ch0_xmlcli = ('dfxRankMask_18', '0x0')
disable_socket1_mc2_ch1_xmlcli = ('dfxRankMask_19', '0x0')
disable_socket1_mc3_ch0_xmlcli = ('dfxRankMask_21', '0x0')
disable_socket1_mc3_ch1_xmlcli = ('dfxRankMask_22', '0x0')

enable_efi_network = ('EfiNetworkSupport', '0x1')
disable_efi_network = ('EfiNetworkSupport', '0x0')

enable_sriov_xmlcli = ('SRIOVEnable', '0x1')
disable_sriov_xmlcli = ('SRIOVEnable', '0x0')

shell_timeout_16s_xmlcli = ('ShellEntryTime', '0x10')
shell_timeout_5s_xmlcli = ('ShellEntryTime', '0x5')
shell_timeout_5s_dec_xmlcli = ('ShellEntryTime', '5')
shell_timeout_10s_xmlcli = ('ShellEntryTime', '10')

enable_wake_on_lan_support_xmlcli = ('WakeOnLanSupport', '0x1')
enable_wake_on_lan_support_dec_xmlcli = ('WakeOnLanSupport', '1')
disable_wake_on_lan_support_xmlcli = ('WakeOnLanSupport', '0x0')  # default value
disable_wake_on_lan_support_dec_xmlcli = ('WakeOnLanSupport', '0')  # default value

reset_on_mem_map_change_disable_xmlcli = ('ResetOnMemMapChange', '0x0')
reset_on_mem_map_change_disable_dec_xmlcli = ('ResetOnMemMapChange', '0')
reset_on_mem_map_change_enable_xmlcli = ('ResetOnMemMapChange', '0x1')
reset_on_mem_map_change_enable_dec_xmlcli = ('ResetOnMemMapChange', '1')

tpm_device_test_xmlcli = ('TpmDevice', '0x1')

upi_link_l0p_enable_xmlci = ("KtiLinkL0pEn", "0x1")
upi_link_l0p_disable_xmlcli = ("KtiLinkL0pEn", "0x0")

qpi_port_link_speed_template_xmlcli = r'Cpu{0}P{1}KtiLinkSpeed'
qpi_link_speed_xmlci = ("QpiLinkSpeed", "0x8F")
qpi_link_speed_mode_xmlci = ("QpiLinkSpeedMode", "0x1")
qpi_port_disable_xmlcli = r'Cpu{0}P{1}KtiPortDisable'
qpi_degrade_enable_xmlcli = ("DfxSystemDegradeMode", "0x1")
qpi_skip_topology_check_xmlcli = ("DfxSkipPorUpiTopoCheck", "0x0")

# Memory & Storage knobs
mem_freq_auto_xmlcli = ('DdrFreqLimit_inst_2', '0x0')
mem_freq_2666_xmlcli = ('DdrFreqLimit_inst_2', '0xF')
mem_freq_2933_xmlcli = ('DdrFreqLimit_inst_2', '0x11')
mem_freq_3200_xmlcli = ('DdrFreqLimit_inst_2', '0x13')
Attempt_Fast_Boot_enable_xmlcli = ("AttemptFastBoot", "0x1")
Attempt_Fast_Boot_disable_xmlcli = ("AttemptFastBoot", "0x0")
Attempt_Fast_Boot_Cold_enable_xmlcli = ("AttemptFastBootCold", "0x1")
Attempt_Fast_Boot_Cold_disable_xmlcli = ("AttemptFastBootCold", "0x0")
enable_enforce_POR_xmlcli = ('EnforcePOR', '0x0')
# Network knobs
enable_AcpiS3S4_xmlcli = ('AcpiS3Enable', '0x1', 'AcpiS4Enable', '0x1')

# virtualization by hanyufengx
enable_vmx_xmlcli = ("ProcessorVmxEnable", "0x1")
# disable_vmx_xmlcli = ("ProcessorVmxEnable", "0x0")

enable_vtd_xmlcli = ('VTdSupport', '0x1')
# disable_vtd_xmlcli = ('VTdSupport', '0x0')

# enable_sriov_xmlcli = ('SRIOVEnable', '0x1')
# disable_sriov_xmlcli = ('SRIOVEnable', '0x0')

hemisphere_umabased_xmcli = ('UmaBasedClustering', '0x2')
disable_umabased_xmcli = ('UmaBasedClustering', '0x0')

enable_tme_xmcli = ('EnableTme', '0x1')
disable_tme_xmcli = ('EnableTme', '0x0')

enable_sgx_xmcli = ('EnableSgx', '0x1')
disable_sgx_xmcli = ('EnableSgx', '0x0')

enable_Hyperv_knob_setting_xmlcli = (*enable_vmx_xmlcli, *enable_vtd_xmlcli, *enable_sriov_xmlcli)
disable_Hyperv_knob_setting_xmlcli = (*disable_vmx_xmlcli, *disable_vtd_xmlcli, *disable_sriov_xmlcli)

enable_sgx_setting_xmcli = (*enable_vmx_xmlcli, *enable_vtd_xmlcli, *disable_umabased_xmcli, *enable_tme_xmcli, *enable_sgx_xmcli)
disable_sgx_setting_xmcli = (*disable_vmx_xmlcli, *disable_vtd_xmlcli, *hemisphere_umabased_xmcli, *disable_tme_xmcli, *disable_sgx_xmcli)
'''


BIOS Serial Definition

Firstly define knob name with type of class BIOS_KNOB_SERIAL, the variable name of knob name should start with 'knob_'
e.g. 
knob_system_shell_timeout = BIOS_KNOB_SERIAL(
    name=r'System Shell Timeout',
    path=['EDKII Menu', 'Boot Options']
)

Secondly define knob serial with type of tuple, the variable name of knob serial should end with '_serial',
variable value is a tuple consist of bios knob variable defined in first step and bios knob value
e.g.
shell_timeout_5s_serial = (knob_system_shell_timeout, '5')
'''
knob_system_shell_timeout = BIOS_KNOB_SERIAL(
    name=r'System Shell Timeout',
    path=['EDKII Menu', 'Boot Options']
)
shell_timeout_5s_serial = (knob_system_shell_timeout, '5')
shell_timeout_10s_serial = (knob_system_shell_timeout, '10')

knob_wake_on_lan_support = BIOS_KNOB_SERIAL(
    name='Wake On Lan Support',
    path=['EDKII Menu', 'Platform Configuration', 'Miscellaneous Configuration']
)
wake_on_lan_support_enable_serial = (knob_wake_on_lan_support, 'Enable')
wake_on_lan_support_disable_serial = (knob_wake_on_lan_support, 'Disable')

knob_reset_on_mem_map_change = BIOS_KNOB_SERIAL(
    name='Reset Platform on Memory Map Change',
    path=['EDKII Menu', 'Platform Configuration', 'Miscellaneous Configuration']
)
reset_on_mem_map_change_enable_serial = (knob_reset_on_mem_map_change, 'X')
reset_on_mem_map_change_disable_serial = (knob_reset_on_mem_map_change, '')

knob_system_time = BIOS_KNOB_SERIAL(
    name='System Time',
    path=['EDKII Menu', 'System Information'])

knob_rtc_system_wakeup = BIOS_KNOB_SERIAL(
    name='RTC Wake system from S4/S5',
    path=['EDKII Menu', 'Platform Configuration', 'Miscellaneous Configuration'])
enable_rtc_wakeup = (knob_rtc_system_wakeup, 'Enable')
disable_rtc_wakeup_serial = (knob_rtc_system_wakeup, 'Disable')

knob_secure_boot_mode = BIOS_KNOB_SERIAL(
    name='Secure Boot Mode',
    path=['EDKII Menu', 'Secure Boot Configuration'])
secure_boot_mode_custom_serial = (knob_secure_boot_mode, 'Custom Mode')
secure_boot_mode_stand_serial = (knob_secure_boot_mode, 'Standard Mode')

knob_PCI_device_filter = BIOS_KNOB_SERIAL(
    name='PCI device filter',
    path=['EDKII Menu', 'Platform Driver Override selection'])
PCI_device_filter_enable_serial = (knob_PCI_device_filter, 'X')
PCI_device_filter_disable_serial = (knob_PCI_device_filter, '')