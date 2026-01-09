import streamlit as st
import time
import pandas as pd
import numpy as np
import plotly.express as px
from src.data_loader import get_macro_indicators, get_batch_asset_data
from src.allocator import get_allocation_strategy, recommend_sectors
from src.analyzer import score_stocks, score_crypto
from src.fii_loader import get_fii_batch
from src.technical_engine import get_technical_signals
from src.quant_engine import run_monte_carlo, get_optimized_allocation
from src.google_auth import get_login_url, get_user_info
from src.payment import is_premium, unlock_premium, generate_real_pix, verify_payment_status

# --- CONFIG & SESSION STATE ---
st.set_page_config(page_title="Poseidon Investimentos", layout="wide", page_icon="🔱")

# Load CSS
try:
    with open("style.css", encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
except Exception as e:
    st.warning("⚠️ Aviso: Não foi possível carregar o estilo visual (style.css). O sistema continua funcional.")

if 'user' not in st.session_state:
    st.session_state.user = None
if 'run_analysis' not in st.session_state:
    st.session_state.run_analysis = False
if 'rebalance_results' not in st.session_state:
    st.session_state.rebalance_results = None

# --- AUTHENTICATION GATE ---
def login_page():
    col1, col2, col3 = st.columns([0.5, 1, 0.5])
    
    with col2:
        st.write("") 
        st.write("")
        st.markdown('<h1 style="text-align:center; font-size: 4rem; margin-bottom: 0;">🔱</h1>', unsafe_allow_html=True)
        st.markdown('<h1 style="text-align:center; margin-top: 0;">Poseidon AI</h1>', unsafe_allow_html=True)
        st.markdown('<p style="text-align:center; color:#888; font-size:1.1rem; margin-bottom:2rem;">O Futuro dos seus Investimentos</p>', unsafe_allow_html=True)
        
        st.markdown('<p style="text-align:center; margin-bottom:1rem;">Para acessar o terminal e liberar o Pix, insira seu e-mail:</p>', unsafe_allow_html=True)
        
        email = st.text_input("Seu E-mail", placeholder="seu@email.com")
        
        if st.button("🚀 ENTRAR NO TERMINAL", use_container_width=True):
            if "@" in email and "." in email:
                st.session_state.user = {
                    "email": email.lower().strip(),
                    "name": email.split("@")[0].capitalize(),
                    "picture": None
                }
                st.rerun()
            else:
                st.error("Por favor, insira um e-mail válido para continuar.")

# Check if user is logged in
if st.session_state.user is None:
    login_page()
    st.stop()

# --- PREMIUM CHECK ---
def check_premium():
    try:
        return is_premium(st.session_state.user.get("email"))
    except Exception:
        return False

user_premium = check_premium()

# User Sidebar Header
with st.sidebar:
    st.write(f"Olá, **{st.session_state.user.get('name', 'Investidor')}**")
    if st.session_state.user.get("picture"):
        st.image(st.session_state.user.get("picture"), width=50)
    
    if st.button("🚪 Sair", use_container_width=True):
        st.session_state.user = None
        st.rerun()
    st.markdown("---")

if user_premium:
    st.sidebar.success("💎 POSEIDON PREMIUM")
else:
    st.sidebar.info("👤 CONTA BÁSICA")
    if st.sidebar.button("🚀 Liberar Acesso Total (PIX)"):
        st.session_state.show_payment = True
    
    # --- ÁREA ADMINISTRATIVA ---
    with st.sidebar.expander("🔐 Área Admin (Privado)"):
        admin_pass = st.text_input("Senha Admin", type="password")
        if admin_pass == "poseidon2026":
            st.write("---")
            st.subheader("Liberar Cliente")
            email_to_unlock = st.text_input("E-mail do Cliente")
            if st.button("Liberar Acesso Premium"):
                if "@" in email_to_unlock:
                    unlock_premium(email_to_unlock)
                    st.success(f"Acesso liberado: {email_to_unlock}")
                else:
                    st.error("E-mail inválido")

if st.session_state.get('show_payment', False) and not user_premium:
    st.markdown('<div class="ui-card premium-card">', unsafe_allow_html=True)
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("🚀 Poseidon Premium")
        st.markdown("""
        - **Otimização de Markowitz**: Maximize retornos.
        - **Monte Carlo**: Projeções estatísticas de futuro.
        - **Calculadora IA**: Rebalanceamento automático.
        """)
        
        if st.button("🔓 Demo Mode (Local Unlock)", use_container_width=True):
            from src.payment import unlock_premium
            if unlock_premium(st.session_state.user.get("email")):
                st.success("Premium Ativado!")
                time.sleep(1)
                st.rerun()
    
    with col2:
        st.subheader("💳 Checkout Pix")
        
        if 'current_payment' not in st.session_state or st.session_state.current_payment is None:
            with st.spinner("Gerando PIX..."):
                pay_info = generate_real_pix(st.session_state.user.get("email"), st.session_state.user.get("name"))
                st.session_state.current_payment = pay_info

        if st.session_state.current_payment:
            pay = st.session_state.current_payment
            if pay.get("qr_code_base64"):
                st.image(f"data:image/png;base64,{pay['qr_code_base64']}", width=200)
            
            st.code(pay['code'], language="text")
            st.caption("Investimento: R$ 99,90 (Acesso Vitalício)")
            
            v_col1, v_col2 = st.columns(2)
            with v_col1:
                if st.button("✅ Verificar", use_container_width=True):
                    status = verify_payment_status(pay['id'])
                    if status == "approved":
                        from src.payment import unlock_premium
                        unlock_premium(st.session_state.user.get("email"))
                        st.session_state.current_payment = None
                        st.rerun()
            with v_col2:
                if st.button("❌ Fechar", use_container_width=True):
                    st.session_state.show_payment = False
                    st.session_state.current_payment = None
                    st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)


