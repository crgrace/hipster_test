# -*- coding: utf-8 -*-
"""
Created on 09/02/2015python 18:26:37 2015

@author: CRGrace@lbl.gov
"""

"""
Low-level bit-banged HIPSTER serial interface for Raspberry Pi.
Intended to run on the Raspberry Pi
"""

import RPi.GPIO as GPIO
import time

# global variables
SLEEPTIME = 0.01    # pause duration in seconds
RST = 17
CSB = 18
SCLK = 22
MOSI = 23
MISO = 24
receivedWord = 0  # this is the word returned from HIPSTER

def setupGPIO():
    """ sets up GPIOs needed for SPI interface 
    """
    global RST, CSB, SCLK, MOSI, MISO

    GPIO.setmode(GPIO.BCM)
    GPIO.setup(RST, GPIO.OUT)  # RST
    GPIO.setup(CSB, GPIO.OUT)  # CSB
    GPIO.setup(SCLK, GPIO.OUT)  # SCLK
    GPIO.setup(MOSI, GPIO.OUT)  # MOSI
    GPIO.setup(MISO, GPIO.IN)   # MISO
    spiInit()

def pause():
    """ pause for a time interval equal to SLEEPTIME microseconds
    """
    global SLEEPTIME
    time.sleep(SLEEPTIME)

def putBit(bit):
    """ outputs bit to SPI bus and receives bit from SPI bus
    """ 
    global SCLK, MISO, MISO, receivedWord

    pause()
    GPIO.output(SCLK, 0)
    GPIO.output(MOSI, int(bit))
    receivedBit = GPIO.input(MISO)
    receivedWord = receivedWord << 1 | receivedBit
    pause()
    GPIO.output(SCLK, 1)

def spiReset():
    global RST
    GPIO.output(RST,0)
    pause()
    GPIO.output(RST,1)

def spiInit():
           
    global RST, CSB, SCLK, MOSI
    GPIO.output(RST,1)
    GPIO.output(CSB,1)
    GPIO.output(SCLK,0)
    GPIO.output(MOSI,0)

def spiMaster(spiWRB,spiAddr,spiData):

    global SCLK,CSB, receivedWord
    wordLength = 16
    receivedWord = 0
    pause()
    # enable SPI slave
    GPIO.output(CSB, 0)
    
    #first send write/read command
    putBit(spiWRB)
    
    # write SPI address
    for i in range(1,wordLength):
        putBit(spiAddr >> (wordLength - 1 - i) & 1)

    # write SPI data
    for i in range(0,wordLength):
        putBit( (spiData >> (wordLength - 1 - i) & 1 ))


    # complete readout of SPI register
    for i in range(0,3):
        putBit(0)
    
    # data sent.  Disable slave.    
    GPIO.output(SCLK, 0)
    pause()
    GPIO.output(CSB, 1)
    pause()
    GPIO.output(SCLK, 1) 
    
    return receivedWord


