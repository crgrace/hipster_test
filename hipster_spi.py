# -*- coding: utf-8 -*-
"""
Created on Wed Aug 5 18:26:37 2015

@author: CRGrace@lbl.gov
"""
import sys, os, socket, time

NUMREGS = 54
MBR = 54  #mailbox register
CR = 53 #command register
WDR = 52 #write data register
DAC1 = 55 #MSBs in DAC1+1, LSBs in DAC1
DAC2 = 57 #MSBs in DAC2+1, LSBs in DAC2 

#bitmasks
#0x8000 = 32768  # used to set WRB bit in SPI command
#0x7FFF = 32767  # used to clear WRB bit in SPI command
#0x5555 = 21845  # used as dummy data in SPI reads
#0x4000 = 16384  # used to set Calibrate bit in CR
#0x1000 = 4096  # used to request CLRF op in CR 
#0x0002 = 2     # used to kickstart BGR
#0xFF7F = 65407 # used 
#0x0040 = 64

# HIPSTER configuration map is global variable
# there are two maps.  One is the emulated map in HIPSTER 
# called spiMap
spiMap = []
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


# cmd default values in decimal    
CMD_DEFAULTS = {'pga_bypass_preamp' : 0,
                'pga_hg' : 1,
                'pga_gain_sel' : 4,
                'offset_mode' : 3,
                'offset_dac_default' : 31,
                'offset_channel' : 0,
                'adc_bias_adj' : 7,
                'adc_comp_bias_adj' : 5,
                'adc_extern_reference' : 0,
                'adc_output_format' : 1,
                'cal_cycles' : 15,
                'calbits' : 3,
                'sso_adc_select' : 0,
                'sso_data_select' : 0,
                'sso_enable' : 0,
                'tx_bypass_eq' : 1,
                'eq_precursor_tap_sign' : 1,
                'eq_cursor_tap_sign' : 1,
                'eq_postcursor_tap_sign' : 1,
                'bypass_tap_ctrl0' : 7,
                'bypass_tap_ctrl1' : 7,
                'bypass_tap_ctrl2' : 7,
                'bypass_tap_ctrl3' : 7,
                'bypass_tap_ctrl4' : 7,
                'bypass_tap_ctrl5' : 7,
                'precursor_tap_ctrl0' : 0,
                'precursor_tap_ctrl1' : 0,
                'precursor_tap_ctrl2' : 0,
                'precursor_tap_ctrl3' : 0,
                'precursor_tap_ctrl4' : 0,
                'precursor_tap_ctrl5' : 0,
                'cursor_tap_ctrl0' : 0,
                'cursor_tap_ctrl1' : 0,
                'cursor_tap_ctrl2' : 0,
                'cursor_tap_ctrl3' : 0,
                'cursor_tap_ctrl4' : 0,
                'cursor_tap_ctrl5' : 0,
                'postcursor_tap_ctrl0' : 0,
                'postcursor_tap_ctrl1' : 0,
                'postcursor_tap_ctrl2' : 0,
                'postcursor_tap_ctrl3' : 0,
                'postcursor_tap_ctrl4' : 0,
                'postcursor_tap_ctrl5' : 0,
                'c1_select' : 131,
                'c2_select' : 3,
                'r1_select' : 5,
                'pll_cp_bias_adj' : 7,
                'clk_mon_sel' : 0,
                'bypass_vco' : 0,
                'observe_vctrl' : 0,
                'observe_pfd' : 0,
                'force_vctrl' : 0,
                'bypass_retimer' : 1,
                'ldo_output_select' : 2,
                'bias_readback' : 0,
                'bgr_kickstart' : 0,
                'master_bias_adj' : 8,
                'cml_bias_adj' : 8,
                'refbuffer_bias_adj' : 8,
                'testbuffer_ctrl' : 0,
                'pd_lvds_tx' : 0,
                'pd_testbuffer' : 1,
                'pd_precursor' : 1,
                'pd_cursor' : 1,
                'pd_postcursor' : 1,
                'pd_ldo' : 0,
                'pd_bgr' : 0,
                'pd_tx0' : 0,
                'pd_tx1' : 0,
                'pd_tx2' : 0,
                'pd_tx3' : 0,
                'pd_tx4' : 0,
                'pd_tx5' : 0,
                'pd_vcobuffer' : 0,
                'pd_readbackclk_mon' : 0,
                'pd_analog_channel0' : 0,
                'pd_analog_channel1' : 0,
                'pd_analog_channel2' : 0,
                'pd_analog_channel3' : 0,
                'pd_analog_channel4' : 0,
                'pd_analog_channel5' : 0,
                'pd_analog_channel6' : 0,
                'pd_analog_channel7' : 0,
                'pd_analog_channel8' : 0,
                'pd_analog_channel9' : 0,
                'pd_analog_channel10' : 0,
                'pd_analog_channel11' : 0,
                'pd_analog_channel12' : 0,
                'pd_analog_channel13' : 0,
                'pd_analog_channel14' : 0,
                'pd_analog_channel15' : 0,
                'pd_analog_channel16' : 0,
                'pd_analog_channel17' : 0,
                'pd_analog_channel18' : 0,
                'pd_analog_channel19' : 0,
                'pd_analog_channel20' : 0,
                'pd_analog_channel21' : 0,
                'pd_analog_channel22' : 0,
                'pd_analog_channel23' : 0,
                'jesd_numlanes' : 2,
                'jesd_ds_en' : 0,
                'jesd_cr_en' : 1,
                'jesd_bid' : 10,
                'jesd_did' : 86,
                'jesd_testmode' : 0,
                'jesd_datasel' : 0,
                'jesd_reset' : 0,
                'jesd_testval0' : 64,
                'jesd_testval1' : 128,
                'jesd_testval2' : 192,
                'jesd_testval3' : 256,
                'jesd_testval4' : 320,
                'jesd_testval5' : 384,
                'jesd_testval6' : 448,
                'jesd_testval7' : 512,
                'jesd_testval8' : 576,
                'jesd_testval9' : 640,
                'jesd_testval10' : 704,
                'jesd_testval11' : 768,
                'jesd_testval12' : 832,
                'jesd_testval13' : 896,
                'jesd_testval14' : 960,
                'jesd_testval15' : 1024,
                'jesd_testval16' : 1088,
                'jesd_testval17' : 1152,
                'jesd_testval18' : 1216,
                'jesd_testval19' : 1280,
                'jesd_testval20' : 1344,
                'jesd_testval21' : 1408,
                'jesd_testval22' : 1472,
                'jesd_testval23' : 1536,
                }   
        

