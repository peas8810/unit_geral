import os
import uuid
import tempfile
import io
import streamlit as st
# PDF utilities
from PyPDF2 import PdfMerger, PdfReader, PdfWriter
from pdf2docx import Converter
from PIL import Image
import pytesseract
from pdf2image import convert_from_path
import img2pdf
# Plagiarism detection
import requests
import difflib
from fpdf import FPDF
import hashlib
from datetime import datetime
# Citação IA
import random
import pdfplumber
from collections import Counter
import nltk
from nltk.corpus import stopwords
# Total IA
import re
import numpy as np
import pandas as pd
from transformers import RobertaTokenizer, RobertaForSequenceClassification
import torch
# LaTeX generation
import pypandoc
from jinja2 import Environment, FileSystemLoader

# --- CONFIGURAÇÕES GERAIS ---
st.set_page_config(page_title="Portal PEAS.Co", layout="wide")
WORK_DIR = "documentos"
os.makedirs(WORK_DIR, exist_ok=True)
# Ajuste do Tesseract (se necessário)
pytesseract.pytesseract.tesseract_cmd = r'/usr/bin/tesseract'

# Funções de cada módulo (resumidas) ...
# TODO: Copiar aqui as funções pdf_para_word, juntar_pdf, dividir_pdf, jpg_para_pdf
# Configurações iniciais
WORK_DIR = "documentos"
os.makedirs(WORK_DIR, exist_ok=True)

# Verifica e configura o Tesseract OCR (pode precisar de ajuste no seu sistema)
pytesseract.pytesseract.tesseract_cmd = r'/usr/bin/tesseract'

# Função para salvar arquivos enviados
def salvar_arquivos(uploaded_files):
    caminhos = []
    for uploaded_file in uploaded_files:
        # Limpa o nome do arquivo
        nome_base, extensao = os.path.splitext(uploaded_file.name)
        nome_limpo = (nome_base.replace(" ", "_")
                      .replace("ç", "c").replace("ã", "a")
                      .replace("á", "a").replace("é", "e")
                      .replace("í", "i").replace("ó", "o")
                      .replace("ú", "u").replace("ñ", "n")) + extensao.lower()
        
        caminho = os.path.join(WORK_DIR, nome_limpo)
        with open(caminho, "wb") as f:
            f.write(uploaded_file.getbuffer())
        caminhos.append(caminho)
    return caminhos

# Função para limpar arquivos temporários
def limpar_diretorio():
    for filename in os.listdir(WORK_DIR):
        file_path = os.path.join(WORK_DIR, filename)
        try:
            if os.path.isfile(file_path):
                os.unlink(file_path)
        except Exception as e:
            st.error(f"Erro ao limpar arquivo {file_path}: {e}")

# Função para baixar arquivos
def criar_link_download(nome_arquivo, label):
    with open(os.path.join(WORK_DIR, nome_arquivo), "rb") as f:
        st.download_button(
            label=label,
            data=f,
            file_name=nome_arquivo,
            mime="application/octet-stream"
        )

# Funções de conversão
def pdf_para_word():
    st.header("PDF para Word")
    uploaded_file = st.file_uploader(
        "Carregue um arquivo PDF",
        type=["pdf"],
        accept_multiple_files=False
    )
    
    if uploaded_file and st.button("Converter para Word"):
        caminho = salvar_arquivos([uploaded_file])[0]
        nome_base = os.path.splitext(os.path.basename(caminho))[0]
        nome_saida = f"pdf2docx_{nome_base}.docx"
        saida = os.path.join(WORK_DIR, nome_saida)
        
        # Remove arquivo existente se houver
        if os.path.exists(saida):
            os.remove(saida)
        
        try:
            cv = Converter(caminho)
            cv.convert(saida)
            cv.close()
            
            if os.path.exists(saida):
                st.success(f"Arquivo convertido: {nome_saida}")
                criar_link_download(nome_saida, f"Baixar {nome_saida}")
            else:
                st.error(f"Falha na conversão: {caminho}")
        except Exception as e:
            st.error(f"Erro na conversão: {str(e)}")

def juntar_pdf():
    st.header("Juntar PDFs")
    uploaded_files = st.file_uploader(
        "Carregue os PDFs para juntar",
        type=["pdf"],
        accept_multiple_files=True
    )
    
    if len(uploaded_files) >= 2 and st.button("Juntar PDFs"):
        caminhos = salvar_arquivos(uploaded_files)
        nome_saida = "merge_resultado.pdf"
        saida = os.path.join(WORK_DIR, nome_saida)
        
        # Remove arquivo existente se houver
        if os.path.exists(saida):
            os.remove(saida)
        
        try:
            merger = PdfMerger()
            for c in caminhos:
                merger.append(c)
            merger.write(saida)
            merger.close()
            
            if os.path.exists(saida):
                st.success("PDFs unidos com sucesso!")
                criar_link_download(nome_saida, f"Baixar {nome_saida}")
            else:
                st.error("Falha ao unir PDFs.")
        except Exception as e:
            st.error(f"Erro ao unir PDFs: {str(e)}")

def dividir_pdf():
    st.header("Dividir PDF")
    uploaded_file = st.file_uploader(
        "Carregue um PDF para dividir",
        type=["pdf"],
        accept_multiple_files=False
    )
    
    if uploaded_file and st.button("Dividir PDF"):
        caminho = salvar_arquivos([uploaded_file])[0]
        nome_base = os.path.splitext(os.path.basename(caminho))[0]
        
        try:
            reader = PdfReader(caminho)
            for i, page in enumerate(reader.pages):
                writer = PdfWriter()
                writer.add_page(page)
                nome_saida = f"split_{nome_base}_pag{i+1}.pdf"
                out_path = os.path.join(WORK_DIR, nome_saida)
                with open(out_path, "wb") as f:
                    writer.write(f)
                st.success(f"Página gerada: {nome_saida}")
                criar_link_download(nome_saida, f"Baixar {nome_saida}")
        except Exception as e:
            st.error(f"Erro ao dividir PDF: {str(e)}")

