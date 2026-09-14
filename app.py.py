import os
import re
import textwrap
import streamlit as st
from datetime import datetime
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from num2words import num2words

# Configuração da página do aplicativo web
st.set_page_config(
    page_title="Gerador de Alvarás - Tropa do Adv",
    page_icon="⚖️",
    layout="wide"
)

# Estilização visual com CSS personalizado (tema escuro padrão)
st.markdown("""
    <style>
    .stApp { background-color: #0e1117; color: #ffffff; }
    .titulo { text-align: center; font-size: 2.2rem; font-weight: bold; color: #ffffff; margin-bottom: 0px; }
    .subtitulo { text-align: center; color: #8a99ad; margin-bottom: 30px; }
    .bloco-dados { background-color: #161b22; padding: 20px; border-radius: 10px; margin-bottom: 20px; border: 1px solid #30363d; }
    </style>
""", unsafe_allow_html=True)

st.markdown('<p class="titulo">⚖️ Sistema de Alvarás - Tropa do Adv</p>', unsafe_allow_html=True)
st.markdown('<p class="subtitulo">Cole o texto do alvará abaixo para extrair os dados e gerar o PDF automaticamente</p>', unsafe_allow_html=True)

# Define o caminho base do projeto
PASTA_PROJETO = os.path.dirname(os.path.abspath(__file__))

def obter_data_extenso():
    meses = {1: "janeiro", 2: "fevereiro", 3: "março", 4: "abril", 5: "maio", 6: "junho", 
             7: "julho", 8: "agosto", 9: "setembro", 10: "outubro", 11: "novembro", 12: "dezembro"}
    hoje = datetime.now()
    return f"{hoje.day} de {meses[hoje.month]} de {hoje.year}"

def formatar_cpf_cnpj(valor):
    numeros = re.sub(r'\D', '', valor)
    if len(numeros) == 11:
        return f"{numeros[:3]}.{numeros[3:6]}.{numeros[6:9]}-{numeros[9:]}"
    elif len(numeros) == 14:
        return f"{numeros[:2]}.{numeros[2:5]}.{numeros[5:8]}/{numeros[8:12]}-{numeros[12:]}"
    return "000.000.000-00" if numeros == "" else valor

def gerar_pdf_bytes(dados):
    """Gera o PDF diretamente na memória RAM e retorna os bytes para download."""
    buffer = io_bytes = open_pdf_buffer()
    return io_bytes

def open_pdf_buffer():
    import io
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    largura, altura = A4
    
    template_path = os.path.join(PASTA_PROJETO, 'template.png')
    if os.path.exists(template_path):
        c.drawImage(template_path, 0, 0, width=largura, height=altura)

    c.setFillColorRGB(0, 0, 0)
    c.setFont("Helvetica-Bold", 10)
    c.drawString(440, altura - 153, f"{dados_globais['processo']}")
    
    x_margem = 105
    y_base = altura - 316 
    
    campos = [
        ("Credor: ", dados_globais['nome']),
        ("CPF/CNPJ: ", dados_globais['cpf']),
        ("Processo N°: ", dados_globais['processo']),
        ("Assunto: ", dados_globais['assunto']),
        ("Contra: ", dados_globais['contra'])
    ]

    for label, valor in campos:
        c.setFont("Helvetica-Bold", 11)
        c.drawString(x_margem, y_base, label)
        c.setFont("Helvetica", 11)
        c.drawString(x_margem + (c.stringWidth(label, "Helvetica-Bold", 11) + 2), y_base, str(valor))
        y_base -= 18

    y_valor = altura - 540
    c.setFont("Helvetica-Bold", 11)
    label_v = f"Valor a receber: R$ {dados_globais['valor_str']} "
    c.drawString(x_margem, y_valor, label_v)
    
    largura_l = c.stringWidth(label_v, "Helvetica-Bold", 11)
    c.setFont("Helvetica", 11)
    extenso_p = f"({dados_globais['extenso']})"
    
    linhas = textwrap.wrap(extenso_p, width=55) 
    for i, linha in enumerate(linhas):
        pos_y = y_valor if i == 0 else y_valor - (i * 14)
        pos_x = x_margem + largura_l if i == 0 else x_margem
        c.drawString(pos_x, pos_y, linha)

    c.setFont("Helvetica-Bold", 11)
    c.drawCentredString(largura/2, altura - 675, dados_globais['advogado'])
    c.drawCentredString(largura/2, altura - 695, f"{obter_data_extenso()}.")
    
    c.save()
    buffer.seek(0)
    return buffer

# Variável global temporária para uso na função do canvas do ReportLab
dados_globais = {}

# Caixa de texto na interface web para colar o alvará
texto_raw = st.text_area(
    "📄 Cole o texto do alvará abaixo:",
    placeholder="Cole aqui o conteúdo copiado do WhatsApp ou do documento...",
    height=250
)

