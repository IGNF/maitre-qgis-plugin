import os
import subprocess
import importlib
from pathlib import Path

from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QDialog,QApplication
from qgis.PyQt.uic import loadUi
from qgis.core import QgsNetworkContentFetcher,QgsApplication
from qgis.PyQt.QtCore  import QUrl
from zipfile import ZipFile
# import pefile
import requests
import xml.etree.ElementTree as ET

from .mapping_version import *

INSTALLATEUR = "PluginIGN_Installer"
XML_RACINE = "https://raw.githubusercontent.com/IGNF/collaboratif-plugins/main/"
PACKAGES = ["pefile"]

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
    def __init__(self,iface):
        self.iface = iface
        self.installateur = None
        self.plugins_xml = None
        self.prefix = None
        self.path_xml_local = None
        self.current_dir = os.path.dirname(__file__)
        self.parent_dir = os.path.dirname(self.current_dir)
        self.path_exe = list(Path(self.parent_dir).glob(f"*{INSTALLATEUR}.exe"))

    def download_xml_plugins(self):
        # définir quel installateur est utilisé pour adapter le nom du XML à télécharger
        if len(self.path_exe) == 0:
            log(f"Installateur non trouvé dans le dossier : {self.parent_dir}")
            return

        if len(self.path_exe) > 1:
            log("Plusieurs installateurs trouvés dans le dossier, impossible de déterminer lequel est utilisé :")
            return

        # formatage de l'url de téléchargement du XML en fonction du nom de l'installateur trouvé dans le dossier
        exe_ss_ext = self.path_exe[0].stem
        self.prefix = exe_ss_ext.replace(INSTALLATEUR, "")
        self.prefix = self.prefix.replace("_", "")
        self.prefix = self.prefix.lower()
        if self.prefix != "":
            self.prefix = f"_{self.prefix}"
        url = rf"{XML_RACINE}plugins{self.prefix}.xml?nocache=1"
        # formatage du chemin local du XML dans le dossier du plugin
        self.path_xml_local = Path(self.parent_dir) / f"plugins{self.prefix}.xml"

        log(f"Téléchargement du xml : {url}")
        self.fetcher = QgsNetworkContentFetcher()
        self.fetcher.finished.connect(self.finish_download)
        self.fetcher.fetchContent(QUrl(url))

    def finish_download(self):
        reply = self.fetcher.reply()
        from qgis.PyQt.QtNetwork import QNetworkReply
        if reply.error() != QNetworkReply.NetworkError.NoError:
            log(f"Erreur de téléchargement du fichier XML : {reply.errorString()}")
            return
        data = self.fetcher.contentAsString()

        # enregistrement du fichier XML dans le dossier du plugin
        try:
            with open(self.path_xml_local, "w") as f:
                f.write(data)
            log(f"Enregistrement terminé de : {self.path_xml_local}")
            # liste des plugins trouvés dans le XML
            self.plugins_xml = self.getplugin_from_xml(self.path_xml_local)
            # y a-t-il une mise à jour de l'installateur à notifier ?
            if self.is_maj_installateur():
                self.installe_installateur()
            # y a-t-il des mises à jour de plugins à notifier ?
            self.is_maj_plugins()
        except Exception as e:
            log(f"Erreur du fichier XML : {e}")
            return

    def getplugin_from_xml(self,tmp_xml,all = False):
        tree = ET.parse(tmp_xml)
        root = tree.getroot()
        list_tmp = ""
        dico_plugin = {}
        # Parcourir les plugins
        for plugin in root.findall("pyqgis_plugin"):
            name = plugin.get("name")
            log(f"plugin trouvé dans le XML : {name}")
            # on ne prend pas en compte l'installateur pour la notification des mises à jour
            if not all:
                if INSTALLATEUR in name:
                    self.installateur = plugin
                    continue
            version = plugin.get("version")
            description = plugin.find("description")
            download_url = plugin.find("download_url").text
            dico_plugin[name] = [version, description.text,download_url]
            list_tmp += f"-{name}\n"
        return dico_plugin

    def dial_maj(self):
        self.dlgMaj = QDialog()
        loadUi(os.path.dirname(__file__) + "/maj.ui", self.dlgMaj)
        icon_path = Path(__file__).parent /"icons"/ "icon.png"
        self.dlgMaj.setWindowIcon(QIcon(str(icon_path)))
        self.dlgMaj.setWindowFlags(WindowCloseButtonHint)
        self.dlgMaj.listWidget_maj.setSelectionMode(NoSelection)
        self.dlgMaj.listWidget_maj.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.dlgMaj.setWindowTitle("Mise à jour disponible")
        self.dlgMaj.pushButton_executer_installateur.clicked.connect(self.execute_installeur)
        self.dlgMaj.pushButton_fermer.clicked.connect(self.dlgMaj.close)# self.dlgMaj.exec()

    def is_maj_plugins(self):
        # comparer les versions des plugins installés (lecture metadata.txt) avec celles du fichier XML téléchargé
        # et afficher une notification si une mise à jour est disponible
        self.dial_maj()
        is_maj = False
        for nom, (version, description, lien) in self.plugins_xml.items():
            version_local = self.get_info_plugins(nom, "version=")
            if version_local is None:
                log(f"Plugin {nom} non trouvé localement ou metadata.txt manquant, impossible de vérifier la version.")
                continue
            if version_local != version:
                log(f"Mise à jour disponible pour {nom} : version locale : {version_local}, version disponible : {version}")
                self.dlgMaj.listWidget_maj.addItem(nom)
                is_maj = True
        if is_maj:
            self.dlgMaj.exec()

    def is_maj_installateur(self):
        # comparer la version de l'installateur (lecture metadata.txt) avec celle du fichier XML téléchargé
        # et afficher une notification si une mise à jour est disponible
        version_xml = self.installateur.get('version')
        version_local = self.get_version_installateur()
        if version_local is None:
            log(f"Installateur {INSTALLATEUR} non trouvé localement (ou pefile n'est pas installé), impossible de vérifier la version.")
            return False

        if version_local != version_xml:
            log(f"Mise à jour disponible pour {self.installateur.get('name')} : version locale : {version_local}, version disponible : {version_xml}")
            log (f"\tInstallation de la mise à jour de l'installateur : {self.installateur.get('name')} ...")
            return True
        else:
            log(f"{self.installateur.get('name')} est à jour (version locale :{version_local} -- version_xml : {version_xml})")

    def installe_installateur(self):
        zip_path = Path(self.parent_dir) / f"{self.installateur.get('name')}.zip"
        # suppression du fichier zip s'il existe déjà
        self.suppr_fichier(zip_path)
        # téléchargement de l'installateur (zip) depuis le lien du XML
        url = self.installateur.find("download_url").text
        self.download_exe(url, zip_path)
        # supprimer l'exe s'il existe déjà dans le dossier avant de dézipper le nouveau
        self.suppr_fichier(self.path_exe[0])
        # dézipper le fichier téléchargé
        self.dezippe_file(zip_path)


    def suppr_fichier(self, zip_path):
        if os.path.exists(zip_path):
            try:
                os.remove(zip_path)
                log(f"\tFichier supprimé : \n\t\t{zip_path}")
            except Exception as e:
                log(f"\tErreur lors de la suppression du fichier  : \n\t\t{e}")

    # retourne les infos des plugins dans le dossier de QGIS
    def get_info_plugins(self, plugin_name, type_info):
        fic_metadata = os.path.join(self.parent_dir, plugin_name,"metadata.txt")
        if os.path.exists(fic_metadata):
            with open(fic_metadata, "r", encoding="utf-8") as f:
                for line in f:
                    if line.startswith(type_info):
                        return line.strip().split("=")[1]
        return None

    def get_version_installateur(self):
        if self.need_package():
            return None # pefile dans ce cas
        import pefile
        if not self.path_exe:
            return None
        with pefile.PE(self.path_exe[0]) as pe:
            # Extraire les informations de version
            for fileinfo in pe.FileInfo:
                for entry in fileinfo:
                    if entry.Key.decode() == 'StringFileInfo':
                        for st in entry.StringTable:
                            for k, v in st.entries.items():
                                if k.decode() == "FileVersion":
                                    return v.decode()
        return None

    def download_exe(self,url,destination):
        try:
            response = requests.get(url, stream=True)
            response.raise_for_status()
            with open(destination, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            log(f"\tTéléchargement terminé : \n\t\t{destination}")

        except Exception as e:
            log(f"\tErreur de téléchargement : \n\t\t{e}")

    def dezippe_file(self,zip_path):
        # Chemin du fichier zip
        # Dossier de destination
        extract_to = Path(self.parent_dir)
        # Décompression
        with ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_to)
            log(f"\tFichier zip extrait : \n\t\t{zip_path}")
        # supprimer le fichier zip après extraction
        try:
            os.remove(zip_path)
            log(f"\tFichier zip supprimé : \n\t\t{zip_path}")
        except Exception as e:
            log(f"\tErreur lors de la suppression du fichier zip : \n\t\t{e}")

    def execute_installeur(self):
        # test si le dial de notification de mise à jour est ouvert et le fermer avant de lancer l'installateur
        try:
            if getattr(self, "dlgMaj", None):
                self.dlgMaj.close()
        except Exception:
            pass
        try:
            subprocess.Popen([str(self.path_exe[0])], cwd=str(self.parent_dir))
        except Exception as e:
            text = (f"Le programme de mise à jour est introuvable :"
                    f"Veuillez lancer l'installateur fournit (*_{INSTALLATEUR}.exe)")
            QMessageBox.warning(None, "Erreur", text)

    def need_package(self):
        # test si les packages necessaires sont installés
        self.package_manquants = ""
        for package in PACKAGES:
            try:
                importlib.import_module(package)
            except ImportError:
                self.package_manquants = package
        #  tout est OK
        if not self.package_manquants:
            return False
        texte = "Le plugin Maître nécessite le package <span style='color:red;'>pefile</span><br><br>"
        texte += "Voulez vous l'installer maintenant?"
        reponse = QMessageBox.question(
            self.iface.mainWindow(),
            "Package manquant",
            texte,
            QMessageBox.Yes | QMessageBox.No,QMessageBox.Yes)
        if reponse == QMessageBox.Yes:
            self.install_package()
            return True
        else:
            texte = "package manquant : <span style='color:red;'>pefile</span><br>"
            texte += "Si une mise à jour de *_PluginIGN_installer existe elle ne pourra pas s'installer"
            QMessageBox.warning(self.iface.mainWindow(),"Avertissement",texte)
        return True

    def install_package(self):
        prefix = Path(QgsApplication.prefixPath())
        install_root = prefix.parent.parent
        osgeo_bat = install_root / "OSGeo4W.bat"
        if not osgeo_bat.exists():
            text = f"Fichier introuvable : {osgeo_bat}\n"
            text += f"Impossible d'installer le package pefile"
            QMessageBox.critical(self.iface.mainWindow(),"Erreur",text)
            return

        texte = "L'installation va commencer, veuillez attendre le message de fin d'installation du package"
        QMessageBox.information(self.iface.mainWindow(), "Installation du package", texte)
        subprocess.run([str(osgeo_bat), "python", "-m", "pip", "install", "pefile"],shell=True)
        text = "Packages installés ! \nVeuillez redémarrer QGIS pour prendre en compte le package."
        QMessageBox.information(self.iface.mainWindow(), "Installation du package", text)