def jpg_para_pdf():
    st.header("Imagens para PDF")
    uploaded_files = st.file_uploader(
        "Carregue imagens para converter em PDF",
        type=["jpg", "jpeg", "png"],
        accept_multiple_files=True
    )
    
    if uploaded_files and st.button("Converter para PDF"):
        caminhos = salvar_arquivos(uploaded_files)
        nome_saida = "img2pdf_resultado.pdf"
        caminho_pdf = os.path.join(WORK_DIR, nome_saida)
        
        # Remove arquivo existente se houver
        if os.path.exists(caminho_pdf):
            os.remove(caminho_pdf)
        
        try:
            # Usando img2pdf para melhor qualidade
            with open(caminho_pdf, "wb") as f:
                f.write(img2pdf.convert([Image.open(img).filename for img in caminhos]))
            
            if os.path.exists(caminho_pdf):
                st.success("PDF gerado com sucesso!")
                criar_link_download(nome_saida, f"Baixar {nome_saida}")
            else:
                st.error("Falha ao gerar PDF.")
        except Exception as e:
            st.error(f"Erro ao converter imagens para PDF: {str(e)}")


# Interface principal
def main():
    st.title("📄 Conversor de Documentos")
    st.markdown("""
    Ferramenta para conversão entre diversos formatos de documentos.
    """)
    
    # Menu lateral
    st.sidebar.title("Menu")
    opcao = st.sidebar.selectbox(
        "Selecione a operação",
        [
            "PDF para Word",
            "Juntar PDFs",
            "Dividir PDF",
            "Imagens para PDF",
         ]
    )
    
    # Limpar arquivos temporários
    if st.sidebar.button("Limpar arquivos temporários"):
        limpar_diretorio()
        st.sidebar.success("Arquivos temporários removidos!")
    
    # Rodapé
    st.sidebar.markdown("---")
    st.sidebar.markdown("Desenvolvido por PEAS.Co")
    
    # Executa a função selecionada
    if opcao == "PDF para Word":
        pdf_para_word()
    elif opcao == "Juntar PDFs":
        juntar_pdf()
    elif opcao == "Dividir PDF":
        dividir_pdf()
    elif opcao == "Imagens para PDF":
        jpg_para_pdf()


if __name__ == "__main__":
    main()


# --- Seção de Propaganda ---

# Incorporação de website (exemplo de iframe para propaganda)
st.markdown(
    "<h3><a href='https://peas8810.hotmart.host/product-page-1f2f7f92-949a-49f0-887c-5fa145e7c05d' target='_blank'>"
    "Técnica PROATIVA: Domine a Criação de Comandos Poderosos na IA e gere produtos monetizáveis"
    "</a></h3>",
    unsafe_allow_html=True
)
st.components.v1.iframe("https://pay.hotmart.com/U99934745U?off=y2b5nihy&hotfeature=51&_hi=eyJjaWQiOiIxNzQ4Mjk4OTUxODE2NzQ2NTc3ODk4OTY0NzUyNTAwIiwiYmlkIjoiMTc0ODI5ODk1MTgxNjc0NjU3Nzg5ODk2NDc1MjUwMCIsInNpZCI6ImM4OTRhNDg0MzJlYzRhZTk4MTNjMDJiYWE2MzdlMjQ1In0=.1748375599003&bid=1748375601381", height=250)


# TODO: Funções de PlagIA (salvar_email, verificar_codigo, extrair_texto, calcular_similaridade, buscar_referencias, gerar_relatorio)
# 🔗 URL da API gerada no Google Sheets
URL_GOOGLE_SHEETS = "https://script.google.com/macros/s/AKfycbyTpbWDxWkNRh_ZIlHuAVwZaCC2ODqTmo0Un7ZDbgzrVQBmxlYYKuoYf6yDigAPHZiZ/exec"

# =============================
# 📋 Função para Salvar E-mails e Código de Verificação no Google Sheets
# =============================
def salvar_email_google_sheets(nome, email, codigo_verificacao):
    dados = {
        "nome": nome,
        "email": email,
        "codigo": codigo_verificacao
    }
    try:
        headers = {'Content-Type': 'application/json'}
        response = requests.post(URL_GOOGLE_SHEETS, json=dados, headers=headers)

        if response.text.strip() == "Sucesso":
            st.success("✅ E-mail, nome e código registrados com sucesso!")
        else:
            st.error(f"❌ Erro ao salvar dados no Google Sheets: {response.text}")
    except Exception as e:
        st.error(f"❌ Erro na conexão com o Google Sheets: {e}")

# =============================
# 🔎 Função para Verificar Código de Verificação na Planilha
# =============================
def verificar_codigo_google_sheets(codigo_digitado):
    try:
        response = requests.get(f"{URL_GOOGLE_SHEETS}?codigo={codigo_digitado}")
        if response.text.strip() == "Valido":
            return True
        else:
            return False
    except Exception as e:
        st.error(f"❌ Erro na conexão com o Google Sheets: {e}")
        return False

# =============================
# 🔐 Função para Gerar Código de Verificação
# =============================
def gerar_codigo_verificacao(texto):
    return hashlib.md5(texto.encode()).hexdigest()[:10].upper()

# =============================
# 📝 Função para Extrair Texto do PDF
# =============================
def extrair_texto_pdf(arquivo_pdf):
    leitor_pdf = PyPDF2.PdfReader(arquivo_pdf)
    texto = ""
    for pagina in leitor_pdf.pages:
        texto += pagina.extract_text() or ""
    return texto.strip()

# =============================
# 📊 Função para Calcular Similaridade
# =============================
def calcular_similaridade(texto1, texto2):
    seq_matcher = difflib.SequenceMatcher(None, texto1, texto2)
    return seq_matcher.ratio()

# =============================
# 🔎 Função para Buscar Artigos na API CrossRef
# =============================
def buscar_referencias_crossref(texto):
    query = "+".join(texto.split()[:10])  
    url = f"https://api.crossref.org/works?query={query}&rows=10"

    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Erro ao acessar a API da CrossRef: {e}")
        return []

    referencias = []
    for item in data.get("message", {}).get("items", []):
        titulo = item.get("title", ["Título não disponível"])[0]
        resumo = item.get("abstract", "")
        link = item.get("URL", "Link não disponível")
        referencias.append({"titulo": titulo, "resumo": resumo, "link": link})

    return referencias

