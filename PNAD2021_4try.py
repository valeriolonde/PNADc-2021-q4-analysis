import pandas as pd
import numpy as np
from tabulate import tabulate

from pathlib import Path

# Define o caminho base
base_path = Path.cwd()
base_path
# Define o caminho relativo para a pasta de dados
data_folder = base_path / "Pasta_PNAD2021_4tri" /"Dados"

# Define o caminho para o arquivo de dicionário
dictionary_path = data_folder / "Dicionario.xls"

# Lê o arquivo de dicionário básico PNAD contínua
dicionario = pd.read_excel(dictionary_path, skiprows=1)

# lê arquivo de dicionário PNAD contínua com parte suplementar

# Define o caminho para o arquivo de dicionário
dictionary_path = data_folder / "Dicionario_PNAD.xlsx"

# Lê o arquivo de dicionário básico PNAD contínua
dicionario_2 = pd.read_excel(dictionary_path, skiprows=1)

## Selecionando a variável tamanho e excluindo os NA 
## e depois transformando em inteiros, 
##  depois transformar numa lista
tamanho_sem_na = dicionario['Tamanho'].dropna().astype(int).tolist()
tamanho_sem_na

## arquivo sem cabeçalho e e widths define a largura de cada coluna
## todos os dados devem ser tratados como strings

## Definindo caminho de dados da PNAD
pnad_path = data_folder / "PNADC_042021.txt"

## Importando os dados da PNAD.
pnad2021 = pd.read_fwf(pnad_path, header = None, widths=tamanho_sem_na, 
                       dtype=str, float_format="%.2f")

## pegando o código da variável no dicionário e excluindo os Na's
codigo = dicionario['Código\nda\nvariável'].dropna()

# percorrer o dicionário em busca do valor 'V1028' para descobri sem precisar olhar o dicionário
for chave, valor in codigo.items():
    if valor == 'V1028':
        print(f"A chave correspondente a 'V1028' é {chave}")

## Acessando o V1028
codigo[91]        

## Colocando o código da variável como nome da coluna
pnad2021 = pnad2021.rename(columns=dict(zip(pnad2021.columns, codigo)))
pnad2021
## Covertendno 'V1028' em float. V1028 é o peso 
pnad2021['V1028'] = pnad2021['V1028'].astype(float)

# Agrupar os dados por UF e somar os valores de V1028 correspondentes
soma_v1028_uf = pnad2021.groupby('UF')['V1028'].sum()

# Convertendo a série em um data frame e renomeando a coluna
pop_total = soma_v1028_uf.to_frame(name='população').reset_index().\
    rename(columns={'index': 'UF'})

# criar um dicionário de mapeamento com as chaves em formato de strings
uf_map = {
    '11': 'RO',
    '12': 'AC',
    '13': 'AM',
    '14': 'RR',
    '15': 'PA',
    '16': 'AP',
    '17': 'TO',
    '21': 'MA',
    '22': 'PI',
    '23': 'CE',
    '24': 'RN',
    '25': 'PB',
    '26': 'PE',
    '27': 'AL',
    '28': 'SE',
    '29': 'BA',
    '31': 'MG',
    '32': 'ES',
    '33': 'RJ',
    '35': 'SP',
    '41': 'PR',
    '42': 'SC',
    '43': 'RS',
    '50': 'MS',
    '51': 'MT',
    '52': 'GO',
    '53': 'DF'
}

# Aplicando o mapeamento à coluna UF
pop_total['UF'] = pop_total['UF'].map(uf_map)

## arredondando os números de população e também tirando o 0.
pop_total['população'] = pop_total['população'].round(2).apply(lambda x: x[1:] if str(x).startswith('0') else x)

## Printando a população
print(pop_total)

## Exercícios. Calcular os domicilios por UF estimados

## Usando a variável VD2002 --- Condicação do domicílio

## filtrando para para o chefe do domicílio. Para descobrir a quantidade de domicílios
domic_uf = pnad2021.query('V2005 == "01"').groupby('UF')['V1028'].sum()

##transformadno em data frame 
dom_total = domic_uf.to_frame().reset_index().rename(columns={'index': 'UF', 0: 'domic_uf'})

# Aplicando o mapeamento à coluna UF
dom_total['UF'] = dom_total['UF'].map(uf_map)

## arredondando os números de população e também tirando o 0.
dom_total['V1028'] = dom_total['V1028'].round(2).apply(lambda x: x[1:] if str(x).startswith('0') else x)

## Printando dom_total
print(dom_total)

## Selecionando as variáveis de interesse que usarei no exercício
pessoas_e_dom  = pd.DataFrame(pnad2021[['V2009', 'VD3005', 'V2003',
                        'V2007','UF', 'VD4020']])


labels = {
    'V2009':'idade' , 
    'VD3005': 'Escolaridade', 
    'V2003': 'Número de Ordem',
    'V2007': 'Sexo',
    'VD4020': 'Rendimento efetivo do trabalho'
}

## Colocando os labels 
pessoas_e_dom = pessoas_e_dom.rename(columns = labels)

## Passando os meus dados para numérico para poder fazer estatísticas
## descritivas e econometria 
pessoas_e_dom = pessoas_e_dom.apply(pd.to_numeric)

# Fazendo uma dummy de Sexo 
dummy_sexo = pd.get_dummies(pessoas_e_dom.Sexo, prefix='Sexo', drop_first=True)

# Juntando a variável dummy ao DataFrame original e deletando Sexo
pessoas_e_dom_2 = pd.concat([pessoas_e_dom, dummy_sexo], axis=1).drop('Sexo', axis=1)

# printando minha base de dados
print(pessoas_e_dom_2)

# Vendo informações do meu data frame
pessoas_e_dom_2.info()

## Tenho vários valores nulos na minha Escolaridade. Irei transformar para 0.
pessoas_e_dom_2['Escolaridade'].fillna(0, inplace=True)

## Deletando os NaN de Rendimento efetivo do trabalho
pessoas_e_dom_2 = pessoas_e_dom_2.dropna(axis=0) ## na linha 

import statsmodels.api as sm

# Definir as variáveis explicativas e a variável resposta
y = pessoas_e_dom_2['Rendimento efetivo do trabalho']
X = pessoas_e_dom_2[['Escolaridade', 'idade', 'Sexo_2']]

# Ajustar o modelo de regressão
modelo = sm.OLS(y, sm.add_constant(X)).fit()

# Imprimir o sumário do modelo
print(modelo.summary())


