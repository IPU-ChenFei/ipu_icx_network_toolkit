For the Test case : 1308839394 SATASSD-Configuration check in AHCI Mode
1) Need to connect the SUT with 8 SATA INTEL SSDs and one M.2 in pch slot.

2We need to update the content_configuration.xml with below details.
    <SSD>
        <!-- SATA drive manufacturer and model number details -->
        <device>SSDSC2KB960G8,SSDSCKKI128G8</device>
        <model_number>S4510/S4610/S4500/S4600,DC S3110 Series</model_number>
    </SSD>