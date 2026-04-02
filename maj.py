import os
import subprocess
from pathlib import Path

from qgis.core import QgsNetworkAccessManager
from qgis.PyQt.QtNetwork import QNetworkRequest
from qgis.PyQt.QtCore  import QUrl,QTimer
import xml.etree.ElementTree as ET

from .mapping_version import *


XML = "https://raw.githubusercontent.com/IGNF/collaboratif-plugins/main/plugins.xml?nocache=1"

class MajPlugins:
    def __init__(self):
        # Vérification des mises à jour des plugins IGN au lancement de QGIS
        # QTimer.singleShot(1000, self.on_verif_maj)
        self.current_dir = os.path.dirname(__file__)
        self.parent_dir = os.path.dirname(self.current_dir)
        self.path_exe = list(Path(self.parent_dir).glob("*PluginHub_Installer.exe"))[0]

    def on_verif_maj(self):
        self.execute_installeur()

    def download_plugins_xml(self):
        print("Téléchargement du fichier XML de mise à jour des plugins IGN...")
        # current_dir = os.path.dirname(__file__)
        # parent_dir = os.path.dirname(current_dir)

        nam = QgsNetworkAccessManager.instance()
        request = QNetworkRequest(QUrl(XML))

        reply = nam.get(request)
        reply.finished.connect(lambda : self.finish_download(reply,self.parent_dir))
        print("Téléchargement en cours...")

    def finish_download(self,reply, parent_dir):
        if reply.error():
            return

        data = reply.readAll()

        # enregistrement du fichier XML dans le dossier du plugin
        with open(Path(parent_dir)/"plugins.xml", "wb") as f:
            f.write(bytes(data))

        self.is_maj_plugins(Path(parent_dir) / "plugins.xml")

    def getplugin_from_xml(self,tmp_xml):
        tree = ET.parse(tmp_xml)
        root = tree.getroot()
        list_tmp = ""
        dico_plugin = {}
        # Parcourir les plugins
        for plugin in root.findall("pyqgis_plugin"):
            name = plugin.get("name")
            version = plugin.get("version")
            description = plugin.find("description")
            download_url = plugin.find("download_url").text
            dico_plugin[name] = [version, description.text,download_url]
            list_tmp += f"-{name}\n"
        return dico_plugin

    def is_maj_plugins(self,fic_xml):
        # comparer les versions des plugins installés avec celles du fichier XML téléchargé
        # et afficher une notification si une mise à jour est disponible
        plugins = self.getplugin_from_xml(fic_xml)
        text = ""
        for row, (nom, valeur) in enumerate(plugins.items()):
            version, description, lien = valeur
            print(nom, version, description, lien)
            version_local = self.get_version_plugins(nom, "version=")
            if version_local != version:
                text += "Une mise à jour est disponible pour les plugins IGN.\n\n"
                text += "Cliquez sur OUI pour installer\n\n"
                text += "Vous pourrez retrouver les mises à jour dans le menu \"IGN\" > \"Vérifiez la mise à jour des plugins\""
                res = QMessageBox.information(None, "Mise à jour disponible", text, QMessageBox.Yes | QMessageBox.No)
                if res == QMessageBox.Yes:
                    self.execute_installeur()
                if res == QMessageBox.No:
                    return
                break

     # retourne les infos des plugins dans le dossier de QGIS
    def get_version_plugins(self,plugin_name,type_info):
        fic_metadata = os.path.join(self.parent_dir, plugin_name,"metadata.txt")
        if os.path.exists(fic_metadata):
            with open(fic_metadata, "r", encoding="utf-8") as f:
                for line in f:
                    if line.startswith(type_info):
                        return line.strip().split("=")[1]
        return None

    def execute_installeur(self):
        try:
            subprocess.Popen([str(self.path_exe)], cwd=str(self.parent_dir))
        except Exception as e:
            QMessageBox.warning(None, "Erreur", f"Impossible de lancer le programme :\n{e}")






