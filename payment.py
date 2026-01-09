from src.auth import load_config, save_config, get_qr_code
from src.mercadopago_client import create_pix_payment, check_payment_status

def is_premium(email=None):
    """
    Verifica se o status premium está ativo.
    """
    data = load_config()
    
    # --- AUTO-CORREÇÃO (LIMPEZA DE BUG) ---
    # Se o arquivo tiver a configuração antiga que libera geral, deletamos ela agora.
    if "is_premium" in data:
        try:
            del data["is_premium"]
            save_config(data)
            data = load_config() # Recarrega limpo
        except Exception:
            pass
    # --------------------------------------

    # 1. Se não tem e-mail, bloqueia
    if not email:
        return False
    
    # 2. Verifica estritamente a lista de pagantes
    premium_users = data.get("premium_emails", [])
    
    # Se a lista não existir ou estiver corrompida, bloqueia
    if not isinstance(premium_users, list):
        return False
        
    # 3. Só libera se o e-mail estiver EXATAMENTE na lista
    return email in premium_users

def unlock_premium(email=None):
    """
    Ativa o status premium.
    Se o e-mail for fornecido, adiciona à lista de e-mails premium.
    """
    data = load_config()
    
    if email:
        # Garante que a lista existe
        if "premium_emails" not in data or not isinstance(data["premium_emails"], list):
            data["premium_emails"] = []
            
        if email not in data["premium_emails"]:
            data["premium_emails"].append(email)
            
        # SEGURANÇA: Remove a flag global se ela existir
        if "is_premium" in data:
            del data["is_premium"]
        
        save_config(data)
        return True
    return False

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
