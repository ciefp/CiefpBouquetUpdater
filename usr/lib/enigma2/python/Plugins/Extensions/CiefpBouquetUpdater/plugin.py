import os
import shutil
import zipfile
import requests
from Components.Pixmap import Pixmap
from Components.ActionMap import ActionMap
from Components.Label import Label
from Components.MenuList import MenuList
from Plugins.Plugin import PluginDescriptor
from Screens.MessageBox import MessageBox
from Screens.Screen import Screen
from Tools.Directories import fileExists
from enigma import eDVBDB

PLUGIN_VERSION = "1.1"
PLUGIN_ICON = "icon.png"
PLUGIN_NAME = "CiefpBouquetUpdater"
TMP_DOWNLOAD = "/tmp/ciefp-E2-75E-34W"
TMP_SELECTED = "/tmp/CiefpBouquetUpdater"
PLUGIN_DESCRIPTION = "Bouquets update Plugin"
GITHUB_API_URL = "https://api.github.com/repos/ciefp/ciefpsettings-enigma2-zipped/contents/"
STATIC_NAMES = ["ciefp-E2-75E-34W"]

class CiefpBouquetUpdater(Screen):
    skin = """
        <screen position="center,center" size="1400,600" title="..:: Ciefp Bouquet Updater ::..    (Version{version})">
            <widget name="left_list" position="0,0" size="520,500" scrollbarMode="showOnDemand" itemHeight="33" font="Regular;28" />
            <widget name="right_list" position="530,0" size="500,500" scrollbarMode="showOnDemand" itemHeight="33" font="Regular;28" />
            <widget name="background" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/CiefpBouquetUpdater/background.png" position="1040,0" size="360,600" />
            <widget name="status" position="0,510" size="840,50" font="Regular;24" />
            <widget name="green_button" position="0,550" size="150,35" font="Bold;28" halign="center" backgroundColor="#1F771F" foregroundColor="#000000" />
            <widget name="yellow_button" position="170,550" size="150,35" font="Bold;28" halign="center" backgroundColor="#9F9F13" foregroundColor="#000000" />
            <widget name="red_button" position="340,550" size="150,35" font="Bold;28" halign="center" backgroundColor="#9F1313" foregroundColor="#000000" />
            <widget name="version_info" position="510,550" size="480,40" font="Regular;20" foregroundColor="#FFFFFF" />
        </screen>
    """.format(version=PLUGIN_VERSION)

    def __init__(self, session):
        Screen.__init__(self, session)
        self.session = session
        self.selected_bouquets = []
        self["left_list"] = MenuList([])
        self["right_list"] = MenuList([])
        self["background"] = Pixmap()
        self["status"] = Label("Loading bouquets...")
        self["green_button"] = Label("Copy")
        self["yellow_button"] = Label("Install")
        self["red_button"] = Label("Exit")
        self["version_info"] = Label("")  # Stalno prikazivanje verzije
        self["actions"] = ActionMap(["OkCancelActions", "ColorActions"], {
            "ok": self.select_item,
            "cancel": self.exit,
            "up": self.up,
            "down": self.down,
            "green": self.copy_files,
            "yellow": self.install,
            "red": self.exit,
        }, -1)
        self.onLayoutFinish.append(self.fetch_version_info)
        self.download_settings()
        self.load_bouquets()

    def fetch_version_info(self):
        try:
            response = requests.get(GITHUB_API_URL)
            response.raise_for_status()
            files = response.json()

            for file in files:
                if any(name in file["name"] for name in STATIC_NAMES) and file["name"].endswith(".zip"):
                    version_with_date = file["name"].replace(".zip", "")  # Izvlačenje naziva verzije i datuma
                    self["version_info"].setText(f"Version: ({version_with_date})")
                    return

            self["version_info"].setText(f"Version: (Date not available)")
        except Exception as e:
            self["version_info"].setText(f"Version: (Error fetching date)")

    def download_settings(self):
        self["status"].setText("Fetching file list from GitHub...")
        try:
            # Query GitHub API for available files
            response = requests.get(GITHUB_API_URL)
            response.raise_for_status()  # Raise error for bad response
            files = response.json()
            # Find desired ZIP file
            zip_url = None
            for file in files:
                if any(name in file["name"] for name in STATIC_NAMES) and file["name"].endswith(".zip"):
                    zip_url = file["download_url"]
                    break
            if not zip_url:
                raise Exception("No matching ZIP file found on GitHub.")
            # Download ZIP file
            self["status"].setText("Downloading settings from GitHub...")
            zip_path = os.path.join("/tmp", "latest.zip")
            zip_response = requests.get(zip_url)
            with open(zip_path, 'wb') as f:
                f.write(zip_response.content)
            # Extract ZIP file
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                temp_extract_path = "/tmp/temp_extract"
                if not os.path.exists(temp_extract_path):
                    os.makedirs(temp_extract_path)
                zip_ref.extractall(temp_extract_path)
                extracted_root = os.path.join(temp_extract_path, os.listdir(temp_extract_path)[0])
                if os.path.exists(TMP_DOWNLOAD):
                    shutil.rmtree(TMP_DOWNLOAD)
                shutil.move(extracted_root, TMP_DOWNLOAD)
            self["status"].setText("Settings downloaded and extracted successfully.")
            self.parse_satellites()
        except Exception as e:
            self["status"].setText(f"Error: {str(e)}")

    def load_bouquets(self):
        bouquets_file = os.path.join(TMP_DOWNLOAD, "bouquets.tv")
        if not fileExists(bouquets_file):
            self["status"].setText("Error: bouquets.tv not found!")
            return
        with open(bouquets_file, 'r') as file:
            bouquets = []
            for line in file:
                if "FROM BOUQUET" in line:
                    start = line.find('"') + 1
                    end = line.find('"', start)
                    if start != -1 and end != -1:
                        bouquet_name = line[start:end]
                        bouquets.append(bouquet_name)
            self["left_list"].setList(bouquets)
            self["status"].setText("Bouquets loaded successfully.")

    def select_item(self):
        selected = self["left_list"].getCurrent()
        if selected:
            if selected in self.selected_bouquets:
                self.selected_bouquets.remove(selected)
            else:
                self.selected_bouquets.append(selected)
            self["right_list"].setList(self.selected_bouquets)

    def copy_files(self):
        """
        Kopira selektovane bukete u ciljni direktorijum i ažurira bouquets.tv.
        """
        if not self.selected_bouquets:
            self["status"].setText("No bouquets selected!")
            return

        # Ciljni direktorijum
        target_dir = TMP_SELECTED
        if not os.path.exists(target_dir):
            try:
                os.makedirs(target_dir)
            except PermissionError:
                self["status"].setText("Permission denied: Unable to create directory.")
                return

        # Kopiranje fajlova
        copied_files = []
        for bouquet in self.selected_bouquets:
            source_path = os.path.join(TMP_DOWNLOAD, bouquet)
            destination_path = os.path.join(target_dir, bouquet)

            if os.path.exists(source_path):
                try:
                    shutil.copy(source_path, destination_path)
                    copied_files.append(bouquet)
                except Exception as e:
                    self["status"].setText(f"Error copying {bouquet}: {str(e)}")
                    return

        # Ažuriranje bouquets.tv
        bouquets_tv_path = os.path.join('/etc/enigma2', 'bouquets.tv')
        if os.path.exists(bouquets_tv_path):
            with open(bouquets_tv_path, 'r') as f:
                lines = f.readlines()

            updated = False
            for bouquet in copied_files:
                if not any(bouquet in line for line in lines):
                    tmp_bouquets_tv = os.path.join(TMP_DOWNLOAD, 'bouquets.tv')
                    if os.path.exists(tmp_bouquets_tv):
                        with open(tmp_bouquets_tv, 'r') as f:
                            for line in f:
                                if bouquet in line:
                                    lines.append(line)
                                    updated = True
                                    break

            if updated:
                with open(bouquets_tv_path, 'w') as f:
                    f.writelines(lines)

        self["status"].setText("Files copied and bouquets.tv updated successfully!")

    def install(self):
        """
        Instalira selektovane bukete u /etc/enigma2.
        """
        if not self.selected_bouquets:
            self.session.open(MessageBox, "No bouquets selected!", MessageBox.TYPE_ERROR)
            return

        self.session.openWithCallback(
            self.install_confirmed,
            MessageBox,
            "Install selected bouquets and common files?",
            MessageBox.TYPE_YESNO
        )

    def install_confirmed(self, result):
        """
        Potvrda instalacije selektovanih buketa i zajedničkih fajlova.
        """
        if not result:
            return

        enigma2_dir = "/etc/enigma2"
        tuxbox_dir = "/etc/tuxbox"
        installed_files = []

        # Lista zajedničkih fajlova za kopiranje
        common_files = {
            'satellites.xml': tuxbox_dir,  # satellites.xml ide u /etc/tuxbox
            'lamedb': enigma2_dir  # lamedb ide u /etc/enigma2
        }

        # Kopiranje selektovanih buketa
        for bouquet in self.selected_bouquets:
            source_path = os.path.join(TMP_SELECTED, bouquet)
            destination_path = os.path.join(enigma2_dir, bouquet)

            if os.path.exists(source_path):
                try:
                    shutil.copy(source_path, destination_path)
                    installed_files.append(bouquet)
                except Exception as e:
                    self.session.open(MessageBox, f"Failed to install {bouquet}: {str(e)}", MessageBox.TYPE_ERROR)
                    return

        # Kopiranje zajedničkih fajlova
        for file_name, target_dir in common_files.items():
            source_path = os.path.join(TMP_DOWNLOAD, file_name)
            destination_path = os.path.join(target_dir, file_name)

            if os.path.exists(source_path):
                try:
                    if not os.path.exists(target_dir):
                        os.makedirs(target_dir)  # Kreiranje direktorijuma ako ne postoji
                    shutil.copy(source_path, destination_path)
                    installed_files.append(file_name)
                except Exception as e:
                    self.session.open(MessageBox, f"Failed to copy common file {file_name}: {str(e)}",
                                      MessageBox.TYPE_ERROR)
                    return

        if installed_files:
            self.reload_settings()
            self["status"].setText("Installation successful! Common files and bouquets are now active.")
        else:
            self["status"].setText("No files installed.")

    def reload_settings(self):
        try:
            eDVBDB.getInstance().reloadServicelist()
            eDVBDB.getInstance().reloadBouquets()
            self.session.open(
                MessageBox,
                "Reload successful! New bouquets and common files are now active. .::ciefpsettings::.",
                MessageBox.TYPE_INFO,
                timeout=5
            )
        except Exception as e:
            self.session.open(
                MessageBox,
                "Reload failed: " + str(e),
                MessageBox.TYPE_ERROR,
                timeout=5
            )

    def up(self):
        self["left_list"].up()

    def down(self):
        self["left_list"].down()
    
    def exit(self):
        self.close()

def main(session, **kwargs):
    session.open(CiefpBouquetUpdater)        
        
def Plugins(**kwargs):
    return [
        PluginDescriptor(
            name="{0} v{1}".format(PLUGIN_NAME, PLUGIN_VERSION),
            description="Bouquets update Plugin",
            icon=PLUGIN_ICON,
            where=PluginDescriptor.WHERE_PLUGINMENU,
            fnc=main
        )
    ]