if st.button("🚀 Processar e Gerar Alvará", type="primary"):
    if not texto_raw.strip():
        st.warning("⚠️ Por favor, cole o texto do alvará na caixa acima.")
    else:
        texto_raw = texto_raw.replace("\\", "/")

        try:
            # Extrações via Expressões Regulares (mesma lógica do script original)
            cpf_match = re.search(r"(?:CPF[:\s]*)?(\d{3}\.?\d{3}\.?\d{3}-?\d{2})", texto_raw, re.I)
            cpf_raw = cpf_match.group(1) if cpf_match else "000.000.000-00"

            nome_match = re.search(r"(?:Sra\.|Sr\.|NOME[:\s]*)\s*\*?([^*,\n]+)\*?", texto_raw, re.I)
            nome = nome_match.group(1).strip().replace('*', '') if nome_match else "Não Encontrado"

            proc_match = re.search(r"(\d{7}-\d{2}\.\d{4}\.\d\.\d{2}\.\d{4})", texto_raw)
            proc = proc_match.group(1) if proc_match else "Não Encontrado"

            assunto_match = re.search(r"(?:Assunto|•)\*?:\s*\*?([^*,\n]+)\*?", texto_raw, re.I)
            assunto = assunto_match.group(1).strip().replace('*', '') if assunto_match else "Não Encontrado"

            contra_match = re.search(r"(?:contrária|Reqda|Reqdo|Contra)\*?:\s*\*?([^*,\n]+)\*?", texto_raw, re.I)
            contra = contra_match.group(1).strip().replace('*', '') if contra_match else "Não Encontrado"

            valor_match = re.search(r"liberação\s+do\s+valor\s+de\s+\*?R\$\s*([\d.,]+)\*?", texto_raw, re.I)
            if valor_match:
                valor_str = valor_match.group(1).strip()
            else:
                partes = re.split(r"Prezado\s+Sr\(a\)\.", texto_raw, flags=re.I)
                texto_corpo = partes[1] if len(partes) > 1 else texto_raw
                vm = re.search(r"R\$\s*([\d.,]+)", texto_corpo)
                valor_str = vm.group(1).strip() if vm else "0,00"

            adv_match = re.search(r"(?:Atenciosamente,)\s*(?:[\r\n\s]*)(Dr[a]?\.\s*\*?[^*,\n]+\*?)|(Dr[a]?\.\s*\*?[^*,\n]+\*?)", texto_raw, re.I)
            advogado = "Não Encontrado"
            if adv_match:
                bruto = (adv_match.group(1) or adv_match.group(2)).strip().replace('*', '')
                advogado = bruto
            else:
                linhas_texto = texto_raw.splitlines()
                for linha in linhas_texto:
                    if "Dr." in linha or "Dra." in linha:
                        advogado = linha.replace('*', '').strip()
                        break

            num_limpo = valor_str.replace('.', '').replace(',', '.')
            try:
                extenso = num2words(float(num_limpo), lang='pt_BR', to='currency').title()
            except:
                extenso = "Zero Reais"

            # Preenche os dados globais para a montagem do PDF
            dados_globais = {
                'nome': nome, 
                'processo': proc, 
                'contra': contra, 
                'assunto': assunto, 
                'valor_str': valor_str,
                'extenso': extenso, 
                'advogado': advogado, 
                'cpf': formatar_cpf_cnpj(cpf_raw),
            }

            st.success("✅ Dados extraídos e mapeados com sucesso!")
            st.markdown("---")

            # Exibe os dados extraídos de forma limpa na tela
            st.markdown("### 📋 Dados Mapeados:")
            st.markdown('<div class="bloco-dados">', unsafe_allow_html=True)
            col1, col2 = st.columns(2)
            with col1:
                st.write(f"**Credor:** {nome}")
                st.write(f"**CPF/CNPJ:** {dados_globais['cpf']}")
                st.write(f"**Processo:** {proc}")
                st.write(f"**Assunto:** {assunto}")
            with col2:
                st.write(f"**Contra:** {contra}")
                st.write(f"**Valor:** R$ {valor_str}")
                st.write(f"**Advogado:** {advogado}")
            st.markdown('</div>', unsafe_allow_html=True)

            # Gera o PDF em memória e cria o botão de Download direto na interface
            pdf_buffer = open_pdf_buffer()
            nome_limpo_arquivo = re.sub(r'[\\/*?:"<>|]', "", nome)
            
            st.download_button(
                label="📥 Baixar Alvará em PDF",
                data=pdf_buffer,
                file_name=f"ALVARA_{nome_limpo_arquivo}.pdf",
                mime="application/pdf",
                type="primary"
            )

        except Exception as e:
            st.error(f"❌ Ocorreu um erro durante o processamento do texto: {e}")