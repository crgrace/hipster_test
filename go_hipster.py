import hipster_spi as h
import configure_si5338 as c

# restore HIPSTER SPI programming to default
h.restoreSpiMapToDefault()

# powerdown TX and ADCs
h.powerDownAllTXs()
h.powerDownAllADCs()

# configure HIPSTER to observe feedback divider
h.setBitInRegister(18,0)

# set HIPSTER biasing
h.setBias("MASTER",6)
h.setBias("CML",6)

# configure SI5338 clock chip
c.configureSi5338("RegisterMap.txt")

# lock PLL
h.lockPLL()

# power up transmitter #1
h.clearBitInRegister(22,9)

# set JESD testmode to Send /K/
h.setBitInRegister(27,0)

