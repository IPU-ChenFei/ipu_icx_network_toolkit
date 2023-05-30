1) For any USB HDD read/write TC's need the following config tags updated in the content_config.xml
a. 1509810653-PI_USB_BigDataCopyReliability_L

    <usb>
        <device>
              <type>Mass Storage</type>
              <bcd>2.10</bcd>
              <bcd_mouse>2.00</bcd_mouse>
              <bcd_keyboard>1.10</bcd_keyboard>
              <bcd_usb_key>2.10</bcd_usb_key>
              <bcd_hub>3.10</bcd_hub>
              <bcd_hdd>2.00</bcd_hdd>
              <bcd_hdd_centos>2.10</bcd_hdd_centos>
              <hdd_model_number>WDC WD10SDRW-11A0XS0</hdd_model_number> # HDD model NUmber for read/write check for HDD
              <hdd_serial_number>WD-WXK2AC0AAXLL</hdd_serial_number> # HDD Serial Number read/write check for HDD
        </device>
    </usb>
2) Make sure a HDD is connected in the front panel USB3.0 port of the system.

