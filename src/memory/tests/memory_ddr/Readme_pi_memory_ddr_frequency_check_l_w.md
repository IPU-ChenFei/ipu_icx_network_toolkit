For Test cases, H81114-PI_Memory_DDR5_Frequency_Check_L and H102738-PI_Memory_DDR5_Frequency_Check_W,

1) We need need to update the content_configuration.xml, tag : Supported_Frquencies based on CPU family.

Example :

<Supported_Frquencies>
    <SPR>
        <frequencies>4000,4400,4800</frequencies>
    </SPR>
</Supported_Frquencies>

Note : If SUT has 2 DPC memory configuration then it will support upto 4400 MHz.
If SUT is 2 DPC then frequencies we need to keep are 4000, 4400.

2) ITP should be connected.
