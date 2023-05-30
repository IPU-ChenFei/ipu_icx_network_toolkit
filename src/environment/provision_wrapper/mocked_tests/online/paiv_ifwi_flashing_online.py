import sys
import time

sleep_time_secs = 2
return_code = 0

print('Running mocked: paiv_ifwi_flashing_online.py')
print(sys.argv)

print('Sleep {}s.'.format(sleep_time_secs))
time.sleep(sleep_time_secs)

print('Returning code: {}'.format(return_code))
sys.exit(return_code)