# REG default values in decimal            
REG_DEFAULTS = [18,127,599,15,3,0,1,7,
                30583,30583,0,0,0,0,0,0,
                131,3,117,8704,34944,0,30,0,
                0,0,22186,0,64,128,192,256,
                320,384,448,512,576,640,704,768,
                832,896,960,1024,1088,1152,1216,1280,
                1344,1408,1472,1536]

# emulated HIPSTER spiMap for debugging purposes  
# the [0,0,0] are the three special registers (WDR, CR, and MBR)                  
spiMap = list(REG_DEFAULTS + [0,0,0])


def setBit(word,bit):
    """ sets a single bit in word.  Returns the word with that bit set.
        bit[0] is the LSB, so:
        setBit(word,0) would set the LSB (bit[0]) to one
    """
    mask = (1 << bit)
    return(word | mask)

def clearBit(word,bit):
    """ clears a single bit in word.  Returns the word with that bit cleared.
        bit[0] is the LSB, so:
        clearBit(word,0) would clear the LSB (bit[0]) to zero
    """
    mask = ~(1 << bit)
    return(word & mask)

def setBitInRegister(register,bit):
    """ sets a single bit in a HIPSTER register
    """
    oldCommand = readRegister(register)
    newCommand = setBit(oldCommand,bit)
    writeRegister(register,newCommand)

def clearBitInRegister(register,bit):
    """ clears a single bit in a HIPSTER register
    """
    oldCommand = readRegister(register)
    newCommand = clearBit(oldCommand,bit)
    writeRegister(register,newCommand)

def writeRegister(register,data,deviceID=0):
    """ writes 16-bit data to SPI register
    The serverOp command length is five bytes.  First byte is device ID and  
    indicates if it is a read or write and what device is requested.
    Bytes 2 and 3 are the 16-bit register address
    Bytes 4 and 5 are the 16-bit data word
    First bit of deviceID indicates read or write (write = 1, read = 0)
    Default device ID is 0 (HIPSTER)

    deviceID :  device
    ----------------
        0    : HIPSTER
        1    | DAC 1
        2    | DAC 2
        3    | Si5338 clock generator

    """

    # if this is a HIPSTER write, set WRB bit (set bit15 = 1) &
    # force bit 14 of SPI address = 1 is a kludge to deal with the
    # client not sending a fixed number of bytes when register 0 is
    # requested.  Yuck.
    spiCommand = (0xC000 | register) & 0xFFFF
    #print "writeRegisterTCPIP: spiCommand = ",spiCommand
    message = str((deviceID << 32) | (int(spiCommand) << 16) | int(data & 0xFFFF))
    serverOp(message)

def readRegister(register,data=5555,deviceID=0):
    """ reads 16-bit data from SPI register
    The serverOp command length is five bytes.  First byte is device ID and  
    indicates if it is a read or write and what device is requested.
    Bytes 2 and 3 are the 16-bit register address
    Bytes 4 and 5 are the 16-bit data word
    First bit of deviceID indicates read or write (write = 1, read = 0)
    Default device ID is 0 (HIPSTER)
    """
    # force bit 14 of SPI address = 1 is a kludge to deal with the
    # client not sending a fixed number of bytes when register 0 is
    # requested.  Yuck.

    message = str(((deviceID << 32) | (0x4000 | register) << 16) | int(data & 0xFFFF))
    dataHIPSTER = serverOp(message) 
    ##print "readRegister: ",dataHIPSTER, "hex:",format(dataHIPSTER,'#04x')
    return int(dataHIPSTER)

def dumpRegister(register,deviceID=0):
    """ reads 16-bit data from device and displays on screen
    """
    dataHIPSTER = readRegister(register)
    print "dumpRegister: ",dataHIPSTER, "hex:",format(dataHIPSTER,'#04x')
     
def serverOp(message,serverName="hipster-pi2.dhcp.lbl.gov",port=50000,verbose=False):
#def serverOp(message,serverName="131.243.115.189",port=50000,verbose=False):
#def serverOp(message,serverName="localhost",port=50000,verbose=False):
    """The serverOp command length is five bytes.  First byte is device ID and  
    indicates if it is a read or write and what device is requested.
    Bytes 2 and 3 are the 16-bit register address
    Bytes 4 and 5 are the 16-bit data word
    """
    if (verbose): print "serverOp: message sent = ",message
    # Create a TCP/IP socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # Bind the socket to the address given to the function
    # Then send the message and close the connection
    
    serverAddress = (serverName, port)
    if (verbose): print "serverAddress = ",serverAddress

    try:
        sock.connect(serverAddress)
        sock.sendall(message)
        amountReceived = 0
        amountExpected = len(message)  
        if (verbose): print "amountExpected = ",amountExpected
        while amountReceived < amountExpected:
            dataReceived = sock.recv(16)
            if (verbose): print "Data Received = ",dataReceived
            amountReceived += len(dataReceived)
            if (verbose): print "amountReceived = ",amountReceived

        if (verbose): print "Data Received = ",dataReceived
    finally:
        sock.close()
    
    data = int(dataReceived) & 0xFFFF 
    return data

