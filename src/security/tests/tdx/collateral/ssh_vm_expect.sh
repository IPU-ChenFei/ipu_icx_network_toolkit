#!/bin/expect
set timeout {}
spawn {}
expect "{}'s password:"
send "{}\r"
expect eof

lassign [wait] pid spawnid os_error_flag value