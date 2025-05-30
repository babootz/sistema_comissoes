import streamlit as st
import pandas as pd
from datetime import datetime
import copy
from utils import (
    gerar_pdf,
    dataframe_para_html,
    salvar_excel,
    carregar_excel,
    baixar_arquivo,
)
import os

# Função para gerar PDF das comissões pendentes
def generate_pending_commissions_pdf(comissoes):
    try:
        # Filtra comissões com saldo pendente maior que zero
        pendentes = [c for c in comissoes if float(c.get("saldo_pendente", 0)) > 0]
        if not pendentes:
            return None

        # Prepara um DataFrame resumido para o PDF
        df_pendentes = pd.DataFrame(pendentes)[
            ["segurado", "placa", "seguradora", "data_efetivacao", "comissao_liquida", "saldo_pendente"]
        ]
        df_pendentes["data_efetivacao"] = pd.to_datetime(df_pendentes["data_efetivacao"]).dt.strftime("%d/%m/%Y")

        # Converte o DataFrame em HTML estilizado para o PDF
        html_content = dataframe_para_html(df_pendentes)

        # Gera o PDF a partir do HTML
        pdf_bytes = gerar_pdf(html_content)
        return pdf_bytes
    except Exception as e:
        st.error(f"Erro ao gerar PDF: {e}")
        return None

# --- Configuração Inicial ---
st.set_page_config(page_title="Sistema de Comissões", layout="wide", initial_sidebar_state="collapsed")

def load_css():
    css_path = os.path.join("static", "styles.css")
    if os.path.exists(css_path):
        with open(css_path) as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

load_css()

# --- Estado da Aplicação ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'comissoes_data' not in st.session_state:
    st.session_state.comissoes_data = []
if 'show_history' not in st.session_state:
    st.session_state.show_history = False
if 'confirm_delete_all' not in st.session_state:
    st.session_state.confirm_delete_all = False
if 'edited_rows_info' not in st.session_state:
    st.session_state.edited_rows_info = None 
if 'show_edit_confirm_dialog' not in st.session_state:
    st.session_state.show_edit_confirm_dialog = False

# Função para autenticar usuário (exemplo simples)
def authenticate(password):
    SENHA_CORRETA = "sua_senha_aqui"
    return password == SENHA_CORRETA

# Função para carregar comissões da planilha
def load_comissoes():
    try:
        dados = carregar_excel()
        if isinstance(dados, list):
            return dados
        elif isinstance(dados, pd.DataFrame):
            return dados.to_dict(orient="records")
        else:
            return []
    except Exception as e:
        st.error(f"Erro ao carregar dados: {e}")
        return []

# Função para log de ações simples (pode ser ampliada)
def log_action(acao, mensagem):
    print(f"[{datetime.now()}] {acao} - {mensagem}")

# --- Tela de Login ---
def show_login_screen():
    st.markdown('<div class="login-container">', unsafe_allow_html=True)
    st.markdown('<div class="login-box">', unsafe_allow_html=True)
    st.markdown("<h1>Bem-vindo!</h1>", unsafe_allow_html=True)
    st.markdown("<p>Insira a senha para acessar o Sistema de Comissões.</p>", unsafe_allow_html=True)
    
    password = st.text_input("Senha", type="password", key="login_password", label_visibility="collapsed", placeholder="Senha")
    
    if st.button("Entrar", key="login_button"):
        if authenticate(password):
            st.session_state.logged_in = True
            log_action("Login", "Usuário autenticado com sucesso.")
            st.session_state.comissoes_data = load_comissoes()
            st.experimental_rerun()
        else:
            st.error("Senha incorreta.")
            log_action("Login Falhou", "Tentativa com senha incorreta.")
            
    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

# --- Callback para Edição no Data Editor ---
def handle_edit():
    if "data_editor_state" in st.session_state:
        edited_rows = st.session_state.data_editor_state.get("edited_rows")
        if edited_rows:
            edited_index = list(edited_rows.keys())[0]
            changes = edited_rows[edited_index]
            
            try:
                df_display = st.session_state.get("current_display_df", pd.DataFrame(st.session_state.comissoes_data))
                original_row_data = df_display.iloc[edited_index].to_dict()
                segurado_original = original_row_data.get('segurado')
                placa_original = original_row_data.get('placa')
                
                if segurado_original and placa_original:
                    st.session_state.edited_rows_info = {
                        "segurado": segurado_original,
                        "placa": placa_original,
                        "changes": changes
                    }
                    st.session_state.show_edit_confirm_dialog = True
                    st.experimental_rerun()
                else:
                    st.warning("Não foi possível identificar a linha editada (Segurado/Placa ausentes).")
            except IndexError:
                st.warning("Erro ao acessar a linha editada no DataFrame.")
            except Exception as e:
                st.error(f"Erro inesperado ao processar edição: {e}")

# --- Tela Principal ---
def show_main_screen():
    st.title("💰 Sistema de Gerenciamento de Comissões")

    # Atualiza dados se não estiver editando
    if not st.session_state.show_edit_confirm_dialog and not st.session_state.confirm_delete_all:
        st.session_state.comissoes_data = load_comissoes()

    comissoes_df = pd.DataFrame(st.session_state.comissoes_data)

    for col in ['premio_liquido', 'comissao_percentual', 'comissao_liquida', 'saldo_pendente']:
        if col in comissoes_df.columns:
             comissoes_df[col] = pd.to_numeric(comissoes_df[col], errors='coerce').fillna(0.0)
    if 'data_efetivacao' in comissoes_df.columns:
        comissoes_df['data_efetivacao_dt'] = pd.to_datetime(comissoes_df['data_efetivacao'], errors='coerce')

    # Aqui vai sua lógica para exibir, editar, filtrar, adicionar, remover comissões
    # (coloque seu código atual para as operações na planilha)

    # Exemplo de exibição simples da tabela atual:
    st.dataframe(comissoes_df)

    # Ações Gerais — botão de baixar PDF atualizado para usar generate_pending_commissions_pdf:
    st.subheader("⚙️ Ações Gerais")
    col_action3, col_action4 = st.columns(2)
    with col_action3:
        pdf_data = None
        comissoes_atuais = st.session_state.comissoes_data
        if comissoes_atuais:
             pendentes = [c for c in comissoes_atuais if float(c.get("saldo_pendente", 0)) > 0]
             if pendentes:
                 pdf_bytes = generate_pending_commissions_pdf(comissoes_atuais)
                 if pdf_bytes:
                     pdf_data = pdf_bytes

        st.download_button(
            label="📄 Baixar PDF Pendentes",
            data=pdf_data if pdf_data else b"",
            file_name=f"comissoes_pendentes_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
            mime="application/pdf",
            key="pdf_download_button",
            disabled=pdf_data is None,
            help="Gerar e baixar um PDF com as comissões que possuem saldo pendente."
        )

# --- Controle de Fluxo ---
if not st.session_state.logged_in:
    show_login_screen()
else:
    show_main_screen()
