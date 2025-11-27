# Ciefp Bouquet Updater for Enigma2

**Version:** 1.4  
**Author:** Based on original ciefp settings  
**Plugin Name:** CiefpBouquetUpdater  
**Supported platforms:** OpenATV, OpenBH, VTI, Egami, OpenPLI, BlackHole, and other Enigma2-based images

![Plugin Screenshot](https://raw.githubusercontent.com/ciefp/CiefpBouquetUpdater/main/bouquetupdater.jpg)
*(Replace with actual screenshot if available)*

## Description

Ciefp Bouquet Updater is an Enigma2 plugin that allows users to easily download, preview, and selectively install the latest **ciefp-E2-75E-34W** satellite settings (bouquets, favorites, picons, lamedb) directly from the official GitHub repository:

https://github.com/ciefp/ciefpsettings-enigma2-zipped

The plugin downloads the latest ZIP package, extracts it, displays all available bouquets in the correct order (as defined in `bouquets.tv`), and lets you:
- Select only the bouquets you want
- Install them safely into `/etc/enigma2`
- Automatically update `bouquets.tv`
- Replace common files like `lamedb` (with confirmation)
- Reload bouquets and services without reboot

Perfect for users who want up-to-date ciefp settings without downloading and installing the entire package manually.

## Features

- Automatic download of the latest ciefp 75E-34W settings from GitHub
- Displays current version/date from the latest ZIP filename
- Shows bouquets in correct order (as in original `bouquets.tv`)
- Multi-selection of desired bouquets
- Two-step installation:
  - **Copy** – prepares selected bouquets in a temporary folder
  - **Install** – copies selected bouquets + common files (`lamedb`) to `/etc/enigma2`
- Safely overwrites old files
- Automatic reload of bouquets and servicelist
- Clean and user-friendly interface with colored buttons

## Installation

1. Copy the plugin folder to your receiver:

2. Make sure the following files are present:
- `plugin.py`
- `background.png`
- `icon.png` (optional, shown in plugin menu)

3. Restart Enigma2 GUI or reboot the receiver

4. The plugin will appear in the **Plugins** menu as:  
**CiefpBouquetUpdater v1.4**

## Usage

1. Open the plugin from the menu
2. Wait for the latest settings to be downloaded from GitHub
3. Use **OK** to select/deselect bouquets from the left list  
Selected items appear on the right
4. Press **GREEN** → "Copy" to prepare selected files
5. Press **YELLOW** → "Install" to install them permanently
6. Confirm installation (includes overwriting `lamedb`)
7. Bouquets and services are automatically reloaded

**Red button** = Exit

## Supported Satellites

Currently supports the official ciefp package:
- **75°E – 34°W** multi-satellite setup

## Requirements

- Enigma2-based image (OpenATV, OpenBH, etc.)
- Internet connection
- Python 2.7+ (standard on all E2 images)
- Write permissions to `/etc/enigma2` and `/tmp`

## Changelog

### v1.4 (27.11.2025)
- Improved GitHub API handling
- Better error messages
- Automatic version detection from ZIP filename
- Safer file installation (deletes old files before copying)
- Full support for latest ciefp zipped repository structure

## Credits

- Original settings by **ciefp** – https://github.com/ciefp
- Plugin developed and maintained for the Enigma2 community

## Disclaimer

This plugin downloads and installs third-party channel lists. Use at your own risk.  
Always make a backup of your current `/etc/enigma2/` folder before installing new settings.

## License

This plugin is distributed under the **GPLv3 License**.  
You are free to modify and redistribute it.

---

**Enjoy always up-to-date ciefp settings with just a few clicks!**  
.:: ciefpsettings ::.
