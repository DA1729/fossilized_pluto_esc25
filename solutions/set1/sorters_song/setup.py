import chipwhisperer as cw


SCOPETYPE = 'CWNANO'
PLATFORM = 'CWNANO'


try:
    if not scope.connectStatus:
        scope.con()
except NameError:
    scope = cw.scope()

try:
    if SS_VER == "SS_VER_2_1":
        target_type = cw.targets.SimpleSerial2
    elif SS_VER == "SS_VER_2_0":
        raise OSError("SS_VER_2_0 is deprecated. Use SS_VER_2_1")
    else:
        target_type = cw.targets.SimpleSerial
except:
    SS_VER="SS_VER_1_1"
    target_type = cw.targets.SimpleSerial

try:
    target = cw.target(scope, target_type)
except:
    print("INFO: Caught exception on reconnecting to target - attempting to reconnect to scope first.")
    print("INFO: This is a work-around when USB has died without Python knowing. Ignore errors above this line.")
    scope = cw.scope()
    target = cw.target(scope, target_type)

if "STM" in PLATFORM or PLATFORM == "CWLITEARM" or PLATFORM == "CWNANO":
    prog = cw.programmers.STM32FProgrammer
elif PLATFORM == "CW303" or PLATFORM == "CWLITEXMEGA":
    prog = cw.programmers.XMEGAProgrammer
elif "neorv32" in PLATFORM.lower():
    prog = cw.programmers.NEORV32Programmer
elif "SAM4S" in PLATFORM or PLATFORM == "CWHUSKY":
    prog = cw.programmers.SAM4SProgrammer
else:
    prog = None

import time
time.sleep(0.05)
scope.default_setup()

def reset_target(scope):
    if PLATFORM == "CW303" or PLATFORM == "CWLITEXMEGA":
        scope.io.pdic = 'low'
        time.sleep(0.1)
        scope.io.pdic = 'high_z' #XMEGA doesn't like pdic driven high
        time.sleep(0.1) #xmega needs more startup time
    elif "neorv32" in PLATFORM.lower():
        raise IOError("Default iCE40 neorv32 build does not have external reset - reprogram device to reset")
    elif PLATFORM == "CW308_SAM4S" or PLATFORM == "CWHUSKY":
        scope.io.nrst = 'low'
        time.sleep(0.25)
        scope.io.nrst = 'high_z'
        time.sleep(0.25)
    else:  
        scope.io.nrst = 'low'
        time.sleep(0.05)
        scope.io.nrst = 'high_z'
        time.sleep(0.05)

fw_path = "../../../challenges/set1/sortersSong-CWNANO.hex".format(PLATFORM)
cw.program_target(scope, prog, fw_path)

print("Resetting target...")
reset_target(scope)
print("Target is now running.")

target.simpleserial_write('x', b'')
resp = target.simpleserial_read('r', 1)
if resp is not None:
    print("x: ", resp)
    
num = 1
pos=1
target.simpleserial_write('p', bytearray([1, num&0xff, 0, pos]))
resp = target.simpleserial_read('r', 2)
if resp is not None:
    print("p: ", int.from_bytes(resp, byteorder='little', signed=False))
    
target.simpleserial_write('c', b'')
resp = target.simpleserial_read('r', 1)
if resp is not None:
    print("c: ", resp)

# check the answer
target.simpleserial_write('a', bytearray([3, 15, 22, 24, 41, 82, 86, 89, 90, 96, 106, 179, 217, 219, 250]))
resp = target.simpleserial_read('r', 20)
if resp is not None:
    print("a: ", resp)
    
#check number of queries
target.simpleserial_write('q', b"0")
resp = target.simpleserial_read('r', 4)
if resp is not None:
    print(f"Number of Queries (cumulative): {int.from_bytes(resp, byteorder='little', signed=False)}") #number of queries since powerup             


# Challenge 2
target.simpleserial_write('x', b'')
resp = target.simpleserial_read('r', 1)
if resp is not None:
    print("x: ", resp)

num = 456
pos=1
target.simpleserial_write('p', bytearray([2,  num&0xff, (num>>8)&0xff, pos]))
resp = target.simpleserial_read('r', 2)
if resp is not None:
    print("p: ", int.from_bytes(resp, byteorder='little', signed=False))

target.simpleserial_write('d', b'')
resp = target.simpleserial_read('r', 1)
if resp is not None:
    print("d: ", resp)

# check the answer
target.simpleserial_write('b', bytearray([90, 5, 29, 11, 21, 26, 49, 33, 101, 68, 244, 73, 18, 94, 8, 133, 98, 147, 221, 152, 116, 153, 26, 208, 217, 211, 169, 237, 28, 253]))
resp = target.simpleserial_read('r', 20)
if resp is not None:
    print("b: ", resp)

#check number of queries
target.simpleserial_write('q', b"0")
resp = target.simpleserial_read('r', 4)
if resp is not None:
    print(f"Number of Queries (cumulative): {int.from_bytes(resp, byteorder='little', signed=False)}") #number of queries since powerup


scope.dis()
target.dis()


