#!/usr/bin/python3.6

import os,sys,getopt
from PIL import Image

FILEHEADER_LENGTH = 128

BQ_AQUARIS_X5_SCREEN_W = 720
BQ_AQUARIS_X5_SCREEN_H = 1280

IMAGE_STARTS = 1
IMAGE_ENDS = 2

OFFSET_SPLASH = 512
SPLASH_MAX_SIZE = 31224
OFFSET_BOOTLOADER = 31744
BOOTLOADER_MAX_SIZE = 65016

SPLASHIMG_SIZE = 96768

def is_padding(quartet):
	if quartet[1:] == quartet[:-1] and quartet[0] == 0:
		return True
	return False

def determine_quartet_identity(byte_quartet, prev_byte_quartet):
	if not is_padding(byte_quartet):
		if len(prev_byte_quartet) > 0 and is_padding(prev_byte_quartet):
			return IMAGE_STARTS
	else:
		if len(prev_byte_quartet) > 0 and (not is_padding(prev_byte_quartet)):
			return IMAGE_ENDS

def get_splash_pictures_coordinates(filename):
	pictures_coordinates = list()
	picture_coordinates = list()

	byte_quartet = list()
	prev_byte_quartet = list()

	f = open(filename, 'rb')
	fsize = os.path.getsize(filename)

	print(fsize)

	for index in range(FILEHEADER_LENGTH, fsize, 4):

		f.seek(index, 0)
		byte_quartet = f.read(4)

		quartet_identity = determine_quartet_identity(byte_quartet, prev_byte_quartet)
		if quartet_identity == IMAGE_STARTS:
			picture_coordinates.append(index)
		elif quartet_identity == IMAGE_ENDS:		
			picture_coordinates.append(index)
			pictures_coordinates.append(picture_coordinates)
			picture_coordinates = list()
		
		prev_byte_quartet = byte_quartet

	f.close()
	return pictures_coordinates

def quartet_to_pixels(byte_quartet, coords, img_matrix):
	x,y = coords
	for i in range(byte_quartet[3]):
		img_matrix[x,y] = (byte_quartet[2], byte_quartet[1], byte_quartet[0])
		x += 1

		if x == BQ_AQUARIS_X5_SCREEN_W:
			x = 0
			y += 1
	return (x,y)

def extract_pictures(filename):
	pictures_coordinates = get_splash_pictures_coordinates(filename)

	for picture_coordinates in pictures_coordinates:
		f = open(filename, 'rb')
		fsize = os.path.getsize(filename)
		byte_quartet = list()

		img = Image.new('RGB', (BQ_AQUARIS_X5_SCREEN_W, BQ_AQUARIS_X5_SCREEN_H))
		img_matrix = img.load()

		coords = (0, 0)

		for index in range(picture_coordinates[0], picture_coordinates[1], 4):
			f.seek(index, 0)
			byte_quartet = f.read(4)
			coords = quartet_to_pixels(byte_quartet, coords, img_matrix)

		img.save('splash_%d.bmp' % index)
	f.close()

def rgb_to_brgle_bytes(picture):
	im = Image.open(picture)

	img_matrix = im.load()
	hex_image = list()

	current_pixel = [0] * 3
	previous_pixel = list()
	pixel_quartet = [0] * 4

	for y in range(BQ_AQUARIS_X5_SCREEN_H):
		for x in range(BQ_AQUARIS_X5_SCREEN_W):
			current_pixel[0] = img_matrix[x,y][0]
			current_pixel[1] = img_matrix[x,y][1]
			current_pixel[2] = img_matrix[x,y][2]
			
			if current_pixel == previous_pixel:	
				pixel_quartet[3] += 1
				if pixel_quartet[3] == 255:
					hex_image.extend(pixel_quartet)
					pixel_quartet[3] = 0
				elif y == BQ_AQUARIS_X5_SCREEN_H - 1 and x == BQ_AQUARIS_X5_SCREEN_W - 1:
					hex_image.extend(pixel_quartet)
			else:
				if len(previous_pixel) > 0:
					hex_image.extend(pixel_quartet)
				pixel_quartet[0] = current_pixel[2]
				pixel_quartet[1] = current_pixel[1]
				pixel_quartet[2] = current_pixel[0]
				pixel_quartet[3] = 1

				if y == BQ_AQUARIS_X5_SCREEN_H - 1 and x == BQ_AQUARIS_X5_SCREEN_W - 1:
					hex_image.extend(pixel_quartet)

			previous_pixel = list(current_pixel)

	return hex_image

def create_splash(new_splashimg, splash_picture, fastboot_picture):

	splash_picture_matrix = list()
	fastboot_picture_matrix = list()

	splash_picture_size = 0
	fastboot_picture_size = 0

	f_out = open(new_splashimg, 'wb')

	splash_header = open('splash_header', 'rb')	
	f_out.write(splash_header.read())
	splash_header.close()

	for index in range(FILEHEADER_LENGTH, OFFSET_SPLASH):
		f_out.write((0).to_bytes(1, sys.byteorder))

	if splash_picture:
		splash_picture_matrix = rgb_to_brgle_bytes(splash_picture)
		splash_picture_size = len(splash_picture_matrix)

		for index in range(0, splash_picture_size):
			f_out.write(splash_picture_matrix[index].to_bytes(1, sys.byteorder))
	else:
		splash_picture = open('splash_picture', 'rb')
		splash_picture_size = os.path.getsize('splash_picture')

		f_out.write(splash_picture.read())
		splash_picture.close()

	for index in range(OFFSET_SPLASH + splash_picture_size, OFFSET_BOOTLOADER):
		f_out.write((0).to_bytes(1, sys.byteorder))

	if fastboot_picture:
		fastboot_picture_matrix = rgb_to_brgle_bytes(fastboot_picture)
		fastboot_picture_size = len(fastboot_picture_matrix)
		
		for index in range(0, fastboot_picture_size):
			f_out.write(fastboot_picture_matrix[index].to_bytes(1, sys.byteorder))
	else:
		fastboot_picture = open('fastboot_picture', 'rb')
		fastboot_picture_size = os.path.getsize('fastboot_picture')
		
		f_out.write(fastboot_picture.read())
		fastboot_picture.close()

	for index in range(OFFSET_BOOTLOADER + fastboot_picture_size, SPLASHIMG_SIZE):
			f_out.write((0).to_bytes(1, sys.byteorder))

	f_out.close()

def main(argv):

	action = ''
	new_splash = ''
	splash_picture = False
	fastboot_picture = False

	try:
		opts, args = getopt.getopt(argv,"a:e:co:s:f:")
	except getopt.GetoptError:
		sys.exit(2)
	
	for opt, arg in opts:
		if opt in ("-a"):
			pictures_coordinates = get_splash_pictures_coordinates(arg)
			print(pictures_coordinates)
		elif opt in ("-e"):
			extract_pictures(arg)
		elif opt in ("-c"):
			action = create_splash
		elif opt in ("-o"):
			new_splash = arg
		elif opt in ("-s"):
			splash_picture = arg
		elif opt in ("-f"):
			fastboot_picture = arg

	if action == create_splash and new_splash != '':
		create_splash(new_splash, splash_picture, fastboot_picture)

if __name__ == "__main__":
	main(sys.argv[1:])