# =============================
# 📄 Classe para Gerar Relatório PDF Personalizado
# =============================
class PDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 16)
        self.cell(0, 10, "Relatório de Similaridade de Plágio - PlagIA - PEAS.Co", ln=True, align='C')

    def chapter_title(self, title):
        self.set_font('Arial', 'B', 12)
        self.cell(0, 10, self._encode_text(title), ln=True)
        self.ln(3)

    def chapter_body(self, body):
        self.set_font('Arial', '', 10)
        self.multi_cell(0, 8, self._encode_text(body))
        self.ln()

    # 🔎 Função para corrigir acentuação e caracteres especiais
    def _encode_text(self, text):
        try:
            return text.encode('latin-1', 'replace').decode('latin-1')
        except UnicodeEncodeError:
            return ''.join(char if ord(char) < 128 else '?' for char in text)

def gerar_relatorio_pdf(referencias_com_similaridade, nome, email, codigo_verificacao):
    pdf = PDF()
    pdf.add_page()

    # Adicionando os dados do usuário no PDF
    data_hora = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    pdf.chapter_title("Dados do Solicitante:")
    pdf.chapter_body(f"Nome: {nome}")
    pdf.chapter_body(f"E-mail: {email}")
    pdf.chapter_body(f"Data e Hora: {data_hora}")
    pdf.chapter_body(f"Código de Verificação (Link para inserir o código e conferir: https://iaplagio-wtwg4f3x2ejse4rspbqe2s.streamlit.app/): {codigo_verificacao}")
    
    # Referências encontradas
    pdf.chapter_title("Top Referências encontradas:")
    soma_percentual = 0
    # Considera no máximo 5 referências, mas se houver menos, divide pelo número real
    refs_selecionadas = referencias_com_similaridade[:5]
    num_refs = len(refs_selecionadas)
    if num_refs == 0:
        pdf.chapter_body("Nenhuma referência encontrada.")
    else:
        for i, (ref, perc, link) in enumerate(refs_selecionadas, 1):
            soma_percentual += perc
            pdf.chapter_body(f"{i}. {ref} - {perc*100:.2f}%\n{link}")
        plagio_medio = (soma_percentual / num_refs) * 100
        pdf.chapter_body(f"Plágio médio: {plagio_medio:.2f}%")

    pdf_file_path = "/tmp/relatorio_plagio.pdf"
    pdf.output(pdf_file_path, 'F')
      
    return pdf_file_path

# =============================
# 💻 Interface do Streamlit
# =============================
if __name__ == "__main__":
    st.title("PlagIA - PEAS.Co")
    
    # --- Registro de Usuário ---
    st.subheader("📋 Registro de Usuário - Apenas para validação")
    nome = st.text_input("Nome completo")
    email = st.text_input("E-mail")

    if st.button("Salvar Dados"):
        if nome and email:
            salvar_email_google_sheets(nome, email, "N/A")
        else:
            st.warning("⚠️ Por favor, preencha todos os campos.")

    # --- Upload e Processamento do PDF ---
    arquivo_pdf = st.file_uploader("Faça upload de um arquivo PDF SEM OS NOMES DOS AUTORES E TÍTULO DA REVISTA, PARA GARANTIR AVALIAÇÃO SOMENTE DO TEXTO", type=["pdf"])

    if st.button("Processar PDF"):
        if arquivo_pdf is not None:
            texto_usuario = extrair_texto_pdf(arquivo_pdf)
            referencias = buscar_referencias_crossref(texto_usuario)

            referencias_com_similaridade = []
            for ref in referencias:
                texto_base = ref["titulo"] + " " + ref["resumo"]
                link = ref["link"]
                similaridade = calcular_similaridade(texto_usuario, texto_base)
                referencias_com_similaridade.append((ref["titulo"], similaridade, link))

            referencias_com_similaridade.sort(key=lambda x: x[1], reverse=True)

            if referencias_com_similaridade:
                codigo_verificacao = gerar_codigo_verificacao(texto_usuario)
                salvar_email_google_sheets(nome, email, codigo_verificacao)
                st.success(f"Código de verificação gerado: **{codigo_verificacao}**")

                # Gerar e exibir link para download do relatório
                pdf_file = gerar_relatorio_pdf(referencias_com_similaridade, nome, email, codigo_verificacao)
                with open(pdf_file, "rb") as f:
                    st.download_button("📄 Baixar Relatório de Plágio", f, "relatorio_plagio.pdf")
            else:
                st.warning("Nenhuma referência encontrada.")
        else:
            st.error("Por favor, carregue um arquivo PDF.")

    # --- Texto Justificado ---
    st.markdown(
        """
        <div style="text-align: justify;">
        Powered By - PEAS.Co
        </div>
        """, 
        unsafe_allow_html=True
    )

    # --- Verificação de Código ---
    st.header("Verificar Autenticidade")
    codigo_digitado = st.text_input("Digite o código de verificação:")

    if st.button("Verificar Código"):
        if verificar_codigo_google_sheets(codigo_digitado):
            st.success("✅ Documento Autêntico e Original!")
        else:
            st.error("❌ Código inválido ou documento falsificado.")

    # --- Seção de Propaganda ---

      # Incorporação de website (exemplo de iframe para propaganda)
st.markdown(
    "<h3><a href='https://peas8810.hotmart.host/product-page-1f2f7f92-949a-49f0-887c-5fa145e7c05d' target='_blank'>"
    "Técnica PROATIVA: Domine a Criação de Comandos Poderosos na IA e gere produtos monetizáveis"
    "</a></h3>",
    unsafe_allow_html=True
)
st.components.v1.iframe("https://pay.hotmart.com/U99934745U?off=y2b5nihy&hotfeature=51&_hi=eyJjaWQiOiIxNzQ4Mjk4OTUxODE2NzQ2NTc3ODk4OTY0NzUyNTAwIiwiYmlkIjoiMTc0ODI5ODk1MTgxNjc0NjU3Nzg5ODk2NDc1MjUwMCIsInNpZCI6ImM4OTRhNDg0MzJlYzRhZTk4MTNjMDJiYWE2MzdlMjQ1In0=.1748375599003&bid=1748375601381", height=250)




