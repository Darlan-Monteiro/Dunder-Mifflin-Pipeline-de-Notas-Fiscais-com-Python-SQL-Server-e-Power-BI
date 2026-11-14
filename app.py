import os
import random
from datetime import datetime, timedelta
import re
from brazilfiscalreport.danfe import Danfe, DanfeConfig, Margins

# config de caminho para salvar as nfs
pasta_destino = "Pastas para armazenar as NFs"
os.makedirs(pasta_destino, exist_ok=True)

# config correta do DANFE
caminho_logo = "logo.png" if os.path.exists("logo.png") else ""
config = DanfeConfig(
    logo=caminho_logo,
    margins=Margins(top=5, right=5, bottom=5, left=5)
)

# vendedores pra aba de dados adicionais
vendedores = ["Jim Halpert", "Dwight Schrute", "Phyllis Vance", "Stanley Hudson", "Andy Bernard"]
# blocos de clientes, produtos e transportadoras para gerar as NFs
clientes = [
    {"nome": "Lackawanna County", "cnpj": "11111111000111", "end": "Court House Square", "num": "200"},
    {"nome": "Blue Cross of Pennsylvania", "cnpj": "22222222000122", "end": "Health Avenue", "num": "505"},
    {"nome": "Dunmore High School", "cnpj": "33333333000133", "end": "High School Rd", "num": "100"},
    {"nome": "Stone and Son Suit Warehouse", "cnpj": "44444444000144", "end": "Fashion District", "num": "42"},
    {"nome": "HarperCollins Publishing", "cnpj": "55555555000155", "end": "Writer's Block", "num": "707"},
    {"nome": "Schrute Farms Bed and Breakfast", "cnpj": "66666666000166", "end": "Beet Farm Road", "num": "1"}
]

produtos = [
    {"codigo": "DM-A4-75", "nome": "Papel Sulfite A4 75g (Caixa 10 Resmas)", "preco": 189.90, "unidade": "CX", "peso": 25.0},
    {"codigo": "DM-A3-90", "nome": "Papel Sulfite A3 90g (Caixa 5 Resmas)", "preco": 245.50, "unidade": "CX", "peso": 18.5},
    {"codigo": "DM-PREM-80", "nome": "Papel Premium Dunder Mifflin Infinity 80g", "preco": 210.00, "unidade": "CX", "peso": 20.0},
    {"codigo": "DM-FOTO-180", "nome": "Papel Fotografico Brilhante 180g (Pacote 100 fls)", "preco": 45.00, "unidade": "PCT", "peso": 1.2},
    {"codigo": "DM-CART-150", "nome": "Cartolina Branca 150g (Pacote 50 fls)", "preco": 68.90, "unidade": "PCT", "peso": 3.5},
    {"codigo": "DM-POST-AM", "nome": "Bloco de Notas Adesivas Amarelo (Kit 5)", "preco": 25.50, "unidade": "KIT", "peso": 0.5},
    {"codigo": "DM-ENV-P", "nome": "Envelopes Pardos A4 (Caixa 500 un)", "preco": 115.00, "unidade": "CX", "peso": 5.0}
]

transportadoras = [
    {"nome": "Vance Refrigeration Logistics", "cnpj": "77777777000177", "ie": "111222333", "end": "Warehouse Sec 5", "mun": "Sao Paulo", "placa": "BVR-1994", "rntc": "445566"},
    {"nome": "Madge and Warehouse Transports", "cnpj": "88888888000188", "ie": "999888777", "end": "Loading Dock A", "mun": "Sao Paulo", "placa": "DMG-2005", "rntc": "112233"}
]

data_base = datetime(2026, 1, 1)
total_notas_geradas = 250