def calibrateADC():
    """executes calibration command.  It does so in two steps.
    1.  Load Command Register with calibration enabled
    3.  Clear Command Register
    """
    writeRegister(CR,0x4000)
    writeRegister(CR,0)  # clear command register

    
def loadValueToCorrectionLogic(adc,stage,weight,value):    
    """loads data value into Correction Logic register file (CLRF)
    It does this in three steps.
    1.  Load data we wish to write into Write Data Register (WDR)
    2.  Load Command Register with ADC, Stage, and Weight we wish to write
    3.  Clear Command Register  
    """
    command = 0x9000 | 0x1000 | stage | (adc << 4) | (weight << 11) 
    writeRegister(WDR,value)
    writeRegister(CR,command)   # execute CLRF load
    writeRegister(CR,0)  # clear command register
    
def readValueFromCorrectionLogic(adc,stage,weight):
    """reads data value from Correction Logic register file (CLRF)
    It does this in three steps.
    1.  Load Command Register with ADC, Stage, and Weight we wish to read
    3.  Clear Command Register
    3.  Read back requested value from Mailbox Register
    """    
    command = 0x1000 | stage | (adc << 4) | (weight << 11) 
    writeRegister(CR,command)  # execute CLRF read
    writeRegister(CR,0) # clear command register
    return readRegister(MBR)

def dumpCorrectionLogic(whichADC):
    """ Dumps contents of CLRF for specific ADC
    """
    print "CLRF Dump"
    print "ADC   Stage   Weight   Value"
    print "---------------------------"    
    for stage in range(0,8):
        for weight in (0,1):
            value = readValueFromCorrectionLogic(whichADC,stage,weight)
            if (weight == 0):
                whichWeight = "w0"
            else:
                whichWeight = "w2"
            print whichADC,"   ",stage,"     ",whichWeight,"     ",value
            
def restoreDefaultsToCorrectionLogic():
    """restores Correction Logic register file (CLRF) to default values
    Applying a hardware reset to HIPSTER does this as well
    The defaults are loaded into the CLRF in two steps.
    1. Load Command Register with Load Default request bit set
    2. Clear Command Register
    """
    command = 0x2000    
    writeRegister(CR,command)
    writeRegister(CR,0) # clear command register 

def testCLRF(verbose=False):
    """ Tests Correction Logic Register File using MATS++ algorithm
    MATS stands for Modified Algorithmic Test Sequence
    The algorithm checks each register for the following faults:
    sticky 0, sticky 1, failed 0->1 transition and failed 1->0 transition.
    Walks up and then back down the register file.
    There are 24 ADCs.  Each ADC has 8 calibrated stages.  Each stage
    has 2 weights.
    After testing you must restore the defaults to the CLRF by
    executing the restoreDefaultsToCorrectionLogic() function.
    Otherwise calibration will fail.
    """

    errors = 0
    softReset()
    for adc in range(0,24):
        for stage in range(0,8):
            for weight in (0,1):
                loadValueToCorrectionLogic(adc,stage,weight,0)
                
    for adc in range(0,24):
        for stage in range(0,8):
            for weight in (0,1):
                if (readValueFromCorrectionLogic(adc,stage,weight) != 0):
                    print "testCLRF: CLRF error (1st pass). Expected 0"
                    errors += 1
                loadValueToCorrectionLogic(adc,stage,weight,0xFFFF)
                
    for adc in range(23,-1,-1):
        for stage in range(7,-1,-1):
            for weight in (1,0):
                if (readValueFromCorrectionLogic(adc,stage,weight) != 0xFFFF):
                    print "testCLRF: CLRF error. Expected 0xFFFF"
                    errors = +1
                loadValueToCorrectionLogic(adc,stage,weight,0)

    for adc in range(0,24):
        for stage in range(0,8):
            for weight in (0,1):
                if (readValueFromCorrectionLogic(adc,stage,weight) != 0):
                    print "testCLRF: CLRF error (2nd pass). Expected 0"
                    errors += 1

    if (errors != 0):
        print "testCLRF: CLRF test failed.  There were ",errors," errors."
    else:
        if (verbose): print "testCLRF: CLRF test passed."  
    restoreDefaultsToCorrectionLogic()

def testSPI(verbose=False):
    """ Tests SPI registers using MATS++ algorithm
    MATS stands for Modified Algorithmic Test Sequence
    The algorithm checks each register for the following faults:
    sticky 0, sticky 1, failed 0->1 transition and failed 1->0 transition.
    Walks up and then back down the register file.

    The algorithm is modifed here to ensure that HIPSTER is not put into 
    a high-current state.  To get arround this we will do two tests.  In the
    first one we will hold the master_bias to minimum (by writing 0xFFFF) to
    register 20.  In the second we will test register 20 alone with all other
    registers set to 0xFFFF.
    """

    errors = 0
    softReset()
    if (verbose): 
        print "VERBOSEMODE"
    # put SPI in low-current state
    writeRegister(20,0xFFFF)
    
    for register in range(0,52): 
        if (register == 20):
            continue
        writeRegister(register,0)

    for register in range(0,52): 
        if (verbose): print "register = ",register,"[register] = ",readRegister(register)
        if (register == 20):
            continue
        if (readRegister(register) != 0):
            print "testSPI: SPI error (1st pass). Expected 0."
            errors += 1
        writeRegister(register,0xFFFF)           

    for register in range(51,-1,-1): 
        if (register == 20):
            continue
        if (readRegister(register,verbose) != 0xFFFF):
            print "testSPI: SPI error. Expected 0xFFFF."
            errors += 1
        writeRegister(register,0)    

    for register in range(0,52): 
        if (register == 20):
            continue
        if (readRegister(register) != 0):
            print "testSPI: SPI error (2nd pass). Expected 0."
            errors += 1
        writeRegister(register,0xFFFF)  

    # now test register 20 as other registers are in low-current stage
    writeRegister(20,0)
    if (readRegister(20) != 0):
        print "testSPI: SPI register 20 error (1st pass). Expected 0"
        errors += 1
    writeRegister(20,0xFFFF)       
    if (readRegister(20) != 0xFFFF):
        print "testSPI: SPI register 20 error. Expected 0xFFFF"
        errors += 1
    writeRegister(20,0)
    if (readRegister(20) != 0):
        print "testSPI: SPI register 20 error (2nd pass). Expected 0"
        errors += 1
    writeRegister(20,0xFFFF)   #leave SPI in low-current state

    if (errors != 0):
        print "testSPI: SPI test failed.  There were ",errors," errors."
    else:
        if (verbose): print "testSPI: SPI test passed."  
        
