IFWI Flashing using Banino for SPR platform:
------------------------------------------------------
Following information has to be populated for performing the IFWI flashing
1. For profile 0 flashing user need to keep the bin file in below location 
    <ifwi_profile_bin_path><profile0></profile0></ifwi_profile_bin_path>
    
2. For profile 3 flashing user need to keep the bin file in below location 
    <ifwi_profile_bin_path><profile3></profile3></ifwi_profile_bin_path>
    
3. For profile 4 flashing user need to keep the bin file in below location 
    <ifwi_profile_bin_path><profile4></profile4></ifwi_profile_bin_path>
    
4. For profile 5 flashing user need to keep the bin file in below location 
    <ifwi_profile_bin_path><profile5></profile5></ifwi_profile_bin_path>

IFWI Flashing including profile Image building using Dediprog for ICX, SKX platforms:
-------------------------------------------------------------------------------------------------
Case of non provider container following information has to be updated in content_configuration.xml file
1.user needs to set the common/ifwi/profile_container value to False
2.user needs to populate path of the folder of the ifwi and name of ifwi which needs to be modified in the
  in the section common/ifwi/ifwi-file/path and common/ifwi/ifwi-file/name
3.user needs to populate path of the path of the spsfit tool and name of the executable to be used to modify
Profile information
4.user needs to populate as common/profiles/profile0/<bootProfile>0 - No_FVME</bootProfile>
ifwi binary in the section common/ifwi/fit_tool/path and common/ifwi/fit_tool/name


Case of provider container following information has to be updated in content_configuration.xml file
1.user needs to set the  common/ifwi/profile_container value to True.
2.user needs to populate path of the folder of the ifwi container folder in the section common/ifwi/container/path
3.user needs to populate name of the build xml in the section common/ifwi/container/build_xml.
4.user needs to populate name of the build file in the section common/ifwi/container/build_file.
5.user needs to modify python build file in case build xml is different which is present in the build file.
Profile information
6.user needs to populate as common/profiles/profile0/<bootProfile>Boot Guard Profile 0 - No_FVME</bootProfile>
7.user needs to populate as common/build_xml_modifier/<bootProfile>BtGuardProfileConfig</bootProfile>