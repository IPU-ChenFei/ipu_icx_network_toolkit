For test cases, H79592-PI_PCIe_Config_Display_L, H110750-PI_PCIe_Config_Display_W,
1) In content_configuration.xml, we need to update lnkcap tag under cpu_root according to silicon family.
Ex : 
<cpu_root> 
    <SPR>
        <lnkcap>32.0GT/s</lnkcap>
    </SPR>
</cpu_root>
2) In system_configuration.xml, we need to update cpu family and stepping with the connected silicon in SUT.
Ex:
<cpu>
    <family>SPR</family>
    <stepping>D0</stepping>
</cpu>
Note : Make sure platform booted with fully PCI cards populated irrespective of generations.
