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

fw_path = "../../../challenges/set2/ghostBlood-CWNANO.hex".format(PLATFORM)
cw.program_target(scope, prog, fw_path)

print("Resetting target...")
reset_target(scope)
print("Target is now running.")

tx = b'\x00\x00\x00\x00\x00\x00'
target.simpleserial_write('s', tx)
response = target.simpleserial_read('r', 1)
if response is not None:
    print(response)

key = b'\x00'*16 
target.simpleserial_write('d', key)
response = target.simpleserial_read('r', 21)
if response is not None:
    print(response)

queries = b'\x00'
target.simpleserial_write('q', queries)
response = target.simpleserial_read('r', 4)
if response is not None:
    print(f"Number of Queries (cumulative): {int.from_bytes(response, byteorder='little', signed=False)}") #number of queries since powerup


scope.dis()
target.dis()


