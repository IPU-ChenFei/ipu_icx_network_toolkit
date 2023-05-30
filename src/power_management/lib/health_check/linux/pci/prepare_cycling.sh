#!/bin/bash
# Run this only once to get baseline config

if [  -e /var/log/cycling ]
then
	rm -r -f /var/log/cycling
fi
