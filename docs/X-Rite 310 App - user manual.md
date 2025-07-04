# 📘 Manuel utilisateur – Application X-Rite 310

Ce manuel vous guidera dans l'utilisation de l'application X-Rite 310 et la configuration du densitomètre.

---

## 🗂️ Sommaire

- [1. Présentation de l'application](#1-présentation-de-lapplication)
- [2. Interface principale](#2-interface-principale)
- [3. Connexion avec le densitomètre](#3-connexion-avec-le-densitomètre)
- [4. Configuration du densitomètre X-Rite 310](#4-configuration-du-densitomètre-x-rite-310)
- [5. Modes de fonctionnement](#5-modes-de-fonctionnement)
- [6. Dépannage courant](#6-dépannage-courant)

---

## 1. Présentation de l'application

L’application permet de :

- Recevoir automatiquement les mesures densitométriques du X-Rite 310 via port série.
- Visualiser les courbes de densité pour les canaux VIS, C/M/Y, etc.
- Comparer les mesures à des courbes de référence.
- Exporter/importer des fichiers de mesure.

---

## 2. Interface principale

L'application se compose de plusieurs onglets :

- **Communication** : permet de configurer le port COM, le débit (baudrate), etc.
- **Courbes** : un onglet par jeu de courbes. On peut en ajouter, supprimer, renommer.
- **Barre de menu** :
  - **Fichier** : ouvrir, sauvegarder, ouvrir le dossier de mesure
  - **Édition** : réinitialiser les mesures
  - **Aide** : consulter ce manuel

---

## 3. Connexion avec le densitomètre

### Configuration minimale

- Connecter le densitomètre via un **câble RS232 droit**.
- Utiliser un adaptateur **USB–RS232 compatible**.
- Ouvrir le port COM correspondant dans l'application.

### Réglages logiciels

- Dans l’onglet **Communication**, sélectionner :
  - **Port série COM** approprié (COM 3 ou 4 le plus souvent, dépendant du cable/adaptateur tuilisé)
  - **Baudrate** : `1200` (recommandé) ou `300` (plus lent mais plus stable si problème)

---

## 4. Configuration du densitomètre X-Rite 310

Allumer le densitomètre, puis entrer successivement les **modes suivants** :
(les modes sélectionnés sont sauvegardés apres extinction du densitoètre)

### ⚙️ Réglage recommandé (mode série automatique, 1200 bauds)

| Étape               | Appuyer sur             | Effet attendu          |
|---------------------|-------------------------|-------------------------|
| Entrer mode         | `F → MODE → 11`         | Active le mode TECHNET |
| Définir baudrate    | `F → MODE → 13`         | 1200 bauds             |
| Format complet      | `F → MODE → 18`         | Données longues        |
| Envoi auto          | `F → MODE → 03`         | Envoi automatique après mesure |
| Format sur 1 ligne  | `F → MODE → 21`         | Valeurs sur une seule ligne |

👉 Ne pas activer le mode 10 ni 14/15 si mode 11 est actif.

---

## 5. Modes de fonctionnement

| Mode | Description |
|------|-------------|
| `300 bauds` | Plus lent, utile pour les câbles longs ou adaptateurs peu fiables |
| `1200 bauds` | Rapide et recommandé pour usage courant |
| `03` | Auto-print : déclenchement automatique de l’envoi des données |
| `05` | Auto-print avec date/heure incluse |
| `18` | Format long (plus d'infos, utile pour la courbe gamma) |
| `21` | Sortie sur une ligne (facile à parser) |

---

## 6. Dépannage courant

### ❌ Je n’ai rien en sortie
- Vérifier que le port COM est correct.
- Vérifier que le baudrate correspond à celui du densitomètre.
- Vérifier que le bouton **PRINT** du 310 a été pressé.
- Si rien ne sort même après `PRINT`, vérifier que **mode 03 est activé**.

---

## 📌 Fichier de configuration

Les réglages sont mémorisés manuelleùent entre les sessions dans un fichier `.json` dans le dossier de mesure.

---

## 📘 Manuel externe (disponible dans le dossiers docs)
- [X-rite 310 densitometer operation manual](cours_sensitometrie.pdf)
- [Cours de sentitométrie(Jacques VERREES - INSAS)](310-42_310_Densitometer_Operation_Manual_en.pdf)
