<h1> USB Blaster - Postcode Reading </h1>

1. Make Sure You Have Connected Usbblaster Jtag Header On Platform And Other End To Hostmachine.
1. Make Sure You Have Cpld Version 2vb.Pof Or Latest Version Flashed.
1. Make Sure You Install Qaurtus Application <mark>C:\Intelfpga_Pro\18.1\Qprogrammer\Bin64 </mark>
1. Make Sure You Give Proper Config Path Of The Qaurtus Application. Refer <mark>Postcode_Usbblaster_System_Configuration.xml</mark> Available In DTAF CORE Framework Data Folder.
1. Create Folder In C: Drive Named Postcode, In that Extract The <mark>Postcode.zip</mark> File. You Will See A Name Rfat_Modified.Tcl
1. You Can Get The Postcode.zip File From [\\\Bdcspiec010.Gar.Corp.Intel.Com\Os_Image](\\Bdcspiec010.Gar.Corp.Intel.Com\Os_Image) or Dtaf_Core Tools Location.
1. For Usage, refer the examples in this file --> <mark>Test_Usbblaster_Physical_Control_Provider.py</mark>