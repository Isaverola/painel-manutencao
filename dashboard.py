import streamlit as st
import pandas as pd
import plotly.express as px
import os

# --- Configuração da Página ---
st.set_page_config(page_title="Dashboard de Manutenção", layout="wide")

# --- CSS PARA FUNDO PRETO/DEGRADÊ ---
st.markdown(
    """
    <style>
    /* Fundo da aplicação principal */
    .stApp {
        background: linear-gradient(to bottom, #0e1117, #262730);
        color: white;
    }
    /* Ajuste para cartões métricos (opcional, para destacar) */
    [data-testid="stMetricValue"] {
        color: #00f2c3 !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)

st.title("📊 Dashboard de Manutenção") 

# --- 1. FUNÇÕES DE LIMPEZA E EXTRAÇÃO ---

def extrair_id_maquina(texto):
    if not isinstance(texto, str):
        return "N/I"
    texto_limpo = texto.strip().replace('#', '')
    if ' - ' in texto_limpo:
        return texto_limpo.split(' - ')[0].strip()
    return texto_limpo.split(' ')[0].strip()

def extrair_nome_maquina(texto):
    if not isinstance(texto, str):
        return "Desconhecido"
    if ' - ' in texto:
        partes = texto.split(' - ')
        if len(partes) > 1:
            return partes[1].strip()
    return texto

def converter_duracao(valor):
    try:
        if pd.isna(valor) or valor == 0 or valor == '0':
            return 0.0
        if isinstance(valor, str):
            valor = valor.strip()
            if ':' in valor:
                partes = valor.split(':')
                if len(partes) == 3:
                    return int(partes[0]) + (int(partes[1])/60) + (int(partes[2])/3600)
                elif len(partes) == 2:
                    return int(partes[0]) + (int(partes[1])/60)
        return 0.0
    except:
        return 0.0

def limpar_numero(valor):
    if isinstance(valor, str):
        limpo = valor.replace('R$', '').replace(' ', '')
        if ',' in limpo and '.' in limpo: 
            limpo = limpo.replace('.', '').replace(',', '.')
        elif ',' in limpo:
            limpo = limpo.replace(',', '.')
        try:
            return float(limpo)
        except:
            return 0.0
    return valor

# --- 2. CARREGAMENTO DE DADOS ---
@st.cache_data
def load_data():
    arquivos_map = {
        "os": ["Planilha sem título - Acompanhamento OSs.csv", "Acompanhamento OSs.csv"],
        "pecas": ["Planilha sem título - Custos com peças.csv", "Custos com peças.csv"],
        "fretes": ["Planilha sem título - Custos com fretes.csv", "Custos com fretes.csv"],
        "he": ["Planilha sem título - Horas Extras.csv", "Horas Extras.csv"]
    }
    
    dfs = {}
    
    # Função para ler CSV de forma resiliente
    def tentar_ler(caminho):
        try:
            return pd.read_csv(caminho)
        except:
            try:
                return pd.read_csv(caminho, sep=';')
            except:
                try:
                    return pd.read_csv(caminho, sep=';', encoding='latin-1')
                except:
                    return pd.read_csv(caminho, encoding='latin-1')

    for chave, lista_nomes in arquivos_map.items():
        arquivo_encontrado = None
        for nome in lista_nomes:
            if os.path.exists(nome):
                arquivo_encontrado = nome
                break
            elif os.path.exists(nome + ".csv"):
                arquivo_encontrado = nome + ".csv"
                break
        
        if arquivo_encontrado:
            dfs[chave] = tentar_ler(arquivo_encontrado)
            if not dfs[chave].empty and len(dfs[chave].columns) < 2:
                 try:
                     dfs[chave] = pd.read_csv(arquivo_encontrado, sep=';', encoding='latin-1')
                 except:
                     pass
        else:
            dfs[chave] = pd.DataFrame()

    df_os = dfs.get("os", pd.DataFrame())
    df_pecas = dfs.get("pecas", pd.DataFrame())
    df_fretes = dfs.get("fretes", pd.DataFrame())
    df_he = dfs.get("he", pd.DataFrame())

    try:
        for df in [df_os, df_pecas, df_fretes, df_he]:
            if not df.empty:
                df.columns = df.columns.str.strip()

        if not df_os.empty:
            df_os['Início'] = pd.to_datetime(df_os['Início'], dayfirst=False, errors='coerce')
            df_os['Mes'] = df_os['Início'].dt.to_period('M').astype(str)
            col_ativo = 'Ativo ' if 'Ativo ' in df_os.columns else 'Ativo'
            if col_ativo in df_os.columns:
                df_os['ID_Maquina'] = df_os[col_ativo].apply(extrair_id_maquina)
                df_os['Nome_Temp'] = df_os[col_ativo].apply(extrair_nome_maquina)
                if not df_os.empty:
                    mapa_nomes = df_os.groupby('ID_Maquina')['Nome_Temp'].agg(lambda x: x.mode()[0] if not x.mode().empty else "Desconhecido").to_dict()
                    df_os['Maquina_Label'] = df_os['ID_Maquina'].map(mapa_nomes)
                else:
                    df_os['Maquina_Label'] = df_os['ID_Maquina']
            else:
                df_os['ID_Maquina'] = "N/A"
                df_os['Maquina_Label'] = "N/A"

            if 'Duração' in df_os.columns:
                df_os['Duracao_Horas'] = df_os['Duração'].apply(converter_duracao)
            if 'Custo real dos técnicos (custo m.o.)' in df_os.columns:
                df_os['Custo real dos técnicos (custo m.o.)'] = df_os['Custo real dos técnicos (custo m.o.)'].apply(limpar_numero)

        if not df_pecas.empty:
            df_pecas['Data de lançamento'] = pd.to_datetime(df_pecas['Data de lançamento'], dayfirst=False, errors='coerce')
            df_pecas['Mes'] = df_pecas['Data de lançamento'].dt.to_period('M').astype(str)
            if 'Valor/moeda objeto' in df_pecas.columns:
                df_pecas['Valor/moeda objeto'] = df_pecas['Valor/moeda objeto'].apply(limpar_numero)

        if not df_fretes.empty:
            df_fretes['Data de lançamento'] = pd.to_datetime(df_fretes['Data de lançamento'], dayfirst=False, errors='coerce')
            df_fretes['Mes'] = df_fretes['Data de lançamento'].dt.to_period('M').astype(str)
            if 'Valor/moeda objeto' in df_fretes.columns:
                df_fretes['Valor/moeda objeto'] = df_fretes['Valor/moeda objeto'].apply(limpar_numero)

        if not df_he.empty:
            df_he['DATA DA OCORRÊNCIA'] = pd.to_datetime(df_he['DATA DA OCORRÊNCIA'], dayfirst=False, errors='coerce')
            df_he['Mes'] = df_he['DATA DA OCORRÊNCIA'].dt.to_period('M').astype(str)
            if 'VALOR' in df_he.columns:
                df_he['VALOR'] = df_he['VALOR'].apply(limpar_numero)

    except Exception as e:
        st.error(f"Erro Crítico no tratamento: {e}")
        return None, None, None, None

    return df_os, df_pecas, df_fretes, df_he

# --- 3. EXECUÇÃO ---
df_os, df_pecas, df_fretes, df_he = load_data()

if df_os is not None and not df_os.empty:
    
    st.sidebar.header("Filtros")
    todos_meses = sorted(list(set(df_os['Mes'].dropna().unique()) | set(df_pecas['Mes'].dropna().unique())))
    todos_meses = [m for m in todos_meses if m != 'NaT' and m != 'nan']
    
    mes_selecionado = st.sidebar.multiselect("Selecione o Mês", todos_meses, default=[])

    if not mes_selecionado:
        st.warning("👈 Selecione um mês no menu lateral para visualizar os dados.")
        st.stop()

    df_os_filt = df_os[df_os['Mes'].isin(mes_selecionado)]
    df_pecas_filt = df_pecas[df_pecas['Mes'].isin(mes_selecionado)]
    df_fretes_filt = df_fretes[df_fretes['Mes'].isin(mes_selecionado)]
    df_he_filt = df_he[df_he['Mes'].isin(mes_selecionado)]

    qtd_os_unicas = df_os_filt['CÓDIGO DA OS'].nunique()
    c_mo = df_os_filt['Custo real dos técnicos (custo m.o.)'].sum()
    c_pc = df_pecas_filt['Valor/moeda objeto'].sum()
    c_fr = df_fretes_filt['Valor/moeda objeto'].sum()
    custo_total = c_mo + c_pc + c_fr
    qtd_maquinas = df_os_filt['ID_Maquina'].nunique()
    he_total = df_he_filt['VALOR'].sum()

    if not df_os_filt.empty:
        top_id = df_os_filt['ID_Maquina'].mode()[0]
        try:
            nome_campeao = df_os_filt[df_os_filt['ID_Maquina'] == top_id]['Maquina_Label'].iloc[0]
        except:
            nome_campeao = top_id
        qtd_top = df_os_filt['ID_Maquina'].value_counts().iloc[0]
        texto_destaque = f"{nome_campeao}"
    else:
        texto_destaque = "-"
        qtd_top = 0

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("N° O.S", qtd_os_unicas)
    col2.metric("Custo Total", f"R$ {custo_total:,.2f}")
    col3.metric("Ativos Atendidos", qtd_maquinas)
    col4.metric("Horas Extras", f"{he_total:,.1f} h")

    st.markdown("---")
    
    aviso1, aviso2 = st.columns(2)
    aviso1.info(f"🏆 **Máquina com Mais Manutenções:** {texto_destaque} - {qtd_top} vezes")
    
    if not df_os_filt.empty:
        falha_comum = df_os_filt['Descrição da falha'].mode()[0]
        aviso2.warning(f"⚠️ **Falha com mais recorrências:** {falha_comum}")

    st.markdown("---")

    labels_pt = {
        'Mes': 'Mês', 'CÓDIGO DA OS': 'Qtd O.S.', 'Valor': 'R$', 
        'Maquina_Label': 'Máquina', 'ID_Maquina': 'ID',
        'Descrição da falha': 'Falhas', 'Duracao_Horas': 'Horas', 
        'VALOR': 'Horas', 'Valor/moeda objeto': 'R$'
    }
    
    st.subheader(f"Ranking de intervenções por máquinas que mais pararam ({', '.join(mes_selecionado)})")
    if 'Maquina_Label' in df_os_filt.columns:
        ranking_maq = df_os_filt['Maquina_Label'].value_counts().nlargest(10).reset_index()
        ranking_maq.columns = ['Maquina_Label', 'Intervenções']
        
        fig_rank = px.bar(ranking_maq, x='Intervenções', y='Maquina_Label', text_auto=True, orientation='h',
                          color='Intervenções', color_continuous_scale='Reds', labels=labels_pt)
        fig_rank.update_layout(yaxis={'categoryorder':'total ascending'}, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig_rank, use_container_width=True)

    c1, c2 = st.columns(2)
    
    with c1:
        st.subheader("1. Quantidade de O.S")
        g1 = df_os_filt.groupby('Mes')['CÓDIGO DA OS'].nunique().reset_index()
        fig1 = px.bar(g1, x='Mes', y='CÓDIGO DA OS', text_auto=True, labels=labels_pt)
        fig1.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig1, use_container_width=True)
        
    with c2:
        st.subheader("2. Composição de Custos")
        res_mo = df_os_filt.groupby('Mes')['Custo real dos técnicos (custo m.o.)'].sum().reset_index()
        res_mo['Tipo'] = 'Mão de Obra'
        res_mo.rename(columns={'Custo real dos técnicos (custo m.o.)': 'Valor'}, inplace=True)
        
        res_pc = df_pecas_filt.groupby('Mes')['Valor/moeda objeto'].sum().reset_index()
        res_pc['Tipo'] = 'Peças'
        res_pc.rename(columns={'Valor/moeda objeto': 'Valor'}, inplace=True)

        res_fr = df_fretes_filt.groupby('Mes')['Valor/moeda objeto'].sum().reset_index()
        res_fr['Tipo'] = 'Frete'
        res_fr.rename(columns={'Valor/moeda objeto': 'Valor'}, inplace=True)
        
        df_final = pd.concat([res_mo, res_pc, res_fr])
        fig2 = px.bar(df_final, x='Mes', y='Valor', color='Tipo', text_auto='.2s', labels=labels_pt)
        fig2.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig2, use_container_width=True)

    c3, c4 = st.columns(2)

    with c3:
        st.subheader("3. Ativos/Componentes Atendidos")
        g3 = df_os_filt.groupby('Mes')['ID_Maquina'].nunique().reset_index()
        fig3 = px.bar(g3, x='Mes', y='ID_Maquina', text_auto=True, labels=labels_pt)
        fig3.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig3, use_container_width=True)

    with c4:
        st.subheader("4. Total de Falhas")
        g4 = df_os_filt.groupby('Mes')['Descrição da falha'].count().reset_index()
        fig4 = px.bar(g4, x='Mes', y='Descrição da falha', text_auto=True, labels=labels_pt)
        fig4.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig4, use_container_width=True)

    c5, c6 = st.columns(2)

    with c5:
        st.subheader("5. Tempo médio de reparo (MTBF) - Horas")
        if 'Duracao_Horas' in df_os_filt.columns:
            g5 = df_os_filt.groupby('Mes')['Duracao_Horas'].mean().reset_index()
            fig5 = px.line(g5, x='Mes', y='Duracao_Horas', markers=True, labels=labels_pt)
            fig5.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig5, use_container_width=True)

    with c6:
        st.subheader("6. Custo de Frete")
        g6 = df_fretes_filt.groupby('Mes')['Valor/moeda objeto'].sum().reset_index()
        fig6 = px.bar(g6, x='Mes', y='Valor/moeda objeto', text_auto='.2s', color_discrete_sequence=['gold'], labels=labels_pt)
        fig6.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig6, use_container_width=True)

    st.subheader("7. Horas Extras")
    g7 = df_he_filt.groupby('Mes')['VALOR'].sum().reset_index()
    fig7 = px.bar(g7, x='Mes', y='VALOR', text_auto='.1f', color_discrete_sequence=['purple'], labels=labels_pt)
    fig7.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
    st.plotly_chart(fig7, use_container_width=True)

else:
    st.info("Aguardando arquivos...")