def readValueFromOffsetDAC():
    """reads out Offset DAC value 
    It does this is three steps.
    1.  Load Command Register with Offset DAC access request bit set
    2.  Clear Command Register
    3.  Read back requested value from Mailbox Register
    """
    command = 0x0400
    writeRegister(CR,command)
    writeRegister(CR,0) # clear command register    
    return readRegister(MBR)    

def powerDownTX(whichTX):
    """ powers down a TX driver
        usage: powerDownTX(<whichTX>). which TX from 0 to 5.
    """

    if (whichTX < 0) or (whichTX > 5):
        print "powerDownTX: Range Error.  TX out of range."
        print "usage: powerDownTX(<whichTX>). whichTX from 0 to 5"
    else:
        setBitInRegister(22,whichTX+8)

def powerDownAllTXs():
    """ powers down all TXs
    """

    for whichTX in range(0,6):
        powerDownTX(whichTX)

def powerUpTX(whichTX):
    """ powers up a TX driver specified by whichTX
        usage: powerUpTX(<whichTX>). which TX from 0 to 5.
    """

    if (whichTX < 0) or (whichTX > 5):
        print "powerUpTX: Range Error.  TX out of range."
        print "usage: powerUpTX(<whichTX>). whichTX from 0 to 5"
    else:
        clearBitInRegister(22,whichTX+8)

def powerUpAllTXs():
    """ powers up all TXs
    """

    for whichTX in range(0,6):
        powerUpTX(whichTX)

def powerDownADC(whichADC):
    """ powers down an ADC 
        print "usage: powerDownADC(<whichADC>).  whichADC from 0 to 23"
    """

    if (whichADC < 0) or (whichADC > 23):
        print "powerDownADC: Range Error.  ADC out of range."
        print "usage: powerDownADC(<whichADC>).  whichADC from 0 to 23"
    else:
        if (whichADC < 16):
            # ADCs 0 through 15 in SPI register 23
            setBitInRegister(23,whichADC)
        else:
            # ADCs 16 through 23 in SPI register 24
            setBitInRegister(24,whichADC-16)

def powerDownAllADCs():
    """ powers down all ADCs
    """
    for whichADC in range(0,24):
        powerDownADC(whichADC)

def powerUpADC(whichADC):
    """ powers up an ADC
        print "usage: powerUpADC(<whichADC>).  whichADC from 0 to 23"
    """

    if (whichADC < 0) or (whichADC > 23):
        print "powerUpADC: Range Error.  ADC out of range."
        print "usage: powerUpADC(<whichADC>).  whichADC from 0 to 23"
    else:
        if (whichADC < 16):
            # ADCs 0 through 15 in SPI register 23
            clearBitInRegister(23,whichADC)
        else:
            # ADCs 16 through 23 in SPI register 24
            clearBitInRegister(23,whichADC-16)

def powerUpAllADCs():
    """ powers up all ADCs
    """
    for whichADC in range(0,24):
        powerUpADC(whichADC)

def disableTestBuffer():
    """ disables the testbuffer. 
    """
    
    setBitInRegister(22,1)

def enableTestBuffer():
    """ enables the testbuffer. 
    """
    
    clearBitInRegister(22,1)

def enableInternalReferences():
    """ enables internal ADC references. 
    """

    clearBitInRegister(2,8)    

def configureTestBuffer(whichSignal):    
    """ configures the analog testbuffers.
    """
    if (whichSignal == "BGR_AFE"):
        command = 0
    elif (whichSignal == "VREF_P"):
        command = 1
    elif (whichSignal == "VREF_N"):
        command = 2
    elif (whichSignal == "VCM"):
        command = 3
    elif (whichSignal == "VTH_P"):
        command = 4
    elif (whichSignal == "VTH_N"):
        command = 5
    elif (whichSignal == "VMASTERBIAS"):
        command = 6
    else:
        print("configureTestBuffer: Test buffer signal unknown.")
        print("Valid inputs are: \"BGR_AFE\" \"VREF_P\" \"VREF_N\" \
        \"VCM\" \"VTH_P\"\ \"VTH_N\" \"VMASTERBIAS\" ")
    writeRegister(21,command) 

def readbackBias(whichSignal):
    """ configures the bias readback
        The current selected here will be sent to I_AFE for the AFE
        or I_TX for the TX 

        Available readback currents:
        MASTER: HIPSTER master bias current
        ADC: ADC bias current
        CML_50U: CML bias current (actual current is 8X this value)
        REFBUFFER: ADC Reference Buffer bias current
        PLL_CP: PPLL charge pump current
    """
    #print "whichSignal = ", whichSignal
    oldCommand = readRegister(20)  # bias_readback is bits 1:0 of reg 20  
    if (whichSignal == "MASTER"): 
        command = 0
    elif (whichSignal == "ADC") or (whichSignal == "CML_50U"):  
        command = 1
    elif (whichSignal == "REFBUFFER") or (whichSignal == "PLL_CP"):
        command = 3
    else:
        print("readbackBias: bias readback signal unknown.")
        print("Valid inputs are: \"MASTER\" \"ADC\" \"CML_50U\" \
        \"REFBUFFER\" \"PLL_CP\" ")

    newCommand = (oldCommand & 0xFFFC) | command
    writeRegister(20,newCommand)

