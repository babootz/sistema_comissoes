# Novo Sistema de Gerenciamento de Comissões Web

Este é um sistema web moderno e profissional para gerenciamento de comissões, desenvolvido em Python com Streamlit.

## Funcionalidades Principais

*   **Interface Profissional:** Design limpo e moderno com CSS customizado.
*   **Login Seguro:** Acesso via senha única (padrão: `0000`).
*   **Gerenciamento Completo:** Adição, visualização, filtragem e pesquisa de comissões.
*   **Edição Segura:** Edição de qualquer campo de uma comissão existente, com diálogo de confirmação (checkbox) antes de salvar.
*   **Exclusão Total Segura:** Opção para excluir todas as comissões com diálogo de confirmação (checkbox) para evitar acidentes.
*   **Identificação Única:** Utiliza a combinação "Segurado" + "Placa" para identificar unicamente cada registro (sem IDs automáticos).
*   **Relatórios PDF:** Geração e download de relatórios PDF elegantes contendo apenas as comissões com saldo pendente.
*   **Histórico Detalhado:** Registro de todas as ações importantes realizadas no sistema (login, adição, edição, exclusão, geração de PDF) com data e hora.

## Estrutura do Projeto

```
novo_sistema_comissoes/
├── app.py                 # Aplicação principal Streamlit
├── utils.py               # Funções auxiliares (dados, cálculos, PDF, log, etc.)
├── styles.css             # Arquivo CSS para customização da interface
├── requirements.txt       # Dependências Python do projeto
├── data/                  # Diretório para armazenamento de dados
│   ├── comissoes.json     # Arquivo JSON com os dados das comissões
│   └── history.json       # Arquivo JSON com o histórico de ações
└── templates/
    └── pdf_template.html  # Template HTML para a geração do PDF
```

## Como Executar Localmente

1.  **Pré-requisitos:** Certifique-se de ter Python 3.7+ e pip instalados.
2.  **Clone ou Baixe:** Obtenha os arquivos do projeto.
3.  **Navegue até o Diretório:** Abra um terminal ou prompt de comando e navegue até a pasta `novo_sistema_comissoes`.
4.  **Instale as Dependências:**
    ```bash
    pip install -r requirements.txt
    ```
5.  **Execute a Aplicação:**
    ```bash
    streamlit run app.py
    ```
6.  **Acesse:** Abra seu navegador e acesse o endereço fornecido pelo Streamlit (geralmente `http://localhost:8501`).

## Implantação (Ex: Streamlit Community Cloud)

Este aplicativo está pronto para ser implantado em plataformas como o Streamlit Community Cloud (gratuito):

1.  **Conta GitHub:** Certifique-se de ter uma conta no GitHub.
2.  **Repositório:** Crie um novo repositório no GitHub e envie todos os arquivos da pasta `novo_sistema_comissoes` para ele.
3.  **Streamlit Cloud:**
    *   Acesse [share.streamlit.io](https://share.streamlit.io/).
    *   Faça login com sua conta GitHub.
    *   Clique em "New app".
    *   Selecione o repositório que você criou.
    *   Verifique se o branch principal e o caminho do arquivo `app.py` estão corretos.
    *   Clique em "Deploy!".
4.  **Acesso:** Após a implantação, você receberá um URL público para acessar sua aplicação web.

**Observação:** Os arquivos `data/comissoes.json` e `data/history.json` serão criados automaticamente na primeira execução se não existirem. Em ambientes de implantação como o Streamlit Cloud, esses dados podem ser reiniciados a cada nova implantação ou reinicialização do container, a menos que você configure um armazenamento persistente (o que geralmente não está disponível no plano gratuito).

