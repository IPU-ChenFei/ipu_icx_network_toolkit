#!/bin/expect
set timeout {}
spawn {}
expect "Please input the pccs password, and use the \"Enter key\" to end"
send "{}\r"
expect eof

lassign [wait] pid spawnid os_error_flag value