# TODO: Funções de CitatIA (salvar_email, verificar_codigo, gerar_codigo, get_popular_phrases, extract_top_keywords, get_publication_statistics, evaluate_article_relevance, generate_report)
nltk.download('stopwords')

STOP_WORDS = set(stopwords.words('portuguese'))

# 🔗 URL da API do Google Sheets
URL_GOOGLE_SHEETS = "https://script.google.com/macros/s/AKfycbyHRCrD5-A_JHtaUDXsGWQ22ul9ml5vvK3YYFzIE43jjCdip0dBMFH_Jmd8w971PLte/exec"

# URLs das APIs
SEMANTIC_API = "https://api.semanticscholar.org/graph/v1/paper/search"
CROSSREF_API = "https://api.crossref.org/works"

# =============================
# 📋 Função para Salvar E-mails e Código de Verificação no Google Sheets
# =============================
def salvar_email_google_sheets(nome, email, codigo_verificacao):
    dados = {
        "nome": nome,
        "email": email,
        "codigo": codigo_verificacao
    }
    try:
        headers = {'Content-Type': 'application/json'}
        response = requests.post(URL_GOOGLE_SHEETS, json=dados, headers=headers)
        if response.text.strip() == "Sucesso":
            st.success("✅ E-mail, nome e código registrados com sucesso!")
        else:
            st.error(f"❌ Erro ao salvar dados no Google Sheets: {response.text}")
    except Exception as e:
        st.error(f"❌ Erro na conexão com o Google Sheets: {e}")

# =============================
# 🔎 Função para Verificar Código de Verificação na Planilha
# =============================
def verificar_codigo_google_sheets(codigo_digitado):
    try:
        response = requests.get(f"{URL_GOOGLE_SHEETS}?codigo={codigo_digitado}")
        if response.text.strip() == "Valido":
            return True
        else:
            return False
    except Exception as e:
        st.error(f"❌ Erro na conexão com o Google Sheets: {e}")
        return False

# =============================
# 🔐 Função para Gerar Código de Verificação
# =============================
def gerar_codigo_verificacao(texto):
    return hashlib.md5(texto.encode()).hexdigest()[:10].upper()

# Função para obter artigos mais citados
def get_popular_phrases(query, limit=10):
    suggested_phrases = []

    # Pesquisa na API Semantic Scholar
    semantic_params = {"query": query, "limit": limit, "fields": "title,abstract,url,externalIds,citationCount"}
    semantic_response = requests.get(SEMANTIC_API, params=semantic_params)
    if semantic_response.status_code == 200:
        semantic_data = semantic_response.json().get("data", [])
        for item in semantic_data:
            suggested_phrases.append({
                "phrase": f"{item.get('title', '')}. {item.get('abstract', '')}",
                "doi": item['externalIds'].get('DOI', 'N/A'),
                "link": item.get('url', 'N/A'),
                "citationCount": item.get('citationCount', 0)
            })

    # Pesquisa na API CrossRef
    crossref_params = {"query": query, "rows": limit}
    crossref_response = requests.get(CROSSREF_API, params=crossref_params)
    if crossref_response.status_code == 200:
        crossref_data = crossref_response.json().get("message", {}).get("items", [])
        for item in crossref_data:
            suggested_phrases.append({
                "phrase": f"{item.get('title', [''])[0]}. {item.get('abstract', '')}",
                "doi": item.get('DOI', 'N/A'),
                "link": item.get('URL', 'N/A'),
                "citationCount": item.get('is-referenced-by-count', 0)
            })

    # Ordenar por número de citações
    suggested_phrases.sort(key=lambda x: x.get('citationCount', 0), reverse=True)

    return suggested_phrases

# Função para extrair as 10 palavras mais importantes dos artigos
def extract_top_keywords(suggested_phrases):
    all_text = " ".join([item['phrase'] for item in suggested_phrases])
    words = re.findall(r'\b\w+\b', all_text.lower())
    words = [word for word in words if word not in STOP_WORDS and len(word) > 3]  # Filtra stopwords e palavras curtas
    word_freq = Counter(words).most_common(10)
    return [word for word, freq in word_freq]

# Função para simular estatísticas de publicações mensais
def get_publication_statistics(total_articles):
    start_date = datetime.now() - timedelta(days=365)  # Último ano
    publication_dates = [start_date + timedelta(days=random.randint(0, 365)) for _ in range(total_articles)]
    monthly_counts = Counter([date.strftime("%Y-%m") for date in publication_dates])
    proportion_per_100 = (total_articles / 100) * 100  # Normaliza para 100
    return monthly_counts, proportion_per_100

# Modelo PyTorch para prever chance de ser referência
class ArticlePredictor(nn.Module):
    def __init__(self):
        super(ArticlePredictor, self).__init__()
        self.fc1 = nn.Linear(1, 16)
        self.fc2 = nn.Linear(16, 8)
        self.fc3 = nn.Linear(8, 1)

    def forward(self, x):
        x = torch.relu(self.fc1(x))
        x = torch.relu(self.fc2(x))
        x = torch.sigmoid(self.fc3(x))
        return x

# Avalia a probabilidade do artigo se tornar uma referência
def evaluate_article_relevance(publication_count):
    model = ArticlePredictor()
    data = torch.tensor([[publication_count]], dtype=torch.float32)
    probability = model(data).item() * 100  # Probabilidade em porcentagem

    if probability >= 70:
        descricao = "A probabilidade de este artigo se tornar uma referência é alta. Isso ocorre porque há poucas publicações sobre o tema, o que aumenta as chances de destaque."
    elif 30 <= probability < 70:
        descricao = "A probabilidade de este artigo se tornar uma referência é moderada. O tema tem uma quantidade equilibrada de publicações, o que mantém as chances de destaque em um nível intermediário."
    else:
        descricao = "A probabilidade de este artigo se tornar uma referência é baixa. Há muitas publicações sobre o tema, o que reduz as chances de destaque."

    return round(probability, 2), descricao

