'''
Copyright (c) 2019-2020, Intel Corporation. All rights reserved.
This is the entry point for all IFWI Pre Build Activities that has to happen 
before the BUILD is triggered
Title      	: IFWI_StrapsOverrideBits.py
Author(s)  	: Chandni, Vyas; Santosh, Deshpande
Description	: Things to perform: 
			`1. This python file will apply straps on IFWI and generate an IFWI as provided in csv file. 
Inputs		: Each function has relevant header details for input and output
Output		: Each function has relevant header details for input and output
Usage		: python IFWI_StrapsOverrideBits.py -i Inputbinfile -c csvfile
'''
#Program to override strap from Not-commited values into harness
import csv, struct, array, sys, operator
import argparse
import shutil
import IFWI_PreOSBuildCommonCode

__all__ = ["OverrideStrapBits"]

def setup_arg_parse():
	parser = argparse.ArgumentParser()
	parser.add_argument('-i', help='FullIFWIBinNamePath',required=True,metavar="Inputbinfile")
	parser.add_argument('-c', help='FullCSVFileNamePath',required=True,metavar="csvfile")
	parser.add_argument('-t', help='IFWIType',required=True,metavar="BFx")
	parser.add_argument('-o', help='OutputFileName',required=False,metavar="OutputFileName")
	args = parser.parse_args()
	return args

def OverrideStrapBits(FullIFWIBinNamePath, FullCSVFileNamePath):
	base_offset = 0x0
	# Read CSV file
	filereader = csv.DictReader(open(FullCSVFileNamePath), delimiter=",")
	updatedfile = []
	
	# Go over the CSV file and update the offset column
	for row in filereader:
		offset = row['Offset']
		row['Offset'] = hex(int(offset, 0) + base_offset)
		updatedfile.append(row)

	# Sort the CSV file according to the offset column    
	sortedfile = sorted(updatedfile, key=lambda d: int(d['Offset'], 0))
	
	with open(FullIFWIBinNamePath, "rb") as ifwi_0:
		ifwi_0.seek(base_offset)
		byte_count = 0
		shift = 0
		value = 0
		buf_0 = []

		for line in ifwi_0: 
			for byte in line:
				value = value + (byte << (8 * shift))
				byte_count = byte_count + 1
				shift = (shift + 1) % 4
				if (shift == 0):
					buf_0.append(value)
					value = 0
				if byte_count > 4096:
					break
			if byte_count > 4096:
				break

	# Go over the CSV file and compare it to the IFWI or IFWIs
	for row in sortedfile:
		offset = row['Offset']
		start_bit = row['Start Bit']
		strap_size = row['Strap Size']
		harness = row['Value']
		strap_mask = (1 << int(strap_size, 0)) - 1
		strap_shift = int(start_bit, 0) + ((int(offset, 0) % 4) * 8)
		buf_index = int (int(offset, 0) / 4)
		print (hex(buf_index),offset, harness+'L')
		actual_dword_0 = buf_0[buf_index]
		actual_0 = (actual_dword_0 >> strap_shift) & strap_mask
		if (harness != ''):
			harness_int = int(harness, 0)
		else:
			print ("Value is BLANK, ignored this record...")
		if (actual_0 != harness_int):
			print ("Offset - " + offset + ", start bit - " + start_bit + ", strap size - " + strap_size + ", Straps Override value - " + harness + ", IFWI value - " + str(hex(actual_0).rstrip("L")))
			print ("")
			updated_dword = (actual_dword_0 & ~(strap_mask << strap_shift)) | (harness_int << strap_shift)
			buf_0[buf_index] = updated_dword

	with open(FullIFWIBinNamePath, "rb+") as ifwi_1:
		Location = base_offset
		ifwi_1.seek(base_offset)
		for dword in buf_0:
			#print "Value: ", hex(dword), " @Offset: ", hex(Location)
			dword_0 = dword & 0xff
			dword_1 = (dword >> 8) & 0xff
			dword_2 = (dword >> 16) & 0xff
			dword_3 = (dword >> 24) & 0xff
			ifwi_1.write(struct.pack('h',dword_0)[:-1])
			ifwi_1.write(struct.pack('h',dword_1)[:-1])
			ifwi_1.write(struct.pack('h',dword_2)[:-1])
			ifwi_1.write(struct.pack('h',dword_3)[:-1])
			Location = Location + 4
	return ("Updated Same IFWI successfully")


def main():
	args = setup_arg_parse()
	FullIFWIBinNamePath = args.i
	FullCSVFileNamePath = args.c
	OutputFileName=args.o
	BFx=args.t

	OverrideStrapBits(FullIFWIBinNamePath, FullCSVFileNamePath, BFx)

if __name__ == "__main__":
	main()
