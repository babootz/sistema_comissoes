from io import BytesIO
from xhtml2pdf import pisa
import pandas as pd
import openpyxl
import base64

def gerar_pdf(html_content):
    pdf = BytesIO()
    pisa_status = pisa.CreatePDF(BytesIO(html_content.encode("utf-8")), dest=pdf)
    if pisa_status.err:
        return None
    return pdf.getvalue()

# Exemplo de função utilitária para converter DataFrame em HTML (você pode adaptar isso conforme usava antes)
def dataframe_para_html(df):
    return df.to_html(index=False, border=0, classes="table")

def salvar_excel(df, caminho):
    df.to_excel(caminho, index=False)

def carregar_excel(caminho):
    return pd.read_excel(caminho)

def baixar_arquivo(data, nome_arquivo):
    b64 = base64.b64encode(data).decode()
    href = f'<a href="data:application/octet-stream;base64,{b64}" download="{nome_arquivo}">Clique aqui para baixar</a>'
    return href