# Função para extrair texto de um arquivo PDF
def extract_text_from_pdf(pdf_path):
    text = ""
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text += page.extract_text() or ""
    return text.strip()

# Função para identificar o tema principal do artigo
def identify_theme(user_text):
    words = re.findall(r'\b\w+\b', user_text)
    keywords = [word.lower() for word in words if word.lower() not in STOP_WORDS]
    keyword_freq = Counter(keywords).most_common(10)
    return ", ".join([word for word, freq in keyword_freq])

# Função para gerar relatório detalhado
def generate_report(suggested_phrases, top_keywords, tema, probabilidade, descricao, monthly_counts, proportion_per_100, output_path="report.pdf"):
    doc = SimpleDocTemplate(output_path, pagesize=A4)
    styles = getSampleStyleSheet()

    justified_style = ParagraphStyle(
        'Justified',
        parent=styles['BodyText'],
        alignment=4,  # Alinhamento justificado
        spaceAfter=10,
    )

    content = [
        Paragraph("<b>Relatório de Sugestão de Melhorias no Artigo - CitatIA - PEAS.Co</b>", styles['Title']),
        Paragraph(f"<b>Tema Identificado com base nas principais palavras do artigo:</b> {tema}", justified_style),
        Paragraph(f"<b>Probabilidade do artigo ser uma referência:</b> {probabilidade}%", justified_style),
        Paragraph(f"<b>Explicação:</b> {descricao}", justified_style)
    ]

    content.append(Paragraph("<b>Estatísticas de Publicações:</b>", styles['Heading3']))
    content.append(Paragraph("<b>Publicações de artigos com mesmo tema:</b>", justified_style))
    for month, count in monthly_counts.items():
        content.append(Paragraph(f"• {month}: {count} publicações", justified_style))
    content.append(Paragraph(f"<b>Proporção de publicações a cada 100 artigos:</b> {proportion_per_100:.2f}%", justified_style))

    content.append(Paragraph("<b>Artigos mais acessados, baixados e/ou citados com base no tema:</b>", styles['Heading3']))
    if suggested_phrases:
        for item in suggested_phrases:
            content.append(Paragraph(f"• {item['phrase']}<br/><b>DOI:</b> {item['doi']}<br/><b>Link:</b> {item['link']}<br/><b>Citações:</b> {item.get('citationCount', 'N/A')}", justified_style))

    content.append(Paragraph("<b>Palavras-chave mais citadas nos artigos mais acessados:</b>", styles['Heading3']))
    if top_keywords:
        for word in top_keywords:
            content.append(Paragraph(f"• {word}", justified_style))
    else:
        content.append(Paragraph("Nenhuma palavra-chave relevante encontrada.", justified_style))

    doc.build(content)

# Interface com Streamlit
def main():
    st.title("CitatIA - Potencializador de Artigos - PEAS.Co")
    
    # Registro de usuário
    st.subheader("📋 Registro de Usuário")
    nome = st.text_input("Nome completo")
    email = st.text_input("E-mail")
    if st.button("Salvar Dados"):
        if nome and email:
            codigo_verificacao = gerar_codigo_verificacao(email)
            salvar_email_google_sheets(nome, email, codigo_verificacao)
            st.success(f"Código de verificação gerado: **{codigo_verificacao}**")
        else:
            st.warning("⚠️ Por favor, preencha todos os campos.")

    # Upload do PDF
    uploaded_file = st.file_uploader("Envie o arquivo PDF", type='pdf')
    if uploaded_file:
        with open("uploaded_article.pdf", "wb") as f:
            f.write(uploaded_file.getbuffer())
        st.info("🔍 Analisando o arquivo...")

        user_text = extract_text_from_pdf("uploaded_article.pdf")
        tema = identify_theme(user_text)

        # Buscando artigos e frases populares com base no tema identificado
        suggested_phrases = get_popular_phrases(tema, limit=10)
        # Extrair as 10 palavras mais importantes dos artigos
        top_keywords = extract_top_keywords(suggested_phrases)
        # Calculando a probabilidade com base nas referências encontradas
        publication_count = len(suggested_phrases)
        probabilidade, descricao = evaluate_article_relevance(publication_count)
        # Gerar estatísticas de publicações
        monthly_counts, proportion_per_100 = get_publication_statistics(publication_count)

        st.success(f"✅ Tema identificado: {tema}")
        st.write(f"📈 Probabilidade do artigo ser uma referência: {probabilidade}%")
        st.write(f"ℹ️ {descricao}")
        st.write("<b>Estatísticas de Publicações:</b>", unsafe_allow_html=True)
        for month, count in monthly_counts.items():
            st.write(f"• {month}: {count} publicações")
        st.write(f"<b>Proporção de publicações a cada 100 artigos:</b> {proportion_per_100:.2f}%", unsafe_allow_html=True)
        st.write("<b>Palavras-chave mais citadas:</b>", unsafe_allow_html=True)
        if top_keywords:
            for word in top_keywords:
                st.write(f"• {word}")
        else:
            st.write("Nenhuma palavra-chave relevante encontrada.")

        # Gerar e exibir link para download do relatório
        generate_report(suggested_phrases, top_keywords, tema, probabilidade, descricao, monthly_counts, proportion_per_100)
        with open("report.pdf", "rb") as file:
            st.download_button("📥 Baixar Relatório", file, "report.pdf")

    # Verificação de código
    st.header("Verificar Autenticidade")
    codigo_digitado = st.text_input("Digite o código de verificação:")
    if st.button("Verificar Código"):
        if verificar_codigo_google_sheets(codigo_digitado):
            st.success("✅ Documento Autêntico e Original!")
        else:
            st.error("❌ Código inválido ou documento falsificado.")

    # Texto explicativo ao final da página
    st.markdown("""
    ---
    Powered By - PEAS.Co
    """)


