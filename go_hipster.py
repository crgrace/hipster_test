import hipster_spi as h
import configure_si5338 as c

verbose = True
# restore HIPSTER SPI programming to default
if (verbose): print "Loading SPI map into HIPSTER"
h.restoreSpiMapToDefault()
if (verbose): print "Configuring HIPSTER"

# powerdown TX and ADCs
#h.powerDownAllTXs()
h.powerDownAllADCs()

# configure HIPSTER to observe feedback divider
h.setBitInRegister(19,0)

# set HIPSTER biasing
h.setBias("MASTER",7)
h.setBias("CML",5)

# configure SI5338 clock chip
if (verbose): print "Configuring Si5338 Clock Chip"
c.configureSi5338("RegisterMap.txt")

# configure and lock PLL

h.setBiasPLL(12)  # CP current
h.writeRegister(16,0x00b6)  # C1
h.writeRegister(17,0x0001)  # C2
h.setBitInRegister(18,6)  # R1 bit 2
h.clearBitInRegister(18,5)  # R1 bit 1
h.setBitInRegister(18,4)  # R1 bit 0

if (verbose): print "Locking PLL"
h.lockPLL()

# power up transmitter #1
h.clearBitInRegister(22,9)

# take JESD out of reset 
# (need to figure out why we need to do this!)
h.setBitInRegister(27,7)

# set JESD testmode to Send /K/
h.setBitInRegister(27,0)

if (verbose): print "Done"
