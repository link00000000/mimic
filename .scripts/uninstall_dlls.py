from os.path import basename, splitext, join, abspath, isdir
from os import system, mkdir
import ctypes, sys
from urllib.request import urlretrieve
from zipfile import ZipFile

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

if not is_admin():
    ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
    sys.exit()

if not isdir(join('.scripts', 'tmp')):
    mkdir(join('.scripts', 'tmp'))

url = 'https://github.com/CatxFish/obs-virtual-cam/releases/download/2.0.4/OBS-VirtualCam2.0.4.zip'
file_name = join('.scripts', 'tmp', basename(url))
file_name_no_ext = splitext(file_name)[0]
urlretrieve(url, file_name)

with ZipFile(file_name, 'r') as zip_ref:
    zip_ref.extractall(path=file_name_no_ext)

dll_32 = abspath(f'{file_name_no_ext}\\obs-virtualcam\\bin\\32bit\obs-virtualsource.dll')
dll_64 = abspath(f'{file_name_no_ext}\\obs-virtualcam\\bin\\64bit\obs-virtualsource.dll')

system(f'regsvr32 /u "{dll_32}"')
system(f'regsvr32 /u "{dll_64}"')
