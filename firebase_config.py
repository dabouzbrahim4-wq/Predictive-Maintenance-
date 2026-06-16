import json
import os

def _load_credentials():

    # 1) Railway / Render
    if all(key in os.environ for key in CREDENTIAL_KEYS):
        return credentials.Certificate(
            _credential_dict(os.environ)
        )

    # 2) Variable واحدة تحتوي JSON كامل
    firebase_json = os.getenv("FIREBASE_JSON")

    if firebase_json:
        return credentials.Certificate(
            json.loads(firebase_json)
        )

    # 3) GOOGLE_APPLICATION_CREDENTIALS
    google_credentials_path = os.getenv(
        "GOOGLE_APPLICATION_CREDENTIALS"
    )

    if google_credentials_path:
        return credentials.Certificate(
            google_credentials_path
        )

    # 4) Local JSON file
    if LOCAL_CREDENTIALS_FILE.exists():
        return credentials.Certificate(
            str(LOCAL_CREDENTIALS_FILE)
        )

    # 5) Streamlit Secrets
    try:
        return credentials.Certificate(
            _credential_dict(st.secrets)
        )
    except (KeyError, StreamlitSecretNotFoundError):
        pass

    raise RuntimeError(
        "Firebase credentials not found."
    )
