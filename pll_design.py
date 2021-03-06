#!/usr/bin/python
# -*- coding: utf-8 -*-

# HOW TO USE
#
# 1. set f_ref to the reference input frequency
# 2. set f_out to the VCO output frequency
# 3. set k_vco to the measured VCO gain (4 GHz/V in HIPSTER)
# 4. set f_loop to the desired PLL Loop bandwidth (must be < ~15*f_ref)
# 5. set master-bias_adj and pll_cp_bias_adj to desired values
# 6. set pm to desired phase margin (in degrees)
# 7. run script.  If PLL is not realizable, adjust inputs and run again
# 8. once you have a realizable PLL, load values for C1, C2, & R1 into HIPSTER

import math

###
# TO BE CHANGED BY USER
###

#f_ref = 75e6  # input reference frequency in Hz
f_ref = 50e6
#f_ref = 23.66e6
#f_ref = 37.5e6
#f_ref = 23.667e6
#f_out = 2.25e9 # PLL output frequency in Hz
f_out = 1.5e9 
#f_out = 710e6 
#f_out = 710e6
k_vco = 4e9 # VCO gain (measured) in Hz/V
f_loop = 2e6  # desired PLL Loop bandwidth in Hz
master_bias_adj = 7 # 4-bit decimal number indicating masterbias current
pll_cp_bias_adj = 14 # 4-bit decimal number indicating charge-pump current
pm = 80 # desired loop phase margin in degrees (higher PM leads to lower jitter)

###############

##
#  Error Checking
##
assert (master_bias_adj >= 0 and master_bias_adj <= 15), "master_bias_adj out of range"
assert (pll_cp_bias_adj >= 0 and pll_cp_bias_adj <= 15), "pll_cp_bias_adj out of range"
assert (k_vco < 8e9), "kvo out of range (expected less than 8 GHz/V)"
    
i_masterbias = 93.75e-6 - master_bias_adj*6.25e-6
i_cp = (1.875*i_masterbias) - pll_cp_bias_adj*(i_masterbias/8)
gamma = 1.024
pi = 3.14159
divide_ratio = f_out / f_ref
wc_loop = 2*pi*f_loop # PLL Loop bandwidth in rad/s

pole = (math.sqrt( ((1+gamma)**2)* (math.tan(pm*pi/180)**2)+4*gamma) - (1+gamma)*math.tan(pm*pi/180)) / (2*wc_loop)
zero = gamma/(wc_loop*wc_loop*pole)
total_cap = (i_cp*k_vco)/(divide_ratio*wc_loop**2)*math.sqrt( (1+(wc_loop**2)*(zero**2)) / (1+(wc_loop**2)*(pole**2)) )
c2 = total_cap * (pole/zero)
c1 = total_cap - c2
r1 = zero/c1

c1_code = int(math.floor(c1/0.625e-12))
c2_code = int(math.floor(c2/25e-15))
r1_code = int(math.floor((r1-2.5e3)/2.5e3)) 

if (c1_code > 255) or (c2_code > 255) or (r1_code > 7):
    print "PLL not realiziable.  Consider increasing charge pump bias current or relaxing phase margin."
    print "Max C1, C2 codes = 255 (ff).  Max R1 code = 7"
    
if (c1_code < 0) or (c2_code < 0) or (r1_code < 0):
    print "PLL not realiziable.  Negative values not allowed."
    print "Consider reducing charge pump bias current"  
    
print "Desired Phase Margin = ",pm,"degrees"    
print "Master bias current = ",i_masterbias*1e6,"uA"
print "Charge pump current = ",i_cp*1e6,"uA"
print "C1 =", c1
print "C2 =", c2
print "R1 =", r1
print " "
print "SPI settings:"
print "master_bias_adj decimal =", master_bias_adj, "hex =", hex(master_bias_adj).split('x')[1]
print "pll_cp_bias_adj decimal =", pll_cp_bias_adj, "hex =", hex(pll_cp_bias_adj).split('x')[1]
print "C1 decimal =", c1_code, "hex =", hex(c1_code).split('x')[1]
print "C2 decimal =", c2_code, "hex =", hex(c2_code).split('x')[1]
print "R1 decimal =", r1_code, "hex =", hex(r1_code).split('x')[1]
