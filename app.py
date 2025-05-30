import streamlit as st
import pandas as pd
from datetime import datetime
import copy # Needed for deep copies when editing
from utils import (
    gerar_pdf,
    dataframe_para_html,
    salvar_excel,
    carregar_excel,
    baixar_arquivo,
)


# --- Configuração Inicial ---
st.set_page_config(page_title="Sistema de Comissões", layout="wide", initial_sidebar_state="collapsed")
import streamlit as st
import os

def load_css():
    # Cria o caminho para o arquivo CSS dentro da pasta static
    css_path = os.path.join("static", "styles.css")
    with open(css_path) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

load_css()

# --- Estado da Aplicação ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'comissoes_data' not in st.session_state:
    st.session_state.comissoes_data = load_comissoes()
if 'show_history' not in st.session_state:
    st.session_state.show_history = False
if 'confirm_delete_all' not in st.session_state:
    st.session_state.confirm_delete_all = False
if 'edited_rows_info' not in st.session_state:
    st.session_state.edited_rows_info = None 
if 'show_edit_confirm_dialog' not in st.session_state:
    st.session_state.show_edit_confirm_dialog = False

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
            st.session_state.comissoes_data = load_comissoes() # Carrega dados frescos
            st.rerun()
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
                    # Tentar limpar o estado editado para evitar re-trigger imediato
                    # Pode ser necessário ajustar como o estado é limpo
                    # del st.session_state.data_editor_state["edited_rows"][edited_index]
                    st.rerun()
                else:
                    st.warning("Não foi possível identificar a linha editada (Segurado/Placa ausentes).")
            except IndexError:
                 st.warning("Erro ao acessar a linha editada no DataFrame.")
            except Exception as e:
                 st.error(f"Erro inesperado ao processar edição: {e}")

