from io import BytesIO
from xhtml2pdf import pisa
import pandas as pd
import base64

def gerar_pdf(html_content):
    """Gera um PDF a partir de conteúdo HTML usando xhtml2pdf"""
    pdf = BytesIO()
    pisa_status = pisa.CreatePDF(BytesIO(html_content.encode("utf-8")), dest=pdf)
    if pisa_status.err:
        return None
    return pdf.getvalue()

def dataframe_para_html(df):
    """Converte DataFrame em HTML formatado para PDF"""
    return df.to_html(index=False, border=0, classes="table table-striped")

def salvar_excel(df, caminho):
    """Salva DataFrame como arquivo Excel"""
    df.to_excel(caminho, index=False)

def carregar_excel(caminho):
    """Carrega planilha Excel para DataFrame"""
    return pd.read_excel(caminho)

def baixar_arquivo(data, nome_arquivo):
    """Cria link de download para o arquivo gerado"""
    b64 = base64.b64encode(data).decode()
    href = f'<a href="data:application/octet-stream;base64,{b64}" download="{nome_arquivo}">Clique aqui para baixar</a>'
    return href
import streamlit as st

def load_css(file_name):
    with open(file_name) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
