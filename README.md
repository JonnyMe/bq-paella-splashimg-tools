# bq-paella-splashimg-tools
Tool to analize, extract and create BQ Aquaris X5 Cyanogen Edition splash.img

## Overview
Files in this project are all useful to make the tool work (except from the demo directory). The `splash.img` file already present is a copy of the original splash.img from paella firmware ([https://storage.googleapis.com/support-files.bq.com/Bootloader/Cyanogen%20OS/cm-13.1.4-ZNH2KAS5FE-paella-signed-fastboot-a6851b4fbe.zip](https://storage.googleapis.com/support-files.bq.com/Bootloader/Cyanogen%20OS/cm-13.1.4-ZNH2KAS5FE-paella-signed-fastboot-a6851b4fbe.zip))

## Usage

### Analize splash.img:
```
./paella_splashimg_tools.py -a splash.img
```
This command prints picture offsets

### Extract pictures from splash.img:
```
./paella_splashimg_tools.py -e splash.img
```
This command extracts both splash and fastboot pictures

### Create custom splash.img:
To create a custom splash.img there are several available combinations:
```
./paella_splashimg_tools.py -c splash.img
```
This command creates the standard splash.img (original pictures)
```
./paella_splashimg_tools.py -c splash.img -s splash_picture.jpg(/bmp,... it has to be RGB format)
```
This command creates a splash.img with custom splash picture and default fastboot picture
```
./paella_splashimg_tools.py -c splash.img -f fastboot_picture.jpg
```
This command creates a splash.img with default splash picture and custom fastboot picture
```
./paella_splashimg_tools.py -c splash.img  -s splash_picture.jpg -f fastboot_picture.jpg
```
This command creates a splash.img with custom splash picture and custom fastboot picture