print(f"Gerando NFs, aguarde...")
# loop para gerar as notas fiscais
for i in range(1, total_notas_geradas + 1):
    cliente = random.choice(clientes)
    vendedor = random.choice(vendedores)
    transp = random.choice(transportadoras)
    # datas de emissão e saída aleatórias
    dias_add = random.randint(0, 300)
    hora_emissao = random.randint(8, 16)
    data_emissao = data_base + timedelta(days=dias_add, hours=hora_emissao, minutes=random.randint(0, 59))
    data_saida = data_emissao + timedelta(hours=1, minutes=random.randint(10, 45))
    # quantidade de itens por nota fiscal
    qtd_itens = random.randint(1, 4)
    itens_escolhidos = random.sample(produtos, qtd_itens)
    # variáveis para acumular os valores totais da nota fiscal
    detalhes_xml = ""
    valor_total_nf = 0.0
    valor_total_icms = 0.0
    total_volumes = 0
    peso_liquido_total = 0.0
    # loop para gerar os detalhes de cada item da nota fiscal
    for idx, prod in enumerate(itens_escolhidos, start=1):
        qtd = random.randint(1, 15)
        valor_produto = round(qtd * prod['preco'], 2)
        valor_icms = round(valor_produto * 0.18, 2)
        # acumula os valores totais da nota fiscal
        valor_total_nf += valor_produto
        valor_total_icms += valor_icms
        total_volumes += qtd
        peso_liquido_total += (qtd * prod['peso'])
        # bloco para gerar o XML do detalhe do item
        detalhes_xml += f"""
          <det nItem="{idx}">
            <prod>
              <cProd>{prod['codigo']}</cProd><cEAN>SEM GTIN</cEAN><xProd>{prod['nome']}</xProd>
              <NCM>48025610</NCM><CFOP>5102</CFOP><uCom>{prod['unidade']}</uCom><qCom>{qtd:.4f}</qCom>
              <vUnCom>{prod['preco']:.2f}</vUnCom><vProd>{valor_produto:.2f}</vProd>
              <cEANTrib>SEM GTIN</cEANTrib><uTrib>{prod['unidade']}</uTrib><qTrib>{qtd:.4f}</qTrib>
              <vUnTrib>{prod['preco']:.2f}</vUnTrib><indTot>1</indTot>
            </prod>
            <imposto>
              <ICMS><ICMS00><orig>0</orig><CST>00</CST><modBC>0</modBC><vBC>{valor_produto:.2f}</vBC><pICMS>18.00</pICMS><vICMS>{valor_icms:.2f}</vICMS></ICMS00></ICMS>
            </imposto>
          </det>"""

    peso_bruto_total = peso_liquido_total * 1.05 
    # bloco para gerar o XML completo da nota fiscal
    xml_content = f"""<?xml version="1.0" encoding="UTF-8"?>
    <nfeProc versao="4.00" xmlns="http://www.portalfiscal.inf.br/nfe">
      <NFe>
        <infNFe Id="NFe3526015959431500015755001000000{i:03d}12345678" versao="4.00">
          <ide>
            <cUF>35</cUF><natOp>Venda de Papeis e Suprimentos</natOp><mod>55</mod><serie>1</serie>
            <nNF>{i}</nNF>
            <dhEmi>{data_emissao.strftime("%Y-%m-%d")}T{data_emissao.strftime("%H:%M:%S")}-03:00</dhEmi>
            <dhSaiEnt>{data_saida.strftime("%Y-%m-%d")}T{data_saida.strftime("%H:%M:%S")}-03:00</dhSaiEnt>
            <tpNF>1</tpNF><idDest>1</idDest><cMunFG>3550308</cMunFG>
            <tpImp>1</tpImp><tpEmis>1</tpEmis>
            <tpAmb>1</tpAmb>
            <finNFe>1</finNFe><indFinal>1</indFinal><indPres>1</indPres>
          </ide>
          <emit>
            <CNPJ>99888777000199</CNPJ><xNome>Dunder Mifflin Paper Company - Scranton Branch</xNome>
            <enderEmit>
              <xLgr>1725 Slough Avenue</xLgr><nro>S/N</nro><xBairro>Scranton Business Park</xBairro>
              <cMun>3550308</cMun><xMun>Sao Paulo</xMun><UF>SP</UF><CEP>01136000</CEP>
              <fone>1140028922</fone>
            </enderEmit>
            <IE>112233445566</IE><CRT>3</CRT>
          </emit>
          <dest>
            <CNPJ>{cliente['cnpj']}</CNPJ><xNome>{cliente['nome']}</xNome>
            <enderDest>
              <xLgr>{cliente['end']}</xLgr><nro>{cliente['num']}</nro><xBairro>Centro</xBairro>
              <cMun>3550308</cMun><xMun>Sao Paulo</xMun><UF>SP</UF><CEP>01311000</CEP>
            </enderDest>
            <IE>ISENTO</IE><indIEDest>9</indIEDest>
          </dest>
          {detalhes_xml}
          <total>
            <ICMSTot>
              <vBC>{valor_total_nf:.2f}</vBC><vICMS>{valor_total_icms:.2f}</vICMS><vICMSDeson>0.00</vICMSDeson>
              <vFCP>0.00</vFCP><vBCST>0.00</vBCST><vST>0.00</vST><vFCPST>0.00</vFCPST>
              <vFCPSTRet>0.00</vFCPSTRet><vProd>{valor_total_nf:.2f}</vProd><vFrete>0.00</vFrete>
              <vSeg>0.00</vSeg><vDesc>0.00</vDesc><vII>0.00</vII><vIPI>0.00</vIPI>
              <vIPIDevol>0.00</vIPIDevol><vPIS>0.00</vPIS><vCOFINS>0.00</vCOFINS><vOutro>0.00</vOutro>
              <vNF>{valor_total_nf:.2f}</vNF><vTotTrib>0.00</vTotTrib>
            </ICMSTot>
          </total>
          <transp>
            <modFrete>0</modFrete>
            <transporta>
              <CNPJ>{transp['cnpj']}</CNPJ><xNome>{transp['nome']}</xNome><IE>{transp['ie']}</IE>
              <xEnder>{transp['end']}</xEnder><xMun>{transp['mun']}</xMun><UF>SP</UF>
            </transporta>
            <veicTransp>
              <placa>{transp['placa']}</placa><UF>SP</UF><RNTC>{transp['rntc']}</RNTC>
            </veicTransp>
            <vol>
              <qVol>{total_volumes}</qVol><esp>VOLUMES</esp><marca>DUNDER M.</marca>
              <pesoL>{peso_liquido_total:.3f}</pesoL><pesoB>{peso_bruto_total:.3f}</pesoB>
            </vol>
          </transp>
          <infAdic>
            <infCpl>Vendedor Responsavel: {vendedor} | Faturamento Automatico Dunder Mifflin 2026.</infCpl>
          </infAdic>
        </infNFe>
      </NFe>
      <protNFe versao="4.00">
        <infProt>
          <tpAmb>1</tpAmb><verAplic>SP_NFE</verAplic>
          <chNFe>3526015959431500015755001000000{i:03d}12345678</chNFe>
          <dhRecbto>{data_emissao.strftime("%Y-%m-%d")}T{data_emissao.strftime("%H:%M:%S")}-03:00</dhRecbto>
          <nProt>135260000000{i:03d}</nProt><digVal>ABC</digVal><cStat>100</cStat>
          <xMotivo>Autorizado o uso da NF-e</xMotivo>
        </infProt>
      </protNFe>
    </nfeProc>"""
    
    # limpa o nome do cliente para não gerar erro no Windows
    nome_cliente_limpo = re.sub(r'[^A-Za-z0-9]', '', cliente['nome'])
    nome_arquivo = f"NF_DunderMifflin_{i:03d}_{nome_cliente_limpo}.pdf"
    # bloco para gerar o PDF do DANFE a partir do XML
    caminho_pdf = os.path.join(pasta_destino, nome_arquivo)
    danfe = Danfe(xml=xml_content, config=config)
    danfe.output(caminho_pdf)

print(f"Todas as notas foram geradas na pasta '{pasta_destino}'!")