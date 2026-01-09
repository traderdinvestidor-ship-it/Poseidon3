import streamlit as st
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
import json

# Scopes required: email and profile
SCOPES = [
    'https://www.googleapis.com/auth/userinfo.email',
    'https://www.googleapis.com/auth/userinfo.profile',
    'openid'
]

def create_flow(state=None):
    """Cria o fluxo OAuth usando as credenciais do st.secrets, detectando ambiente local/prod."""
    try:
        # Pega a URI de produção dos segredos
        prod_uri = st.secrets["google_oauth"]["redirect_uri"]
        
        # Detecta porta e endereço atual do Streamlit
        current_port = st.get_option("browser.serverPort")
        
        # Detecta se estamos rodando localmente (localhost ou 127.0.0.1)
        is_local = "localhost" in st.get_option("browser.serverAddress") or \
                   "127.0.0.1" in st.get_option("browser.serverAddress") or \
                   not st.get_option("browser.serverAddress") or \
                   st.get_option("browser.serverAddress") == "0.0.0.0"
        
        if is_local:
            # Em ambiente local, tentamos primeiro o que está no secrets.
            # Se não houver, montamos dinamicamente com a porta atual.
            redirect_uri = st.secrets["google_oauth"].get("redirect_uri_local")
            if not redirect_uri:
                redirect_uri = f"http://localhost:{current_port}"
        else:
            redirect_uri = prod_uri
        
        client_config = {
            "web": {
                "client_id": st.secrets["google_oauth"]["client_id"],
                "client_secret": st.secrets["google_oauth"]["client_secret"],
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": [redirect_uri],
            }
        }
        
        return Flow.from_client_config(
            client_config,
            scopes=SCOPES,
            redirect_uri=redirect_uri,
            state=state
        )
    except Exception as e:
        st.error(f"Erro ao carregar segredos do Google: {e}")
        return None

import hmac
import hashlib
import base64

def _sign_state(state):
    """Gera uma assinatura para o state usando o client_secret."""
    secret = st.secrets["google_oauth"]["client_secret"].encode()
    msg = state.encode()
    signature = hmac.new(secret, msg, hashlib.sha256).digest()
    return f"{state}.{base64.urlsafe_b64encode(signature).decode().strip('=')}"

def _verify_state(signed_state):
    """Verifica se a assinatura do signed_state é válida."""
    try:
        if "." not in signed_state:
            return False
        state, signature = signed_state.rsplit(".", 1)
        # Recalcula a assinatura
        expected_signed = _sign_state(state)
        # Compara (usa hmac.compare_digest para segurança)
        return hmac.compare_digest(signed_state, expected_signed)
    except Exception:
        return False

def get_login_url():
    """Gera a URL de login do Google com um state assinado (não depende de sessão)."""
    flow = create_flow()
    if flow:
        authorization_url, state = flow.authorization_url(prompt='consent')
        # Em vez de salvar na sessão, assinamos o state
        signed_state = _sign_state(state)
        # Recria a URL com o state assinado
        authorization_url, _ = flow.authorization_url(prompt='consent', state=signed_state)
        return authorization_url
    return None

def get_user_info(code, signed_state):
    """Troca o código pelo token e busca informações do usuário, validando a assinatura do state."""
    # Valida a assinatura do state (segurança contra CSRF sem depender de st.session_state)
    if not _verify_state(signed_state):
        st.error("""
        **Erro de Autenticação (State Invalid)**.
        A assinatura de segurança não confere ou expirou.
        
        **Causa provável:** O link de login expirou ou houve tentativa de manipulação.
        **Tente novamente** a partir da página inicial.
        """)
        return None

    # O Flow precisa do state original para validar internamente
    state = signed_state.split(".")[0]
    flow = create_flow(state=signed_state) # Passamos o signed_state pois é o que o Google vai devolver
    if not flow:
        return None
        
    try:
        # Note: google-auth-oauthlib vai validar que o state recebido 
        # é o mesmo que passamos no create_flow
        flow.fetch_token(code=code)
        creds = flow.credentials
        
        # Chama a API de UserInfo
        service = build('oauth2', 'v2', credentials=creds)
        user_info = service.userinfo().get().execute()
        return user_info
    except Exception as e:
        st.error(f"Erro ao autenticar: {e}")
        return None
