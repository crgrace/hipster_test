# -*- coding: utf-8 -*-
"""
Created on Fri Sep 4 21:26:37 2015

@author: CRGrace@lbl.gov

"""

#To analyze the data from the SSO the following steps are taken:

#while (!histogramFull):
#    Increment the DAC.  If the DAC is at maximum, reset it to minimum
#    Acquire some amount of data from the SSO
#    Put data into histogram

#findDNL()
#findINL()

#import serial
import time
import math
from hipster_spi import *

def reversed( x, num_bits=16 ):
    answer = 0
    for i in range( num_bits ):                   # for each bit number
        if (x & (1 << i)):                        # if it matches that bit
            answer |= (1 << (num_bits - 1 - i))   # set the "opposite" bit in answer
    return answer


def getSerialData(numWords=1,port="/dev/ttyUSB1",baud=3000000):
    ser = serial.Serial(port,baud,timeout=0)
    ser.flushInput()
    _ = ser.readline()
    currentWord = 0
    for i in range(numWords):
        try:
            serialWord = ser.readline()
            if (len(serialWord) == 9):
                receivedData[currentWord] = int(ser.readline()[0:3],16)
                currentWord = currentWord + 1
        except:
            print('data communciation error')
    return receivedData  

def simpleRamp(start,end,step,numSamples):
    """ runs really simple ramp, averaging based on Numsamples)
    """
    inputValues = []
    code = []
    i = 0
    input = start
    while (input < end):
        inputValues.append(input)    
        setADC1(input)
        time.sleep(1)
        code.append(round(mean(getSSO(numSamples))))
        i += 1
        input += step
    return inputValues,code 

def dumpRamp(start,end,step,numSamples):
    """ runs simple ramp, dumps codes to file 
    """
    fileName = "hipster_adc_codes.txt"
    file = open(fileName, 'w+')
    inputValues = []
    i = 0
    input = start
    while (input < end):
        inputValues.append(input)    
        setADC1(input)
        time.sleep(0.5)
        for _ in range(numSamples):
            print >> file, int(getSSO(1)[0])
        i += 1
        input += step
    return  
    
def genNoiseHisto(inputValue,numSamples):
    """ runs many samples of DC input to measure noise
    """
    fileName = "hipster_noise_codes.txt"
    file = open(fileName, 'w+')
    setADC1(inputValue)
    for _ in range(numSamples):
        print >> file, int(getSSO(1)[0])
    
    

def runRamp(whichDAC,startCode = 0, endCode = 65535):
    """ gets ADC data from the SSO via a ramp and builds histogram
    """
    histo = 4096*[0]
    enableDACs()
    for code in range(startCode,endCode-1):
        setDAC("ADC1_A",code)
        setDAC("ADC1_B",code)
        time.sleep(0.1)
        word = int(round(getSSO(1)))
        histo[word] += 1
    end
    return histo    

def getList(fileName = "hipster_noise_codes.txt"):
    """ loads in list of codes from file
    """

    #codeList = []

    try:
        codeList = map(int,open(fileName).read().splitlines())
    except:
        print "Input file ",fileName," does not exist"
        return
    
    return codeList
    
def getHisto(fileName = "hipster_adc_codes.txt"):
    """ creats histogram from codes written to file, one code per line
    """

    histo = 4095*[0]

    try:
        f = open(fileName)
    except:
        print "Input file ",fileName," does not exist"
        return
    
    for line in iter(f):
        words = line.split()
        #print type(words)
        #print words
        histo[int(words[0])] += 1

    return histo

def mean(list):
    """ returns average of numbers contained in list
    """
    #print "mean: ",list
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

def findDNL(histo,debug=False):
    """ calculates DNL
        The algorithm ignores all codes below bottomCode and all codes
        above topCode.
        Assumes a linear ramp as input signal.

    """
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
    
    if (debug==True):
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
