import json
import os
from datetime import datetime
import streamlit as st
import base64
from xhtml2pdf import pisa
from io import BytesIO
from jinja2 import Environment, FileSystemLoader, select_autoescape
import pandas as pd # Import pandas here if needed for date conversion in PDF

DATA_DIR = "data"
COMISSOES_FILE = os.path.join(DATA_DIR, "comissoes.json")
HISTORY_FILE = os.path.join(DATA_DIR, "history.json")
TEMPLATES_DIR = "templates"

# --- Funções de Gerenciamento de Dados ---

def initialize_data_files():
    """Cria os arquivos JSON e diretórios se não existirem."""
    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(TEMPLATES_DIR, exist_ok=True) # Ensure templates dir exists
    if not os.path.exists(COMISSOES_FILE):
        with open(COMISSOES_FILE, "w") as f:
            json.dump([], f)
    if not os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "w") as f:
            json.dump([], f)
    # Check if template exists, maybe create a default one if needed?
    # For now, assume it's provided or created elsewhere.

def load_data(file_path):
    """Carrega dados de um arquivo JSON."""
    try:
        with open(file_path, "r") as f:
            # Handle potential datetime strings during load if needed, but better to handle during use
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        # Return empty list for commissions/history, or {} for config, etc.
        return [] 

def save_data(data, file_path):
    """Salva dados em um arquivo JSON."""
    with open(file_path, "w") as f:
        # Ensure datetime objects are converted to strings before saving if they exist
        json.dump(data, f, indent=4, default=str) # Use default=str for basic datetime handling

def load_comissoes():
    """Carrega os dados das comissões."""
    return load_data(COMISSOES_FILE)

def save_comissoes(comissoes):
    """Salva os dados das comissões."""
    save_data(comissoes, COMISSOES_FILE)

def load_history():
    """Carrega o histórico de ações."""
    return load_data(HISTORY_FILE)

def save_history(history):
    """Salva o histórico de ações."""
    save_data(history, HISTORY_FILE)

# --- Funções de Histórico ---

def log_action(action, details=""):
    """Registra uma ação no histórico."""
    history = load_history()
    log_entry = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "action": action,
        "details": details
    }
    history.append(log_entry)
    save_history(history)

# --- Funções de Autenticação ---

SENHA_MESTRA = "0000"

def authenticate(password):
    """Verifica a senha fornecida."""
    return password == SENHA_MESTRA

# --- Funções de Cálculo ---

def calcular_comissao_liquida(premio_liquido, comissao_percentual):
    if premio_liquido is None or comissao_percentual is None:
        return 0.0
    try:
        premio_liquido_float = float(premio_liquido)
        comissao_percentual_float = float(comissao_percentual)
        comissao_bruta = premio_liquido_float * (comissao_percentual_float / 100)
        comissao_apos_imposto = comissao_bruta * (1 - 0.13482028) 
        comissao_liquida = comissao_apos_imposto / 2
        return round(comissao_liquida, 2)
    except (ValueError, TypeError):
        return 0.0

def calcular_saldo_pendente(comissao_liquida, pagamentos):
    comissao_liquida_float = 0.0
    if comissao_liquida is not None:
        try:
            comissao_liquida_float = float(comissao_liquida)
        except (ValueError, TypeError):
            pass # Keep it 0.0 if conversion fails
            
    if not isinstance(pagamentos, list):
        pagamentos = []
        
    total_pago = 0.0
    for p in pagamentos:
        try:
            valor = p.get("valor")
            if valor is not None:
                total_pago += float(valor)
        except (ValueError, TypeError):
            pass # Ignore payments that cannot be converted to float
            
    return round(comissao_liquida_float - total_pago, 2)

# --- Funções Auxiliares de Interface ---

def load_css(file_name):
    """Carrega um arquivo CSS local."""
    try:
        with open(file_name) as f:
            st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
    except FileNotFoundError:
        st.warning(f"Arquivo CSS '{file_name}' não encontrado. Usando estilos padrão.")

# --- Função de Geração de PDF ---

def generate_pending_commissions_pdf(comissoes):
    """Gera um PDF com as comissões pendentes usando WeasyPrint e Jinja2."""
    comissoes_pendentes = [
        c for c in comissoes 
        if c.get("saldo_pendente") is not None and float(c.get("saldo_pendente", 0)) > 0
    ]
    
    total_pendente = sum(float(c.get("saldo_pendente", 0)) for c in comissoes_pendentes)
    
    # Configurar Jinja2
    env = Environment(
        loader=FileSystemLoader(TEMPLATES_DIR),
        autoescape=select_autoescape(['html', 'xml'])
    )
    # Adicionar módulo datetime ao ambiente Jinja para formatação
    env.globals['modules'] = {'datetime': datetime}
    
    try:
        template = env.get_template("pdf_template.html")
    except Exception as e:
        st.error(f"Erro ao carregar o template PDF: {e}")
        return None

    # Preparar dados para o template
    # Converter datas string para objetos datetime se necessário para formatação no template
    for comissao in comissoes_pendentes:
        if isinstance(comissao.get('data_efetivacao'), str):
            try:
                comissao['data_efetivacao_obj'] = datetime.strptime(comissao['data_efetivacao'], '%Y-%m-%d')
            except ValueError:
                 comissao['data_efetivacao_obj'] = None # Handle error or keep original string
        else:
             comissao['data_efetivacao_obj'] = comissao.get('data_efetivacao') # Assume it's already datetime or None

    context = {
        "comissoes": comissoes_pendentes,
        "total_pendente": total_pendente,
        "data_geracao": datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    }
    
    try:
        html_content = template.render(context)
        # Use WeasyPrint para gerar o PDF em memória
        pdf_bytes = pdf = BytesIO()
pisa.CreatePDF(BytesIO(html_content.encode('utf-8')), dest=pdf)
pdf.getvalue()
        return pdf_bytes
    except Exception as e:
        st.error(f"Erro ao gerar o PDF: {e}")
        log_action("Erro Geração PDF", str(e))
        return None