def setBias(whichBias,value):
    """ configures the various bias blocks
    """
    
    if (value > 15):
        print "setBias: Error. Input value must be less than 16)"
        print "Bias not set"
        return

    oldCommand = readRegister(20)
    if (whichBias == "MASTER"):
        newCommand = (oldCommand & 0xFF0F) | (value << 4)
    elif (whichBias == "CML"):
        newCommand = (oldCommand & 0XF0FF) | (value << 8)
    elif (whichBias == "REFBUFFER"):
        newCommand = (oldCommand & 0x0FFF) | (value << 12)
    else:
        print("setBias: bias destination unknown.  Bias not set.")
        print("Valid inputs are: \"MASTER\" \"CML\" \"REFBUFFER\" ")
        return

    writeRegister(20,newCommand)
        
def setADCBias(whichBias,value):
    """ configures the ADC bias current
        ADC bias current is master_bias current * ADC setting 
        (see datasheet)
    """

    if (value > 15):
        print "setADCBias: Error. Input value must be less than 16)"
        print "Bias not set"
        return

    oldCommand = readRegister(2)

    if (whichBias == "ADC"):
        newCommand = (oldCommand & 0xFFF0) | value
    elif (whichBias == "COMP"):
        newCommand = (oldCommand & 0XFF0F) | (value << 4)
    else:
        print("setADCBias: bias destination unknown.  Bias not set.")
        print("Valid inputs are: \"ADC\" \"COMP\" \"REFBUFFER\" ")
        return

    writeRegister(2,newCommand)

def setBiasPLL(value):
    """ configures the PLL charge pump current
        PLL current is master_bias current * PLL setting
        (see datasheet)
    """

    if (value > 15):
        print "setPLLBias: Error. Input value must be less than 16)"
        print "Bias not set"
        return

    oldCommand = readRegister(18)
    newCommand = (oldCommand & 0XFF0F) | (value << 4)
    writeRegister(18,newCommand)

def kickstartBGR():
    """forces HIPSTER to restart the BGR.  This will only be
    needed if the BGR startup circuit fails.
    Since the SPI registers are not self clearing, this function
    must both assert and remove the BGR reset
    Care must also be taken not to change the static configuration.
    To do this, the function first reads back the Register setting 
    and only modifies the BGR kickstart bit.
    """
    
    oldCommand = readRegister(20)  # bgr kickstart is bit 2 of reg 20
    newCommand = setBit(oldCommand,2)
    writeRegister(20,newCommand)
    writeRegister(20,oldCommand)

def kickstartPLL(vctrl=0.8):
    """ kickstarts the PLL by forcing and then removing force
    """

    setDAC("VCTRL",vctrl)
    #force PLL control voltage
    setBitInRegister(19,8)
    #remove force
    clearBitInRegister(19,8)

def lockPLL():
    """ performs operations to lock HIPSTER PLL.  This function does
    the following:
    1. disables internal bandgap
    2. enables external DAC and sets it to voltage that constrains the 
        VCO to slower speeds than the feedback divider
    3. raises bandgap voltage to nominal in small steps to keep PLL in lock
    """
    
    # disable internal BGR
    setBitInRegister(22,6)        

    enableDACs()
    setDAC("BGR_AFE",0.01)
    setDAC("BGR_TX",1.0)
    for bgrValue in (1.0,1.05,1.1,1.15,1.2,1.23):
        time.sleep(0.01)
        setDAC("BGR_TX",bgrValue)
    setDAC("BGR_AFE",1.23)
    setDAC("BGR_TX",1.23)


def observeVCTRL(disable=False):
    
    if (disable):
        clearBitInRegister(19,2)
    else:
        setBitInRegister(19,2)

def forceVCTRL(value=1.0):
    
    setDAC("VCTRL",value)
    setBitInRegister(19,8)

def unforceVCTRL():
    
    clearBitInRegister(19,8)
def softReset():
    """ forces the JESD204B interface to reset.  This
    should be used when testing the CLRF.  This could also be useful
    if there is an issue with the PLL Lock Detect signal.
    Since the SPI registers are not self clearing, this function
    must both assert and remove the soft reset.
    Care must also be taken not to change the static configuration.
    To do this, the function first reads back the Register setting 
    and only modifies the JESD reset bits
    Reg 27<7:6> = 01 to assert
    Reg 27<7:6> = 10 to deassert
    """
    oldCommand = readRegister(27) # jesd reset is bits 7:6 of reg 27
    newCommand = setBit(oldCommand,6)  # assert reset
    writeRegister(27,newCommand)
    newCommand = clearBit(setBit(oldCommand,7),6)
    writeRegister(27,newCommand) # deassert reset
    writeRegister(27,oldCommand) # restore original setting

def enableDACs(verbose=False):
    """ the DAC8568 needs the internal reference started after reset
        The internal reference is powered on with 0x08000001
        The function enables internal references on both DACs
	This function also puts DACs in software LDAC mode so the outputs
	will be updated as soon as new data is received
    """
    
    # the DAC uses 32-bit commands.  To keep the communications to 16-bits
    # we send the top 16 bits in one write and the bottom 16 bits in a second 
    
    commandBits = 8
    DACcommand = (commandBits << 24) | 1 #bit F0 = 1 
    DACcommand_MSB = (DACcommand >> 16) & 0xFFFF
    DACcommand_LSB = DACcommand & 0xFFFF
    writeRegister(DACcommand_MSB,DACcommand_LSB,1)
    writeRegister(DACcommand_MSB,DACcommand_LSB,2)
    # now put DACs in software LDAC mode
    commandBits = 0x1800
    DACcommand = (commandBits << 16) | 0xFF
    DACcommand_MSB = (DACcommand >> 16) & 0xFFFF
    DACcommand_LSB = DACcommand & 0xFFFF
    writeRegister(DACcommand_MSB,DACcommand_LSB,1)
    writeRegister(DACcommand_MSB,DACcommand_LSB,2)
    if (verbose):
        print "DACcommand = ",DACcommand
        print "DACcommand_MSB (register) = ",DACcommand_MSB
        print "DACcommand_LSB (data) = ",DACcommand_LSB


