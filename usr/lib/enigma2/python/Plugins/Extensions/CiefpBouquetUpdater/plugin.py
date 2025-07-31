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

PLUGIN_VERSION = "1.4"
PLUGIN_ICON = "icon.png"
PLUGIN_NAME = "CiefpBouquetUpdater"
TMP_DOWNLOAD = "/tmp/ciefp-E2-75E-34W"
TMP_SELECTED = "/tmp/CiefpBouquetUpdater"
PLUGIN_DESCRIPTION = "Bouquets update Plugin"
GITHUB_API_URL = "https://api.github.com/repos/ciefp/ciefpsettings-enigma2-zipped/contents/"
STATIC_NAMES = ["ciefp-E2-75E-34W"]

class CiefpBouquetUpdater(Screen):
    skin = """
        <screen position="center,center" size="1600,800" title="..:: Ciefp Bouquet Updater ::..    (Version{version})">
            <widget name="left_list" position="0,0" size="620,700" scrollbarMode="showOnDemand" itemHeight="33" font="Regular;28" />
            <widget name="right_list" position="630,0" size="610,700" scrollbarMode="showOnDemand" itemHeight="33" font="Regular;28" />
            <widget name="background" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/CiefpBouquetUpdater/background.png" position="1240,0" size="360,800" />
            <widget name="status" position="0,710" size="840,50" font="Regular;24" />
            <widget name="red_button" position="0,750" size="150,35" font="Bold;28" halign="center" backgroundColor="#9F1313" foregroundColor="#000000" />
            <widget name="green_button" position="170,750" size="150,35" font="Bold;28" halign="center" backgroundColor="#1F771F" foregroundColor="#000000" />
            <widget name="yellow_button" position="340,750" size="150,35" font="Bold;28" halign="center" backgroundColor="#9F9F13" foregroundColor="#000000" />
            <widget name="version_info" position="510,750" size="480,40" font="Regular;20" foregroundColor="#FFFFFF" />
        </screen>
    """.format(version=PLUGIN_VERSION)

    def __init__(self, session):
        Screen.__init__(self, session)
        self.session = session
        self.selected_bouquets = []  # Lista selektovanih naziva buketa
        self.bouquet_names = {}  # Mapiranje naziva na fajlove
        self["left_list"] = MenuList([])
        self["right_list"] = MenuList([])
        self["background"] = Pixmap()
        self["status"] = Label("Loading bouquets...")
        self["green_button"] = Label("Copy")
        self["yellow_button"] = Label("Install")
        self["red_button"] = Label("Exit")
        self["version_info"] = Label("")
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
                    version_with_date = file["name"].replace(".zip", "")
                    self["version_info"].setText(f"Version: ({version_with_date})")
                    return
            self["version_info"].setText(f"Version: (Date not available)")
        except Exception as e:
            self["version_info"].setText(f"Version: (Error fetching date)")

    def download_settings(self):
        self["status"].setText("Fetching file list from GitHub...")
        try:
            response = requests.get(GITHUB_API_URL)
            response.raise_for_status()
            files = response.json()
            zip_url = None
            for file in files:
                if any(name in file["name"] for name in STATIC_NAMES) and file["name"].endswith(".zip"):
                    zip_url = file["download_url"]
                    break
            if not zip_url:
                raise Exception("No matching ZIP file found on GitHub.")
            self["status"].setText("Downloading settings from GitHub...")
            zip_path = os.path.join("/tmp", "latest.zip")
            zip_response = requests.get(zip_url)
            with open(zip_path, 'wb') as f:
                f.write(zip_response.content)
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

    def parse_satellites(self):
        pass  # Ova funkcija nije implementirana u originalnom kodu, ostavljena kao placeholder

    def load_bouquets(self):
        self.bouquet_names = {}  # Rečnik: {puna_linija: ime_fajla}
        bouquet_dir = TMP_DOWNLOAD
        bouquets_file = os.path.join(bouquet_dir, "bouquets.tv")

        if not os.path.exists(bouquet_dir):
            self["status"].setText("Error: Temporary directory not found!")
            return

        # Čitanje redosleda iz bouquets.tv
        bouquet_order = []
        if fileExists(bouquets_file):
            with open(bouquets_file, 'r', encoding='utf-8') as file:
                for line in file:
                    if "FROM BOUQUET" in line:
                        start = line.find('"') + 1
                        end = line.find('"', start)
                        if start != -1 and end != -1:
                            bouquet_file = line[start:end]
                            bouquet_order.append(bouquet_file)
        else:
            self["status"].setText("Error: bouquets.tv not found!")
            return

        # Skeniranje .tv fajlova i izvlačenje naziva
        bouquet_display_list = []
        name_to_file = {}

        for bouquet_file in bouquet_order:
            file_path = os.path.join(bouquet_dir, bouquet_file)
            if os.path.exists(file_path):
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        first_line = f.readline().strip()
                        if first_line.startswith("#NAME"):
                            display_name = first_line.replace("#NAME", "", 1).strip()  # Uklanjamo #NAME
                            self.bouquet_names[first_line] = bouquet_file
                            name_to_file[bouquet_file] = display_name
                except Exception as e:
                    self["status"].setText(f"Error reading {bouquet_file}: {str(e)}")
                    return

        # Popunjavanje liste prema redosledu iz bouquets.tv
        for bouquet_file in bouquet_order:
            if bouquet_file in name_to_file:
                bouquet_display_list.append(name_to_file[bouquet_file])

        if not bouquet_display_list:
            self["status"].setText("No valid bouquet files found!")
            return

        self["left_list"].setList(bouquet_display_list)
        self["status"].setText("Bouquets loaded successfully.")

    def select_item(self):
        selected_name = self["left_list"].getCurrent()
        if selected_name:
            if selected_name in self.selected_bouquets:
                self.selected_bouquets.remove(selected_name)
            else:
                self.selected_bouquets.append(selected_name)
            self["right_list"].setList(self.selected_bouquets)

    def copy_files(self):
        if not self.selected_bouquets:
            self["status"].setText("No bouquets selected!")
            return

        target_dir = TMP_SELECTED
        if not os.path.exists(target_dir):
            try:
                os.makedirs(target_dir)
            except PermissionError:
                self["status"].setText("Permission denied: Unable to create directory.")
                return

        copied_files = []
        for bouquet_name in self.selected_bouquets:
            bouquet_file = next((f for l, f in self.bouquet_names.items() if bouquet_name in l), None)
            if not bouquet_file:
                continue
            source_path = os.path.join(TMP_DOWNLOAD, bouquet_file)
            destination_path = os.path.join(target_dir, bouquet_file)

            if os.path.exists(source_path):
                try:
                    shutil.copy(source_path, destination_path)
                    copied_files.append(bouquet_file)
                except Exception as e:
                    self["status"].setText(f"Error copying {bouquet_file}: {str(e)}")
                    return

        bouquets_tv_path = os.path.join('/etc/enigma2', 'bouquets.tv')
        if os.path.exists(bouquets_tv_path):
            with open(bouquets_tv_path, 'r') as f:
                lines = f.readlines()

            updated = False
            for bouquet_file in copied_files:
                if not any(bouquet_file in line for line in lines):
                    tmp_bouquets_tv = os.path.join(TMP_DOWNLOAD, 'bouquets.tv')
                    if os.path.exists(tmp_bouquets_tv):
                        with open(tmp_bouquets_tv, 'r') as f:
                            for line in f:
                                if bouquet_file in line:
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
        if not result:
            return

        enigma2_dir = "/etc/enigma2"
        installed_files = []

        common_files = {
            'lamedb': enigma2_dir
        }

        # Kopiranje selektovanih buketa uz brisanje starih fajlova
        for bouquet_name in self.selected_bouquets:
            bouquet_file = next((f for l, f in self.bouquet_names.items() if bouquet_name in l), None)
            if not bouquet_file:
                continue
            source_path = os.path.join(TMP_SELECTED, bouquet_file)
            destination_path = os.path.join(enigma2_dir, bouquet_file)

            if os.path.exists(source_path):
                try:
                    if os.path.exists(destination_path):
                        os.remove(destination_path)  # Briše stari fajl pre kopiranja
                    shutil.copy(source_path, destination_path)
                    installed_files.append(bouquet_file)
                except Exception as e:
                    self.session.open(MessageBox, f"Failed to install {bouquet_file}: {str(e)}", MessageBox.TYPE_ERROR)
                    return

        # Kopiranje zajedničkih fajlova uz brisanje starih
        for file_name, target_dir in common_files.items():
            source_path = os.path.join(TMP_DOWNLOAD, file_name)
            destination_path = os.path.join(target_dir, file_name)

            if os.path.exists(source_path):
                try:
                    if not os.path.exists(target_dir):
                        os.makedirs(target_dir)
                    if os.path.exists(destination_path):
                        os.remove(destination_path)  # Briše stari lamedb pre kopiranja
                    shutil.copy(source_path, destination_path)
                    installed_files.append(file_name)
                except Exception as e:
                    self.session.open(MessageBox, f"Failed to copy common file {file_name}: {str(e)}", MessageBox.TYPE_ERROR)
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
