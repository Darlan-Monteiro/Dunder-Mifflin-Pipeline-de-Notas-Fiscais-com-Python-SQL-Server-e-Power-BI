# Dunder Mifflin · Pipeline de Notas Fiscais com Python, SQL Server e Power BI

![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)
![SQL Server](https://img.shields.io/badge/SQL%20Server-T--SQL-CC2927?logo=microsoftsqlserver&logoColor=white)
![Power BI](https://img.shields.io/badge/Power%20BI-DAX-F2C811?logo=powerbi&logoColor=black)
![Figma](https://img.shields.io/badge/Design-Figma-F24E1E?logo=figma&logoColor=white)

Projeto de ponta a ponta que simula o processamento de notas fiscais eletrônicas (NF-e) da **Dunder Mifflin Paper Company**, a empresa da série *The Office*. O fluxo gera as notas em PDF, extrai os dados de dentro dos PDFs, grava tudo em um banco **SQL Server** e entrega um painel de faturamento no **Power BI**.

**Painel online:** [abrir o dashboard no Power BI](https://app.powerbi.com/view?r=eyJrIjoiZDFkOWEyZjYtOWRiNi00Mzg2LTg0NzMtYWJiYzY2YmU0OGM3IiwidCI6IjY1OWNlMmI4LTA3MTQtNDE5OC04YzM4LWRjOWI2MGFhYmI1NyJ9)

![Dashboard Dunder Mifflin]<img width="1253" height="717" alt="dashboard" src="https://github.com/user-attachments/assets/e49371f0-1ea7-4f99-a5ae-e8483d430f71" />


> Projeto de portfólio feito por fã. Todas as empresas, pessoas, CNPJs e valores são **fictícios**. Dunder Mifflin e The Office pertencem aos seus respectivos detentores de direitos, e este projeto não tem qualquer vínculo com eles.

---

## Sumário

- [O problema que o projeto simula](#o-problema-que-o-projeto-simula)
- [Arquitetura](#arquitetura)
- [Tecnologias](#tecnologias)
- [Estrutura do repositório](#estrutura-do-repositório)
- [Como cada etapa funciona](#como-cada-etapa-funciona)
- [Como executar](#como-executar)
- [Modelo de dados no SQL Server](#modelo-de-dados-no-sql-server)
- [Consultas SQL de exemplo](#consultas-sql-de-exemplo)
- [Dashboard no Power BI](#dashboard-no-power-bi)
- [Medidas DAX](#medidas-dax)
- [Resultados da base atual](#resultados-da-base-atual)
- [Limitações conhecidas e próximos passos](#limitações-conhecidas-e-próximos-passos)
- [Autor](#autor)

---

## O problema que o projeto simula

Em muitas empresas, as notas fiscais chegam como **PDF** (a DANFE) e alguém precisa digitar os dados para controlar faturamento, impostos e logística. Esse trabalho é lento e sujeito a erro.

Aqui, o processo é automatizado:

1. As notas são geradas em PDF, no layout oficial da DANFE.
2. Um extrator lê cada PDF e transforma o texto em dados estruturados.
3. Os dados vão para um banco relacional, sem duplicar notas já processadas.
4. O Power BI transforma os dados em informação de negócio.

Como não existe uma base pública de NFs reais em PDF (os dados são protegidos por sigilo fiscal e pela LGPD), o projeto também gera as notas fictícias.

## Arquitetura

```
┌──────────────┐    ┌───────────────┐    ┌────────────────────┐    ┌──────────────┐    ┌───────────┐
│   app.py     │ -> │  PDFs (DANFE) │ -> │ extrair_dados_nf.py│ -> │   main.py    │ -> │ SQL Server│
│ gera XML+PDF │    │ 250 notas     │    │ pdfplumber + regex │    │ carga incre- │    │ AutomacaoNFs│
└──────────────┘    └───────────────┘    └────────────────────┘    │ mental       │    └─────┬─────┘
                                                                    └──────────────┘          │
                                                                                         ┌────▼─────┐
                                                                                         │ Power BI │
                                                                                         │ + Figma  │
                                                                                         └──────────┘
```

## Tecnologias

| Camada | Ferramenta | Uso |
|---|---|---|
| Geração das NFs | Python, `BrazilFiscalReport` | Monta XMLs de NF-e fictícios e converte em DANFE PDF |
| Extração | `pdfplumber`, `re` (regex), `pandas` | Lê texto e tabelas dos PDFs |
| Carga | `pyodbc` | Insere os dados no SQL Server |
| Banco | SQL Server (T-SQL) | Armazenamento e consultas |
| Visualização | Power BI e DAX | Medidas, modelo e relatório |
| Design | Figma | Tela de fundo do painel |

## Estrutura do repositório

```
.
├── app.py                  # Gera os XMLs de NF-e e os PDFs (DANFE)
├── extrair_dados_nf.py     # Extrai os campos dos PDFs
├── main.py                 # Carga incremental no SQL Server
├── requirements.txt        # Dependências Python
├── sql/
│   └── 01_create_table.sql # Criação do banco e da tabela
├── docs/
│   └── dashboard.png       # Print do painel
└── powerbi/
    └── (arquivo .pbix e tema, se quiser versionar)
```

## Como cada etapa funciona

### 1. Geração das notas (`app.py`)

- Cria **250 NF-e** com dados fictícios: 6 clientes, 5 vendedores, 7 produtos de papelaria e 2 transportadoras.
- Cada nota tem de 1 a 4 itens, com quantidades aleatórias e ICMS de 18%.
- Monta o XML no padrão NF-e 4.00 (com protocolo de autorização) e converte em PDF com a biblioteca [BrazilFiscalReport](https://github.com/Engenere/BrazilFiscalReport).
- Os PDFs são salvos na pasta `Pastas para armazenar as NFs`, com nomes como `NF_DunderMifflin_001_StoneandSonSuitWarehouse.pdf`.

### 2. Extração dos dados (`extrair_dados_nf.py`)

- Abre cada PDF com `pdfplumber` e lê o texto e as tabelas de todas as páginas.
- Cabeçalho, impostos e transporte são capturados por **expressões regulares** (número da nota, série, data de emissão, cliente, totais, transportadora, vendedor).
- A tabela de produtos é lida como tabela (`extract_tables`), e cada item vira uma linha.
- Números no formato brasileiro (`1.890,00`) são convertidos para decimal pela função `limpar_numero_br`.
- O resultado é uma lista de dicionários com **49 campos por linha de item**.

### 3. Carga no SQL Server (`main.py`)

- Conecta ao SQL Server com autenticação do Windows (driver *ODBC Driver 17*).
- **Carga incremental**: consulta os `Nome_Arquivo` já gravados em `Faturamento_NFs` e processa apenas os PDFs novos, sem duplicar notas.
- Converte a data de `DD/MM/AAAA` para `AAAA-MM-DD` e insere os dados com comandos parametrizados (`?`), o que evita SQL Injection e problemas de formatação.
- Usa um único `commit()` ao final do lote.

### 4. Visualização (Power BI)

O Power BI lê a tabela `Faturamento_NFs` do SQL Server. O painel tem seis cartões, um gráfico de área por mês, três rankings (produto, cliente, vendedor), uma rosca por transportadora e filtros por período, cliente e vendedor. Os rankings de cliente e vendedor usam **parâmetros de campo** para alternar a métrica exibida (valor total, ticket médio, número de notas).

## Como executar

### Pré-requisitos

- Python 3.10 ou superior
- SQL Server (a Express é gratuita) e acesso ao SSMS ou Azure Data Studio
- [ODBC Driver 17 for SQL Server](https://learn.microsoft.com/sql/connect/odbc/download-odbc-driver-for-sql-server)
- Power BI Desktop, para abrir o relatório

### Passo a passo

```bash
# 1. Clone o repositório
git clone https://github.com/Darlan-Monteiro/<nome-do-repositorio>.git
cd <nome-do-repositorio>

# 2. Crie e ative o ambiente virtual
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # Linux/Mac

# 3. Instale as dependências
pip install -r requirements.txt
```

Se preferir o [uv](https://docs.astral.sh/uv/), o equivalente é:

```bash
uv venv
uv pip install -r requirements.txt
```

**4. Crie o banco e a tabela:** abra o arquivo `sql/01_create_table.sql` no SSMS e execute (veja o script na seção [Modelo de dados](#modelo-de-dados-no-sql-server)).

**5. Ajuste a conexão** no começo do `main.py`, se necessário:

```python
servidor_sql = r"."            # ou r"NOME-PC\SQLEXPRESS"
banco_dados  = "AutomacaoNFs"
```

**6. Gere as notas fiscais:**

```bash
python app.py
```

**7. Extraia e grave no banco:**

```bash
python main.py
```

Rodar o `main.py` de novo é seguro: ele só processa PDFs que ainda não estão no banco.

**8. Abra o Power BI Desktop**, conecte ao SQL Server (`Obter dados > SQL Server`), importe `Faturamento_NFs` e crie as medidas da seção [Medidas DAX](#medidas-dax).

## Modelo de dados no SQL Server

Tabela única, **uma linha por item de nota fiscal**. Os campos de cabeçalho (cliente, total da nota, transportadora) se repetem em todos os itens da mesma nota.

```sql
CREATE DATABASE AutomacaoNFs;
GO
USE AutomacaoNFs;
GO

CREATE TABLE Faturamento_NFs (
    Id                    INT IDENTITY(1,1) PRIMARY KEY,
    Nome_Arquivo          NVARCHAR(255),
    Chave_Acesso          VARCHAR(44),
    Numero_NF             VARCHAR(15),
    Serie_NF              VARCHAR(5),
    Data_Emissao          DATE,
    Natureza_Operacao     NVARCHAR(120),
    CNPJ_Emitente         VARCHAR(18),
    IE_Emitente           VARCHAR(20),
    Cliente               NVARCHAR(150),
    CNPJ_Destinatario     VARCHAR(18),
    IE_Destinatario       VARCHAR(20),
    Endereco_Destinatario NVARCHAR(200),
    Municipio_Destinatario NVARCHAR(100),
    UF_Destinatario       CHAR(2),
    CEP_Destinatario      VARCHAR(9),
    BC_ICMS_Nota          DECIMAL(15,2),
    Valor_ICMS_Nota       DECIMAL(15,2),
    Valor_Total_Produtos  DECIMAL(15,2),
    Valor_Frete           DECIMAL(15,2),
    Valor_Seguro          DECIMAL(15,2),
    Desconto              DECIMAL(15,2),
    Outras_Despesas       DECIMAL(15,2),
    Valor_IPI_Nota        DECIMAL(15,2),
    Valor_Total_Nota      DECIMAL(15,2),
    Transportadora        NVARCHAR(150),
    CNPJ_Transportadora   VARCHAR(18),
    IE_Transportadora     VARCHAR(20),
    Codigo_ANTT           VARCHAR(10),
    Placa_Veiculo         VARCHAR(10),
    UF_Placa_Veiculo      CHAR(2),
    UF_Transportadora     CHAR(2),
    Qtd_Volumes           INT,
    Peso_Bruto            DECIMAL(12,3),
    Peso_Liquido          DECIMAL(12,3),
    Codigo_Produto        VARCHAR(30),
    Descricao_Produto     NVARCHAR(200),
    NCM_SH                VARCHAR(10),
    CST                   VARCHAR(5),
    CFOP                  VARCHAR(5),
    Unidade               VARCHAR(5),
    Quantidade_Item       DECIMAL(15,4),
    Valor_Unitario        DECIMAL(15,2),
    Valor_Total_Item      DECIMAL(15,2),
    BC_ICMS_Item          DECIMAL(15,2),
    Valor_ICMS_Item       DECIMAL(15,2),
    Perc_ICMS_Item        DECIMAL(5,2),
    Valor_IPI_Item        DECIMAL(15,2),
    Perc_IPI_Item         DECIMAL(5,2),
    Vendedor              NVARCHAR(100),
    Data_Processamento    DATETIME DEFAULT GETDATE()
);
```

> Os tipos acima foram definidos a partir do `INSERT` do `main.py`. Ajuste conforme a sua tabela, se for diferente.

## Consultas SQL de exemplo

Como a tabela tem uma linha por item, as consultas por nota precisam **eliminar a repetição** antes de somar. Caso contrário, o faturamento sai inflado.

**Faturamento total e ticket médio**

```sql
WITH notas AS (
    SELECT DISTINCT Nome_Arquivo, Valor_Total_Nota
    FROM Faturamento_NFs
)
SELECT COUNT(*)                 AS Total_Notas,
       SUM(Valor_Total_Nota)    AS Faturamento,
       AVG(Valor_Total_Nota)    AS Ticket_Medio,
       MAX(Valor_Total_Nota)    AS Maior_Nota
FROM notas;
```

**Faturamento por mês**

```sql
WITH notas AS (
    SELECT DISTINCT Nome_Arquivo, Data_Emissao, Valor_Total_Nota
    FROM Faturamento_NFs
)
SELECT FORMAT(Data_Emissao, 'yyyy-MM') AS Mes,
       COUNT(*)                        AS Notas,
       SUM(Valor_Total_Nota)           AS Faturamento
FROM notas
GROUP BY FORMAT(Data_Emissao, 'yyyy-MM')
ORDER BY Mes;
```

**Ranking de produtos (aqui se usa a linha do item)**

```sql
SELECT Descricao_Produto,
       SUM(Quantidade_Item)  AS Unidades,
       SUM(Valor_Total_Item) AS Faturamento
FROM Faturamento_NFs
GROUP BY Descricao_Produto
ORDER BY Faturamento DESC;
```

**Ranking de vendedores**

```sql
WITH notas AS (
    SELECT DISTINCT Nome_Arquivo, Vendedor, Valor_Total_Nota
    FROM Faturamento_NFs
)
SELECT Vendedor,
       COUNT(*)              AS Notas,
       SUM(Valor_Total_Nota) AS Faturamento,
       AVG(Valor_Total_Nota) AS Ticket_Medio
FROM notas
GROUP BY Vendedor
ORDER BY Faturamento DESC;
```

## Dashboard no Power BI

**Identidade visual:** azul-marinho e dourado, inspirados no logo da Dunder Mifflin. A tela de fundo foi desenhada no Figma.

| Visual | Campos |
|---|---|
| Cartões (6) | Faturamento geral, total de notas, ticket médio, maior nota, total de ICMS, itens vendidos |
| Faturamento por mês | `Calendario[Mês]` x faturamento geral |
| Faturamento por produto | `Descricao_Produto` x faturamento por produto |
| Faturamento por cliente | `Cliente`, com parâmetro de campo (valor total / ticket médio) |
| Desempenho dos vendedores | `Vendedor`, com parâmetro de campo (valor vendido / número de notas) |
| Notas por transportadora | `Transportadora` x faturamento geral, em rosca |
| Filtros | Período, cliente e vendedor |

### Perguntas de negócio que o painel responde

- Quanto a empresa faturou e como isso variou ao longo dos meses?
- Quais produtos e clientes concentram a receita?
- Qual vendedor entrega mais valor e qual tem o maior ticket médio?
- Quanto de ICMS foi gerado no período?
- Como as notas se dividem entre as transportadoras?

## Medidas DAX

> **Atenção ao modelo:** como a tabela tem uma linha por item, `Valor_Total_Nota` se repete em cada item da mesma nota. Somar a coluna direto infla o faturamento. As medidas abaixo agrupam por `Nome_Arquivo` antes de somar.

```dax
Faturamento Geral =
SUMX(
    SUMMARIZE(Faturamento_NFs, Faturamento_NFs[Nome_Arquivo]),
    CALCULATE(MAX(Faturamento_NFs[Valor_Total_Nota]))
)

Total de Notas Emitidas =
DISTINCTCOUNT(Faturamento_NFs[Nome_Arquivo])

Ticket Médio =
DIVIDE([Faturamento Geral], [Total de Notas Emitidas])

Maior Nota Emitida =
MAX(Faturamento_NFs[Valor_Total_Nota])

Total ICMS =
SUMX(
    SUMMARIZE(Faturamento_NFs, Faturamento_NFs[Nome_Arquivo]),
    CALCULATE(MAX(Faturamento_NFs[Valor_ICMS_Nota]))
)

Total Itens Vendidos =
SUM(Faturamento_NFs[Quantidade_Item])

Faturamento por Produto =
SUM(Faturamento_NFs[Valor_Total_Item])
```

**Tabela calendário**

```dax
Calendario =
ADDCOLUMNS(
    CALENDAR(DATE(2026,1,1), DATE(2026,12,31)),
    "Ano", YEAR([Date]),
    "Mês Nº", MONTH([Date]),
    "Mês",
        VAR MesMinusculo = FORMAT([Date], "mmm", "pt-BR")
        RETURN UPPER(LEFT(MesMinusculo, 1)) & MID(MesMinusculo, 2, 10)
)
```

Relacione `Calendario[Date]` a `Faturamento_NFs[Data_Emissao]` e ordene `Mês` por `Mês Nº`.

## Resultados da base atual

Valores da base gerada na última execução (o `app.py` usa dados aleatórios, então cada execução produz números diferentes):

| Indicador | Valor |
|---|---|
| Notas emitidas | 250 |
| Linhas de itens | 644 |
| Período | 02/01/2026 a 26/10/2026 |
| Faturamento geral | R$ 677.804,40 |
| Ticket médio | R$ 2.711,22 |
| Maior nota | R$ 9.365,60 |
| Total de ICMS | R$ 122.004,79 |
| Itens vendidos | 5.232 |

**O que os dados mostram**

- O papel Sulfite A3 90g é o produto que mais fatura (cerca de 25,8% do total).
- Lackawanna County é o maior cliente (cerca de 25,1% do faturamento).
- Stanley Hudson lidera em valor vendido, e Andy Bernard tem o maior ticket médio.
- Fevereiro foi o mês de maior faturamento. Outubro está incompleto, com notas só até o dia 26.

## Limitações conhecidas e próximos passos

Pontos que identifiquei ao analisar a base e que fazem parte do roadmap:

- [ ] **Extração de CNPJ**: o extrator associa os CNPJs pela ordem de aparição no PDF, o que pode trocar emitente, destinatário e transportadora. A correção é ler cada CNPJ dentro do seu bloco de campo.
- [ ] **Campos vazios**: chave de acesso, natureza da operação, CEP, código ANTT e placa não estão sendo capturados corretamente.
- [ ] **Dados logísticos zerados**: o gerador cria notas com frete, peso e volumes em zero, e todos os clientes em SP. Preencher esses campos permitiria uma segunda página de logística (mapa por UF, frete sobre faturamento, peso por transportadora).
- [ ] **Reprodutibilidade**: adicionar `random.seed(...)` no `app.py` para gerar sempre a mesma base.
- [ ] **Modelo relacional**: separar a tabela única em `Notas`, `Itens`, `Clientes`, `Produtos` e `Transportadoras` (modelo estrela).
- [ ] **Validação**: usar o XML de origem como gabarito para medir a acurácia do extrator.
- [ ] **Testes automatizados** para as funções de limpeza e extração.
- [ ] **Segunda página** do painel com análises de impostos e logística.

## Autor

**Darlan Monteiro**

- GitHub: [@Darlan-Monteiro](https://github.com/Darlan-Monteiro)
