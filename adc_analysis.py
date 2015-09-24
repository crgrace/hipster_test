# -*- coding: utf-8 -*-
"""
Created on Fri Sep 4 21:26:37 2015

@author: CRGrace@lbl.gov

"""

"""
To analyze the data from the SSO the following steps are taken:

while (!histogramFull):
    Increment the DAC.  If the DAC is at maximum, reset it to minimum
    Acquire some amount of data from the SSO
    Put data into histogram

findDNL()
findINL()
"""

#import serial
import time
import math


#def test_Serial():
#    """ gets ADC data from the SSO and builds histograms that can later
#    be used to measure linearity and noise
#    """
#    port = "/dev/ttyUSB1"
#    baud = 3000000
#    ser = serial.Serial(port,baud,timeout=0)
#    
#    for _ in range(10): 
#        try:
#            receivedLine = ser.readline()
#            print "received code = ",receivedLine
#            print "received code minus 10 = ",int(receivedLine)-10
#        except:
#            print('data communciation error')

"""
def getSerialData(numWords=1,port="/dev/ttyUSB1",baud=3000000):
    ser = serial.Serial(port,baud,timeout=0)
    for i in range(numWords):
        try:
            receivedData[i] = int(ser.readline())
        except:
            print('data communciation error')
    return receivedData  
"""

def runRamp(whichDAC,startCode = 0, endCode = 65535):
    """ gets ADC data from the SSO via a ramp and builds histogram
    """
    histo = 4096*[0]
    enableDACs()
    for code in range(startCode,endCode-1):
        setDAC(whichDAC,code)
        #sleep(?)
        #word = getSerialData()
        histo[word] += 1
    end
    return histo    

def mean(list):
    """ returns average of numbers contained in list
    """

    return sum(list) * ( 1.0/len(list))

def variance(list):
    """ returns variance of numbers contained in list
    """
    sumOfSquares = 0
    ave = mean(list)
    for value in list:
        sumOfSquares += (ave - value)**2
    variance = sumOfSquares / len(list)
    return variance

def calcLinearity(histo):
    """ analyzes the ADC histogram to get DNL and INL
    """
    DNL = findDNL(histo)
    INL = findINL(histo)
    return DNL,INL   

def findNoise(histo):
    """ calculate the idle channel noise of the ADC.  
        Input assumed to be a constant (grounded input)
    """

    return math.sqrt(variance(histo))

def getADCDataJESD():
    """ gets ADC data from the backend data and builds histograms 
        that can later be used to measure linearity and noise
    """
    pass

def findDNL(histo):
    """ calculates DNL
        The algorithm ignores all codes below bottomCode and all codes
        above topCode.
        Assumes a linear ramp as input signal.

    """
    debug = 0
    numBits = round(math.log(len(histo))/math.log(2))
    totalHits = 0.0
    missingCodes = 0.0
    codeCount = 0.0
    DNL = len(histo)*[0.0]
    # find the range of the data (top and bottom of histogram)
    i = 0
    while (histo[i] == 0.0):
        i += 1
    bottomCode = i

    i = len(histo)-1    
    while (histo[i] == 0.0):
        i -= 1
    topCode = i
    
    # get statistics from histogram 
    for i in range(bottomCode,topCode):
        totalHits += histo[i]
        codeCount += 1
    meanHits = totalHits/codeCount
    for i in range(bottomCode,topCode):
        DNL[i] = (histo[i] - meanHits)/meanHits
    
    if (debug):
        print "totalHits = ",totalHits
        print "codeCount = ",codeCount
        print "meanHits = ",meanHits
        print "topCode = ",topCode
        print "bottomCode = ",bottomCode
        

    return DNL

def findINL(DNL):
    """ calculates INL from the DNL
    """
    INL = len(DNL)*[0]
    for i in range(1,len(DNL)):
        INL[i] = INL[i-1] + DNL[i]

    return INL

def findExtremes(array):
    maxValue,maxCode = max(array),array.index(max(array))
    minValue,minCode = min(array),array.index(min(array))
    return maxValue,maxCode,minValue,minCode  
  

#    return [DNL,maxDNLCode,INL,maxINLCode]
def test():
    # first test with a 4-bit ADC
    histo = [0, 10, 9, 10, 9, 9, 8, 10]
    return histo      