def selectDAC(whichDAC):
    """ lookup table to determine which physical DAC and which channel
    should be selected
    The two DACs are:
    
    DAC1:
    A: VREF_N -- HIPSTER ADC negative reference voltage
    B: OFFSET_BOT -- Bottom voltage for Offset DAC
    C: VREF_P -- HIPSTER ADC positive reference voltage
    D: OFFSET_TOP -- Top voltage for Offset DAC
    E: VTH_N -- HIPSTER ADC negative comparator threshold voltage
    F: ADC_1 -- ADC input voltage 1.  Drives J9(1-12) and J13(1-12)
    G: VTH_P -- HIPSTER ADC negative comparator threshold voltage
    H: ADC_2 -- ADC input voltage 2.  Drives J14(1-12) and J17(1-12)

    
    DAC2:
    B: VCM -- HIPSTER ADC common-mode voltage
    F: BGR_AFE -- bandgap reference voltage for front end
    H: BGR_TX -- bandgap reference voltage for TX section
    D: VCTRL -- Driven VCO control voltage for PLL eval

    """

    if (whichDAC == "VREF_N"):
        (DAC, channel) = 1, 0                
    elif (whichDAC == "OFFSET_BOT"):
        (DAC, channel) = 1, 1
    elif (whichDAC == "VREF_P"):
        (DAC, channel) = 1, 2
    elif (whichDAC == "OFFSET_TOP"):
        (DAC, channel) = 1, 3
    elif (whichDAC == "VTH_N"):
        (DAC, channel) = 1, 4
    elif (whichDAC == "ADC_1"):
        (DAC, channel) = 1, 5
    elif (whichDAC == "VTH_P"):
        (DAC, channel) = 1, 6
    elif (whichDAC == "ADC_2"):
        (DAC, channel) = 1, 7
    elif (whichDAC == "VCM"):
        (DAC, channel) = 1, 0
    elif (whichDAC == "BGR_AFE"):
        (DAC, channel) = 2, 5
    elif (whichDAC == "BGR_TX"):
        (DAC, channel) = 2, 7
    elif (whichDAC == "VCTRL"):
        (DAC, channel) = 2, 3
    else:
        print "setDAC: Error.  ",DAC," is invalid DAC ID."
        print "usage: available DACs are: \"VREF_P\" \"VREF_N\" \"VTH_P\" \"VTH_N\" \"VCM\" \"OFFSET_TOP\" \"OFFSET_BOT\" \"BGR_AFE\" \"BGR_TX\" \"VCTRL\" \"ADC_1\" \"ADC_2\" "
        return
    return DAC, channel


def setDAC(whichDAC,desiredVoltage,verbose=False):
    """ sets output of test DACs on HIPSTER eval board
    The eval board includes two octal 16-bit DACs (part number DAC8568)
    for a total of 16 DACs, 12 of which are actually used.
    
    The output voltage of the DACs is:
    Vout = (data/2^16)*Vref*1.2 (Vref=2.5 when internal reference used)
    The 1.2 comes from additional gain on the board added to extend the DAC
    range beyond 2.5 V.
    The DACs themselves are identified by their names in the board sch
    The DAC Register is:
        31 : 0
        30:28 : X
        27:24 : commands (set to 0011 to update DAC on each register load)
        23    : broadcast mode (set to 0)
        22:20 : DAC select (1 of 8)
        19:4  : 16-bit data word
        3:0   : function bits (X)
    """
    if (verbose): print "desiredVoltage = ",desiredVoltage
    if not(0 < desiredVoltage < 3):
        print "setDAC: error.  Voltage out of range (0 - 3 V)."   

    DAC, channel = selectDAC(whichDAC)

    # vout = (data/2^16)*2.5
    if (whichDAC == "VREF_P"):
        data = int(round(65536*desiredVoltage/(2.5*1.2)))
    else:
        data = int(round(65536*desiredVoltage/2.5))
    
    #build 32-bit DAC word
    commandBits = 3 # updates DAC channel on each register load
    
    # the DAC uses 32-bit commands.  To keep the communications to 16-bits
    # we send the top 16 bits in one write and the bottom 16 bits in a second 
    DACcommand = (commandBits << 24) | (channel << 20) | (data << 4)
    if (verbose):
        print "data = ",data	
        print "channel = ",channel
        print "DACcommand = ",DACcommand
    DACcommand_MSB = (DACcommand >> 16) & 0xFFFF
    DACcommand_LSB = DACcommand & 0xFFFF
    writeRegister(DACcommand_MSB,DACcommand_LSB,DAC)

def setDACRaw(whichDAC,data):
    """ sets output of test DAC8568s on HIPSTER eval board directly
    with a 16-bit word (rather than a desired voltage)
    see setDAC() for an explanation of the command register
    """
   
    DAC, channel = selectDAC(whichDAC)
    commandBits = 3 # updates DAC channel on each register load
    
    # the DAC uses 32-bit commands.  To keep the communications to 16-bits
    # we send the top 16 bits in one write and the bottom 16 bits in a second 
    DACcommand = (commandBits << 24) | (channel << 20) | (data << 4)
    DACcommand_MSB = (DACcommand >> 16) & 0xFFFF
    DACcommand_LSB = DACcommand & 0xFFFF
    writeRegister(DACcommand_MSB,DACcommand_LSB,DAC)
    

