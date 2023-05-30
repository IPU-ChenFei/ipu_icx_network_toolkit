To run Test case H79540-PI_Security_TPM2.0 PCR value check_PCR0_UEFI
------------------------------------------------------
Following information has to be populated for performing the IFWI flashing
1. System has Latest IFWI(Current (N-version)) flashed. As per TC, need to flash (N-1 version) i.e previous IFWI.
   To flash N-1 version IFWI, user need to keep N-1 version IFWI bin file in below location in content_configuration
   .xml:
    <previous_ifwi_version></previous_ifwi_version>
    
2. After the system has been flashed with N-1 IFWI, so it has to be reverted to latest(Current (N-version)). For
   current(N) version flashing, user need to keep the N version (current) bin file in below location in 
   content_configuration.xml:
    <current_ifwi_version></current_ifwi_version>

3. Better to execute the test at the end of execution or as part of the CC events after flashing the required BKC config
4. Connect USB in sut(It should be visible in OS)

To run Test case H79543 PI_Security_TPM2.0PCRvaluecheck_PCR1_chnagebootmedia_UEFI :
-----------------------------------------------------------------------------
1. Check the jumper position of J5E1 [It should be open [position -1] which enables the onboard TPM]
If not enabled, please enable it
2. Need one empty SSD to be connected and update the name in content config file.
<boot_media_device></boot_media_device>
3. Connect USB in sut(It should be visible in OS)

To run Test case H79542 PI_Security_TPM2_PCRvaluecheck_PCR4_UEFI :
-----------------------------------------------------------------------------
1. Check the jumper position of J5E1 [It should be open [position -1] which enables the onboard TPM]
If not enabled, please enable it
2. Connect USB in sut(It should be visible in OS)
