import os
import subprocess
from pathlib import Path

from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QDialog
from qgis.PyQt.uic import loadUi
from qgis.core import QgsNetworkAccessManager
from qgis.PyQt.QtNetwork import QNetworkRequest
from qgis.PyQt.QtCore  import QUrl,QTimer
import xml.etree.ElementTree as ET

from .mapping_version import *

INSTALLATEUR = "PluginIGN_Installer"
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
        self.path_exe = list(Path(self.parent_dir).glob(f"*{INSTALLATEUR}.exe"))

    def on_verif_maj(self):
        self.execute_installeur()

    def download_plugins_xml(self):
        log("Téléchargement du fichier XML de mise à jour des plugins IGN...")
        # current_dir = os.path.dirname(__file__)
        # parent_dir = os.path.dirname(current_dir)

        nam = QgsNetworkAccessManager.instance()
        request = QNetworkRequest(QUrl(XML))

        self.reply = nam.get(request)
        self.reply.finished.connect(lambda : self.finish_download(self.reply,self.parent_dir))
        log(f"preparation d'enregistrement sous  : {Path(self.parent_dir)/"plugins.xml"}...")
        log(f"Téléchargement en cours de {XML}...")

    def finish_download(self,reply, parent_dir):
        # log(f"enregistrement de : {Path(parent_dir)/"plugins.xml"}...")
        if reply.error():
            log(f"Erreur de telechargement du fichier XML : {reply.errorString()}")
            return
        data = reply.readAll()
        # enregistrement du fichier XML dans le dossier du plugin
        try:
            with open(Path(parent_dir)/"plugins.xml", "wb") as f:
                f.write(bytes(data))
            log(f"enregistrement de : {Path(parent_dir)/"plugins.xml"} terminé.")
            self.is_maj_plugins(Path(parent_dir) / "plugins.xml")
        except Exception as e:
            log(f"Erreur du fichier XML : {e}")
            return

    def getplugin_from_xml(self,tmp_xml):
        tree = ET.parse(tmp_xml)
        root = tree.getroot()
        list_tmp = ""
        dico_plugin = {}
        # Parcourir les plugins
        for plugin in root.findall("pyqgis_plugin"):
            name = plugin.get("name")
            log(f"plugin trouvé dans le XML : {name}")
            # on ne prend pas en compte l'installateur pour la notification des mises à jour
            if INSTALLATEUR in name:
                continue
            version = plugin.get("version")
            description = plugin.find("description")
            download_url = plugin.find("download_url").text
            dico_plugin[name] = [version, description.text,download_url]
            list_tmp += f"-{name}\n"
        return dico_plugin

    def open_installateur(self):
        self.execute_installeur()

    def dial_maj(self):
        self.dlgMaj = QDialog()
        loadUi(os.path.dirname(__file__) + "/maj.ui", self.dlgMaj)
        icon_path = Path(__file__).parent /"icons"/ "icon.png"
        self.dlgMaj.setWindowIcon(QIcon(str(icon_path)))
        self.dlgMaj.setWindowFlags(WindowCloseButtonHint)
        self.dlgMaj.listWidget_maj.setSelectionMode(NoSelection)
        self.dlgMaj.listWidget_maj.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.dlgMaj.setWindowTitle("Mise à jour disponible")
        self.dlgMaj.pushButton_executer_installateur.clicked.connect(self.open_installateur)
        self.dlgMaj.pushButton_fermer.clicked.connect(self.dlgMaj.close)# self.dlgMaj.exec()

    def is_maj_plugins(self,fic_xml):
        # comparer les versions des plugins installés (lecture metadata.txt) avec celles du fichier XML téléchargé
        # et afficher une notification si une mise à jour est disponible
        plugins = self.getplugin_from_xml(fic_xml)
        self.dial_maj()
        is_maj = False
        for nom, (version, description, lien) in plugins.items():
            version_local = self.get_version_plugins(nom, "version=")
            if version_local is None:
                log(f"Plugin {nom} non trouvé localement ou metadata.txt manquant, impossible de vérifier la version.")
                continue
            if version_local != version:
                self.dlgMaj.listWidget_maj.addItem(nom)
                is_maj = True
        if is_maj:
            self.dlgMaj.exec()

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
                    f"Veuillez lancer l'installateur fournit (*_{INSTALLATEUR}.exe)")
            QMessageBox.warning(None, "Erreur", text)