def setDACsToDefaults():
    """ sets output of test DACs on HIPSTER eval board to their default
    values.  The defaults values are as follows:
    VBG = 1.23
    VREF_P = 2.5
    VTH_P = 1.9375
    VCM = 1.75
    VTH_N = 1.5625
    VREF_N = 1.0
    OFFSET_TOP = 1.0
    OFFSET_BOT = 0.5
    """
    setDAC("BGR_AFE",1.23)
    setDAC("BGR_TX",1.23)
    setDAC("VREF_P",2.5)
    setDAC("VTH_P",1.9375)
    setDAC("VCM",1.75)
    setDAC("VTH_N",1.5625)
    setDAC("VREF_N",1.0)
    setDAC("OFFSET_TOP",1.0)
    setDAC("OFFSET_BOT",0.5)

def configureSSO(whichADC,dataSelect=1):
    """ configures the SSO
        whichADC selects which ADC to read out (0 - 23)
        dataSelect = 0 --> raw decisions, dataSelect = 1 --> ADC data
    """
    Command = 0x8000 | dataSelect << 6 | whichADC 
    writeRegister(22,Command)
 
def enableSSO():
    """ enables the SSO
    """
    setBitInRegister(5,7)
    
def disableSSO():
    """ disables the SSO
    """
    clearBitInRegister(5,7)

def powerDownHIPSTER():
    """ fully powers down HIPSTER
    """ 
    
    writeRegister(20,0xFFFF)
    writeRegister(22,0xFFFF)

def make_bin_from_int(a):
    '''returns a 16-bit string calculated from integer argument'''
    assert isinstance(a,int),'Only integers can be converted'
    assert a >= 0,'Input value must be positive'
    assert a < 2**16,'Only 16-bit integers are allowed'
    s = []
    for i in range(0, 16):
        s.append((a >> (15-i)) % 2)
 
    return ''.join(str(e) for e in s)       

def test_make_bin_from_int():
    """test max, min, and a random value in between"""
    assert make_bin_from_int(0) == '0000000000000000'
    assert make_bin_from_int(65535) == '1111111111111111'
    assert make_bin_from_int(3) == '0000000000000011'
    print "max_bin_from_test() passes all tests"
    return

def buildConfigMap(reg,cmd):
    reg.append(cmd['pga_bypass_preamp'] | (cmd['pga_hg'] << 1) | (cmd['pga_gain_sel'] << 2))
    reg.append(cmd['offset_mode'] | (cmd['offset_dac_default'] << 2) | (cmd['offset_channel'] << 8))
    reg.append(cmd['adc_bias_adj'] | cmd['adc_comp_bias_adj'] << 4 | cmd['adc_extern_reference'] << 8 | cmd['adc_output_format'] << 9)
    reg.append(cmd['cal_cycles'])
    reg.append(cmd['calbits'])
    reg.append(cmd['sso_adc_select'] | cmd['sso_data_select'] << 6 | cmd['sso_enable'] << 7)
    reg.append(cmd['tx_bypass_eq'])
    reg.append(cmd['eq_precursor_tap_sign'] | cmd['eq_cursor_tap_sign'] << 1 | cmd['eq_postcursor_tap_sign'] << 2)
    reg.append(cmd['bypass_tap_ctrl0'] | cmd['bypass_tap_ctrl1'] << 4 | cmd['bypass_tap_ctrl2'] << 8 | cmd['bypass_tap_ctrl3'] << 12)    
    reg.append(cmd['bypass_tap_ctrl4'] | cmd['bypass_tap_ctrl5'] << 4 | (119 << 8) )  # unused additional 77 in SPI map
    reg.append(cmd['precursor_tap_ctrl0'] | cmd['precursor_tap_ctrl1'] << 4 | cmd['precursor_tap_ctrl2'] << 8 | cmd['precursor_tap_ctrl3'] << 12)    
    reg.append(cmd['precursor_tap_ctrl4'] | cmd['precursor_tap_ctrl5'] << 4 )
    reg.append(cmd['cursor_tap_ctrl0'] | cmd['cursor_tap_ctrl1'] << 4 | cmd['cursor_tap_ctrl2'] << 8 | cmd['cursor_tap_ctrl3'] << 12)    
    reg.append(cmd['cursor_tap_ctrl4'] | cmd['cursor_tap_ctrl5'] << 4 )
    reg.append(cmd['postcursor_tap_ctrl0'] | cmd['postcursor_tap_ctrl1'] << 4 | cmd['postcursor_tap_ctrl2'] << 8 | cmd['postcursor_tap_ctrl3'] << 12)    
    reg.append(cmd['postcursor_tap_ctrl4'] | cmd['postcursor_tap_ctrl5'] << 4 )
    reg.append(cmd['c1_select'])
    reg.append(cmd['c2_select'])
    reg.append(cmd['r1_select'] | cmd['pll_cp_bias_adj'] << 4)
    reg.append(cmd['clk_mon_sel'] | cmd['bypass_vco'] << 1 | cmd['observe_vctrl'] << 2 | cmd['observe_pfd'] << 4 | cmd['force_vctrl'] << 8 | cmd['bypass_retimer'] << 9 | cmd['ldo_output_select'] << 12)
    reg.append(cmd['bias_readback'] | cmd['bgr_kickstart'] << 2 | cmd['master_bias_adj'] << 4 | cmd['cml_bias_adj'] << 8 | cmd['refbuffer_bias_adj'] << 12)
    reg.append(cmd['testbuffer_ctrl'])
    reg.append(cmd['pd_lvds_tx'] | cmd['pd_testbuffer'] << 1 | cmd['pd_precursor'] << 2 | cmd['pd_cursor'] << 3 | cmd['pd_postcursor'] << 4 | cmd['pd_ldo'] << 5 | cmd['pd_bgr'] << 6 | cmd['pd_tx0'] << 8 | cmd['pd_tx1'] << 9 | cmd['pd_tx2'] << 10 | cmd['pd_tx3'] << 11 | cmd['pd_tx4'] << 12 | cmd['pd_tx5'] << 13 | cmd['pd_vcobuffer'] << 14 | cmd['pd_readbackclk_mon'] << 15)
    reg.append(cmd['pd_analog_channel0'] | cmd['pd_analog_channel1'] << 1 | cmd['pd_analog_channel2'] << 2 | cmd['pd_analog_channel3'] << 3 | cmd['pd_analog_channel4'] << 4 | cmd['pd_analog_channel5'] << 5 | cmd['pd_analog_channel6'] << 6 | cmd['pd_analog_channel7'] << 7 | cmd['pd_analog_channel8'] << 8 | cmd['pd_analog_channel9'] << 9 | cmd['pd_analog_channel10'] << 10 | cmd['pd_analog_channel11'] << 11 | cmd['pd_analog_channel12'] << 12 | cmd['pd_analog_channel13'] << 13 | cmd['pd_analog_channel14'] << 14 | cmd['pd_analog_channel15'] << 15)
    reg.append(cmd['pd_analog_channel16'] | cmd['pd_analog_channel17'] << 1 | cmd['pd_analog_channel18'] << 2 | cmd['pd_analog_channel19'] << 3 | cmd['pd_analog_channel20'] << 4 | cmd['pd_analog_channel21'] << 5 | cmd['pd_analog_channel22'] << 6 | cmd['pd_analog_channel23'] << 7)
    reg.append(0)  # unused SPI command (still need to account for it)
    reg.append(cmd['jesd_numlanes'] | cmd['jesd_ds_en'] << 2 | cmd['jesd_cr_en'] << 3 | cmd['jesd_bid'] << 4 | cmd['jesd_did'] << 8)
    reg.append(cmd['jesd_testmode'] | cmd['jesd_datasel'] << 4 | cmd['jesd_reset'] << 6)
    reg.append(cmd['jesd_testval0'])
    reg.append(cmd['jesd_testval1'])
    reg.append(cmd['jesd_testval2'])
    reg.append(cmd['jesd_testval3'])
    reg.append(cmd['jesd_testval4'])
    reg.append(cmd['jesd_testval5'])
    reg.append(cmd['jesd_testval6'])
    reg.append(cmd['jesd_testval7'])
    reg.append(cmd['jesd_testval8'])
    reg.append(cmd['jesd_testval9'])
    reg.append(cmd['jesd_testval10'])
    reg.append(cmd['jesd_testval11'])
    reg.append(cmd['jesd_testval12'])
    reg.append(cmd['jesd_testval13'])
    reg.append(cmd['jesd_testval14'])
    reg.append(cmd['jesd_testval15'])
    reg.append(cmd['jesd_testval16'])
    reg.append(cmd['jesd_testval17'])
    reg.append(cmd['jesd_testval18'])
    reg.append(cmd['jesd_testval19'])
    reg.append(cmd['jesd_testval20'])
    reg.append(cmd['jesd_testval21'])
    reg.append(cmd['jesd_testval22'])
    reg.append(cmd['jesd_testval23'])    
    return reg

