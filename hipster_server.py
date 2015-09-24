# -*- coding: utf-8 -*-
"""
Created on Wed Aug 21 18:26:37 2015

@author: CRGrace@lbl.gov
"""

"""
server to allow communications between test program and HIPSTER board
Server can communicate with HIPSTER, 2 DACs, and the Si5338 clock generator
HIPSTER -- custom bit-banged serial interface in hipster_spi_ops.py
Texas Instruments DAC8568 -- SPI 
Si5338 -- I2C
The serverOp command length is five bytes.  First byte is device ID and  
indicates if it is a read or write and what device is requested.
Bytes 2 and 3 are the 16-bit register address
Bytes 4 and 5 are the 16-bit data word


    deviceID :  device
    ----------------
        0    : HIPSTER
        1    | DAC 1
        2    | DAC 2
        3    | Si5338 clock generator
"""

import sys, socket
#import hipster_spi_ops
#import time
#import spidev   # for accessing Raspberry Pi SPI kernal module
#import smbus   # for accessing Raspberry Pi SMBUS (I2C) kernal module


#### globals used for test
#
# HIPSTER configuration map is global variable
# there are two maps.  One is the emulated map in HIPSTER 
# called spiMap
#
#

NUMREGS = 54
MBR = 54  #mailbox register
CR = 53 #command register
WDR = 52 #write data register
DAC1 = 55 #MSBs in DAC1+1, LSBs in DAC1
DAC2 = 57 #MSBs in DAC2+1, LSBs in DAC2 

spiMap = 55*[0] # initialize with all zeros

# second is the copy of the spiMap help in the host computer
# called configMap
configMap = []


clrf = 384*[0]  # initialize with all zeros

#    The model of the CLRF is as follows.  There are 384 memory locations
#    (24 ADCs, 8 calibrated stages/ADC, and 2 weights/stage)
#    So, we use a 9-bit word to model the memory.
#    5-bits for the ADC
#    3 bits for the stage
#    1 bit for the weight
####

def Server(serverName="localhost",port=50000):
#def Server(serverName="131.243.115.189",port=50000):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # Bind the socket to the address given to the function
    serverAddress = (serverName,port)  
    print >>sys.stderr, 'starting server on %s port %s' % serverAddress
    sock.bind(serverAddress)
    sock.listen(1)
    while True:
        print >>sys.stderr, 'waiting for remote connection'
        connection, clientAddress = sock.accept()
        try:
            print >>sys.stderr, 'client connected:', clientAddress
            while True:
                dataString = connection.recv(64)
                print >>sys.stderr, 'received "%s"' % dataString
                print "dataString = ",dataString
                if dataString == "":
                    connection.close()
                    break
                elif (dataString):  # do not parse empty string     
                    receivedData = serverOp(dataString)
                    print "sending ",receivedData," to client."
                    connection.sendall(receivedData)
                else:
                    break
        finally:
            connection.close()

def Client(message="10000",serverName="localhost",port=50000):
    """ this is a small client used for testing the server
    """

    # Create a TCP/IP socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # Connect the socket to the port on the server given by the caller
    serverAddress = (serverName,port)  
    print >>sys.stderr, 'connecting to %s port %s' % serverAddress
    sock.connect(serverAddress)

    try:
    
        #    message = 'This is the message.  It will be repeated.'
        #        message = str(100050000)
        print >>sys.stderr, 'sending "%s"' % message
        sock.sendall(message)

        amountReceived = 0
        amountExpected = len(message)
        while amountReceived < amountExpected:
            data = sock.recv(64)
            amountReceived += len(data)
            print >>sys.stderr, 'received "%s"' % data

    finally:
	    sock.close()

def serverOp(dataString,verbose=False):
    """ do an operation.  Server can read or write from different devices """

    dataHIPSTER = 0
    # first parse the command
    deviceID = ((int(dataString)) >> 32) & 0xFFFF
     # determine if a read or a write is requested
    wrb = ((int(dataString)) >> 16) & 0x8000
    print "dataString ",int(dataString),"wrb = ",wrb
    register = ((int(dataString)) >> 16) & 0x3FFF
    data = int(dataString) & 0xFFFF
    
    if (verbose):
        print "serverOp: deviceID = ", deviceID
        print "serverOp: register = ", register
        print "serverOp: data = ", data
        print "serverOp: wrb = ", wrb

  #  register = hipster_spi.clearBit(register,7)
    register = register & 0xBFFF  # clear bit 7
    if (verbose):
        print "serverOp: new register = ", register

    # execute desired action

    if (deviceID == 0):    # HIPSTER
        dataHIPSTER = regOpHIPSTER(wrb,register,data)
    elif (deviceID == 1):  # DAC1
        # DAC uses 32 bit commands.  Top 16 bits in register, LSBs in data
        regOpDAC(0,(register << 16 | data))   # 0 --> DAC1, 1 --> DAC2
    elif (deviceID == 2):  # DAC2
        regOpDAC(1,(register << 16 | data))
    elif (deviceID == 3):
        regOp5338(wrb,register,data)
    else:
        print "serverOP error: device ID out of range."
        print "deviceID :  device"
        print "----------------"
        print "0    | HIPSTER:"
        print "1    | DAC 1"
        print "2    | DAC 2"
        print "3    | Si5338 clock generator"

    # return initial message if a write, otherwise return from HIPSTER
    if (wrb):
        if (verbose):
            print "serverOp: returning dataString: ",dataString
        return dataString
    elif ((wrb == 0) and deviceID == 0):
        if (verbose):
            print "serverOp: returning dataHIPSTER: ",dataHIPSTER
        return dataHIPSTER     
    else:
        print "serverOp: read request on non-HIPSTER device"

