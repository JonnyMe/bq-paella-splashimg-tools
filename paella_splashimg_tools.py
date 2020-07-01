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

def extract_splash(filename):
	f = open(filename, 'rb')
	fsize = os.path.getsize(filename)
	pictures_coordinates = get_splash_pictures_coordinates(filename)

	for picture_coordinates in pictures_coordinates:
		img = Image.new('RGB', (BQ_AQUARIS_X5_SCREEN_W, BQ_AQUARIS_X5_SCREEN_H))
		img_matrix = img.load()
		byte_quartet = list()
		coords = (0, 0)

		for index in range(picture_coordinates[0], picture_coordinates[1], 4):
			f.seek(index, 0)
			byte_quartet = f.read(4)
			coords = quartet_to_pixels(byte_quartet, coords, img_matrix)

		img.save('splash_%d.bmp' % index)
	f.close()

def append_pixel(hex_image, pixel):
	pixel_bgr = pixel[::-1]

	if len(hex_image) < 4:
		hex_image.extend(pixel_bgr)
		hex_image.append(1)
		return

	if hex_image[-4:-1] == list(pixel_bgr):
		if hex_image[-1] < 255:
			hex_image[-1] += 1
		else:
			hex_image.extend(pixel_bgr)
			hex_image.append(1)
	else:
		hex_image.extend(pixel_bgr)
		hex_image.append(1)

def picture_to_bgr_raw(picture):
	im = Image.open(picture)
	img_matrix = im.load()
	hex_image = list()

	for y in range(0, BQ_AQUARIS_X5_SCREEN_H):
		for x in range(0, BQ_AQUARIS_X5_SCREEN_W):
			append_pixel(hex_image, img_matrix[x,y])

	print(hex_image)
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
		f_out.write((0).to_bytes(1, 'little'))

	if splash_picture:
		splash_picture_matrix = picture_to_bgr_raw(splash_picture)
		splash_picture_size = len(splash_picture_matrix)

		if splash_picture_size > SPLASH_MAX_SIZE:
			print("%s too big (actual:%d, max:%d), abort" % (
				splash_picture,
				splash_picture_size,
				SPLASH_MAX_SIZE
			))
			exit()

		for index in range(0, splash_picture_size):
			f_out.write(splash_picture_matrix[index].to_bytes(1, 'little'))
	else:
		splash_picture = open('splash_picture', 'rb')
		splash_picture_size = os.path.getsize('splash_picture')

		f_out.write(splash_picture.read())
		splash_picture.close()

	for index in range(OFFSET_SPLASH + splash_picture_size, OFFSET_BOOTLOADER):
		f_out.write((0).to_bytes(1, 'little'))

	if fastboot_picture:
		fastboot_picture_matrix = picture_to_bgr_raw(fastboot_picture)
		fastboot_picture_size = len(fastboot_picture_matrix)

		if fastboot_picture_size > BOOTLOADER_MAX_SIZE:
			print("%s too big (actual:%d, max:%d), abort" % (
				fastboot_picture,
				fastboot_picture_size,
				BOOTLOADER_MAX_SIZE
			))
			exit()
		
		for index in range(0, fastboot_picture_size):
			f_out.write(fastboot_picture_matrix[index].to_bytes(1, 'little'))
	else:
		fastboot_picture = open('fastboot_picture', 'rb')
		fastboot_picture_size = os.path.getsize('fastboot_picture')
		
		f_out.write(fastboot_picture.read())
		fastboot_picture.close()

	for index in range(OFFSET_BOOTLOADER + fastboot_picture_size, SPLASHIMG_SIZE):
			f_out.write((0).to_bytes(1, 'little'))

	f_out.close()

def analyze_splash(target_splash):
	pictures_coordinates = get_splash_pictures_coordinates(target_splash)
	print(pictures_coordinates)

def main(argv):
	action = ''
	target_splash = ''
	splash_picture = False
	fastboot_picture = False

	try:
		opts, args = getopt.getopt(argv,"a:e:c:s:f:")
	except getopt.GetoptError:
		sys.exit(2)
	
	for opt, arg in opts:
		if opt in ("-a"):
			action = analyze_splash
			target_splash = arg
		elif opt in ("-e"):
			action = extract_splash
			target_splash = arg
		elif opt in ("-c"):
			action = create_splash
			target_splash = arg
		elif opt in ("-s"):
			splash_picture = arg
		elif opt in ("-f"):
			fastboot_picture = arg

	if len(target_splash) == 0:
		return

	if action == create_splash:
		action(target_splash, splash_picture, fastboot_picture)
	elif action == extract_splash or action == analyze_splash:
		action(target_splash)

if __name__ == "__main__":
	main(sys.argv[1:])
