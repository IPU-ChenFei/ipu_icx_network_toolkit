'''
Copyright (c) 2021-2022, Intel Corporation. All rights reserved.
Retrieves the FIT and SPS/CSME Version from the IFWI Image.
Title      	: IFWI_SPS_VersionRetriever.py
Author(s)  	: Santosh, Deshpande
Description	:
Inputs		: Each function has relevant header details for input and output
Output		: Each function has relevant header details for input and output
'''

import os

def RetrieveSPSVerionDetails(IFWI):

	buf_0 = []
	with open(IFWI, "rb") as IFWIImage:
		BinData = IFWIImage.read()
		IFWIImageLength = len(BinData)
		RBEP_StartAddress = BinData.find(b'RBEP')
		Version_ReaderOffset = (BinData[RBEP_StartAddress:IFWIImageLength].find(b'$MN2'))
		Version_ReaderOffset = ((Version_ReaderOffset + RBEP_StartAddress) & 0xFFFFFFF0) + 0x10
		print (Version_ReaderOffset)
		shift = 0
		value = 0
		for byte in BinData[Version_ReaderOffset:Version_ReaderOffset+0xA]:
			value = value + (byte << (8 * shift))
			shift = (shift + 1) % 2
			if (shift == 0):
				buf_0.append(value)
				value = 0
		print (buf_0)
		VersionInfo=r''

		if (buf_0[0] < 11):
			VersionInfo = "{:02d}.{:02d}.{:02d}.{:03d}".format(buf_0[0], buf_0[1], buf_0[2], buf_0[3])
			FITM_DownloadLink = r'https://ubit-artifactory-sh.intel.com/artifactory/DEG-IFWI-LOCAL/SiEn-EagleStream_Sapphire_Rapids/Ingredients/FITm-SPS/ModularFit_exe_gui_SPS_E5_'+VersionInfo+r'.0.zip'
			SPS_DownloadLink = r'https://ubit-artifactory-sh.intel.com/artifactory/DEG-IFWI-LOCAL/SiEn-EagleStream_Sapphire_Rapids/Ingredients/SPS/SPS_E5_'+VersionInfo+r'.0.zip'
			print (FITM_DownloadLink)
			print (FITM_DownloadLink)
			UserDataReturn = {"Version Info":VersionInfo, "FITM_Download_Link":FITM_DownloadLink, "SPS_Download_Link":SPS_DownloadLink}
		else:
			VersionInfo = "{}.{}.{}.{}".format(buf_0[0], buf_0[1], buf_0[2], buf_0[3])
			if ( buf_0[4] > 0):
				VersionInfo = "{}.{}.{}.{}V{}".format(buf_0[0], buf_0[1], buf_0[2], buf_0[3], buf_0[4])
			UserDataReturn = {"Version Info": VersionInfo, "CSME_Download_Link": r'https://ubit-artifactory-ba.intel.com/artifactory/simple/owr-repos/Submissions/csme/'+VersionInfo, "NOTE":"If this link doesn't work remove the last folder search for closest that is due to naming conventions are non-standard"}
		print(VersionInfo)
		print (UserDataReturn)
		return (UserDataReturn)

def main():
	RootPath = os.getcwd()
#	Payloads = r'C:\POC_IFWI_Quarantine\SPRH\2021WW5.4.1\Payloads\ICL_UR03_D1B0-XXXXXXN_SPSE_SES0_000488_2020WW37.3.1.bin'
	Payloads = r'C:\POC_IFWI_Quarantine\SPRH\2021WW5.4.2\Payloads\MTL_PV01_NNNN-XXXMTPP_CPRF_SES0_01630012_2021WW2.3.38.bin'
#	Payloads = r'C:\POC_IFWI_Quarantine\SPRH\2021WW4.5.2\Payloads\EGSDCRB.SYS.OR.64.2021.03.4.05.1800_SPR_EBG_SPS_IP_Cleaned.bin'
	RetrieveSPSVerionDetails(Payloads)
	
if __name__ == "__main__":
    main()