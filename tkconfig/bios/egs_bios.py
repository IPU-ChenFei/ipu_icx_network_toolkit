#!/usr/bin/env python
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
enable_X2apic_xmlcli = ('ProcessorX2apic', '0x1')
disable_X2apic_xmlcli = ('ProcessorX2apic', '0x0')
enable_acpi_xmlcli = ('ProcessorX2apic', '0x1')
disable_acpi_xmlcli = ('ProcessorX2apic', '0x0')
# enable_sriov_xmlcli = ('SRIOVEnable', '0x1')
# disable_sriov_xmlcli = ('SRIOVEnable', '0x0')

enable_wol_support_xmlcli = ('WakeOnLanSupport', '0x1')
enable_wol_s5_xmlcli = ('WakeOnLanS5', '0x1')
enable_wol_knob_setting_xmlcli = (*enable_wol_support_xmlcli, *enable_wol_s5_xmlcli)

disable_wol_support_xmlcli = ('WakeOnLanSupport', '0x0')
disable_wol_s5_xmlcli = ('WakeOnLanS5', '0x0')
disable_wol_knob_setting_xmlcli = (*disable_wol_support_xmlcli, *disable_wol_s5_xmlcli)

disable_SpeedStep_xmlcli = ('ProcessorEistEnable', '0x0')
disable_C6Enable_xmlcli = ('C6Enable', '0x0')
disable_SpeedStep_xmlcli = (*disable_SpeedStep_xmlcli, *disable_C6Enable_xmlcli)
disable_SpeedStep_and_C6Enable_xmlcli = (*disable_SpeedStep_xmlcli, *disable_C6Enable_xmlcli)

enable_SpeedStep_xmlcli = ('ProcessorEistEnable', '0x1')
enable_C6Enable_xmlcli = ('C6Enable', '0x1')
enable_SpeedStep_xmlcli = (*enable_SpeedStep_xmlcli, *enable_C6Enable_xmlcli)
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

enable_cfr_s3m_xmlcli = ("CFRS3mProvision", "0x1")
enable_cfr_pucode_xmlcli = ("CFRPucodeProvision", "0x1")
enable_Interrupt_Remapping_xmcli = ('InterruptRemap', '0x1')
enable_PCIeENQCMDENQCMDS_xmcli = ('PcieEnqCmdSupport', '0x1')

enable_vmx_xmlcli = ('ProcessorVmxEnable', '0x1')
disable_vmx_xmlcli = ("ProcessorVmxEnable", "0x0")

enable_tme_xmcli = ('EnableTme', '0x1')
disable_tme_xmcli = ('EnableTme', '0x0')

enable_sgx_xmcli = ("EnableSgx", "0x1")
disable_sgx_xmcli = ("EnableSgx", "0x0")

hemisphere_umabased_xmcli = ('UmaBasedClustering', '0x2')
disable_umabased_xmcli = ('UmaBasedClustering', '0x0')

knob_setting_sriov_common_xmlcli = (*enable_X2apic_xmlcli, *enable_vtd_xmlcli, *enable_sriov_xmlcli)
knob_setting_dsa_commom_xmlcli = (*enable_X2apic_xmlcli, *enable_vtd_xmlcli, *enable_Interrupt_Remapping_xmcli, *enable_PCIeENQCMDENQCMDS_xmcli, *enable_vmx_xmlcli)
knob_setting_virtual_common_xmlcli = (*enable_vmx_xmlcli, *enable_vtd_xmlcli)
knob_setting_security_common_xmlcli = (*enable_smx_xmlcli, *enable_txt_xmlcli, *enable_X2apic_xmlcli, *enable_vtd_xmlcli)
enable_sgx_setting_xmlcli = (*enable_vmx_xmlcli, *enable_X2apic_xmlcli, *enable_vtd_xmlcli, *disable_umabased_xmcli, *enable_tme_xmcli, *enable_sgx_xmcli)
disable_sgx_setting_xmlcli = (*disable_sgx_xmcli,*disable_tme_xmcli,*hemisphere_umabased_xmcli)

