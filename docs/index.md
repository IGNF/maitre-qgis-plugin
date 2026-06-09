<table>
<colgroup>
<col style="width: 21%" />
<col style="width: 78%" />
</colgroup>
<tbody>
<tr>
<td rowspan="2"><img src="images/image1.jpeg"
style="width:1.38681in;height:1.47153in"
alt="logo_IGN_pour_lettre" /></td>
<td style="text-align: center;font-size: 24px;"><strong>Plugin Maitre
v1.7.2</strong></td>
</tr>
<tr>
<td style="text-align: center;"></td>
</tr>
</tbody>
</table>
  

<div  style="background-color: white; border: 1px solid black; padding: 10px; text-align: justify;">
  <h2 style="color: #00ADC5">Sommaire</h2>
</div>


- [1. Prérequis](#1-prérequis)
- [2. Résumé](#2-résumé)
- [3. Installation](#3-installation)
- [4. Présentation](#4-présentation)
	- [4.1 Onglet menu IGN](#41-onglet-menu-ign)
	- [4.2 Barres d’outils](#42-barres-doutils)
	- [4.3 Suivi des versions et documentation](#43-suivi-des-versions-et-documentation)




<div  style="background-color: #00ADC5; border: 1px solid black; padding: 5px; text-align: justify;margin-bottom:10px;">
  <h2 id="1-prérequis" style="color: white;margin:0;" >1. Prérequis</h2>
</div>

Version de QGIS : version 3 supérieure à 3.28
Cette version est compatible QGIS 4

<div  style="background-color: #00ADC5; border: 1px solid black; padding: 5px; text-align: justify;margin-bottom:10px;">
  <h2 id="2-résumé" style="color: white;margin:0;" >2. Résumé</h2>
</div>

Le plugin Maitre crée un menu IGN dans la barre des menus.

Ce menu permet de configurer l'interface (intégration des différents plugins IGN dans les menus et / ou dans des barres d'outils, d'ouvrir les documentations des plugins IGN, de vérifier les mises à jour disponibles des plugins pris en compte


<div  style="background-color: #00ADC5; border: 1px solid black; padding: 5px; text-align: justify;margin-bottom:10px;">
  <h2 id="3-installation" style="color: white;margin:0;" >3. Installation</h2>
</div>

Le plugin Maitre s’installe avec l’exécutable d’installation
(\*\_PluginIGN_installer »

Le plugin a besoin du package « pefile » pour tester la mise à jour de
l’installateur.

Si ce package n’est pas installé le plugin maitre propose de
l’installer :

![](images/image2.png)

Si on choisit de ne pas l’installer ce n’est pas bloquant mais si une
mise à jour de l’installateur est disponible, elle ne pourra pas
s’installer.

Si on choisit d’installer le package « pefile » il est primordial à la
fin de l’installation de redémarrer QGIS pour que ce package soit prit
en compte.

<div  style="background-color: #00ADC5; border: 1px solid black; padding: 5px; text-align: justify;margin-bottom:10px;">
  <h2 id="4-présentation" style="color: white;margin:0;" >4. Présentation</h2>
</div>

![](images/image3.png)

L’interface permet d’organiser l’affichage des plugins en les classant
dans des onglets.

### <span style="color: white; background-color: #00ADC5; padding: 2px 5px;">4.1 Onglet menu IGN</span>  

Par défaut l’onglet menu IGN affiche dans le menu IGN les plugins
cochés.

Les plugins proposés sont détectés automatiquement.

### <span style="color: white; background-color: #00ADC5; padding: 2px 5px;">4.2 Barres d'outils</span> 

- Ajouter une barre d’outils ![](images/image4.png)

Choisir un nom et cliquer sur Ajouter crée un nouvel onglet. Les
plugins cochés dans cet onglet s’ajouteront dans un groupe dans la
barre d’outils QGIS.

<figure>
<img src="images/image6.png"
style="width:1.97177in;height:2.52493in" />
<figcaption aria-hidden="true"><p><img src="images/image5.png"
style="width:2.30554in;height:0.95074in" /></p></figcaption>
</figure>

- Renommer la barre d’outils ![](images/image7.png)

Pour changer le nom du groupe (routier pour l’exemple ci-dessus).

### <span style="color: white; background-color: #00ADC5; padding: 2px 5px;">4.3 Suivi des versions et documentation</span> 

 <img src="images/image8.png"> Affiche l’historique des versions la documentation de l’outil.

 ![](images/image9.png) 
