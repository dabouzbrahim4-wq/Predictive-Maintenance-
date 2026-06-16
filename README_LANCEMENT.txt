Sentinel-X Maintenance Console
==============================

Lancement direct
----------------
Double-cliquez sur :

    Lancer_Sentinel_X.bat

Le lanceur verifie Python, installe les dependances manquantes depuis requirements.txt,
puis lance l'application Streamlit.

Firebase
--------
Pour utiliser les donnees live Firebase, placez un fichier JSON Firebase Admin SDK valide
dans ce dossier avec le nom attendu par firebase_config.py :

    predectivemaintenance-aef92-firebase-adminsdk-fbsvc-511e12fdf5.json

Si Firebase n'est pas disponible ou si la cle est invalide, l'application demarre quand
meme avec le mode demo local.

Commande manuelle
-----------------
Vous pouvez aussi lancer l'application avec :

    python -m streamlit run app.py