enable_vmx_xmcli = ('ProcessorVmxEnable', '0x1')
enable_Iax0_xmcli = ("IaxEn_0", '0x1')
enable_Hqm0_xmcli = ("HqmEn_0", '0x1')
enable_Hqm1_xmcli = ("HqmEn_1", '0x1')
enable_Hqm2_xmcli = ("HqmEn_2", '0x1')
enable_Hqm3_xmcli = ("HqmEn_3", '0x1')
enable_Hqm4_xmcli = ("HqmEn_4", '0x1')
enable_Hqm5_xmcli = ("HqmEn_5", '0x1')
enable_Hqm6_xmcli = ("HqmEn_6", '0x1')
enable_Hqm7_xmcli = ("HqmEn_7", '0x1')
disable_Hqm0_xmcli = ("HqmEn_0", '0x0')
disable_Hqm1_xmcli = ("HqmEn_1", '0x0')
disable_Hqm2_xmcli = ("HqmEn_2", '0x0')
disable_Hqm3_xmcli = ("HqmEn_3", '0x0')
disable_Hqm4_xmcli = ("HqmEn_4", '0x0')
disable_Hqm5_xmcli = ("HqmEn_5", '0x0')
disable_Hqm6_xmcli = ("HqmEn_6", '0x0')
disable_Hqm7_xmcli = ("HqmEn_7", '0x0')

knob_setting_hqm_enable_common_xmlcli = (*enable_Hqm0_xmcli, *enable_Hqm1_xmcli, *enable_Hqm2_xmcli, *enable_Hqm3_xmcli, *enable_Hqm4_xmcli, *enable_Hqm5_xmcli, *enable_Hqm6_xmcli, *enable_Hqm7_xmcli)
knob_setting_hqm_disable_common_xmlcli = (*disable_Hqm0_xmcli, *disable_Hqm1_xmcli, *disable_Hqm2_xmcli, *disable_Hqm3_xmcli, *disable_Hqm4_xmcli, *disable_Hqm5_xmcli, *disable_Hqm6_xmcli, *disable_Hqm7_xmcli)
knob_setting_hqm_disablecpu1_common_xmlcli = (*enable_Hqm0_xmcli, *enable_Hqm1_xmcli, *enable_Hqm2_xmcli, *enable_Hqm3_xmcli, *disable_Hqm4_xmcli, *disable_Hqm5_xmcli, *disable_Hqm6_xmcli, *disable_Hqm7_xmcli)
knob_setting_hqm_disablecpu0_common_xmlcli = (*disable_Hqm0_xmcli, *disable_Hqm1_xmcli, *disable_Hqm2_xmcli, *disable_Hqm3_xmcli, *enable_Hqm4_xmcli, *enable_Hqm5_xmcli, *enable_Hqm6_xmcli, *enable_Hqm7_xmcli)
# knob_setting_sriov_common_xmlcli = (*enable_vtd_xmlcli, *enable_sriov_xmlcli)
# knob_setting_dsa_commom_xmlcli = (*enable_vtd_xmlcli, *enable_Interrupt_Remapping_xmcli, *enable_PCIeENQCMDENQCMDS_xmcli, *enable_vmx_xmcli)
knob_setting_iax_dmatest_common_xmlcli = (*enable_PCIeENQCMDENQCMDS_xmcli, *enable_Iax0_xmcli, *enable_X2apic_xmlcli, *enable_vtd_xmlcli, *enable_vmx_xmcli, *enable_cfr_s3m_xmlcli, *enable_cfr_pucode_xmlcli)

