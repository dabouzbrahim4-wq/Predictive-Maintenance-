import json
import os
from pathlib import Path

import streamlit as st
from streamlit.errors import StreamlitSecretNotFoundError
import firebase_admin
from firebase_admin import credentials, db

DATABASE_URL = "https://predectivemaintenance-aef92-default-rtdb.firebaseio.com/"

LOCAL_CREDENTIALS_FILE = (
    Path(__file__).with_name(
        "predectivemaintenance-aef92-firebase-adminsdk-fbsvc-511e12fdf5.json"
    )
)

CREDENTIAL_KEYS = (
    "type",
    "project_id",
    "private_key_id",
    "private_key",
    "client_email",
    "client_id",
    "auth_uri",
    "token_uri",
    "auth_provider_x509_cert_url",
    "client_x509_cert_url",
    "universe_domain",
)


def _credential_dict(source):
    firebase_credentials = {
        key: source[key]
        for key in CREDENTIAL_KEYS
    }

    firebase_credentials["private_key"] = (
        firebase_credentials["private_key"]
        .replace("\\n", "\n")
    )

    return firebase_credentials


def _load_credentials():

    # =====================================
    # Railway / Render Environment Variables
    # =====================================
    if all(key in os.environ for key in CREDENTIAL_KEYS):
        print("Firebase credentials loaded from ENV variables")

        return credentials.Certificate(
            _credential_dict(os.environ)
        )

    # =====================================
    # FIREBASE_JSON Variable
    # =====================================
    firebase_json = os.getenv("FIREBASE_JSON")

    if firebase_json:
        print("Firebase credentials loaded from FIREBASE_JSON")

        return credentials.Certificate(
            json.loads(firebase_json)
        )

    # =====================================
    # GOOGLE_APPLICATION_CREDENTIALS
    # =====================================
    google_credentials_path = os.getenv(
        "GOOGLE_APPLICATION_CREDENTIALS"
    )

    if google_credentials_path:
        print("Firebase credentials loaded from GOOGLE_APPLICATION_CREDENTIALS")

        return credentials.Certificate(
            google_credentials_path
        )

    # =====================================
    # Local JSON File
    # =====================================
    if LOCAL_CREDENTIALS_FILE.exists():
        print("Firebase credentials loaded from local JSON file")

        return credentials.Certificate(
            str(LOCAL_CREDENTIALS_FILE)
        )

    # =====================================
    # Streamlit Secrets
    # =====================================
    try:
        print("Firebase credentials loaded from Streamlit Secrets")

        return credentials.Certificate(
            _credential_dict(st.secrets)
        )

    except (KeyError, StreamlitSecretNotFoundError):
        pass

    # =====================================
    # No Credentials Found
    # =====================================
    raise RuntimeError(
        "Firebase credentials not found."
    )


if not firebase_admin._apps:

    cred = _load_credentials()

    firebase_admin.initialize_app(
        cred,
        {
            "databaseURL": DATABASE_URL
        }
    )

root = db.reference("/")
