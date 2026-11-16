import os
import pyodbc
from extrair_dados_nf import extrair_dados_nfs

# Configurações de Caminho e Conexão
pasta_pdfs = "Pastas para armazenar as NFs"
servidor_sql = r"."
banco_dados = "AutomacaoNFs"

# bloco de conexão com o SQL Server usando pyodbc
string_conexao = (
    f"DRIVER={{ODBC Driver 17 for SQL Server}};"
    f"SERVER={servidor_sql};"
    f"DATABASE={banco_dados};"
    f"Trusted_Connection=yes;"
)

print(f"Conectando ao SQL Server no banco '{banco_dados}'")
conn = pyodbc.connect(string_conexao)
cursor = conn.cursor()

# bloco para criar a tabela Faturamento_NFs caso ela não exista
cursor.execute("SELECT DISTINCT Nome_Arquivo FROM Faturamento_NFs")
arquivos_ja_processados = [linha[0] for linha in cursor.fetchall()]

# blocos para listar os arquivos PDF na pasta e identificar os novos
todos_arquivos_pasta = [f for f in os.listdir(pasta_pdfs) if f.endswith(".pdf")]
arquivos_novos = [f for f in todos_arquivos_pasta if f not in arquivos_ja_processados]
# bloco para processar os novos arquivos PDF
if not arquivos_novos:
    print("Nenhuma nota fiscal nova encontrada. O Banco de Dados já está atualizado.")
else:
    print(f"Processando {len(arquivos_novos)} novos PDFs. Aguarde.")
    
    caminhos_novos_pdfs = [os.path.join(pasta_pdfs, f) for f in arquivos_novos]
    dados_novos = extrair_dados_nfs(caminhos_novos_pdfs)
    
    if dados_novos:
        print("Inserindo os novos dados no SQL Server")
        
        # bloco SQL para inserir os dados extraídos na tabela Faturamento_NFs       
        sql_insert = """
            INSERT INTO Faturamento_NFs (
                Nome_Arquivo, Chave_Acesso, Numero_NF, Serie_NF, Data_Emissao, Natureza_Operacao,
                CNPJ_Emitente, IE_Emitente, Cliente, CNPJ_Destinatario, IE_Destinatario,
                Endereco_Destinatario, Municipio_Destinatario, UF_Destinatario, CEP_Destinatario,
                BC_ICMS_Nota, Valor_ICMS_Nota, Valor_Total_Produtos, Valor_Frete, Valor_Seguro,
                Desconto, Outras_Despesas, Valor_IPI_Nota, Valor_Total_Nota,
                Transportadora, CNPJ_Transportadora, IE_Transportadora, Codigo_ANTT, Placa_Veiculo,
                UF_Placa_Veiculo, UF_Transportadora, Qtd_Volumes, Peso_Bruto, Peso_Liquido,
                Codigo_Produto, Descricao_Produto, NCM_SH, CST, CFOP, Unidade,
                Quantidade_Item, Valor_Unitario, Valor_Total_Item, BC_ICMS_Item, Valor_ICMS_Item,
                Perc_ICMS_Item, Valor_IPI_Item, Perc_IPI_Item, Vendedor
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        # bloco para inserir cada linha de dados extraídos no banco de dados
        for d in dados_novos:
            data_str = d.get("Data de Emissão", "")
            data_sql = None
            if len(data_str) == 10:
                dia, mes, ano = data_str.split("/")
                data_sql = f"{ano}-{mes}-{dia}"
            # bloco para preparar os valores a serem inseridos no banco de dados
            valores = (
                d["Nome do Arquivo"], d["Chave de Acesso"], d["Número da NF"], d["Série NF"], data_sql, d["Natureza da Operação"],
                d["CNPJ Emitente"], d["IE Emitente"], d["Cliente"], d["CNPJ Destinatário"], d["IE Destinatário"],
                d["Endereço Destinatário"], d["Município Destinatário"], d["UF Destinatário"], d["CEP Destinatário"],
                d["BC ICMS Nota"], d["Valor ICMS Nota"], d["Valor Total Produtos"], d["Valor Frete"], d["Valor Seguro"],
                d["Desconto"], d["Outras Despesas"], d["Valor IPI Nota"], d["Valor Total da Nota"],
                d["Transportadora"], d["CNPJ Transportadora"], d["IE Transportadora"], d["Código ANTT"], d["Placa Veículo"],
                d["UF Placa Veículo"], d["UF Transportadora"], d["Qtd Volumes"], d["Peso Bruto (KG)"], d["Peso Líquido (KG)"],
                d["Código do Produto"], d["Descrição do Produto"], d["NCM/SH"], d["CST"], d["CFOP"], d["Unidade"],
                d["Quantidade Item"], d["Valor Unitário"], d["Valor Total Item"], d["BC ICMS Item"], d["Valor ICMS Item"],
                d["% ICMS Item"], d["Valor IPI Item"], d["% IPI Item"], d["Vendedor"]
            )
            
            # Enfileira a inserção da linha
            cursor.execute(sql_insert, valores)
            
        # Confirma as alterações no banco de dados
        conn.commit()
        print(f"Foram adicionadas {len(dados_novos)} novas linhas ao Banco de Dados.")
    else:
        print("Os PDFs eram válidos, mas nenhum produto foi encontrado dentro deles.")


conn.close()