enable_cfr_s3m_xmlcli = ("CFRS3mProvision", "0x1")
enable_cfr_pucode_xmlcli = ("CFRPucodeProvision", "0x1")
enable_Interrupt_Remapping_xmcli = ('InterruptRemap', '0x1')
enable_PCIeENQCMDENQCMDS_xmcli = ('PcieEnqCmdSupport', '0x1')
enable_vmx_xmcli = ('ProcessorVmxEnable', '0x1')
enable_Iax0_xmcli = ("IaxEn_0", '0x1')
enable_Dsa0_xmcli = ("DsaEn_0", '0x1')
enable_cpm0_xmcli = ("CpmEn_0", '0x1')
enable_cpm1_xmcli = ("CpmEn_1", '0x1')
enable_cpm2_xmcli = ("CpmEn_2", '0x1')
enable_cpm3_xmcli = ("CpmEn_3", '0x1')
enable_cpm4_xmcli = ("CpmEn_4", '0x1')
enable_cpm5_xmcli = ("CpmEn_5", '0x1')
enable_cpm6_xmcli = ("CpmEn_6", '0x1')
enable_cpm7_xmcli = ("CpmEn_7", '0x1')
disable_cpm0_xmcli = ("CpmEn_0", '0x0')
disable_cpm1_xmcli = ("CpmEn_1", '0x0')
disable_cpm2_xmcli = ("CpmEn_2", '0x0')
disable_cpm3_xmcli = ("CpmEn_3", '0x0')
disable_cpm4_xmcli = ("CpmEn_4", '0x0')
disable_cpm5_xmcli = ("CpmEn_5", '0x0')
disable_cpm6_xmcli = ("CpmEn_6", '0x0')
disable_cpm7_xmcli = ("CpmEn_7", '0x0')

knob_setting_hqm_disable0 = (disable_Hqm0_xmcli)
knob_setting_hqm_disable1 = (*enable_Hqm0_xmcli, *disable_Hqm1_xmcli)
knob_setting_hqm_disable2 = (*enable_Hqm1_xmcli, *disable_Hqm2_xmcli)
knob_setting_hqm_disable3 = (*enable_Hqm2_xmcli, *disable_Hqm3_xmcli)
knob_setting_hqm_disable4 = (*enable_Hqm3_xmcli, *disable_Hqm4_xmcli)
knob_setting_hqm_disable5 = (*enable_Hqm4_xmcli, *disable_Hqm5_xmcli)
knob_setting_hqm_disable6 = (*enable_Hqm5_xmcli, *disable_Hqm6_xmcli)
knob_setting_hqm_disable7 = (*enable_Hqm6_xmcli, *disable_Hqm7_xmcli)

knob_setting_Cpm_disable0 = (disable_cpm0_xmcli)
knob_setting_Cpm_disable1 = (*enable_cpm0_xmcli, *disable_cpm1_xmcli)
knob_setting_Cpm_disable2 = (*enable_cpm1_xmcli, *disable_cpm2_xmcli)
knob_setting_Cpm_disable3 = (*enable_cpm2_xmcli, *disable_cpm3_xmcli)
knob_setting_Cpm_disable4 = (*enable_cpm3_xmcli, *disable_cpm4_xmcli)
knob_setting_Cpm_disable5 = (*enable_cpm4_xmcli, *disable_cpm5_xmcli)
knob_setting_Cpm_disable6 = (*enable_cpm5_xmcli, *disable_cpm6_xmcli)
knob_setting_Cpm_disable7 = (*enable_cpm6_xmcli, *disable_cpm7_xmcli)

