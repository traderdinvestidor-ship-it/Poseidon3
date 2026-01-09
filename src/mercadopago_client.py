import mercadopago
import streamlit as st

def get_mp_sdk():
    """Inicializa o SDK do Mercado Pago usando o token dos secrets."""
    try:
        access_token = st.secrets["mercadopago"]["access_token"]
        return mercadopago.SDK(access_token)
    except Exception as e:
        st.error(f"Erro ao inicializar Mercado Pago: {e}")
        return None

def create_pix_payment(amount, email, name="Poseidon User"):
    """Cria um pagamento Pix no Mercado Pago."""
    sdk = get_mp_sdk()
    if not sdk:
        return None
        
    # O user_id pode ser usado como integrator_id opcionalmente
    user_id = st.secrets["mercadopago"].get("user_id", "")
    
    payment_data = {
        "transaction_amount": amount,
        "description": "Assinatura Poseidon Premium",
        "payment_method_id": "pix",
        "payer": {
            "email": email,
            "first_name": name.split()[0] if name else "User",
            "last_name": name.split()[-1] if len(name.split()) > 1 else "Poseidon"
        }
    }
    
    # Chamada simplificada para evitar o erro de 'RequestOptions Object' no SDK
    payment_response = sdk.payment().create(payment_data)
    payment = payment_response["response"]
    
    if payment_response["status"] == 201:
        return {
            "id": payment["id"],
            "qr_code": payment["point_of_interaction"]["transaction_data"]["qr_code"],
            "qr_code_base64": payment["point_of_interaction"]["transaction_data"]["qr_code_base64"],
            "status": payment["status"]
        }
    else:
        st.error(f"Erro ao criar pagamento: {payment}")
        return None

def check_payment_status(payment_id):
    """Consulta o status de um pagamento específico."""
    sdk = get_mp_sdk()
    if not sdk:
        return None
        
    payment_response = sdk.payment().get(payment_id)
    payment = payment_response["response"]
    
    if payment_response["status"] == 200:
        return payment["status"]
    return None
