# 📘 Manuel utilisateur – Application X-Rite 310

  

Ce manuel vous guidera dans l'utilisation de l'application X-Rite 310 et la configuration du densitomètre.

  

---

  

## 🗂️ Sommaire

  

- [1. Présentation de l'application](#1-presentation-de-lapplication)
- [2. Interface principale](#2-interface-principale)
- [3. Connexion avec le densitomètre](#3-connexion-avec-le-densitometre)
- [4. Configuration du densitomètre X-Rite 310](#4-configuration-du-densitometre-x-rite-310)
- [5. Modes de fonctionnement](#5-modes-de-fonctionnement)
- [6. Dépannage courant](#6-depannage-courant)

  

---

  

## 1. Présentation de l'application

  

L’application permet de :

  

- Recevoir automatiquement les mesures densitométriques du X-Rite 310 via port série.

- Visualiser les courbes de densité pour les canaux V/C/M/Y, etc...

- Comparer les mesures à des courbes de référence.

- observer l'évolutions des mesures danss le temps.

- Exporter/importer des fichiers de mesure.

  

---

  

## 2. Interface principale

  

L'application se compose de plusieurs onglets :

  

- **Communication** : permet de configurer le port COM, le débit (baudrate), etc...

- **Historic** : permet de comparer les valeurs(gamma, d-min, d-max) de plusieurs fichiers de mesures

- **Courbes** : un onglet par jeu de courbes. On peut en ajouter, supprimer, renommer.

- **Barre de menu** :
	- **Fichier** : 
		- ouvrir un ficher de mesure,
		- sauvegarder un fichier de mesure,
		- ouvrir le dossier de mesure

	- **Édition** : réinitialiser les mesures

	- **Aide** :
		- manuel de densitométrie,
		- manuel utilisateur du densitomètre X-rite 310,
		- consulter ce manuel
  

---

  

## 3. Connexion avec le densitomètre

  

### Configuration minimale

  

- Connecter le densitomètre via un **câble RS232 droit**.

- Utiliser un adaptateur **USB–RS232 compatible** si nécessaire et installer le driver correspondant.

- Ouvrir le port COM correspondant dans l'application.

  

### Réglages logiciels

  
Dans l’onglet **Communication**, sélectionner :

- **Port série COM** approprié (COM 3 ou 4 le plus souvent, dépendant du cable/adaptateur utilisé)
- **Baudrate** : `1200` (recommandé) ou `300` (plus lent mais plus stable si problème)

  

---

  

## 4. Configuration du densitomètre X-Rite 310

Allumer le densitomètre, puis entrer successivement les **modes suivants** :


> ℹ️ les modes sélectionnés sont sauvegardés apres extinction du densitomètre, il n'est donc pas nécéssaire de faire cette manipulation à chaque usage

  

### ⚙️ Réglage recommandé (mode série automatique, 1200 bauds)

| Étape | Appuyer sur | Effet attendu |
|---------------------|-------------------------|-------------------------|
| Entrer mode         | `F → MODE → 11`         | Active le mode TECHNET |
| Définir baudrate    | `F → MODE → 13`         | 1200 bauds             |
| Format complet      | `F → MODE → 18`         | Données longues        |
| Envoi auto          | `F → MODE → 03`         | Envoi automatique après mesure |
| Format sur 1 ligne  | `F → MODE → 21`         | Valeurs sur une seule ligne |

> ⚠️ Ne pas activer le mode 10 ni 14/15 si mode 11 est actif.


---
  

## 5. Modes de fonctionnement

| Mode | Description |
| ------ | ------------- |
| `12` | 300 bauds, plus lent, utile pour les câbles longs ou adaptateurs peu fiables |
| `13` | 1200 bauds, rapide et recommandé pour usage courant |
| `03` | Auto-print : déclenchement automatique de l’envoi des données |
| `05` | Auto-print avec date/heure incluse |
| `18` | Format long (plus d'infos, utile pour la courbe gamma) |
| `21` | Sortie sur une ligne sans retour chariot |


---
  

## 6. Dépannage courant

### ❌ Je n’ai rien en sortie

- Vérifier que le port COM sélectionné est correct.

- Vérifier que le baudrate correspond à celui du densitomètre.

- Vérifier que le bouton **PRINT** du 310 a bien été pressé(un bip sonore doit se faire entendre).

- Si rien ne sort même après `PRINT`, vérifier que le **mode 03 est activé**.
  

---


## 📘 Manuel externe (disponible dans le dossiers docs)

- [X-rite 310 densitometer operation manual](cours_sensitometrie.pdf)

- [Cours de sentitométrie(Jacques VERREES - INSAS)](310-42_310_Densitometer_Operation_Manual_en.pdf)