# knob_setting_sriov_common_xmlcli = (*enable_vtd_xmlcli, *enable_sriov_xmlcli)
knob_setting_sriov_disable_xmlcl = (*disable_X2apic_xmlcli, *disable_vtd_xmlcli, *enable_sriov_xmlcli)
# knob_setting_dsa_commom_xmlcli = (*enable_vtd_xmlcli, *enable_Interrupt_Remapping_xmcli, *enable_PCIeENQCMDENQCMDS_xmcli, *enable_vmx_xmcli)
# knob_setting_iax_dmatest_common_xmlcli = (*enable_PCIeENQCMDENQCMDS_xmcli, *enable_Iax0_xmcli, *enable_vtd_xmlcli, *enable_vmx_xmcli, *enable_cfr_s3m_xmlcli, *enable_cfr_pucode_xmlcli)
knob_setting_iax_stability_common_xmlcli = (*enable_X2apic_xmlcli, *enable_vtd_xmlcli, *enable_vmx_xmcli,  *enable_PCIeENQCMDENQCMDS_xmcli, *enable_Dsa0_xmcli)
knob_setting_socket_disable_common_xmlcli = (*disable_cpm0_xmcli, *disable_cpm1_xmcli, *disable_cpm2_xmcli, *disable_cpm3_xmcli, *disable_cpm4_xmcli, *disable_cpm5_xmcli, *disable_cpm6_xmcli, *disable_cpm7_xmcli)
knob_setting_socket_enable_common_xmlcli = (*enable_cpm0_xmcli, *enable_cpm1_xmcli, *enable_cpm2_xmcli, *enable_cpm3_xmcli, *enable_cpm4_xmcli, *enable_cpm5_xmcli, *enable_cpm6_xmcli, *enable_cpm7_xmcli)
knob_setting_socket0_disable_common_xmlcli = (*disable_cpm0_xmcli, *disable_cpm1_xmcli, *disable_cpm2_xmcli, *disable_cpm3_xmcli, *enable_cpm4_xmcli, *enable_cpm5_xmcli, *enable_cpm6_xmcli, *enable_cpm7_xmcli)
knob_setting_socket1_disable_common_xmlcli = (*enable_cpm0_xmcli, *enable_cpm1_xmcli, *enable_cpm2_xmcli, *enable_cpm3_xmcli, *disable_cpm4_xmcli, *disable_cpm5_xmcli, *disable_cpm6_xmcli, *disable_cpm7_xmcli)

interrupt_remapping_enable_xmlcli = ("InterruptRemap", "0x1")
interrupt_remapping_disable_xmlcli = ("InterruptRemap", "0x0")

pcie_enqcmd_enqcmds_enable_xmlcli = ("PcieEnqCmdSupport", "0x1")
pcie_enqcmd_enqcmds_disable_xmlcli = ("PcieEnqCmdSupport", "0x0")

volmem_1lm_enable_xmlcli = ("volMemMode", "0x0")
volmem_2lm_enable_xmlcli = ("volMemMode", "0x1")

emcicsmi_disable_xmlcli = ("EmcaCsmiEn", "0x0")

disable1mbcmr_disable_xmlcli = ("DfxTdxDisable1MbCmrExclude", "0x0")
disable1mbcmr_enable_xmlcli = ("DfxTdxDisable1MbCmrExclude", "0x1")

txt_enable_xmlcli = ("ProcessorLtsxEnable", "0x1")
txt_disable_xmlcli = ("ProcessorLtsxEnable", "0x0")

tme_enable_xmlcli = ("EnableTme", "0x1")
tme_disable_xmlcli = ("EnableTme", "0x0")

mktme_bypass_enable_xmlcli= ("EnableTmeBypass", "0x1")
mktme_bypass_disable_xmlcli = ("EnableTmeBypass", "0x0")

mktme_enable_xmlcli = ("EnableMktme", "0x1")
mktme_disable_xmlcli = ("EnableMktme", "0x0")

mktme_integrity_enable_xmlcli = ("MktmeIntegrity", "0x1")
mktme_integrity_disable_xmlcli = ("MktmeIntegrity", "0x0")

tdx_enable_xmlcli = ("EnableTdx", "0x1")
tdx_disable_xmlcli = ("EnableTdx", "0x0")

keysplit_enable_xmlcli = ("KeySplit", "3")

