from src.auth import load_config, save_config, get_qr_code
from src.mercadopago_client import create_pix_payment, check_payment_status

def is_premium(email=None):
    """
    Verifica se o status premium está ativo.
    Se o e-mail for fornecido, verifica na lista de e-mails premium.
    Caso contrário, verifica o flag global.
    """
    data = load_config()
    
    # Se a flag global estiver ativa, libera para todos (Admin/Dev mode)
    if data.get("is_premium", False):
        return True
    
    if email:
        premium_users = data.get("premium_emails", [])
        return email in premium_users
    
    return False

def unlock_premium(email=None):
    """
    Ativa o status premium.
    Se o e-mail for fornecido, adiciona à lista de e-mails premium.
    Caso contrário, ativa o flag global.
    """
    data = load_config()
    
    if email:
        if "premium_emails" not in data:
            data["premium_emails"] = []
        if email not in data["premium_emails"]:
            data["premium_emails"].append(email)
    else:
        data["is_premium"] = True
        
    save_config(data)
    return True

def generate_real_pix(email, name="Investidor Poseidon"):
    """
    Gera um pagamento Pix real usando a API do Mercado Pago.
    """
    # Valor fixo da assinatura
    AMOUNT = 49.99
    
    payment = create_pix_payment(AMOUNT, email, name)
    if payment:
        return {
            "id": payment["id"],
            "code": payment["qr_code"],
            "qr_code_base64": payment["qr_code_base64"],
            "status": payment["status"]
        }
    return None

def verify_payment_status(payment_id):
    """
    Verifica se o pagamento foi aprovado.
    """
    return check_payment_status(payment_id)

def get_pix_qr(pix_code):
    """Gera um fluxo de imagem de QR Code a partir da string Pix."""
    return get_qr_code(pix_code)
