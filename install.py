#!/usr/bin/env python3
from os import path
import sys
import os
import time
import threading

here = path.abspath(path.dirname(__file__))
os.chdir(here)
sys.path.append('./custom_libraries')  # Change to your desired libraries folder

print("Raspberry Pi Setup Script")

avaiable_options = ["--no-dep", "--only-lib", "--no-build-isolation"]
options = []
if len(sys.argv) > 1:
    options = list.copy(sys.argv[1:])


# define color print
def warn(msg, end='\n', file=sys.stdout, flush=False):
    print(f'\033[0;33m{msg}\033[0m', end=end, file=file, flush=flush)

def error(msg, end='\n', file=sys.stdout, flush=False):
    print(f'\033[0;31m{msg}\033[0m', end=end, file=file, flush=flush)

# check if run as root
if os.geteuid() != 0:
    warn("Script must be run as root. Try \"sudo python3 setup.py\".")
    sys.exit(1)

# utils
def run_command(cmd=""):
    import subprocess
    p = subprocess.Popen(cmd,
                         shell=True,
                         stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT)
    result = p.stdout.read().decode('utf-8')
    status = p.poll()
    return status, result

errors = []
at_work_tip_sw = False

def working_tip():
    char = ['/', '-', '\\', '|']
    i = 0
    global at_work_tip_sw
    while at_work_tip_sw:
        i = (i + 1) % 4
        sys.stdout.write('\033[?25l')  # cursor invisible
        sys.stdout.write('%s\033[1D' % char[i])
        sys.stdout.flush()
        time.sleep(0.5)

    sys.stdout.write(' \033[1D')
    sys.stdout.write('\033[?25h')  # cursor visible
    sys.stdout.flush()

def do(msg="", cmd=""):
    print(f" - {msg} ... ", end='', flush=True)
    global at_work_tip_sw
    at_work_tip_sw = True
    _thread = threading.Thread(target=working_tip)
    _thread.daemon = True
    _thread.start()
    status, result = run_command(cmd)
    at_work_tip_sw = False
    _thread.join()
    if status == 0 or status == None or result == "":
        print('Done')
    else:
        print('Error')
        errors.append(f"{msg} error:\n  Status:{status}\n  Error:{result}")

def check_os_version():
    _, result = run_command("cat /etc/os-release|grep VERSION_ID")
    return result.strip()

def check_os_bit():
    _, os_bit = run_command("getconf LONG_BIT")
    return int(os_bit)

# Dependencies list installed with apt
APT_INSTALL_LIST = [
    'raspi-config',
    "i2c-tools",
    "espeak",
    'libsdl2-dev',
    'libsdl2-mixer-dev',
    'portaudio19-dev',  # pyaudio
    'sox',
]

# Dependencies list installed with pip3
PIP_INSTALL_LIST = [
    'smbus2',
    'gpiozero',
    'pyaudio',
    'spidev',
    'pyserial',
    'pillow',
    "'pygame>=2.1.2'",
]

# main function
def install():
    _is_bsps = ''
    status, _ = run_command("pip3 help install|grep break-system-packages")
    if status == 0:
        _is_bsps = "--break-system-packages"

    # Install dependencies with apt
    if "--no-dep" not in options:
        print("Install dependencies with apt-get:")
        do(msg="update apt-get", cmd='apt-get update')
        for dep in APT_INSTALL_LIST:
            do(msg=f"install {dep}", cmd=f'apt-get install {dep} -y')

    # Install dependencies with pip3
    print("Install dependencies with pip3:")
    if _is_bsps != '':
        _is_bsps = "--break-system-packages"
        print("\033[38;5;8m pip3 install with --break-system-packages\033[0m")
    do(msg="update pip3", cmd=f'python3 -m pip install --upgrade pip {_is_bsps}')
    for dep in PIP_INSTALL_LIST:
        do(msg=f"install {dep}", cmd=f'pip3 install {dep} {_is_bsps}')

    # Setup interfaces
    print("Setup interfaces")
    do(msg="turn on I2C", cmd='raspi-config nonint do_i2c 0')
    do(msg="turn on SPI", cmd='raspi-config nonint do_spi 0')

    # Report error
    if len(errors) == 0:
        print("Finished")
    else:
        print("\n\nError happened in install process:")
        for error in errors:
            print(error)

if __name__ == "__main__":
    try:
        install()
    except KeyboardInterrupt:
        if len(errors) > 0:
            print("\n\nError happened in install process:")
            for error in errors:
                print(error)
        print("\n\nCanceled.")
    finally:
        sys.stdout.write(' \033[1D')
        sys.stdout.write('\033[?25h') # cursor visible 
        sys.stdout.flush()
