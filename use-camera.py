#!/usr/bin/python3

# Reference
# https://github.com/sparkfun/SparkFun_HM01B0_Camera_ArduinoLibrary/blob/master/examples/Example1_StopMotion/Example1_StopMotion.ino

import os
import serial
import serial.tools.list_ports as list_ports
import argparse
import os.path
from array import *

from PIL import Image
import numpy as np
import re
from datetime import datetime

dict_Resolutions = {
    'QVGA':     (324, 244),
}

# height = 244
# width = 324

VERSION     = 0
SUBVERSION  = 1

image_count = 0

def map0(idx, iw, ih):
    return [int(idx%iw), int(idx/iw)]

def map1(idx, iw, ih):
    return [int(idx/ih), ih-int(idx%ih)-1]

def map2(idx, iw, ih):
    return [iw-int(idx%iw)-1, ih-int(idx/iw)-1]

def map3(idx, iw, ih):
    return [iw-int(idx/ih)-1, int(idx%ih)]


def create_bmp(args, rawdata):
    global image_count

    (width, height) = dict_Resolutions.get(args.resolution, ("Resolution not supported", 0, 0))

    # print("width: {}, height: {}".format(width, height))

    if args.spin == 0:
        image_width = width
        map = map0
    elif args.spin == 1:
        image_width = height
        map = map1
    elif args.spin == 2:
        image_width = width
        map = map2
    else:
        image_width = height
        map = map3

    image_height = int((height*width)/image_width)
    # print("iw: {}, ih: {}".format(image_width, image_height))

    (um, vm) = map(width*height-1, image_width, image_height)
    # print("um: {}, vm: {}".format(um, vm))

    bitmap = np.zeros((image_width, image_height), dtype=np.uint8)

    # fill up bitmap array - always write u dimension first 
    # (that's how data from the camera was streamed out)
    idx = 0
    for pixel in rawdata:
        (u, v) = map(idx, image_width, image_height)
        idx += 1
        bitmap[u, v] = pixel
      
    # print(idx)

    path = os.path.dirname(args.outputfilepath)
    # Check if the path exists
    if not os.path.exists(path):
        # Create the directory
        os.makedirs(path)

    basename = datetime.now().strftime('%Y%m%d_%H%M%S')
    outputfile = os.path.join(path, basename + '.bmp')

    # print (bitmap)
    img = Image.fromarray(bitmap, 'L')
    img.save(outputfile)
    img.show()

    print ("%s created" % (basename + '.bmp'))

    image_count += 1

# ***********************************************************************************
#
# Help if serial port could not be opened
#
# ***********************************************************************************
def phase_serial_port_help(args):
    devices = list_ports.comports()

    # First check to see if user has the given port open
    for dev in devices:
        if(dev.device.upper() == args.port.upper()):
            print(dev.device + " is currently open. Please close any other terminal programs that may be using " +
                    dev.device + " and try again.")
            exit()

    # otherwise, give user a list of possible com ports
    print(args.port.upper() +
            " not found but we detected the following serial ports:")
    for dev in devices:
        if 'CH340' in dev.description:
            print(
                dev.description + ": Likely an Arduino or derivative. Try " + dev.device + ".")
        elif 'FTDI' in dev.description:
            print(
                dev.description + ": Likely an Arduino or derivative. Try " + dev.device + ".")
        elif 'USB Serial Device' in dev.description:
            print(
                dev.description + ": Possibly an Arduino or derivative.")
        else:
            print(dev.description)

def sync(ser):
    # Wait for camera to be ready
    while True:
        try:
            line = ser.readline()
            line = line.decode('utf-8')
        except KeyboardInterrupt:
            exit()
        
        # Check if camera is ready
        if 'Ready' in line:
            print('Camera is now ready')
            return
        

def do_convert(args):

    (width, height) = dict_Resolutions.get(args.resolution, ("Resolution not supported", 0, 0))

    try:
        with serial.Serial(args.port, args.baud) as ser:
            ser.close()
            ser.open()
            print('Waiting for camera...')
            ser.reset_input_buffer()
            sync(ser)

            while True:
                print()
                input('Press Enter to take a picture')
                print('Taking a picture')
                ser.write(b'\x55')  # Speical character for trigger camera
                rawdata = None
                framestart = False
                framestop = False
                while(1):
                    line = None
                    try:                    
                        line = ser.readline()
                        line = line.decode('utf-8')
                    except KeyboardInterrupt:
                        exit()

                    if line == "+++ frame +++\n":
                        framestart = True
                        rawdata = []
                        count = 0
                        print('Picture taken. Transferring image...')
                        continue
                    elif line == '--- frame ---\n':
                        framestop = True
                        print('Transferring finished')

                    if framestart == True and framestop == False:
                        count += 1
                        linelist = re.findall(r"[\w']+", line)

                        if len(linelist) != 17:
                            # data lost
                            print("Didn't retrieve all the data. Consider lowering baud rate. Exiting...")
                            exit()

                        for item in linelist[1 : ]:
                            store = int(item, base=16)
                            if(store > 255):
                                store = 255
                            rawdata.append(store)

                    elif framestart == True and framestop == True:
                        print('Saving image as a bmp file')
                        create_bmp(args, rawdata)

                        framestart = False
                        framestop = False
                        break

    except serial.SerialException:
        phase_serial_port_help(args)

    exit()

def main():
    parser = argparse.ArgumentParser(
        description = 'This program converts raw data from HM01B0 to bmp files from a serial connection.')

    parser.add_argument('-o', '--output', 
                        dest        = 'outputfilepath',
                        required    = False,
                        help        = 'output file path',
                        metavar     = 'FILEPATH',
                        default     = './output/',
                        type        = str
                        )

    parser.add_argument('-p', '--port', 
                        dest        = 'port',
                        required    = True,
                        help        = 'serial port (COM*, /dev/tty*)',
                        metavar     = 'SERIAL_PORT',
                        )

    parser.add_argument('-b', '--baud', 
                        dest        = 'baud',
                        required    = False,
                        help        = 'Baud rate that the board is configured for',
                        type        = int,
                        default     = 230400,
                        )
    
    parser.add_argument('-s', '--spin', 
                    dest        = 'spin',
                    required    = False,
                    help        = 'A number 0-3 for how many times to rotate the image (90 degree increments)',
                    type        = int,
                    default     = 1,
                    )

    parser.add_argument('-r', '--resolution', 
                        dest        = 'resolution',
                        required    = False,
                        help        = 'Resolution',
                        choices     = ['QVGA'],
                        default     = 'QVGA',
                        )

    parser.add_argument('-v', '--version',
                        help        = 'Program version',
                        action      = 'version',
                        version     = '%(prog)s {ver}'.format(ver = 'v%d.%d' %\
                            (VERSION, SUBVERSION))
                        )

    args = parser.parse_args()

    do_convert(args)

    print ("done!")


if __name__ == "__main__":
   main()