# --- Seção de Propaganda ---
# Incorporação de website (exemplo de iframe para propaganda)
st.markdown(
    "<h3><a href='https://peas8810.hotmart.host/product-page-1f2f7f92-949a-49f0-887c-5fa145e7c05d' target='_blank'>"
    "Técnica PROATIVA: Domine a Criação de Comandos Poderosos na IA e gere produtos monetizáveis"
    "</a></h3>",
    unsafe_allow_html=True
)
st.components.v1.iframe("https://pay.hotmart.com/U99934745U?off=y2b5nihy&hotfeature=51&_hi=eyJjaWQiOiIxNzQ4Mjk4OTUxODE2NzQ2NTc3ODk4OTY0NzUyNTAwIiwiYmlkIjoiMTc0ODI5ODk1MTgxNjc0NjU3Nzg5ODk2NDc1MjUwMCIsInNpZCI6ImM4OTRhNDg0MzJlYzRhZTk4MTNjMDJiYWE2MzdlMjQ1In0=.1748375599003&bid=1748375601381", height=250)


if __name__ == "__main__":
    main()




# TODO: Funções de TotalIA (preprocess_text, analyze_text_roberta, calculate_entropy, analyze_text, extract_text_from_pdf, generate_pdf_report)
# 🔗 URL da API gerada no Google Sheets
URL_GOOGLE_SHEETS = "https://script.google.com/macros/s/AKfycbyTpbWDxWkNRh_ZIlHuAVwZaCC2ODqTmo0Un7ZDbgzrVQBmxlYYKuoYf6yDigAPHZiZ/exec"

# =============================
# 📋 Função para Salvar E-mails no Google Sheets
# =============================
def salvar_email_google_sheets(nome, email, codigo="N/A"):
    dados = {"nome": nome, "email": email, "codigo": codigo}
    try:
        headers = {'Content-Type': 'application/json'}
        response = requests.post(URL_GOOGLE_SHEETS, json=dados, headers=headers)
        if response.text.strip() == "Sucesso":
            st.success("✅ Seus dados foram registrados com sucesso!")
        else:
            st.error(f"❌ Falha ao salvar no Google Sheets: {response.text}")
    except Exception as e:
        st.error(f"❌ Erro na conexão com o Google Sheets: {e}")

# =============================
# 💾 Carregamento do Modelo Roberta (recurso pesado)
# =============================
@st.cache_resource
def load_model():
    tokenizer = RobertaTokenizer.from_pretrained('roberta-base')
    model = RobertaForSequenceClassification.from_pretrained('roberta-base')
    return tokenizer, model

try:
    tokenizer, model = load_model()
except Exception as e:
    st.error(f"Falha ao carregar o modelo Roberta: {e}")
    st.stop()

# =============================
# 🔧 Funções de Análise de Texto
# =============================
@st.cache_data
def preprocess_text(text: str) -> str:
    text = text.lower()
    text = re.sub(r'[^a-zA-Z0-9\s]', '', text)
    return re.sub(r'\s+', ' ', text).strip()

def analyze_text_roberta(text: str) -> float:
    inputs = tokenizer(text, return_tensors="pt", truncation=True, padding=True, max_length=512)
    outputs = model(**inputs)
    prob = torch.softmax(outputs.logits, dim=1)[0, 1].item()
    return prob * 100

def calculate_entropy(text: str) -> float:
    probs = np.array([text.count(c) / len(text) for c in set(text)])
    return -np.sum(probs * np.log2(probs))

def analyze_text(text: str) -> dict:
    clean = preprocess_text(text)
    entropy = calculate_entropy(clean)
    roberta_score = analyze_text_roberta(clean)
    final_score = (roberta_score * 0.7) + (100 * (1 - entropy / 6) * 0.3)
    return {
        'IA (estimada)': f"{final_score:.2f}%",
        'Entropia': f"{entropy:.2f}",
        'Roberta (IA)': f"{roberta_score:.2f}%"
    }

# =============================
# 📄 Funções de PDF (com encoding)
# =============================
def extract_text_from_pdf(pdf_file) -> str:
    text = ""
    with pdfplumber.open(io.BytesIO(pdf_file.read())) as pdf:
        for page in pdf.pages:
            text += page.extract_text() or ""
    return text

class PDFReport(FPDF):
    def _encode(self, txt: str) -> str:
        # substitui en-dash e em-dash por hífen simples
        txt = txt.replace('–', '-').replace('—', '-')
        try:
            return txt.encode('latin-1', 'replace').decode('latin-1')
        except Exception:
            return ''.join(c if ord(c) < 256 else '-' for c in txt)

    def header(self):
        title = self._encode('Relatório TotalIA - PEAS.Co')
        self.set_font('Arial', 'B', 16)
        self.cell(0, 10, title, ln=True, align='C')
        self.ln(5)

    def add_results(self, results: dict):
        self.set_font('Arial', '', 12)
        for k, v in results.items():
            line = f"{k}: {v}"
            self.cell(0, 8, self._encode(line), ln=True)
        self.ln(5)

