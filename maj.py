import os
import subprocess
from pathlib import Path

from qgis.core import QgsNetworkAccessManager
from qgis.PyQt.QtNetwork import QNetworkRequest
from qgis.PyQt.QtCore  import QUrl,QTimer
import xml.etree.ElementTree as ET

from .mapping_version import *

INSTALLATEUR = "PluginHub_Installer"
UPDATE = "update"


XML = "https://raw.githubusercontent.com/IGNF/collaboratif-plugins/main/plugins.xml?nocache=1"

def log(message,reset=False):
    """
    Écrit un message dans le fichier de log avec un horodatage.
    Le fichier est ouvert en mode append pour ne pas écraser les données.
    """
    current_directory = os.path.dirname(__file__)
    # Remonter d'un niveau
    parent_directory = os.path.abspath(Path(current_directory, os.pardir))
    fichier = Path(parent_directory, "log_maitre.txt")
    mode = "w" if reset else "a"  # "w" pour écraser, "a" pour ajouter
    with open(fichier, mode, encoding="utf-8") as f:
        f.write(f"{message}\n")

class MajPlugins:
    def __init__(self):
        # Vérification des mises à jour des plugins IGN au lancement de QGIS
        self.current_dir = os.path.dirname(__file__)
        self.parent_dir = os.path.dirname(self.current_dir)
        self.path_exe = list(Path(self.parent_dir).glob("*PluginHub_Installer.exe"))

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
            # on ne prend pas en compte l'installateur pour la notification des mises à jour
            if INSTALLATEUR in name:
                continue
            version = plugin.get("version")
            description = plugin.find("description")
            download_url = plugin.find("download_url").text
            dico_plugin[name] = [version, description.text,download_url]
            list_tmp += f"-{name}\n"
        return dico_plugin

    def is_maj_plugins(self,fic_xml):
        # comparer les versions des plugins installés (lecture metadata.txt) avec celles du fichier XML téléchargé
        # et afficher une notification si une mise à jour est disponible
        plugins = self.getplugin_from_xml(fic_xml)
        text = ""
        for row, (nom, valeur) in enumerate(plugins.items()):
            if nom == UPDATE:
                continue
            version, description, lien = valeur
            version_local = self.get_version_plugins(nom, "version=")
            if version_local != version:
                log(f"Une mise à jour est disponible pour le plugin {nom} : version locale {version_local} - version disponible {version}")
                text += "Une mise à jour est disponible pour les plugins IGN.\n\n"
                text += "Cliquez sur OUI pour installer\n\n"
                text += "Vous pourrez retrouver les mises à jour dans le menu \"IGN\" > \"Vérifiez la mise à jour des plugins\""

                msg_box = QMessageBox()
                msg_box.setIcon(QMessageBox.Icon.Information)
                msg_box.setWindowTitle("Mise à jour disponible")
                msg_box.setText(text)
                msg_box.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
                # Mettre la fenêtre au premier plan
                msg_box.setWindowFlags(msg_box.windowFlags() | Qt.WindowType.WindowStaysOnTopHint)
                res = msg_box.exec()

                if res == QMessageBox.Yes:
                    self.execute_installeur()
                if res == QMessageBox.No:
                    return
                break

    # retourne les infos des plugins dans le dossier de QGIS
    def get_version_plugins(self, plugin_name, type_info):
        fic_metadata = os.path.join(self.parent_dir, plugin_name,"metadata.txt")
        if os.path.exists(fic_metadata):
            with open(fic_metadata, "r", encoding="utf-8") as f:
                for line in f:
                    if line.startswith(type_info):
                        return line.strip().split("=")[1]
        return None

    def execute_installeur(self):
        try:
            subprocess.Popen([str(self.path_exe[0])], cwd=str(self.parent_dir))
        except Exception as e:
            text = (f"Le programme de mise à jour est introuvable :"
                    f"Veuillez lancer l'installateur fournit (*_PluginHub_Installer.exe)")
            QMessageBox.warning(None, "Erreur", text)






