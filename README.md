# Mimic - A remote IP camera over WebRTC

[![Build Release](https://github.com/link00000000/mimic/actions/workflows/build-release.yml/badge.svg?branch=master)](https://github.com/link00000000/mimic/actions/workflows/build-release.yml)

## Table of Contents 🧾

<!-- vim-markdown-toc GFM -->

- [What is Mimic 🤷‍♀️](#what-is-mimic-)
  - [What is Mimic not?](#what-is-mimic-not)
- [How to use ❓](#how-to-use-)
- [Installing 💿](#installing-)
  - [Using the installer](#using-the-installer)
  - [Running without the installer](#running-without-the-installer)
  - [Building from source](#building-from-source)
- [Uninstalling 📤](#uninstalling-)
  - [Using the installer](#using-the-installer-1)
  - [Uninstalling without the uninstaller](#uninstalling-without-the-uninstaller)
- [Allowing Mimic through the Windows Firewall 🔥🧱](#allowing-mimic-through-the-windows-firewall-)
  - [Removing firewall rule](#removing-firewall-rule)
- [Starting Mimic when Windows starts 🏁](#starting-mimic-when-windows-starts-)
  - [Stop Mimic from starting when Windows starts](#stop-mimic-from-starting-when-windows-starts)
- [Advanced Usage ⚙](#advanced-usage-)
  - [Using with ngrok](#using-with-ngrok)
  - [Using with a VPN](#using-with-a-vpn)
- [Automated builds 🔨](#automated-builds-)
  - [Automated Releases](#automated-releases)

<!-- vim-markdown-toc -->

## What is Mimic 🤷‍♀️

Mimic allows you to use your smartphone or other webcam-enabled device as a webcam for a different computer on Windows. Mimic creates a WebRTC connection between your PC and your other device to stream video to your PC.

Mimic will appear as a standard webcam on your PC just like any other PC. The only requirements are that the host PC is running 64-bit Windows and your device has a webcam and access to a modern web browser.

### What is Mimic not?

- Mimic is not a voice transmitter. Mimic does not capture and send audio, video only.
- Mimic is not a physical webcam. Mimic mimics (😉) a physical camera in software. This means that sometimes applications won't correctly pick up the camera but it should work for most applications.
- Mimic is not an iOS or Android application. Mimic connects to the host using the devices pre-installed web browser instead of a native application. That means theres nothing to install on your webcam-enabled devices, just plug-and-play!

## How to use ❓

1. Make sure both devices are on the same network
2. Install and start Mimic on the host PC (the computer that does not have the camera).
3. Double click the Mimic icon in the system tray.
4. Scan the QR code with your smartphone.

Your device is now a webcam for your PC.

## Installing 💿

### Using the installer

1. Download the latest release from the [releases tab](https://github.com/link00000000/mimic/releases).
2. Download `setup-mimic-win64.exe` for the production build or `setup-mimic-debug.exe` for the debug build.
    - Only 64-bit Windows is supported.
3. Follow the steps in the installer
    - Tick "Create a desktop shortcut" if you would like a shortcut placed on your desktop.
    - Tick "Start Mimic when Windows starts" if you would like mimic to automatically start in the background when Windows starts.

### Running without the installer

1. Download the latest release from the [releases tab](https://github.com/link00000000/mimic/releases).
2. Download `mimic-win64.zip` for the production build or `mimic-debug.zip` for the debug build.
    - Only 64-bit Windows is supported.
3. Extract the zip file to a permanent location
4. Download [obs-virtual-cam build 2.0.4](https://github.com/CatxFish/obs-virtual-cam/releases/download/2.0.4/OBS-VirtualCam2.0.4.zip)
5. Extract `OBS-VirtualCam2.0.4.zip` to a permanent location
6. Install the obs-virtualsource libraries **as administrator**
    ```shell
    regsvr32 /n /i:1 .\obs-virtualcam\bin\32bit\obs-virtualsource.dll
    regsvr32 /n /i:1 .\obs-virtualcam\bin\64bit\obs-virtualsource.dll
    ```

Mimic can now be started using `mimic.exe`.

> ⚠ If you are unable to connect to Mimic from your device, Windows Firewall may be blocking the connection. See [Allowing Mimic through the Windows Firewall](#allowing-mimic-through-the-windows-firewall-)


### Building from source

1. Install build requirements
    - Python 3.9+
    - pipenv (installed with `pip install pipenv`)
    - [Inno Setup](https://jrsoftware.org/isinfo.php) (installed with `choco install InnoSetup` if Chocolatey is installed)
2. Clone the repository
    ```shell
    git clone https://github.com/link00000000/mimic
    ```
3. Install dependencies
    ```shell
    cd mimic
    pipenv install
    ```
4. Build the project
    - Production: `pipenv run build`
    - Debug: `pipenv run build-debug`
5. Build the installer (optional)
    ```shell
    pipenv run installer
    ```
6. Run the installer located at `.\dist\setup-mimic-win64.exe`

Compiled application is available at `.\dist\mimic`.

> ⚠ If you opt to not build the installer, runtime dependencies must be installed. See [Running without the installer](#running-without-the-installer)

## Uninstalling 📤

### Using the installer

Mimic can either be uninstalled using Window's built-in uninstall by searching for "Add or remove programs" or by running `unins000.exe` in the install directory.

> ⚠ The uninstaller will be unable to remove the `OBS-VirtualCam` directory if the virtual camera is in use in *any* running application. Either make sure that all applications that might use the virtual camera are closed before uninstalling or manually delete the directory after closing all applications and uninstalling.

### Uninstalling without the uninstaller

1. Uninstall the obs-virtualsource libraries **as administrator** in the folder the library was placed in during installation.
    ```shell
    regsvr32 /u .\obs-virtualcam\bin\32bit\obs-virtualsource.dll
    regsvr32 /u .\obs-virtualcam\bin\64bit\obs-virtualsource.dll
    ```
2. Delete temporary files at `%localappdata%\mimic`.
3. Delete any remaining Mimic files.
    - Mimic install directory
    - OBS-VirtualCam library directory

> ⚠ If you set a rule in the Windows Firewall, be sure to remove it. See [Removing firewall rule](#removing-firewall-rule).

> ⚠ If you setup Mimic to automatically start with Windows, be sure to remove the startup shortcut. See [Starting Mimic when Windows starts](#starting-mimic-when-windows-starts).

## Allowing Mimic through the Windows Firewall 🔥🧱

Only perform these steps if you cannot connect to Mimic from your other device and you are on the same network.

1. Open the windows firewall by searching for or executing `wf.msc`
2. Click on inbound connections in the left panel
3. Click new rule in the right panel
4. Add the new firewall rule
    1. Select Program
    2. Click Next
    3. Click "Browse..."
    4. Select the location of `mimic.exe`
    5. Click Next
    6. Click Next
    7. Click Next
    8. Enter "Mimic" for the name
    9. Click Finish.

### Removing firewall rule

1. Open the windows firewall by searching for or executing `wf.msc`
2. Click on inbound connections in the left panel
3. Highlight all instances of "Mimic" in the `Inbound Rules` panel
4. Click Delete in the right panel
5. Click Yes

## Starting Mimic when Windows starts 🏁

To start Mimic when windows starts, a shortcut to `mimic.exe` must be placed in the startup folder.

To access the startup folder
1. Press Win+R to open the run dialog.
2. Type "shell:startup"
3. Click OK

> ⚠ Be sure to only place shortcuts in `shell:startup` and not a copy of the binary `.exe`.

### Stop Mimic from starting when Windows starts

To prevent Mimic from automatically starting with Windows, remove the shortcut from `shell:startup`.

## Advanced Usage ⚙

### Using with ngrok

Mimic does work with ngrok. On the host machine, a Mimic can be exposed using the command `ngrok http https://<your_local_ip_address_here>:8080`. On your webcam-enabled device, navigate to the HTTPS URL generated by ngrok to connect to Mimic.

### Using with a VPN

It has not been tested but Mimic should work on devices that are not on the same local network if they are both on the same VPN connection (depending on the VPN). Connect both devices to the same VPN before starting the host application and connecting with you webcam-enabled device.

## Automated builds 🔨

Builds are automatically created on commit using GitHub Actions. Build artifacts for `Windows x64` and `Windows x64 Debug` are available under GitHub actions.

### Automated Releases

If a commit is tagged with the format vX.X.X, production and debug builds will be created and a release will be made with the build artifacts attached.
