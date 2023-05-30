<h1>CPLD Flashing BKM </h1>

1. Make sure you have connected usbblaster JTAG header on platform and other end to hostmachine.
1. Make sure you install qaurtus application C:\intelFPGA_pro\18.1\qprogrammer\bin64
1. Make sure you give proper config path of the qaurtus application. Refer cpld_sample_configuration.xml available in dtaf core data folder.
1. Refer test_usbblaster_cpld_provider.py for usage examples.
1. Make sure during cpld main & secondary flashing you need to turn on the platform power.