# --- Tela Principal ---
def show_main_screen():
    st.title("💰 Sistema de Gerenciamento de Comissões")

    # --- Atualizar Dados Brutos (se não estiver editando/confirmando) ---
    if not st.session_state.show_edit_confirm_dialog and not st.session_state.confirm_delete_all:
        st.session_state.comissoes_data = load_comissoes()

    # Criar DataFrame a partir dos dados brutos
    comissoes_df = pd.DataFrame(st.session_state.comissoes_data)
    # Conversões de tipo
    for col in ['premio_liquido', 'comissao_percentual', 'comissao_liquida', 'saldo_pendente']:
        if col in comissoes_df.columns:
             comissoes_df[col] = pd.to_numeric(comissoes_df[col], errors='coerce').fillna(0.0)
    if 'data_efetivacao' in comissoes_df.columns:
        # Tenta converter para data, mas mantém como string se falhar (para exibição)
        comissoes_df['data_efetivacao_dt'] = pd.to_datetime(comissoes_df['data_efetivacao'], errors='coerce')

    # --- Seção de Adicionar Comissão ---
    with st.expander("➕ Adicionar Nova Comissão", expanded=False):
        with st.form("add_comissao_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                segurado = st.text_input("Segurado", key="add_segurado")
                placa = st.text_input("Placa", key="add_placa")
                data_efetivacao = st.date_input("Data da Efetivação", value=datetime.today(), key="add_data")
            with col2:
                seguradora = st.text_input("Seguradora", key="add_seguradora")
                premio_liquido = st.number_input("Prêmio Líquido", min_value=0.0, format="%.2f", key="add_premio")
                comissao_percentual = st.number_input("Comissão (%)", min_value=0.0, max_value=100.0, format="%.2f", key="add_percentual")
            
            obs = st.text_area("Observações", key="add_obs")
            
            submitted = st.form_submit_button("Adicionar Comissão")
            if submitted:
                if not segurado or not placa:
                    st.warning("Os campos 'Segurado' e 'Placa' são obrigatórios.")
                else:
                    comissoes = st.session_state.comissoes_data
                    identificador_unico = (segurado.strip().lower(), placa.strip().lower())
                    if any((c['segurado'].strip().lower(), c['placa'].strip().lower()) == identificador_unico for c in comissoes):
                        st.error(f"Erro: Já existe uma comissão para o segurado '{segurado}' com a placa '{placa}'.")
                    else:
                        comissao_liquida = calcular_comissao_liquida(premio_liquido, comissao_percentual)
                        saldo_pendente = calcular_saldo_pendente(comissao_liquida, [])
                        
                        nova_comissao = {
                            "segurado": segurado.strip(),
                            "placa": placa.strip().upper(),
                            "data_efetivacao": data_efetivacao.strftime("%Y-%m-%d"),
                            "comissao_percentual": comissao_percentual,
                            "seguradora": seguradora.strip(),
                            "premio_liquido": premio_liquido,
                            "comissao_liquida": comissao_liquida,
                            "pagamentos": [],
                            "obs": obs.strip(),
                            "saldo_pendente": saldo_pendente
                        }
                        comissoes.append(nova_comissao)
                        save_comissoes(comissoes)
                        log_action("Adicionar Comissão", f"Segurado: {segurado}, Placa: {placa}")
                        st.success("Comissão adicionada com sucesso!")
                        st.session_state.comissoes_data = comissoes
                        st.rerun()

    # --- Filtros e Pesquisa ---
    st.subheader("🔍 Filtros e Pesquisa")
    col_filter1, col_filter2, col_filter3 = st.columns(3)
    with col_filter1:
        filtro_segurado = st.text_input("Filtrar por Segurado", key="filter_segurado")
    with col_filter2:
        filtro_placa = st.text_input("Filtrar por Placa", key="filter_placa")
    with col_filter3:
        filtro_seguradora = st.text_input("Filtrar por Seguradora", key="filter_seguradora")

    filtered_df = comissoes_df.copy()
    if filtro_segurado:
        filtered_df = filtered_df[filtered_df['segurado'].str.contains(filtro_segurado, case=False, na=False)]
    if filtro_placa:
        filtered_df = filtered_df[filtered_df['placa'].str.contains(filtro_placa, case=False, na=False)]
    if filtro_seguradora:
        filtered_df = filtered_df[filtered_df['seguradora'].str.contains(filtro_seguradora, case=False, na=False)]
    
    st.session_state.current_display_df = filtered_df.copy()

    # --- Exibição e Edição dos Dados ---
    st.subheader("📊 Painel de Comissões (Clique nas células para editar)")
    if filtered_df.empty:
        st.info("Nenhuma comissão encontrada com os filtros aplicados." if (filtro_segurado or filtro_placa or filtro_seguradora) else "Nenhuma comissão cadastrada ainda.")
    else:
        colunas_exibicao = [
            'segurado', 'placa', 'seguradora', 'data_efetivacao', 
            'premio_liquido', 'comissao_percentual', 'comissao_liquida', 
            'saldo_pendente', 'obs' # 'pagamentos' removido da exibição principal
        ]
        colunas_exibicao = [col for col in colunas_exibicao if col in filtered_df.columns]
        
        column_config_editor = {
            'segurado': st.column_config.TextColumn(required=True),
            'placa': st.column_config.TextColumn(required=True),
            'seguradora': st.column_config.TextColumn(),
            # Usar a coluna de data convertida para o editor
            'data_efetivacao_dt': st.column_config.DateColumn("Data Efetivação", format="DD/MM/YYYY", required=True),
            'premio_liquido': st.column_config.NumberColumn(format="R$ %.2f", required=True),
            'comissao_percentual': st.column_config.NumberColumn(format="%.2f%%", min_value=0, max_value=100, required=True),
            'comissao_liquida': st.column_config.NumberColumn(format="R$ %.2f", disabled=True, help="Calculado automaticamente"),
            'saldo_pendente': st.column_config.NumberColumn(format="R$ %.2f", disabled=True, help="Calculado automaticamente"),
            'obs': st.column_config.TextColumn(),
            # Remover 'data_efetivacao' original da configuração se 'data_efetivacao_dt' for usada
            'data_efetivacao': None 
        }
        column_config_editor = {k: v for k, v in column_config_editor.items() if k in filtered_df.columns or k == 'data_efetivacao_dt'}
        # Renomear a coluna de data no DF exibido para corresponder à config
        df_to_edit = filtered_df.rename(columns={'data_efetivacao_dt': 'data_efetivacao_dt'})
        # Garantir que a coluna original 'data_efetivacao' não seja mostrada se a _dt for usada
        if 'data_efetivacao_dt' in column_config_editor and 'data_efetivacao' in colunas_exibicao:
             colunas_exibicao.remove('data_efetivacao')
             colunas_exibicao.insert(3, 'data_efetivacao_dt') # Inserir na posição correta

        edited_df = st.data_editor(
            df_to_edit[colunas_exibicao],
            key="data_editor_state",
            hide_index=True,
            use_container_width=True,
            column_config=column_config_editor,
            num_rows="fixed", # Mudar para fixed para evitar adição/deleção direta
            on_change=handle_edit,
            disabled=['comissao_liquida', 'saldo_pendente']
        )

    # --- Diálogo de Confirmação de Edição ---
    if st.session_state.show_edit_confirm_dialog and st.session_state.edited_rows_info:
        info = st.session_state.edited_rows_info
        segurado_id = info['segurado']
        placa_id = info['placa']
        changes = info['changes']
        
        with st.dialog("Confirmar Alterações?"): 
            st.warning(f"Você está prestes a alterar a comissão para:\nSegurado: **{segurado_id}** | Placa: **{placa_id}**")
            st.markdown("**Alterações Propostas:**")
            # Mostrar as mudanças de forma mais legível
            for field, value in changes.items():
                # Tratar data vinda do DateColumn
                if field == 'data_efetivacao_dt':
                    try:
                        date_obj = pd.to_datetime(value).date()
                        st.write(f"- Data Efetivação: {date_obj.strftime('%d/%m/%Y')}")
                    except:
                        st.write(f"- Data Efetivação: {value} (Formato inválido?)")
                else:
                    st.write(f"- {field.replace('_', ' ').title()}: {value}")
            # st.json(changes) # Alternativa: mostrar JSON cru
            
            confirm_edit_checkbox = st.checkbox("Sim, confirmo que desejo salvar estas alterações.", key="edit_confirm_check")
            
            col_edit_confirm1, col_edit_confirm2 = st.columns(2)
            with col_edit_confirm1:
                if st.button("Salvar Alterações", key="save_edit_button", disabled=not confirm_edit_checkbox):
                    if confirm_edit_checkbox:
                        comissoes = load_comissoes()
                        edit_success = False
                        for i, comissao in enumerate(comissoes):
                            if comissao['segurado'] == segurado_id and comissao['placa'] == placa_id:
                                original_comissao = copy.deepcopy(comissao) # Para log
                                
                                for field, new_value in changes.items():
                                    # Mapear de volta o nome da coluna de data
                                    actual_field = 'data_efetivacao' if field == 'data_efetivacao_dt' else field
                                    
                                    if actual_field == 'data_efetivacao':
                                        try:
                                            dt_obj = pd.to_datetime(new_value).date()
                                            comissoes[i][actual_field] = dt_obj.strftime("%Y-%m-%d")
                                        except Exception as e:
                                            st.error(f"Erro ao converter data {new_value}: {e}. Alteração da data ignorada.")
                                            continue
                                    elif actual_field in comissoes[i]: # Apenas atualiza campos existentes
                                        comissoes[i][actual_field] = new_value
                                
                                # Recalcular
                                comissoes[i]['comissao_liquida'] = calcular_comissao_liquida(
                                    comissoes[i].get('premio_liquido'), 
                                    comissoes[i].get('comissao_percentual')
                                )
                                comissoes[i]['saldo_pendente'] = calcular_saldo_pendente(
                                    comissoes[i]['comissao_liquida'], 
                                    comissoes[i].get('pagamentos', [])
                                )
                                edit_success = True
                                log_details = f"Segurado: {segurado_id}, Placa: {placa_id}. Antes: {original_comissao}, Depois: {comissoes[i]}"
                                log_action("Editar Comissão", log_details)
                                break
                        
                        if edit_success:
                            save_comissoes(comissoes)
                            st.success("Comissão atualizada com sucesso!")
                            st.session_state.comissoes_data = comissoes
                        else:
                            st.error("Erro: Comissão original não encontrada para aplicar as alterações.")
                            log_action("Erro Edição", f"Comissão não encontrada: Segurado: {segurado_id}, Placa: {placa_id}")
                            
                        st.session_state.edited_rows_info = None
                        st.session_state.show_edit_confirm_dialog = False
                        st.rerun()
                    
            with col_edit_confirm2:
                if st.button("Cancelar Edição", key="cancel_edit_button"):
                    log_action("Edição Cancelada", f"Segurado: {segurado_id}, Placa: {placa_id}")
                    st.session_state.edited_rows_info = None
                    st.session_state.show_edit_confirm_dialog = False
                    st.rerun()

    # --- Ações Gerais --- 
    st.subheader("⚙️ Ações Gerais")
    col_action3, col_action4 = st.columns(2)
    with col_action3:
        # Preparar dados para o botão de download PDF
        pdf_data = None
        comissoes_atuais = st.session_state.comissoes_data
        if comissoes_atuais:
             # Filtrar pendentes para habilitar botão
             pendentes = [c for c in comissoes_atuais if float(c.get("saldo_pendente", 0)) > 0]
             if pendentes:
                 pdf_bytes = generate_pending_commissions_pdf(comissoes_atuais)
                 if pdf_bytes:
                     pdf_data = pdf_bytes
                     log_action("Geração PDF", f"{len(pendentes)} comissões pendentes incluídas.")
                 else:
                     # Erro na geração já foi logado em generate_pending_commissions_pdf
                     pass 

        st.download_button(
            label="📄 Baixar PDF Pendentes",
            data=pdf_data if pdf_data else b"", # Passa bytes ou vazio
            file_name=f"comissoes_pendentes_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
            mime="application/pdf",
            key="pdf_download_button",
            disabled=pdf_data is None, # Desabilita se não há dados ou erro na geração
            help="Gerar e baixar um PDF com as comissões que possuem saldo pendente."
        )
    with col_action4:
        if st.button("📜 Ver/Ocultar Histórico", key="history_button"):
             st.session_state.show_history = not st.session_state.show_history
             st.rerun()

    # --- Seção de Histórico (Condicional) ---
    if st.session_state.show_history:
        st.subheader("📜 Histórico de Ações")
        history_data = load_history()
        if not history_data:
            st.info("Nenhuma ação registrada no histórico.")
        else:
            history_df = pd.DataFrame(history_data)
            history_df = history_df.sort_values(by="timestamp", ascending=False)
            st.dataframe(history_df, hide_index=True, use_container_width=True)

    # --- Botão e Lógica de Excluir Tudo ---
    st.divider()
    st.subheader("⚠️ Área de Risco")
    if st.button("❌ Excluir Todas as Comissões", key="delete_all_trigger", type="primary"):
        st.session_state.confirm_delete_all = True
        log_action("Tentativa Excluir Tudo", "Botão 'Excluir Todas' clicado.")
        st.rerun()

    # --- Diálogo de Confirmação para Excluir Tudo --- 
    if st.session_state.confirm_delete_all:
        with st.dialog("Confirmar Exclusão Total"):
            st.warning("**ATENÇÃO:** Esta ação é irreversível e apagará TODOS os registros de comissões permanentemente.")
            confirm_checkbox = st.checkbox("Sim, eu entendo e quero excluir todas as comissões.", key="delete_all_checkbox")
            
            col_confirm1, col_confirm2 = st.columns(2)
            with col_confirm1:
                if st.button("Confirmar Exclusão", key="delete_all_confirm", disabled=not confirm_checkbox):
                    if confirm_checkbox:
                        save_comissoes([])
                        log_action("Excluir Tudo Confirmado", "Todas as comissões foram excluídas.")
                        st.session_state.comissoes_data = []
                        st.session_state.confirm_delete_all = False
                        st.success("Todas as comissões foram excluídas com sucesso!")
                        st.rerun()
            with col_confirm2:
                if st.button("Cancelar", key="delete_all_cancel"):
                    st.session_state.confirm_delete_all = False
                    log_action("Excluir Tudo Cancelado", "Ação de exclusão total cancelada pelo usuário.")
                    st.rerun()

# --- Controle de Fluxo ---
if not st.session_state.logged_in:
    show_login_screen()
else:
    show_main_screen()