directorymode_enable_xmlcli = ("DirectoryModeEn", "0x1")
directorymode_disable_xmlcli = ("DirectoryModeEn", "0x0")

sgx_enable_xmlcli = ("EnableSgx", "0x1")
sgx_disable_xmlcli = ("EnableSgx", "0x0")


tme_mt_tdx_keysplit_xmlcli = ("KeySplit", "3")


enqcmd_enable_xmlcli = ("PcieEnqCmdSupport", "0x1")
enqcmd_disable_xmlcli = ("PcieEnqCmdSupport", "0x0")

dsaen0_enable_xmlcli = ("DsaEn_0", "0x1")
dsaen0_disable_xmlcli = ("DsaEn_0", "0x0")

dsaen4_enable_xmlcli = ("DsaEn_4", "0x1")
dsaen4_disable_xmlcli = ("DsaEn_4", "0x0")

dsaen8_enable_xmlcli = ("DsaEn_8", "0x1")
dsaen8_disable_xmlcli = ("DsaEn_8", "0x0")

dsaen12_enable_xmlcli = ("DsaEn_12", "0x1")
dsaen12_disable_xmlcli = ("DsaEn_12", "0x0")


cfr_s3m_enable_xmlcli = ("CFRS3mProvision", "0x1")
cfr_s3m_disable_xmlcli = ("CFRS3mProvision", "0x0")

cfr_pucode_enable_xmlcli = ("CFRPucodeProvision", "0x1")
cfr_pucode_disable_xmlcli = ("CFRPucodeProvision", "0x0")

package_c_auto_enable_xmlcli = ("PackageCState", "0xFF")

monitor_mwait_enable_xmlcli = ("MonitorMWait", "0x1")

c6_report_enable_xmlcli = ("C6Enable", "0x1")

knob_setting_vtd_common_xmlcli = (*disable_X2apic_xmlcli, *disable_vtd_xmlcli)

knob_setting_pcstates_common_xmlcli = (*disable_X2apic_xmlcli, *disable_vtd_xmlcli, *package_c_auto_enable_xmlcli, *monitor_mwait_enable_xmlcli, *c6_report_enable_xmlcli)

knob_setting_dsa_2g2uuser1_egs_common_xmlcli = (*enqcmd_enable_xmlcli, *dsaen0_enable_xmlcli, *dsaen4_enable_xmlcli, *enable_X2apic_xmlcli, *enable_vtd_xmlcli, *enable_vmx_xmlcli, *cfr_s3m_enable_xmlcli, *cfr_pucode_enable_xmlcli)

knob_setting_dsa_2g2uuser1_bhs_common_xmlcli = (*enqcmd_enable_xmlcli, *enable_X2apic_xmlcli, *enable_vtd_xmlcli, *enable_vmx_xmlcli, *cfr_s3m_enable_xmlcli, *cfr_pucode_enable_xmlcli)

knob_setting_sgx_common_xmlcli = (*volmem_1lm_enable_xmlcli, *tme_enable_xmlcli, *sgx_enable_xmlcli, *disable_X2apic_xmlcli, *disable_vtd_xmlcli)

knob_setting_tdx_common_xmlcli = (*volmem_1lm_enable_xmlcli, *emcicsmi_disable_xmlcli, *txt_enable_xmlcli, *tme_enable_xmlcli, *mktme_enable_xmlcli, *directorymode_disable_xmlcli, *tdx_enable_xmlcli, *sgx_enable_xmlcli, *disable1mbcmr_enable_xmlcli, *tme_mt_tdx_keysplit_xmlcli)
knob_setting_tdx15_common_xmlcli = (*volmem_1lm_enable_xmlcli, *txt_enable_xmlcli, *tme_enable_xmlcli, *mktme_bypass_disable_xmlcli, *mktme_enable_xmlcli, *tdx_enable_xmlcli, *sgx_enable_xmlcli, *tme_mt_tdx_keysplit_xmlcli)

