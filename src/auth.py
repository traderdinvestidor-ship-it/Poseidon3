import pyotp
import qrcode
import json
import os
import io

CONFIG_FILE = "config/user_data.json"

def load_config():
    """Loads user configuration including the secret."""
    if not os.path.exists(CONFIG_FILE):
        return {}
    try:
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    except json.JSONDecodeError:
        return {}

def save_config(data):
    """Saves user configuration."""
    # Ensure directory exists
    os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
    
    with open(CONFIG_FILE, "w") as f:
        json.dump(data, f, indent=4)

def generate_secret():
    """Generates a new random base32 secret."""
    return pyotp.random_base32()

def get_totp_uri(secret, email="usuario@poseidon.ai"):
    """Generates the provisioning URI for Google Authenticator."""
    return pyotp.totp.TOTP(secret).provisioning_uri(name=email, issuer_name="Poseidon AI")

def get_qr_code(uri):
    """Generates a QR code image stream from the URI."""
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(uri)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='PNG')
    img_byte_arr.seek(0)
    return img_byte_arr

def verify_otp(secret, code):
    """Verifies the TOTP code."""
    if not secret:
        return False
    totp = pyotp.TOTP(secret)
    return totp.verify(code)

def is_setup_complete():
    """Checks if the user has completed setup."""
    data = load_config()
    return "secret" in data and data.get("setup_complete", False)