# --- ASSET UNIVERSE ---
STOCK_TICKERS = [
    "VALE3.SA", "PETR4.SA", "WEGE3.SA", "ITUB4.SA", "BBAS3.SA", 
    "BBDC4.SA", "ABEV3.SA", "RENT3.SA", "BPAC11.SA", "PRIO3.SA",
    "CMIG4.SA", "GGBR4.SA", "CSAN3.SA", "RAIL3.SA", "ELET3.SA",
    "VBBR3.SA", "RADL3.SA", "RDOR3.SA", "HYPE3.SA", "BBSE3.SA"
]
BDR_TICKERS = [
    "AAPL34.SA", "GOGL34.SA", "AMZO34.SA", "MSFT34.SA", "TSLA34.SA",
    "NVDC34.SA", "M1TA34.SA", "DISB34.SA", "NFLX34.SA", "PYPL34.SA",
    "IVVB11.SA", "NASD11.SA", "BERK34.SA", "JNJB34.SA", "PGCO34.SA",
    "PEPB34.SA", "MCDC34.SA", "CSCO34.SA", "ITLC34.SA", "VISA34.SA"
]
FII_TICKERS = [
    "HGLG11", "KNIP11", "VISC11", "XPLG11", "XPML11", "MXRF11", 
    "KNCR11", "HGRU11", "VILG11", "BRCO11", "HGBS11", "BTLG11"
]
CRYPTO_TICKERS = ["BTC-USD", "ETH-USD", "SOL-USD", "BNB-USD", "ADA-USD", "XRP-USD", "DOT-USD", "AVAX-USD"]

# --- SIDEBAR (Calibration) ---
st.sidebar.title("🧠 Calibração de Perfil")
st.sidebar.markdown("---")

user_amount = st.sidebar.number_input("Valor disponível para aporte (R$)", min_value=100.0, value=10000.0, step=100.0)
user_horizon = st.sidebar.selectbox("Horizonte de Tempo", ["Curto (< 2 anos)", "Médio (2 a 5 anos)", "Longo (> 10 anos)"])
user_risk = st.sidebar.select_slider("Tolerância ao Risco", options=["Conservador", "Moderado", "Arrojado"], value="Moderado")
user_objective = st.sidebar.text_input("Objetivo Financeiro", "Aposentadoria / Liberdade Financeira")

st.sidebar.markdown("---")
if st.sidebar.button("💡 Gerar Carteira Poseidon"):
    st.session_state.run_analysis = True
    st.session_state.rebalance_results = None

# --- MAIN PAGE ---
st.title("Poseidon Investimentos 🤖💰")
st.markdown(f"#### Bem-vindo, Investidor. Modo: **{user_risk.upper()}**")

# --- MACRO DATA ---
with st.spinner("Analisando Cenário Macroeconômico..."):
    macro_data = get_macro_indicators()
    
col1, col2, col3 = st.columns(3)
col1.metric("Selic Meta (Brasil)", f"{macro_data['selic']}%", "Neutro")
col2.metric("IPCA 12m (Inflação)", f"{macro_data['ipca']}%", "Estável")
col3.metric("Sentimento de Mercado", "Cauteloso", "Volatilidade Alta")

st.markdown("---")

