#!/bin/bash

if ! command -v python3 &> /dev/null
then
    echo "Erreur : Python3 n'est pas installé ou non présent dans le PATH."
    exit 1
fi

echo "Lancement de l'installation des dépendances..."
python3 install_dependencies.py