def regOpHIPSTER(wrb,register,data,verbose=True):
    """ reads or writes to a HIPSTER register via SPI 
    """

    global spiMap

    spiCommand = (wrb << 15 | register) & 0xFFFF
    message = str((int(spiCommand << 16) + int(data & 0xFFFF)))
    # call to SPI driver goes here
#    dataHIPSTER = hipster_spi_ops.spiMaster(wrb,register,data)


#    if (verbose):
#        print "regOpHIPSTER:"
#        print "wrb: ",wrb
#        print "register: ",register
#        print "data: ",data
#        print "returned data: ",dataHIPSTER

#    return str(dataHIPSTER)
    
# read or write data from the fake HIPSTER
 
    if (wrb): # write op requested
        spiMap[register] = data
        if (register == CR):
            executeCRCommand()
        print "Writing ",data, " to Reg ",register&0x7FFF
        dataHIPSTER = 0xFFFF  # all FFFF indicates successful write
    else:  # read op requested
        dataHIPSTER = str(( (0x4000 | register) << 16) | spiMap[register])
        print "Read ", spiMap[register], " from Reg ",register
 
    if (verbose):
        print "dataHIPSTER = ",dataHIPSTER 

    return str(dataHIPSTER)      


def regOpDAC(dacID,data,verbose=True):
    """ writes to a DAC register via SPI
    """
    # strip off wrb bit from data and set to 0 (DAC8568 prefix bit)
    data = data & 0x7FFFFFFF
    if (dacID == 0): # send to DAC1
        pass
#        spi = spidev.SpiDev()    # create spi object
#        spi.open(0,0)  # open spi port 0, device (CS) 0
        # call to SPI driver goes here
    elif (dacID == 1): # send to DAC2
        pass
#        spi = spidev.SpiDev()    # create spi object
#        spi.open(0,1)  # open spi port 0, device (CS) 1
    
    # now split 32-bit word into a list of four bytes
    bytesToSend = 4*[0]
    bytesToSend[0] = (data >> 24) & 0xFF
    bytesToSend[1] = (data >> 16) & 0xFF
    bytesToSend[2] = (data >> 8) & 0xFF
    bytesToSend[3] = data & 0xFF
    #print "bytesToSend = ",bytesToSend
    # execute spi transaction (spi.xfer2 keeps 
    # CS asserted (low) between bytes)    
#        response = spi.xfer2(bytesToSend)
    response = 0
    if (verbose):
        print "regOpDAC:"
        print "dacID: ",dacID
        print "data: ",data
        print "data MSB: ",(data >> 16) & 0xFFFF,"data LSB: ",data & 0xFFFF
        print "returned data: ",response

def regOp5338(wrb,register,data,verbose=True):
    """ read or writes to a Si5338 register via I2C
        Si5338 7-bit slave address is 1110000
    """ 
    # call to I2C driver goes here
    deviceAddress = 0x70  # fixed I2C address for si5338
    
    # change address and data to 8 bits
    register = register & 0xFF
    data = data & 0xFF
    response = 0
    #bus = smbus.SMBus(1)
    if (wrb):  #do a write
        pass
     #   bus.write_byte_data(deviceAddress,register,data)
    else:  # do a read
        pass
      #  response = bus.read_byte_data(deviceAddress,register)
    if (verbose):
        print "regOp5338:"
        print "wrb: ",wrb
        print "register: ",register
        print "data: ",data
        print "response: ",response
    pass

#### this function is for HIPSTER emulation only
#### It is not used to test HIPSTER hardware


def executeCRCommand():
    """ function that writes to the emulated HIPSTER SPI
    This function is called with CR is written.  Ideally this would be
    event driven but would greatly complicate the emulation so this is 
    good enough.  Good practice is to write 0 to CR after completing a 
    command anyway.
    
    Registers 0 through 51 are simple registers
    Registers 51 - 54 are special
    Register 52 = Write Data Register (WDR)
    Register 53 = Command Register (CR)
    Register 54 = Mailbox Register
    See HIPSTER datasheet for a description of these special registers,
    their functions, and how to operate them
    
    The model of the CLRF is as follows.  There are 384 memory locations
    (24 ADCs, 8 calibrated stages/ADC, and 2 weights/stage)
    So, we use a 9-bit word to model the memory.
    5-bits for the ADC
    3 bits for the stage
    1 bit for the weight
    """
        
    global spiMap
    global clrf   #Correction Logic Register File internal to HIPSTER
    
    command = spiMap[CR]
    
    #first decode the SPI command so we know what to do
    whichWeight = (command & 0x0800) >> 11
    whichADC = (command & 0x01F0) >> 4
    whichStage = (command & 0x000F) 
    regOp = (command & 0x1000) >> 12
    wrb = (command & 0x8000) >> 15
    
    # only have to do anything if regOp is set
    if (regOp):
        whichReg = (whichADC << 4) | (whichStage << 1) | whichWeight
        if (wrb == 1):
           clrf[whichReg] = spiMap[WDR]
        else:
           spiMap[MBR] = clrf[whichReg] 
    # check other bits to check for errors
    if (command & 0x4000) >> 14:
        calibrateADC()
    if (command & 0x2000) >> 13:
        loadDefaultsToCorrectionLogic() 
    if (command & 0x0400) >> 10:
        readValueFromOffsetDAC()