if st.session_state.run_analysis:
    st.subheader("📊 Alocação Estratégica Sugerida")
    
    allocation = get_allocation_strategy(user_risk)
    # Chart with Poseidon Colors (Deep Blues and Gold)
    df_alloc = pd.DataFrame(list(allocation.items()), columns=['Classe', 'Proporção'])
    poseidon_colors = ['#00d4ff', '#005f73', '#ffb703', '#94d2bd', '#ee9b00']
    fig = px.pie(df_alloc, values='Proporção', names='Classe', 
                 title=f'💎 Alocação Estratégica Poseidon ({user_risk})', 
                 hole=0.4,
                 color_discrete_sequence=poseidon_colors)
    fig.update_traces(textposition='inside', textinfo='percent+label')
    fig.update_layout(showlegend=False, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color='white')
    st.plotly_chart(fig, width='stretch')
    
    amount_distribution = {k: v * user_amount for k, v in allocation.items()}
    st.info(f"💰 Distribuição Financeira: {amount_distribution}")

    st.subheader("🎯 Seleção Tática de Ativos (Top Picks)")
    tabs = st.tabs(["🇧🇷 Ações Brasil", "🌎 Exterior (BDRs/ETFs)", "₿ Cripto", "🏗️ FIIs"])
    
    with tabs[0]: # Stocks
        if allocation['Ações BR'] > 0:
            with st.spinner("Scanner de Ações BR em execução..."):
                raw_stocks = get_batch_asset_data(STOCK_TICKERS)
                best_stocks = score_stocks(raw_stocks)
                best_stocks['Timing'] = best_stocks['symbol'].apply(get_technical_signals)
                st.dataframe(
                    best_stocks[['symbol', 'name', 'price', 'pe_ratio', 'roe', 'Timing']].style.format({
                        'price': 'R$ {:.2f}', 'pe_ratio': '{:.2f}', 'roe': '{:.2%}'
                    })
                )
                st.caption("*Ranking baseado em P/L baixo e ROE alto.")
                
                # MARKOWITZ OPTIMIZATION BUTTON
                if user_premium:
                    if st.button("🔱 Otimizar Pesos (Markowitz) - Top 5"):
                        with st.spinner("Calculando Fronteira Eficiente (scipy)..."):
                            top_5_tickers = best_stocks['symbol'].head(5).tolist()
                            optimized_weights = get_optimized_allocation(top_5_tickers, user_risk)
                            
                            if optimized_weights:
                                st.success("✅ Pesos Otimizados para Máximo Retorno Ajustado ao Risco!")
                                df_opt = pd.DataFrame(list(optimized_weights.items()), columns=['Ticker', 'Peso Sugerido'])
                                df_opt['Peso Sugerido'] = df_opt['Peso Sugerido'].apply(lambda x: f"{x*100:.1f}%")
                                st.table(df_opt)
                            else:
                                st.warning("Não foi possível otimizar os pesos com os dados atuais. Verifique a conexão com o Yahoo Finance.")
                else:
                    st.markdown("""
                    <div class="lock-area">
                        <h3>🔒 Recurso Premium</h3>
                        <p>Otimização de Markowitz para maximizar seu retorno ajustado ao risco.</p>
                    </div>
                    """, unsafe_allow_html=True)
                    if st.button("💎 Liberar Agora", key="unlock_markowitz"):
                        st.session_state.show_payment = True
                        st.rerun()
        else:
            st.warning("Seu perfil não recomenda exposição a Ações no momento.")

    with tabs[1]: # International
        if allocation['Exterior'] > 0:
            if user_premium:
                with st.spinner("Scanner Global em execução..."):
                    raw_bdr = get_batch_asset_data(BDR_TICKERS)
                    best_bdr = score_stocks(raw_bdr)
                    best_bdr['Timing'] = best_bdr['symbol'].apply(get_technical_signals)
                    st.dataframe(
                        best_bdr[['symbol', 'name', 'price', 'pe_ratio', 'Timing']].style.format({
                            'price': 'R$ {:.2f}', 'pe_ratio': '{:.2f}'
                        })
                    )
                    st.caption("*Integrando ativos globais para diversificação geográfica.")
            else:
                st.markdown("""
                <div class="lock-area">
                    <h3>🔒 Acesso Global Premium</h3>
                    <p>Scanner de BDRs, ETFs e ativos internacionais disponível apenas para membros Premium.</p>
                </div>
                """, unsafe_allow_html=True)
                if st.button("💎 Liberar Agora", key="unlock_global"):
                    st.session_state.show_payment = True
                    st.rerun()
        else:
            st.warning("Seu perfil foca em ativos domésticos.")

    with tabs[2]: # Crypto
        if allocation['Cripto'] > 0:
            if user_premium:
                with st.spinner("Analisando Blockchain..."):
                    raw_crypto = get_batch_asset_data(CRYPTO_TICKERS)
                    best_crypto = score_crypto(raw_crypto)
                    st.dataframe(best_crypto[['symbol', 'price', 'market_cap']].style.format({'price': '$ {:.2f}'}))
            else:
                st.markdown("""
                <div class="lock-area">
                    <h3>🔒 Cripto Scanner Premium</h3>
                    <p>Análise quantitativa de ativos digitais bloqueada para conta básica.</p>
                </div>
                """, unsafe_allow_html=True)
                if st.button("💎 Liberar Agora", key="unlock_crypto"):
                    st.session_state.show_payment = True
                    st.rerun()
        else:
            st.warning("Seu perfil não recomenda exposição a Criptoativos.")
            
    with tabs[3]: # FIIs
        if allocation['FIIs'] > 0:
            if user_premium:
                with st.spinner("Scanner de FIIs em execução (StatusInvest)..."):
                    df_fii = get_fii_batch(FII_TICKERS)
                    df_fii_filt = df_fii[(df_fii['p_vp'] > 0.5) & (df_fii['p_vp'] < 1.2)]
                    st.dataframe(
                        df_fii_filt.style.format({
                            'p_vp': '{:.2f}', 'dy': '{:.2%}', 'vacancy': '{:.2%}'
                        })
                    )
                    st.caption("*Filtro: P/VP entre 0.5 e 1.2 para evitar fundos superavaliados.")
            else:
                st.markdown("""
                <div class="lock-area">
                    <h3>🔒 Radar de FIIs Premium</h3>
                    <p>Seleção tática de Fundos Imobiliários disponível apenas para Poseidon Premium.</p>
                </div>
                """, unsafe_allow_html=True)
                if st.button("💎 Liberar Agora", key="unlock_fiis"):
                    st.session_state.show_payment = True
                    st.rerun()
        else:
            st.warning("Seu perfil não recomenda exposição a FIIs.")

    # 4. Renda Fixa
    st.markdown("---")
    st.subheader("🛡️ Renda Fixa Inteligente (Isentos vs Tributados)")
    col_rf1, col_rf2 = st.columns(2)
    with col_rf1:
        cdb_rate = st.number_input("Taxa CDB ofererecida (% do CDI)", value=110.0)
        lci_rate = st.number_input("Taxa LCI/LCA ofererecida (% do CDI)", value=92.0)
    ir_factor = 0.85 
    cdb_net = cdb_rate * ir_factor
    with col_rf2:
        if cdb_net > lci_rate:
            st.success(f"✅ O **CDB ({cdb_rate}%)** é mais vantajoso!")
            st.write(f"Rentabilidade líquida est. do CDB: {cdb_net:.2f}% do CDI")
        else:
            st.success(f"✅ A **LCI/LCA ({lci_rate}%)** é mais vantajosa!")
            st.write(f"O CDB precisaria render > {(lci_rate/ir_factor):.1f}% para empatar.")

    # 5. Risk
    st.markdown("---")
    st.subheader("⚠️ Análise de Resiliência (Risk Engine)")
    risk_map = {
        "Conservador": {"max_drawdown": "3% a 5%", "volatility": "Baixa", "recovery": "Rápida"},
        "Moderado": {"max_drawdown": "10% a 15%", "volatility": "Média", "recovery": "6-12 meses"},
        "Arrojado": {"max_drawdown": "25% a 40%", "volatility": "Alta", "recovery": "18-24 meses"}
    }
    r_info = risk_map[user_risk]
    col_r1, col_r2, col_r3 = st.columns(3)
    col_r1.warning(f"Queda Máxima Est.: {r_info['max_drawdown']}")
    col_r2.info(f"Volatilidade: {r_info['volatility']}")
    col_r3.success(f"Tempo de Recuperação: {r_info['recovery']}")
    st.caption("Nota: O Drawdown é baseado em crises históricas (Ex: 2008, 2020) para essa alocação de ativos.")

    # 6. MONTE CARLO SIMULATION (PROJEÇÃO DE FUTURO)
    st.markdown("---")
    st.subheader("🔮 Projeção Estatística (Monte Carlo)")
    st.info("Simulamos 1.000 cenários possíveis para o seu patrimônio nos próximos anos.")
    
    col_mc1, col_mc2 = st.columns([1, 2])
    with col_mc1:
        years_sim = st.slider("Horizonte de Simulação (Anos)", 1, 30, 10)
        # Expected return and vol based on risk
        base_returns = {"Conservador": 0.11, "Moderado": 0.14, "Arrojado": 0.18}
        base_vols = {"Conservador": 0.05, "Moderado": 0.12, "Arrojado": 0.25}
        
        exp_ret = base_returns[user_risk]
        exp_vol = base_vols[user_risk]
        
    paths = run_monte_carlo(user_amount, exp_ret, exp_vol, years=years_sim)
    
    # Calculate percentiles for the chart
    final_results = paths[-1, :]
    p10 = np.percentile(final_results, 10)
    p50 = np.percentile(final_results, 50) # Median
    p90 = np.percentile(final_results, 90)
    
    with col_mc2:
        if user_premium:
            # Plot only a sample of paths + percentiles
            fig_mc = px.line(paths[:, :50], labels={'index': 'Dias', 'value': 'Patrimônio (R$)'}, 
                             title=f"Simulação de {years_sim} anos - {user_risk}")
            fig_mc.update_layout(showlegend=False, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color='white')
            st.plotly_chart(fig_mc, width='stretch')
        else:
            st.markdown("""
            <div class="lock-area">
                <h3>🔒 Gráfico Bloqueado</h3>
                <p>Simulação estatística dinâmica de 1.000 caminhos randômicos disponível para Premium.</p>
            </div>
            """, unsafe_allow_html=True)
            st.write(f"🧬 Projeção simplificada (Mediana): R$ {p50:,.2f}")
            if st.button("💎 Desbloquear Simulador", key="unlock_mc"):
                st.session_state.show_payment = True
                st.rerun()
    
    col_stat1, col_stat2, col_stat3 = st.columns(3)
    col_stat1.metric("Cenário Pessimista (10%)", f"R$ {p10:,.2f}")
    col_stat2.metric("Cenário Provável (Mediana)", f"R$ {p50:,.2f}")
    col_stat3.metric("Cenário Otimista (90%)", f"R$ {p90:,.2f}")

    # 7. CALCULADORA DE REBALANCEAMENTO
    st.markdown("---")
    st.subheader("⚖️ Calculadora de Rebalanceamento Inteligente")
    st.info("Insira seu patrimônio atual para o robô calcular os movimentos.")
    
    with st.form("rebalance_form"):
        col_reb_in1, col_reb_in2 = st.columns(2)
        with col_reb_in1:
            current_rf = st.number_input("Renda Fixa Atual (R$)", value=0.0)
            current_fii = st.number_input("FIIs Atual (R$)", value=0.0)
            current_stocks = st.number_input("Ações BR Atual (R$)", value=0.0)
        with col_reb_in2:
            current_exterior = st.number_input("Exterior Atual (R$)", value=0.0)
            current_crypto = st.number_input("Cripto Atual (R$)", value=0.0)
            
        submit_reb = st.form_submit_button("⚖️ Calcular Rebalanceamento")
        
        if submit_reb:
            total_pat = current_rf + current_fii + current_stocks + current_exterior + current_crypto + user_amount
            recalc_data = []
            for classe, perc in allocation.items():
                val_idl = total_pat * perc
                # Use current values from the form inputs at submission
                map_vals = {'Renda Fixa': current_rf, 'FIIs': current_fii, 'Ações BR': current_stocks, 'Exterior': current_exterior, 'Cripto': current_crypto}
                v_at = map_vals.get(classe, 0)
                dif = val_idl - v_at
                recalc_data.append({
                    "Classe": classe,
                    "Ideal (%)": f"{perc*100:.1f}%",
                    "Ação": f"COMPRAR R$ {dif:.2f}" if dif > 0 else f"VENDER R$ {abs(dif):.2f}"
                })
            st.session_state.rebalance_results = recalc_data

    # Display results OUTSIDE the form but INSIDE the analysis block
    if st.session_state.rebalance_results:
        if user_premium:
            st.success("✅ Rebalanceamento Calculado com Sucesso!")
            st.table(pd.DataFrame(st.session_state.rebalance_results))
            st.info(f"Aporte total planejado: R$ {user_amount:.2f}")
        else:
            st.markdown("""
            <div class="lock-area">
                <h3>🔒 Rebalanceamento Inteligente</h3>
                <p>Veja exatamente quanto comprar/vender de cada ativo para manter sua meta.</p>
            </div>
            """, unsafe_allow_html=True)
            if st.button("💎 Ver Recomendações", key="unlock_rebalance"):
                st.session_state.show_payment = True
                st.rerun()

else:
    st.info("👈 Ajuste seu perfil na barra lateral e clique em 'Gerar Carteira Poseidon' para iniciar.")

st.markdown("---")
st.caption("🔴 DISCLAIMER: Esta é uma ferramenta de simulação educacional alimentada por IA. Não constitui recomendação de investimento. Faça sua própria análise.")