knob_setting_tdx_common_xmlcli_1 = (*volmem_1lm_enable_xmlcli, *emcicsmi_disable_xmlcli, *txt_enable_xmlcli, *tme_enable_xmlcli, *mktme_enable_xmlcli, *tdx_enable_xmlcli, *directorymode_disable_xmlcli)
knob_setting_tdx_common_xmlcli_2 = (*sgx_enable_xmlcli, *disable1mbcmr_enable_xmlcli, *tme_mt_tdx_keysplit_xmlcli)
knob_setting_dsa_mktme_sriov_common_xmlcli = (*enable_X2apic_xmlcli, *enable_vtd_xmlcli, *enable_sriov_xmlcli, *interrupt_remapping_enable_xmlcli, *pcie_enqcmd_enqcmds_enable_xmlcli, *enable_vmx_xmlcli, *tme_enable_xmlcli, *mktme_enable_xmlcli)

# knob_setting_sriov_common_xmlcli = (*enable_vtd_xmlcli, *enable_sriov_xmlcli)

knob_setting_dsa_sriov_common_xmlcli = (*enable_X2apic_xmlcli, *enable_vtd_xmlcli, *enable_sriov_xmlcli, *interrupt_remapping_enable_xmlcli, *pcie_enqcmd_enqcmds_enable_xmlcli, *enable_vmx_xmlcli)



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
enable_rtc_wakeup = (knob_rtc_system_wakeup, 'Enable and set wake on time')
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


# Memory & Storage knobs
mem_freq_auto_xmlcli = ('DdrFreqLimit_inst_2', '0x0')
# mem_freq_2666_xmlcli = ('DdrFreqLimit_inst_2', '0xF')
# mem_freq_2933_xmlcli = ('DdrFreqLimit_inst_2', '0x11')
mem_freq_3200_xmlcli = ('DdrFreqLimit_inst_2', '0x13')
mem_freq_3600_xmlcli = ('DdrFreqLimit_inst_2', '0x16')
mem_freq_4000_xmlcli = ('DdrFreqLimit_inst_2', '0x19')
mem_freq_4400_xmlcli = ('DdrFreqLimit_inst_2', '0x1C')
mem_freq_4800_xmlcli = ('DdrFreqLimit_inst_2', '0x1D')
mem_freq_5200_xmlcli = ('DdrFreqLimit_inst_2', '0x1E')
mem_freq_5600_xmlcli = ('DdrFreqLimit_inst_2', '0x1F')
mem_freq_6000_xmlcli = ('DdrFreqLimit_inst_2', '0x20')
mem_freq_6400_xmlcli = ('DdrFreqLimit_inst_2', '0x21')


Attempt_Fast_Boot_enable_xmlcli = ("AttemptFastBoot", "0x1")
Attempt_Fast_Boot_disable_xmlcli = ("AttemptFastBoot", "0x0")
Attempt_Fast_Boot_Cold_enable_xmlcli = ("AttemptFastBootCold", "0x1")
Attempt_Fast_Boot_Cold_disable_xmlcli = ("AttemptFastBootCold", "0x0")
enable_enforce_POR_xmlcli = ('EnforceDdrMemoryFreqPor', '0x0')

disable_SpeedStep_xmlcli = ('ProcessorEistEnable', '0x0')
disable_C6Enable_xmlcli = ('C6Enable', '0x0')
disable_SpeedStep_and_C6Enable_xmlcli = (*disable_SpeedStep_xmlcli, *disable_C6Enable_xmlcli)

enable_SpeedStep_xmlcli = ('ProcessorEistEnable', '0x1')
enable_C6Enable_xmlcli = ('C6Enable', '0x1')
enable_SpeedStep_and_C6Enable_xmlcli = (*enable_SpeedStep_xmlcli, *enable_C6Enable_xmlcli)
