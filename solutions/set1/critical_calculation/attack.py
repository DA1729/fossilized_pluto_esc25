import chipwhisperer as cw
import time

scopetype = 'CWNANO'
platform = 'CWNANO'

try:
    if not scope.connectStatus:
        scope.con()
except NameError:
    scope = cw.scope()

try:
    if ss_ver == "SS_VER_2_1":
        target_type = cw.targets.SimpleSerial2
    elif ss_ver == "SS_VER_2_0":
        raise OSError("ss_ver_2_0 is deprecated")
    else:
        target_type = cw.targets.SimpleSerial
except:
    ss_ver="SS_VER_1_1"
    target_type = cw.targets.SimpleSerial

try:
    target = cw.target(scope, target_type)
except:
    scope = cw.scope()
    target = cw.target(scope, target_type)

if "STM" in platform or platform == "CWLITEARM" or platform == "CWNANO":
    prog = cw.programmers.STM32FProgrammer
elif platform == "CW303" or platform == "CWLITEXMEGA":
    prog = cw.programmers.XMEGAProgrammer
elif "neorv32" in platform.lower():
    prog = cw.programmers.NEORV32Programmer
elif "SAM4S" in platform or platform == "CWHUSKY":
    prog = cw.programmers.SAM4SProgrammer
else:
    prog = None

def reboot_flush():
    scope.io.nrst = False
    time.sleep(0.02)
    scope.io.nrst = "high_z"
    time.sleep(0.02)
    target.flush()

fw_path = "../../../challenges/set1/criticalCalculation-CWNANO.hex".format(platform)
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
                        print(f"flag: {response_str}")
                        print(f"glitch: repeat={scope.glitch.repeat}, ext_offset={scope.glitch.ext_offset}")
                        return True, (scope.glitch.repeat, scope.glitch.ext_offset)
                    else:
                        gc.add("normal")
        param_count += 1
    return False, None

def adaptive_glitch_scan():
    found_flag, found_params = perform_glitch_set(1, 10, 1, 200, step=5, sample_size=3)
    if found_flag:
        return found_params
    found_flag, found_params = perform_glitch_set(5, 15, 100, 150, step=1, sample_size=10)
    if found_flag:
        return found_params
    return None

flag_params = adaptive_glitch_scan()

if flag_params:
    print(f'params: repeat={flag_params[0]}, ext_offset={flag_params[1]}')

gc.glitch_plot(plotdots={"success": "+g", "reset": "xr", "normal": None})
