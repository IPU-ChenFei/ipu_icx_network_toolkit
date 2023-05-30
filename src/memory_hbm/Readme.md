In content_configuration.xml,
1) update tag : bios_post_memory_capacity: with the amount of DDR connected in the SUT.
2) update tag : hbm_memory_per_socket : with the amount of HBM memory in one socket.
example: <hbm_memory_per_socket>64</hbm_memory_per_socket>

1. pi_memory_hbm_mode_memtest.py
2. pi_memory_flat_mode_memtest.py
3. pi_memory_cache_mode_memtest.py
For the above mentioned memtest tests, please update the below tag information mentioned,

usb_name --> should be same as what is showing in BIOS page.
usb_size --> size of the drive, like 8, 16, 32, 64 ...

    <memory_hbm>
        <pi_memory_hbm_mode_memtest>
            <usb_name>UEFI USB SanDisk 3.2Gen1 0401e 43ef492ec530ec584e11bd20b2226b818e3f908dcc1fa74a984cea0efa90c9f0000000000000000000030a8cde6ff94651891558107b8a83841</usb_name>
            <usb_size>32</usb_size>
        </pi_memory_hbm_mode_memtest>
    </memory_hbm>
 