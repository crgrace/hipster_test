# -*- coding: utf-8 -*-
"""
Created on Wed Aug 5 18:26:37 2015

@author: CRGrace@lbl.gov
"""

"""
functions used to configure the Si5338 clock generator.
"""
from hipster_spi import serverOp
from hipster_spi import setBit
from hipster_spi import clearBit
from time import sleep

def configureSi5338(inputFile="reg5338.txt",verbose=False):
    """ configures the Si5338.  To do so it must follow the procedure on
    page 23 of the Si5338 manual (rev 1.5).  Basically it is a procedure to
    make sure the chip is off, then load the register map, then restart the
    output.  The register map can be calucated using the ClockBuilder Desktop
    software available from Silicon Labs.
    """
    
    maxWaitTime = 1  # max allowed setting wait is 1 second
    timeStep = 0.025 # wait 25 ms before polling status registers

    disableOutputs()
    pauseLOL()
    configMap = readConfigMapFromFile(inputFile)
    writeConfigMapTo5338(configMap)
    validateInputClock()
    configurePLLForLocking()
    initiateLockingOfPLL()
    sleep(0.025)
    restartLOL()
    confirmPLLLock(maxWaitTime,timeStep)
    copyFCALRegisters()
    enableOutputs()

def disableOutputs():
    # disable outputs
    writeRegister5338(230,setBit(readRegister5338(230),4))

def pauseLOL():
    # pause LOL
    writeRegister5338(241,setBit(readRegister5338(241),7))

def initiateLockingOfPLL():
    # initiate locking of PLL   
    writeRegister5338(246,setBit(readRegister5338(246),1))


def configurePLLForLocking():
    """ configures the Si5338 PLL
    """
    writeRegister5338(49,clearBit(readRegister5338(49),7))

def validateInputClock(maxWaitTime=1,timeStep=0.025):
    # validate input clock status
    inputClockValid = False
    timeWaiting = 0 
    while (inputClockValid == False):
        inputClockValid = isInputClockValid()
        sleep(timeStep)
        timeWaiting += timeStep
        if (timeWaiting > maxWaitTime):
            print "configure5338: input clock not valid"
            exit()

def isInputClockValid(verbose=False):
    # check input clock alarms in reg218
    # both loss of feedback clock input (reg218[3]) and 
    # loss of signal clock input (reg218[2]) should be low.
    # see page 24 of Si5338 datasheet (rev 1.5)
    statusRegister = readRegister5338(218)
    LOS_FDBK = (statusRegister >> 3) & 1
    LOS_CLKIN =  (statusRegister >> 2) & 1
    #if (LOS_FDBK or LOS_CLKIN):
    if (LOS_CLKIN):
        if (verbose):
            if (LOS_FDBK):
                print "Loss of Signal Feedback Input detected."
            if (LOS_CLKIN):
                print "Loss of Signal Clock Input detected."
        return False        
    else:
        return True

def restartLOL():
    # restart Loss-of-lock detector (LOS)
    oldRegister = readRegister5338(241)
    newRegister = clearBit(oldRegister,7)
    writeRegister5338(241,clearBit(readRegister5338(241),7))
    writeRegister5338(241,0x65)

def confirmPLLLock(maxWaitTime=1,timeStep=0.025):
    # confirm PLL lock status
    pllLock = False   
    timeWaiting = 0
    while (pllLock == False):
        # check PLL status register 
        # PLL is 
        pllLock = isPLLLocked()
        sleep(timeStep)
        timeWaiting += timeStep
        if (timeWaiting > maxWaitTime):
            print "configure5338: 5338 PLL did not lock"
            exit()

def isPLLLocked(verbose=False):
    # check PLL status register to see if PLL is locked
    # PLL is out of lock if PLL_LOL bit is high (reg218[4])
    # or if Lock Acquisition bit is high (reg218[0]) 
    # see page 24 of Si5338 datasheet (rev 1.5)
  
    statusRegister = readRegister5338(218)
    PLL_LOL = (statusRegister >> 4) & 1
    SysCal = statusRegister & 1
    if (PLL_LOL or SysCal):
        if (verbose):
            if (PLL_LOL):
                print "PLL Loss of Lock detected."
            if (SysCal): 
                print "System calibration not finished."
        return False
    else:
        return True

def copyFCALRegisters(): 
    # copy FCAL values to active registers
    # 237[1:0] to 47[1:0]
    # 236[7:0] to 46[7:0]
    # 235[7:0] to 45[7:0]
    # 47[7:2] = 000101b

    # start with 237
    # mask out bits 
    newBits = readRegister5338(237) & 0x03
    # write new reg 47 (setting 47[7:2] to 000101b
    writeRegister5338(47,(5 << 2) | newBits)
      
    # copy reg236 to reg46
    writeRegister5338(46,readRegister5338(236))
   
    # copy reg235 to reg45
    writeRegister5338(45,readRegister5338(235))
 
    # set PLL to FCAL values
    writeRegister5338(49,setBit(readRegister5338(47),7))

def enableOutputs():
    # enable Outputs
    writeRegister5338(230,clearBit(readRegister5338(230),4))

def registerOp5338(wrb,register,data):
    """ register operation for Si5338
    requires that the serverOp() function in hipster.py is available.
    the command is five bytes.  First byte is device ID and  
    indicates if it is a read or write and what device is requested.
    Bytes 2 and 3 are the 16-bit register address
    Bytes 4 and 5 are the 16-bit data word
    First bit of deviceID indicates read or write (write = 1, read = 0)

    deviceID :  device
    ----------------
        0    : HIPSTER
        1    | DAC 1
        2    | DAC 2
        3    | Si5338 clock generator

    """
    deviceID = 3
    if (wrb): 
        register = register | 0x8000
    message = str((deviceID << 32) | (register << 16) | data)
    print "registerOp5338:"
    print "wrb = ",wrb
    print "deviceID = ",deviceID
    print "register = ",register & 0x7FFF
    print "data = ",data

    return serverOp(message)

def readRegister5338(register,data=5555):
    """ register read from Si5338
    """
    wrb = 0
    return registerOp5338(wrb,register,data)
 
def writeRegister5338(register,data):
    """ register write from Si5338 using I2C
    """ 
    wrb = 1
    registerOp5338(wrb,register,data)

def readConfigMapFromFile(inputFile,verbose=False):
    """ read Si5338 configuration map from file.  The file structure is 
    very simple.  All comment lines start with #.  Each register number is
    followed by a comma and a hex value indicated by 'h'
    
    example file with two entries (reg1 = 0, reg2 = 0x31:
    # this is a comment line
    1,00h
    2,31h
    """
    try:
        f = open(inputFile)
    except IOError:
        print "Input file %s does not exist" %inputFile
	return

    configMap = 355*[0]
    for line in iter(f):
	print "config file line # = ",line
        if not (line.startswith("#")):
            register,word = line.split(',') 
            print type(register)
            print type(word)
            print register,word,word[:-1]
        # convert hex word to decimal, drop the trailing 'h', and write to map
            regValue = "0x"+word.split('h')[0]
            configMap[int(register)]  = int(regValue,16)
    f.close()
    return configMap

def writeConfigMapTo5338(configMap):
    """ dumps register map to Si5338
    """
    for command in range(0,len(configMap)):
        writeRegister5338(command,configMap[command])