def generate_pdf_report(results: dict) -> str:
    pdf = PDFReport()
    pdf.add_page()

    # Introdução
    intro = 'Este relatório apresenta uma estimativa sobre a probabilidade de o texto ter sido gerado por IA.'
    pdf.set_font('Arial', '', 12)
    pdf.multi_cell(0, 8, pdf._encode(intro))
    pdf.ln(5)

    # Resultados numéricos
    pdf.add_results(results)

    # Explicação detalhada da Avaliação Roberta
    roberta_value = results['Roberta (IA)']
    pdf.ln(10)
    pdf.set_font('Arial', 'B', 14)
    pdf.cell(0, 10, pdf._encode('O que é a "Avaliação Roberta (Confiabilidade IA)"?'), ln=True)
    pdf.ln(2)

    explanation = (
        f"A 'Avaliação Roberta (Confiabilidade IA)' representa a pontuação gerada pelo modelo RoBerta "
        f"para indicar a probabilidade de que um texto tenha sido escrito por IA. "
        f"No seu relatório, o modelo atribuiu {roberta_value}.\n\n"
        "Como funciona o RoBerta:\n"
        "O RoBerta (Robustly optimized BERT approach) é um modelo de NLP da Meta (Facebook AI), treinado "
        "com grandes volumes de texto para análises semânticas profundas.\n\n"
        "Critérios avaliados:\n"
        " - Coesão textual: IA costuma seguir padrões previsíveis.\n"
        " - Uso de conectores: expressões como 'Portanto', 'Além disso' são frequentes.\n"
        " - Frases genéricas: construção sofisticada, porém superficial.\n"
        " - Padrões linguísticos: falta de nuances humanas (ironias, ambiguidade).\n\n"
        
        " - Interpretação do valor - Entropia:\n"
        "0% - 3%    Alta probabilidade de IA (muito provável que o texto seja gerado por um modelo de linguagem como GPT, Bard, etc.)\n"
        "3% - 6%    Baixa probabilidade de IA (provavelmente texto humano)\n"
        
        " - Interpretação do valor - Roberta:\n"
        "0% - 30%    Baixa probabilidade de IA (provavelmente texto humano)\n"
        "30% - 60%   Área de incerteza (o texto pode conter partes geradas por IA ou apenas seguir um padrão formal)\n"
        "60% - 100%  Alta probabilidade de IA (muito provável que o texto seja gerado por um modelo de linguagem como GPT, Bard, etc.)"
    )
    pdf.set_font('Arial', '', 12)
    pdf.multi_cell(0, 8, pdf._encode(explanation))

    filename = "relatorio_IA.pdf"
    pdf.output(filename, 'F')
    return filename


# =============================
# 🖥️ Interface Streamlit
# =============================
st.title("🔍 TotalIA - Detecção de Texto Escrito por IA - PEAS.Co")
st.write("Faça o upload de um PDF para análise:")

uploaded = st.file_uploader("Escolha um arquivo PDF", type="pdf")
if uploaded:
    texto = extract_text_from_pdf(uploaded)
    resultados = analyze_text(texto)

    st.subheader("🔎 Resultados da Análise")
    for key, val in resultados.items():
        st.write(f"**{key}:** {val}")

    report_path = generate_pdf_report(resultados)
    with open(report_path, "rb") as f:
        st.download_button(
            "📥 Baixar Relatório em PDF",
            f.read(),
            "relatorio_IA.pdf",
            "application/pdf"
        )

# =============================
# 📋 Registro de Usuário (ao final)
# =============================
st.markdown("---")
st.subheader("📋 Registro de Usuário - Cadastre-se")
nome = st.text_input("Nome completo", key="nome")
email = st.text_input("E-mail", key="email")
if st.button("Registrar meus dados"):
    if nome and email:
        salvar_email_google_sheets(nome, email)
    else:
        st.warning("⚠️ Preencha ambos os campos antes de registrar.")

# --- Seção de Propaganda ---

  # Incorporação de website (exemplo de iframe para propaganda)
st.markdown(
    "<h3><a href='https://peas8810.hotmart.host/product-page-1f2f7f92-949a-49f0-887c-5fa145e7c05d' target='_blank'>"
    "Técnica PROATIVA: Domine a Criação de Comandos Poderosos na IA e gere produtos monetizáveis"
    "</a></h3>",
    unsafe_allow_html=True
)
st.components.v1.iframe("https://pay.hotmart.com/U99934745U?off=y2b5nihy&hotfeature=51&_hi=eyJjaWQiOiIxNzQ4Mjk4OTUxODE2NzQ2NTc3ODk4OTY0NzUyNTAwIiwiYmlkIjoiMTc0ODI5ODk1MTgxNjc0NjU3Nzg5ODk2NDc1MjUwMCIsInNpZCI6ImM4OTRhNDg0MzJlYzRhZTk4MTNjMDJiYWE2MzdlMjQ1In0=.1748375599003&bid=1748375601381", height=250)



# TODO: Funções de LaTeX (salvar_contato, carregar_templates, gerar_tex)
# 🔗 URL da API gerada no Google Sheets
URL_GOOGLE_SHEETS = "https://script.google.com/macros/s/AKfycbyTpbWDxWkNRh_ZIlHuAVwZaCC2ODqTmo0Un7ZDbgzrVQBmxlYYKuoYf6yDigAPHZiZ/exec"

# =============================
# 📋 Função para Salvar Nome e E-mail no Google Sheets
# =============================
def salvar_contato_google_sheets(nome, email):
    dados = {
        "nome": nome,
        "email": email
    }
    try:
        headers = {'Content-Type': 'application/json'}
        response = requests.post(URL_GOOGLE_SHEETS, json=dados, headers=headers)
        if response.text.strip() == "Sucesso":
            st.success("✅ Dados registrados com sucesso!")
        else:
            st.error(f"❌ Erro ao salvar no Google Sheets: {response.text}")
    except Exception as e:
        st.error(f"❌ Erro na conexão com Google Sheets: {e}")

# Configuração de diretórios
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")

# Garante que Pandoc esteja disponível
try:
    pypandoc.get_pandoc_version()
except (OSError, RuntimeError):
    pypandoc.download_pandoc()

# Inicializa Jinja2
env = Environment(loader=FileSystemLoader(TEMPLATES_DIR), autoescape=False)

# Título da aplicação
st.title("Gerador de Artigo no Padrão LaTex - PEAS.Co")

# --- Coleta de Nome e E-mail no Cabeçalho ---
st.subheader("Registre seu nome e e-mail")
nome_coleta = st.text_input("Nome:")
email_coleta = st.text_input("E-mail:")
if st.button("Enviar Dados"):
    salvar_contato_google_sheets(nome_coleta, email_coleta)

# Seleção de template
article_type = st.selectbox(
    "Tipo de Artigo:",
    ["Estudo de Caso", "Revisão Bibliográfica"]
)
template_file = (
    "estudo_caso.tex.j2" if article_type == "Estudo de Caso"
    else "revisao_bibliografica.tex.j2"
)
tpl = env.get_template(template_file)

# Modo de edição manual
manual_mode = st.checkbox("Edição Manual")

