import os
import re
import pdfplumber
import pandas as pd

def limpar_numero_br(valor_texto):
    """Converte números no formato brasileiro  em formato decimal"""
    if not valor_texto or valor_texto.strip() == "":
        return 0.0
    valor_limpo = valor_texto.replace(".", "").replace(",", ".")
    return float(valor_limpo)

def extrair_dados_nfs(lista_caminhos_pdfs):
    """
    Extração de todos os campos do DANFE.
    Mapeia Emitente, Destinatário, Impostos, Transportador, Volumes e Produtos
    """
    dados_extraidos = []

    for caminho_arquivo in lista_caminhos_pdfs:
        nome_arquivo = os.path.basename(caminho_arquivo)
        
        with pdfplumber.open(caminho_arquivo) as pdf:
            texto_nfs = ""
            linhas_produtos = []

            # Leitura de todas as páginas
            for numero_pagina, pagina in enumerate(pdf.pages, start=1):
                texto_nfs += pagina.extract_text() + "\n"
                
                tabelas_da_pagina = pagina.extract_tables()
                for tabela in tabelas_da_pagina:
                    for linha in tabela:
                        if linha[0] and linha[0].replace("\n", "").startswith("DM-"):
                            linhas_produtos.append(linha)

     
        # Extração de campos do texto da NF
        busca_nf = re.search(r"Nº\s*(\d{3}\.\d{3}\.\d{3})", texto_nfs)
        numero_nf = busca_nf.group(1) if busca_nf else "000.000.000"

        busca_serie = re.search(r"SÉRIE\s*(\d+)", texto_nfs)
        serie_nf = busca_serie.group(1) if busca_serie else "1"

        busca_chave = re.search(r"CHAVE DE ACESSO\s*\n\s*([\d\s]{44,})", texto_nfs)
        chave_acesso = busca_chave.group(1).replace(" ", "") if busca_chave else ""

        busca_natureza = re.search(r"NATUREZA DA OPERAÇÃO\s*\n(.*?)\s*\n", texto_nfs)
        natureza_op = busca_natureza.group(1).strip() if busca_natureza else ""

        todos_cnpjs = re.findall(r"\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}", texto_nfs)
        cnpj_emitente = todos_cnpjs[0] if len(todos_cnpjs) > 0 else ""
        cnpj_destinatario = todos_cnpjs[1] if len(todos_cnpjs) > 1 else ""
        cnpj_transportadora = todos_cnpjs[2] if len(todos_cnpjs) > 2 else ""

        todas_ies = re.findall(r"(?<!CNPJ:\s)\b(\d{9,12}|ISENTO)\b", texto_nfs)
        ie_emitente = todas_ies[0] if len(todas_ies) > 0 else ""
        ie_destinatario = todas_ies[1] if len(todas_ies) > 1 else "ISENTO"
        ie_transportadora = todas_ies[2] if len(todas_ies) > 2 else ""

        busca_cliente = re.search(r"DESTINATÁRIO / REMETENTE\s*\nNOME / RAZÃO SOCIAL.*?\n(.*?)\s+\d{2}\.\d{3}", texto_nfs)
        cliente = busca_cliente.group(1).strip() if busca_cliente else "Não encontrado"

        busca_data_emi = re.search(r"DATA DA EMISSÃO\s*\n.*?(\d{2}/\d{2}/\d{4})", texto_nfs)
        data_emissao = busca_data_emi.group(1) if busca_data_emi else ""
        
        busca_endereco_dest = re.search(r"ENDEREÇO.*?\n(.*?)\s+(?:Centro|Bairro)", texto_nfs)
        endereco_destinatario = busca_endereco_dest.group(1).strip() if busca_endereco_dest else ""

        busca_cep = re.search(r"CEP\s*\n.*?(\d{5}-\d{3})", texto_nfs)
        cep_destinatario = busca_cep.group(1) if busca_cep else ""

        busca_mun_dest = re.search(r"MUNICÍPIO.*?\n(.*?)\s+(?:SP|\d{4})", texto_nfs)
        municipio_destinatario = busca_mun_dest.group(1).strip() if busca_mun_dest else ""

        todas_ufs = re.findall(r"\b([A-Z]{2})\b", texto_nfs)
        # Filtra apenas as UFs válidas para evitar capturar siglas de outros campos
        ufs_validas = [uf for uf in todas_ufs if uf in ["SP", "RJ", "MG", "ES", "PR", "SC", "RS", "BA"]]
        uf_destinatario = ufs_validas[0] if len(ufs_validas) > 0 else ""
        uf_placa_veiculo = ufs_validas[1] if len(ufs_validas) > 1 else ""
        uf_transportadora = ufs_validas[2] if len(ufs_validas) > 2 else ""

        valores_impostos = re.findall(r"\b(\d{1,3}(?:\.\d{3})*,\d{2})\b", texto_nfs)
        # bloco de valores de impostos e totais da nota
        bc_icms_nota = valores_impostos[1] if len(valores_impostos) > 1 else "0,00"
        v_icms_nota = valores_impostos[2] if len(valores_impostos) > 2 else "0,00"
        v_frete = valores_impostos[7] if len(valores_impostos) > 7 else "0,00"
        v_seguro = valores_impostos[8] if len(valores_impostos) > 8 else "0,00"
        desconto = valores_impostos[9] if len(valores_impostos) > 9 else "0,00"
        outras_despesas = valores_impostos[10] if len(valores_impostos) > 10 else "0,00"
        v_ipi_nota = valores_impostos[11] if len(valores_impostos) > 11 else "0,00"
        v_total_produtos = valores_impostos[6] if len(valores_impostos) > 6 else "0,00"
        v_total_nota = valores_impostos[12] if len(valores_impostos) > 12 else "0,00"


        # extração de transportadora e volumes
        busca_nome_transp = re.search(r"TRANSPORTADOR / VOLUMES TRANSPORTADOS\s*\nNOME / RAZÃO SOCIAL.*?\n(.*?)\s+(?:0 -|1 -)", texto_nfs)
        nome_transportadora = busca_nome_transp.group(1).strip() if busca_nome_transp else ""

        busca_placa = re.search(r"PLACA DO VEÍCULO\s*\n.*?([A-Z]{3}-\d{4})", texto_nfs)
        placa_veiculo = busca_placa.group(1) if busca_placa else ""

        busca_antt = re.search(r"CÓDIGO ANTT\s*\n.*?(\d{6})", texto_nfs)
        codigo_antt = busca_antt.group(1) if busca_antt else ""

        busca_qtd_vol = re.search(r"QUANTIDADE\s*\n.*?(\d+)\s+VOLUMES", texto_nfs)
        qtd_volumes = busca_qtd_vol.group(1) if busca_qtd_vol else "0"

        busca_peso_b = re.search(r"PESO BRUTO\s*\n.*?([\d\.,]+)", texto_nfs)
        peso_bruto = limpar_numero_br(busca_peso_b.group(1)) if busca_peso_b else 0.0

        busca_peso_l = re.search(r"PESO LÍQUIDO\s*\n.*?([\d\.,]+)", texto_nfs)
        peso_liquido = limpar_numero_br(busca_peso_l.group(1)) if busca_peso_l else 0.0

        busca_vendedor = re.search(r"Vendedor Responsavel:\s*(.*?)\s*\|", texto_nfs)
        vendedor = busca_vendedor.group(1).strip() if busca_vendedor else "Não informado"

        # Extração de dados dos produtos
        for item in linhas_produtos:
            codigo_prod = item[0].replace("\n", "").strip()
            descricao_prod = item[1].replace("\n", " ").strip()
            
            ncm = item[2].strip()
            cst = item[3].strip()
            cfop = item[4].strip()
            unidade = item[5].strip()
            
            valores_agrupados_1 = item[6].split()
            qtd = limpar_numero_br(valores_agrupados_1[0]) if len(valores_agrupados_1) > 0 else 0.0
            valor_unitario = limpar_numero_br(valores_agrupados_1[1]) if len(valores_agrupados_1) > 1 else 0.0
            valor_total_item = limpar_numero_br(valores_agrupados_1[2]) if len(valores_agrupados_1) > 2 else 0.0

            valores_agrupados_2 = item[7].split()
            bc_icms_item = limpar_numero_br(valores_agrupados_2[0]) if len(valores_agrupados_2) > 0 else 0.0
            v_icms_item = limpar_numero_br(valores_agrupados_2[1]) if len(valores_agrupados_2) > 1 else 0.0
            v_ipi_item = limpar_numero_br(valores_agrupados_2[2]) if len(valores_agrupados_2) > 2 else 0.0
            perc_icms_item = limpar_numero_br(valores_agrupados_2[3]) if len(valores_agrupados_2) > 3 else 0.0
            perc_ipi_item = limpar_numero_br(valores_agrupados_2[4]) if len(valores_agrupados_2) > 4 else 0.0

            dados_extraidos.append({
                "Nome do Arquivo": nome_arquivo,
                "Chave de Acesso": chave_acesso,
                "Número da NF": numero_nf,
                "Série NF": serie_nf,
                "Data de Emissão": data_emissao,
                "Natureza da Operação": natureza_op,
                
                # EMITENTE
                "CNPJ Emitente": cnpj_emitente,
                "IE Emitente": ie_emitente,
                
                # DESTINATÁRIO
                "Cliente": cliente,
                "CNPJ Destinatário": cnpj_destinatario,
                "IE Destinatário": ie_destinatario,
                "Endereço Destinatário": endereco_destinatario,
                "Município Destinatário": municipio_destinatario,
                "UF Destinatário": uf_destinatario,
                "CEP Destinatário": cep_destinatario,
                
                # TOTAIS DA NOTA
                "BC ICMS Nota": limpar_numero_br(bc_icms_nota),
                "Valor ICMS Nota": limpar_numero_br(v_icms_nota),
                "Valor Total Produtos": limpar_numero_br(v_total_produtos),
                "Valor Frete": limpar_numero_br(v_frete),
                "Valor Seguro": limpar_numero_br(v_seguro),
                "Desconto": limpar_numero_br(desconto),
                "Outras Despesas": limpar_numero_br(outras_despesas),
                "Valor IPI Nota": limpar_numero_br(v_ipi_nota),
                "Valor Total da Nota": limpar_numero_br(v_total_nota),
                
                # TRANSPORTADORA E VOLUMES
                "Transportadora": nome_transportadora,
                "CNPJ Transportadora": cnpj_transportadora,
                "IE Transportadora": ie_transportadora,
                "Código ANTT": codigo_antt,
                "Placa Veículo": placa_veiculo,
                "UF Placa Veículo": uf_placa_veiculo,
                "UF Transportadora": uf_transportadora,
                "Qtd Volumes": qtd_volumes,
                "Peso Bruto (KG)": peso_bruto,
                "Peso Líquido (KG)": peso_liquido,
                
                # DADOS DO PRODUTO (NÍVEL DO ITEM)
                "Código do Produto": codigo_prod,
                "Descrição do Produto": descricao_prod,
                "NCM/SH": ncm,
                "CST": cst,
                "CFOP": cfop,
                "Unidade": unidade,
                "Quantidade Item": qtd,
                "Valor Unitário": valor_unitario,
                "Valor Total Item": valor_total_item,
                "BC ICMS Item": bc_icms_item,
                "Valor ICMS Item": v_icms_item,
                "% ICMS Item": perc_icms_item,
                "Valor IPI Item": v_ipi_item,
                "% IPI Item": perc_ipi_item,
                
                # INFORMAÇÕES ADICIONAIS
                "Vendedor": vendedor
            })

    return dados_extraidos