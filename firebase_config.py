import os
from pathlib import Path

import streamlit as st
from streamlit.errors import StreamlitSecretNotFoundError
import firebase_admin
from firebase_admin import credentials, db

DATABASE_URL = "https://predectivemaintenance-aef92-default-rtdb.firebaseio.com/"
LOCAL_CREDENTIALS_FILE = (
    Path(__file__).with_name(
        "predectivemaintenance-aef92-firebase-adminsdk-fbsvc-3b6ffb0641.json"
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
    firebase_credentials = {key: source[key] for key in CREDENTIAL_KEYS}
    firebase_credentials["private_key"] = firebase_credentials["private_key"].replace(
        "\\n", "\n"
    )
    return firebase_credentials


def _load_credentials():
    google_credentials_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    if google_credentials_path:
        return credentials.Certificate(google_credentials_path)

    if all(key in os.environ for key in CREDENTIAL_KEYS):
        return credentials.Certificate(_credential_dict(os.environ))

    if LOCAL_CREDENTIALS_FILE.exists():
        return credentials.Certificate(str(LOCAL_CREDENTIALS_FILE))

    try:
        return credentials.Certificate(_credential_dict(st.secrets))
    except (KeyError, StreamlitSecretNotFoundError) as exc:
        raise RuntimeError(
            "Firebase credentials were not found. Set GOOGLE_APPLICATION_CREDENTIALS, "
            "provide all Firebase credential environment variables, add Streamlit "
            "secrets, or keep the local service-account JSON file next to firebase_config.py."
        ) from exc


if not firebase_admin._apps:
    cred = _load_credentials()

    firebase_admin.initialize_app(
        cred,
        {"databaseURL": DATABASE_URL}
    )

root = db.reference("/")