if manual_mode:
    # Campos de edição manual
    titulo_pt = st.text_input("Título em Português")
    titulo_en = st.text_input("Título em Inglês")
    autores_input = st.text_input("Autores (separar por vírgula)")
    autores = [a.strip() for a in autores_input.split(",") if a.strip()]
    email_input = st.text_input("E-mails (separar por vírgula)")
    emails = [e.strip() for e in email_input.split(",") if e.strip()]
    recebido = st.text_input("Data Recebido (dd/mm/aaaa)")
    aceito = st.text_input("Data Aceito (dd/mm/aaaa)")
    abstract_pt = st.text_area("Resumo (PT)")
    keywords_pt_input = st.text_input("Palavras-chave PT (ponto e vírgula)")
    keywords_pt = [k.strip() for k in keywords_pt_input.split(";") if k.strip()]
    abstract_en = st.text_area("Abstract (EN)")
    keywords_en_input = st.text_input("Keywords EN (ponto e vírgula)")
    keywords_en = [k.strip() for k in keywords_en_input.split(";") if k.strip()]

    num_sec = st.number_input(
        "Número de seções", min_value=1, max_value=20, value=1
    )
    sections = []
    for i in range(int(num_sec)):
        sec_title = st.text_input(f"Título da Seção {i+1}", key=f"sec_title_{i}")
        sec_content = st.text_area(f"Conteúdo da Seção {i+1}", key=f"sec_content_{i}")
        sections.append({"secao": sec_title, "conteudo": sec_content})

    biblio_input = st.text_area("Bibliografia (uma referência por linha)")
    bibliografia = []
    for idx, line in enumerate(biblio_input.splitlines()):
        if line.strip():
            bibliografia.append({"citekey": f"ref{idx+1}", "texto": line.strip()})

    if st.button("Gerar LaTeX"):
        context = {
            "titulo_pt": titulo_pt,
            "titulo_en": titulo_en,
            "autores": autores,
            "email": emails,
            "data_info": [recebido, aceito],
            "abstract_pt": abstract_pt,
            "keywords_pt": keywords_pt,
            "abstract_en": abstract_en,
            "keywords_en": keywords_en,
            "sections": sections,
            "bibliografia": bibliografia
        }
        final_tex = tpl.render(**context)
        st.subheader("Código LaTeX gerado")
        st.code(final_tex, language="latex")
        st.download_button(
            "Baixar .tex", final_tex,
            file_name="manual.tex", mime="text/x-tex"
        )
else:
    # Upload e conversão automática
    uploaded_file = st.file_uploader(
        "Envie seu arquivo (DOCX ou PDF)", type=["docx", "pdf"]
    )
    if uploaded_file:
        with tempfile.NamedTemporaryFile(
            delete=False, suffix=os.path.splitext(uploaded_file.name)[1]
        ) as tmp:
            tmp.write(uploaded_file.getbuffer())
            tmp_path = tmp.name
        ext = os.path.splitext(tmp_path)[1][1:]
        try:
            body = pypandoc.convert_file(tmp_path, 'latex', format=ext)
        except Exception as e:
            st.error(f"Erro na conversão: {e}")
            body = ""

        title = os.path.splitext(uploaded_file.name)[0]
        context = {
            "titulo_pt": title,
            "titulo_en": "",
            "autores": [],
            "email": [],
            "data_info": ["", ""],
            "abstract_pt": "",
            "keywords_pt": [],
            "abstract_en": "",
            "keywords_en": [],
            "sections": [{"secao": "Conteúdo", "conteudo": body}],
            "bibliografia": []
        }
        final_tex = tpl.render(**context)
        st.subheader("Código LaTeX gerado")
        st.code(final_tex, language="latex")
        st.download_button(
            "Baixar .tex", final_tex,
            file_name=f"{title}.tex", mime="text/x-tex"
        )

# --- Seção de Propaganda ---

# Incorporação de website (exemplo de iframe para propaganda)
st.markdown(
    "<h3><a href='https://peas8810.hotmart.host/product-page-1f2f7f92-949a-49f0-887c-5fa145e7c05d' target='_blank'>"
    "Técnica PROATIVA: Domine a Criação de Comandos Poderosos na IA e gere produtos monetizáveis"
    "</a></h3>",
    unsafe_allow_html=True
)
st.components.v1.iframe("https://pay.hotmart.com/U99934745U?off=y2b5nihy&hotfeature=51&_hi=eyJjaWQiOiIxNzQ4Mjk4OTUxODE2NzQ2NTc3ODk4OTY0NzUyNTAwIiwiYmlkIjoiMTc0ODI5ODk1MTgxNjc0NjU3Nzg5ODk2NDc1MjUwMCIsInNpZCI6ImM4OTRhNDg0MzJlYzRhZTk4MTNjMDJiYWE2MzdlMjQ1In0=.1748375599003&bid=1748375601381", height=250)



# Interface unificada
def main():
    st.title("🔗 Portal de Ferramentas PEAS.Co")
    menu = st.sidebar.radio("Selecione o programa:", [
        "📄 Conversor de Documentos",
        "🕵️‍♂️ PlagIA - Detecção de Plágio",
        "✍️ CitatIA - Sugestão de Citações",
        "🤖 TotalIA - Análise de Texto IA",
        "📝 Gerador LaTeX"
    ])

    if menu == "📄 Conversor de Documentos":
        st.header("📄 Conversor de Documentos")
        # Chama funções de conversão PDF
        # pdf_para_word()
        # juntar_pdf()
        # dividir_pdf()
        # jpg_para_pdf()

    elif menu == "🕵️‍♂️ PlagIA - Detecção de Plágio":
        st.header("🕵️‍♂️ PlagIA - Detecção de Plágio")
        # Implementar interface de PlagIA

    elif menu == "✍️ CitatIA - Sugestão de Citações":
        st.header("✍️ CitatIA - Sugestão de Citações")
        # Implementar interface de CitatIA

    elif menu == "🤖 TotalIA - Análise de Texto IA":
        st.header("🤖 TotalIA - Análise de Texto IA")
        # Implementar interface de TotalIA

    elif menu == "📝 Gerador LaTeX":
        st.header("📝 Gerador de Artigos em LaTeX")
        # Implementar interface de LaTeX

if __name__ == "__main__":
    main()
