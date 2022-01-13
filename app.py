import numpy as np
import streamlit as st
import matplotlib.pyplot as plt
from fbprophet import Prophet
from fbprophet.plot import plot_plotly
from plotly import graph_objs as go
import plotly.express as px
from datetime import date
import warnings
warnings.filterwarnings("ignore")
import pandas as pd
from fbprophet.plot import plot_yearly
from PIL import Image
import streamlit.components.v1 as components
import requests

# Definindo o layout da aplicacao
st.set_page_config(page_title='FastPredict',layout="wide")

# Codificacao de arquivos
encoding = ["utf-8","latin1","iso-8859-1"]

# Definindo o fim do intervalo de dados
HOJE = date.today().strftime("%Y-%m-%d")

# Pegando imagem da aplicacao
image = Image.open('icone.png')

# Logo da aplicacao
st.image(image, caption='', width=100)

# Titulo da aplicacao
st.title("FastPredict")

# Sidebar com os parametros para carregamento do arquivo e layout
st.sidebar.title("Parâmetros do sistema")
parametros  = [",",";"]
separador   = st.sidebar.selectbox("Qual carecter é usado para separar as colunas no seu arquivo?",parametros)
cabecalho   = st.sidebar.number_input("Em qual linha está o seu cabeçalho?", min_value = 1, format = '%d')
color_graphs = st.sidebar.color_picker("Escolha uma cor para os gráficos:")

# Seleciona a coluna de data
arquivos = ["","ARQUIVO","API JSON"]
tipo_carga = st.selectbox("Selecione a forma de carregamento dos dados:",arquivos)

# Verifica se o campo está preenchido
if tipo_carga != "":
    if tipo_carga == "ARQUIVO":
        # Escolha o arquivo de dados
        fonte_dados = st.file_uploader("Escolha o arquivo para a análise", type=['csv','txt','xls','xlsx'])
        # Verifica se foi selecionado um arquivo
        if fonte_dados is not None:
            # Verifica se é um arquivo de TEXTO ou Planilha do Excel
            if ("excel" in fonte_dados.type) or ("officedocument" in fonte_dados.type):
                dados = pd.read_excel(fonte_dados, header=(cabecalho-1))
            else:
                dados = pd.read_csv(fonte_dados, header=(cabecalho-1), sep=separador, dtype=str)
    else:
        # Usar um serviço de API
        fonte_dados = st.text_input("Digite o endereço URL da API")
        # Verifica se um endereco foi inserido
        if fonte_dados != "":
            dados = pd.read_json(fonte_dados)
    
    # Verifica se exite uma fonte de dados selecionada
    if 'dados' in globals():
        # Criando lista em branco para colunas
        colunas = [""]

        # Adicionando o nome dos campos do dataframe
        colunas.extend(dados.columns.to_list())

        # Seleciona a coluna de data
        coluna_data = st.selectbox("Selecione a Coluna de Data:",colunas)

        # Seleciona a coluna para analise
        coluna_analise = st.selectbox("Selecione a Coluna para Análise:",colunas)

        # Seleciona a coluna para filtragem
        coluna_filtro = st.selectbox("Selecione a Coluna para Filtro:",colunas)

        if coluna_filtro != "":
            # Seleciona item para filtro dos dados
            filtro = [""]
            filtro.extend(dados[coluna_filtro].unique().tolist())
            filtro = st.selectbox("Selecione Item para Filtro:",filtro)

        # Verificando se campos data e analise estao preenchidos
        if coluna_data != "" and coluna_analise != "":
            # Removendo linhas com valores nulos
            dados2 = dados.dropna(subset=[coluna_data,coluna_analise])

            # Verifica se ha filtros a serem aplicados
            if coluna_filtro != "" and filtro != "":
                # Aplica o filtro aos dados
                dados2 = dados2[dados2[coluna_filtro] == filtro]

            # Conversao de dados
            dados2[coluna_data] = pd.to_datetime(dados2[coluna_data])
            dados2[coluna_analise] = dados2[coluna_analise].replace(',','.', regex=True)
            dados2[coluna_analise] = dados2[coluna_analise].astype(float)

            # Criando coluna de dia da semana
            dados2["DiadaSemana"] = dados2[coluna_data].dt.day_name()

            # Visualizando dados brutos
            st.subheader("Visualização dos Dados Brutos")
            st.write(dados2)

            # Dividindo a aplicação em colunas
            col1, col2 = st.columns(2)

            with col1:
                # Criando o grafico dos dados brutos
                st.subheader("Quantificação dos Dados")
                df = px.data.tips()
                fig = px.histogram(dados2, x=coluna_data, y=coluna_analise, color_discrete_sequence=[color_graphs])
                fig.update_layout(bargap=0.2)
                st.plotly_chart(fig,use_container_width=True)

            with col2:
                # Criando grafico de linhas
                st.subheader("Distribuição dos Dados")
                df = px.data.tips()
                fig = px.scatter(dados2, x=coluna_data, y=coluna_analise, color_discrete_sequence=[color_graphs])
                fig.update_layout(bargap=0.2)
                st.plotly_chart(fig,use_container_width=True)

            # Define o horizonte de previsao
            num_anos = st.slider("Escolha o horizonte de Previsão (em anos):",0,4)

            if num_anos != 0:

                # Preparando os dados para as previsoes com pacote Prophet
                df_treino = dados2[[coluna_data,coluna_analise]]
                df_treino = df_treino.rename(columns = {coluna_data: "ds", coluna_analise: "y"})

                # Criando o Modelo
                modelo = Prophet(yearly_seasonality=20)

                # Treinando o modelo
                modelo.fit(df_treino)

                # Calcula o periodo de dias
                periodo = num_anos * 365

                # Prepara as datas futuras para as previsoes
                futuro = modelo.make_future_dataframe(periods = periodo)

                # Faz as previsoes
                forecast = modelo.predict(futuro)

                # Gerando dataframe com os dados previstos
                ultima_data_dados = dados2[coluna_data].iloc[-1]
                apenas_previsoes = forecast[(forecast["ds"]>ultima_data_dados)]

                # Visualizando dados brutos
                st.subheader("Visualização dos Dados Previstos")
                st.write(apenas_previsoes)

                # Criando o grafico das previsoes
                st.subheader("Gráfico de Dados Preditivos")
                grafico2 = plot_plotly(modelo, forecast)
                st.plotly_chart(grafico2,use_container_width=True)

                # Fazer download dos dados previstos
                @st.cache
                def convert_df(df):
                    # IMPORTANT: Cache the conversion to prevent computation on every rerun
                    return df.to_csv().encode('utf-8')

                csv = convert_df(forecast)

                st.download_button(
                    label="Faça o download da previsão (CSV)",
                    data=csv,
                    file_name='previsao.csv',
                    mime='text/csv',
                )