def outputCommand(mode,reg,command):
    """sends formatted command to std out"""
    
    if (mode == 1):
        outstring = "spi_master(WRITE,%d,16'b%s)" %(reg,make_bin_from_int(command))
    else:
        outstring = "REG %d, command = %d" %(reg,command)
        
    print outstring      
    
def printMessage(message):
    print message
    
def dumpConfigMap():
    """ prints out the configMap to screen 
    configMap is the host's copy of the map inside HIPSTER
    """    
    
    global configMap
    for reg in range(0,len(configMap)):
        print "dumpConfigMap: Reg = ",reg," Data = ",configMap[reg]

def dumpSpiMap(fileName="SpiMapDump.txt",verbose=False):
    """ reads out the spiMap 
    spiMap is the emulated map inside HIPSTER
    """
    global spiMap
    file = open(fileName, 'w+')
    for reg in range(0,len(spiMap)):
        data = readRegister(reg)
        spiMap[reg] = data
        print >> file,reg," ",format(data,'#04x') 
        if (verbose):
            print "dumpSPIMap: Reg = ",reg," Data = ",format(data,'#04x')
    file.close
    return spiMap

def isSpiMapDefault():
    """ checks to see if current SPIMap is default map """
    return (list(REG_DEFAULTS) == dumpSpiMap()[0:52])

def restoreSpiMapToDefault():
    """ restores HIPSTER SPI Map to default condition
    """
    defaultMap = list(REG_DEFAULTS)
    for reg in range(0,len(defaultMap)):
        writeRegister(reg,defaultMap[reg])
    
          
def writeSpiMap(inputFile,verbose=False):
    """ Loads in ConfigMap from external file and returns SPI regmap list
        configMap is the interal map of the HIPSTER register map.
        spiMap is the actual SPI regmap inside HIPSTER
    """

    global configMap
    cmd = dict(CMD_DEFAULTS)
    #read in config file
    
    try:
        f = open(inputFile)
    except IOError:
        print "Input file %s does not exist" %inputFile
        configMap = list(REG_DEFAULTS)
        return
        
    for line in iter(f):
        if not line.startswith("#"):
            words = line.split()
            cmd[words[0]] = int(words[1])    
            
    f.close()    

    configMap = list(REG_DEFAULTS)
    
#    print configMap
    commands = []

    buildConfigMap(commands,cmd)
    
    # update configMap with commands from config file

    for reg in range(0, len(commands)):
        configMap[reg] = commands[reg]
        writeRegister(reg,configMap[reg])
    if (verbose):
        print "configMap =",configMap


