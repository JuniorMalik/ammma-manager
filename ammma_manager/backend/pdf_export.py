import os
from fpdf import FPDF
from datetime import timedelta

def clean_text(text):
    if not text:
        return ""
    # Substituir caracteres unicode comuns que não estão no latin-1
    replacements = {
        "\u2013": "-", # en-dash
        "\u2014": "-", # em-dash
        "\u2018": "'", # left single quote
        "\u2019": "'", # right single quote
        "\u201c": '"', # left double quote
        "\u201d": '"', # right double quote
        "\u2022": "-", # bullet point
        "\u20ac": "EUR", # euro symbol
        "\u2026": "...", # ellipsis
        "\u00a0": " ", # non-breaking space
    }
    for k, v in replacements.items():
        text = text.replace(k, v)
    return text.encode("latin-1", "replace").decode("latin-1")

def generate_pdf_budget(order, client, gallery_item, logo_path, upload_path, contacts=None):
    if not contacts:
        contacts = {
            "owner_name": "Mayara Perez",
            "owner_role": "Gerente Comercial",
            "owner_phone": "(11) 9 7355 9491",
            "pix_key": "11973559491"
        }

    # Sanitarizar entradas dinâmicas para evitar FPDFUnicodeEncodingException no fallback Linux/Railway
    client_name = clean_text(order.client_name)
    project_name = clean_text(order.project_name)
    
    material_info = order.notes if order.notes else f"Especificações: {order.weight_g}g"
    if " | Tempo:" in material_info:
        material_info = material_info.split(" | Tempo:")[0]
    elif "Tempo:" in material_info:
        material_info = material_info.split("Tempo:")[0].strip()
    material_info = clean_text(material_info)
    
    client_email = clean_text(client.email) if client and client.email else "-"
    client_phone = clean_text(client.phone) if client and client.phone else "-"
    
    owner_name = clean_text(contacts.get("owner_name", "Mayara Perez"))
    owner_role = clean_text(contacts.get("owner_role", "Gerente Comercial"))
    owner_phone = clean_text(contacts.get("owner_phone", "(11) 9 7355 9491"))
    pix_key = clean_text(contacts.get("pix_key", "11973559491"))

    pdf = FPDF()
    
    # Carregar Fontes Unicode para suportar acentos (Windows)
    font_paths = [
        "C:\\Windows\\Fonts\\arial.ttf",
        os.path.join(os.environ.get('WINDIR', 'C:\\Windows'), 'Fonts', 'arial.ttf'),
        "arial.ttf" # Se estiver na mesma pasta
    ]
    
    FONT_NAME = "helvetica" # Fallback padrão
    for f_path in font_paths:
        if os.path.exists(f_path):
            try:
                base_path = os.path.dirname(f_path)
                pdf.add_font("Arial", "", os.path.join(base_path, "arial.ttf"))
                pdf.add_font("Arial", "B", os.path.join(base_path, "arialbd.ttf"))
                pdf.add_font("Arial", "I", os.path.join(base_path, "ariali.ttf"))
                pdf.set_font("Arial", size=12)
                FONT_NAME = "Arial"
                break
            except:
                continue
        # Fallback caso não encontre (Linux/etc)
        pdf.set_font("helvetica", size=12)
        FONT_NAME = "helvetica"

    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    
    # Cores do Tema
    PRIMARY_BLUE = (56, 189, 248) # #38bdf8
    ACCENT_PINK = (219, 39, 119)  # #db2777
    DARK_BG = (15, 23, 42)        # #0f172a
    TEXT_MAIN = (51, 65, 85)      # #334155
    
    # Cabeçalho Preto
    pdf.set_fill_color(*DARK_BG)
    pdf.rect(0, 0, 210, 50, "F")
    
    # Logo
    logo_file = os.path.join(logo_path, "logo-vazado.png")
    if os.path.exists(logo_file):
        pdf.image(logo_file, 20, 10, 60)
    
    # Título Orçamento (Topo Direito)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font(FONT_NAME, "B", 32)
    pdf.set_xy(100, 10)
    pdf.cell(90, 15, "ORÇAMENTO", ln=True, align="R")
    
    pdf.set_font(FONT_NAME, "", 10)
    pdf.set_x(100)
    ref_id = f"ORD-{order.created_at.year}-{order.id:06d}"
    pdf.cell(90, 6, f"Ref: {ref_id}", ln=True, align="R")
    
    # Traduzir mês
    meses = ["janeiro", "fevereiro", "março", "abril", "maio", "junho", "julho", "agosto", "setembro", "outubro", "novembro", "dezembro"]
    data_formatada = f"{order.created_at.day} de {meses[order.created_at.month-1]} de {order.created_at.year}"
    pdf.set_x(100)
    pdf.cell(90, 6, f"Emissão: {data_formatada}", ln=True, align="R")
    
    # Espaçamento após cabeçalho
    pdf.ln(25)
    
    # Seção DE / PARA
    pdf.set_font(FONT_NAME, "B", 11)
    pdf.set_text_color(*PRIMARY_BLUE)
    pdf.cell(95, 10, "DE: AMMMA 3D", ln=0)
    pdf.cell(95, 10, f"Para: {client_name.upper()}", ln=1, align="R")
    
    pdf.set_draw_color(*PRIMARY_BLUE)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(5)
    
    # Detalhes do Emissor (Esquerda)
    pdf.set_font(FONT_NAME, "", 9)
    pdf.set_text_color(*TEXT_MAIN)
    curr_y = pdf.get_y()
    pdf.set_font(FONT_NAME, "B", 9)
    pdf.cell(95, 5, "AMMMA 3D - Impressões e Modelagens", ln=1)
    pdf.set_font(FONT_NAME, "", 9)
    pdf.cell(95, 5, "São Paulo, SP - Brasil", ln=1)
    pdf.cell(95, 5, "Email: ammma3d@gmail.com", ln=1)
    pdf.cell(95, 5, "Instagram: @ammma3d", ln=1)
    
    # Detalhes do Cliente (Direita)
    pdf.set_xy(105, curr_y)
    pdf.set_font(FONT_NAME, "B", 9)
    pdf.cell(95, 5, f"Nome: {client_name}", ln=1, align="R")
    pdf.set_font(FONT_NAME, "", 9)
    if client:
        pdf.set_x(105)
        pdf.cell(95, 5, f"Email: {client_email}", ln=1, align="R")
        pdf.set_x(105)
        pdf.cell(95, 5, f"Telefone: {client_phone}", ln=1, align="R")
    else:
        pdf.set_x(105)
        pdf.cell(95, 5, "Consumidor Final", ln=1, align="R")
        
    pdf.ln(10)
    
    # Tabela de Itens
    pdf.set_font(FONT_NAME, "B", 10)
    pdf.set_text_color(*PRIMARY_BLUE)
    pdf.cell(110, 10, "DESCRIÇÃO DO SERVIÇO / PRODUTO", ln=0)
    pdf.cell(20, 10, "QTD", ln=0, align="C")
    pdf.cell(30, 10, "UNITÁRIO", ln=0, align="C")
    pdf.cell(30, 10, "SUBTOTAL", ln=1, align="R")
    
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(4)
    
    # Item Único (Baseado no Pedido)
    pdf.set_text_color(*TEXT_MAIN)
    pdf.set_font(FONT_NAME, "B", 11)
    pdf.cell(110, 7, f"{project_name}", ln=0)
    pdf.set_font(FONT_NAME, "", 10)
    pdf.cell(20, 7, "1", ln=0, align="C")
    
    # Preço original ou sugerido
    price_to_show = order.original_price if order.original_price else order.suggested_price
    pdf.cell(30, 7, f"R$ {price_to_show:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."), ln=0, align="C")
    
    pdf.set_font(FONT_NAME, "B", 11)
    pdf.cell(30, 7, f"R$ {price_to_show:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."), ln=1, align="R")
    
    # Detalhes do Material
    pdf.set_font(FONT_NAME, "I", 8)
    pdf.set_text_color(100, 116, 139)
    pdf.multi_cell(110, 5, f"{material_info}")
    
    pdf.ln(10)
    
    # Inserir Foto da Galeria (se selecionada)
    image_y = pdf.get_y()
    has_image = False
    
    if gallery_item and gallery_item.image_path:
        image_name = os.path.basename(gallery_item.image_path)
        abs_image_path = os.path.join(upload_path, image_name)
        if os.path.exists(abs_image_path):
            # Garantir espaço para a imagem
            if pdf.get_y() > 200: 
                pdf.add_page()
                image_y = pdf.get_y()
            pdf.image(abs_image_path, x=10, y=image_y, w=85, h=40)
            has_image = True
                
    # Bloco de Totais (ao lado da imagem)
    if image_y > 240: 
        pdf.add_page()
        image_y = pdf.get_y()
    
    pdf.set_y(image_y)
    pdf.set_fill_color(248, 250, 252)
    pdf.rect(100, image_y, 100, 40, "F")
    
    start_y = image_y + 5
    pdf.set_xy(105, start_y)
    pdf.set_font(FONT_NAME, "", 10)
    pdf.set_text_color(*TEXT_MAIN)
    pdf.cell(60, 8, "Soma dos Itens:")
    pdf.cell(30, 8, f"R$ {price_to_show:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."), align="R", ln=1)
    
    if order.discount_amount and order.discount_amount > 0:
        pdf.set_x(105)
        pdf.set_text_color(*ACCENT_PINK)
        pdf.cell(60, 8, "Desconto:")
        pdf.cell(30, 8, f"-R$ {order.discount_amount:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."), align="R", ln=1)
    
    pdf.set_xy(105, pdf.get_y() + 2)
    pdf.set_draw_color(203, 213, 225)
    pdf.line(105, pdf.get_y(), 195, pdf.get_y())
    pdf.ln(4)
    
    pdf.set_x(105)
    pdf.set_font(FONT_NAME, "B", 14)
    pdf.set_text_color(*ACCENT_PINK)
    pdf.cell(40, 12, "TOTAL:")
    pdf.cell(50, 12, f"R$ {order.suggested_price:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."), align="R", ln=1)
    
    # Ajustar Y para o bloco de condições gerais
    if has_image:
        new_y = image_y + 60
    else:
        new_y = image_y + 45
    pdf.set_y(new_y)
    
    # Condições Gerais
    current_y = pdf.get_y() + 10
    if current_y + 35 > 240:
        pdf.add_page()
        current_y = 20
        
    pdf.set_y(current_y)
    pdf.set_fill_color(248, 250, 252)
    pdf.set_draw_color(*PRIMARY_BLUE)
    pdf.set_line_width(0.5)
    
    pdf.rect(10, current_y, 190, 35, "F")
    pdf.line(10, current_y, 10, current_y + 35) # Borda esquerda azul
    
    pdf.set_xy(13, current_y + 3)
    pdf.set_font(FONT_NAME, "B", 9)
    pdf.set_text_color(*TEXT_MAIN)
    pdf.cell(0, 6, "Condições Gerais:", ln=1)
    
    pdf.set_font(FONT_NAME, "", 8)
    pdf.set_x(13)
    # Trocado '•' por '-' para evitar FPDFUnicodeEncodingException no fallback Linux/Railway
    pdf.multi_cell(180, 5, "- Prazo de entrega estimado: 7 a 10 dias úteis após aprovação.\n- Validade deste orçamento: 7 dias corridos.\n- Forma de Pagamento: 50% para confirmação e 50% na entrega.")
    
    # Rodapé com QR Code
    FOOTER_Y = 245
    pdf.set_y(FOOTER_Y)
    
    # --- ESQUERDA: Logo + Contato ---
    LOGO_X = 12
    LOGO_Y = FOOTER_Y + 5
    LOGO_W = 28
    if os.path.exists(logo_file):
        pdf.image(logo_file, LOGO_X, LOGO_Y, LOGO_W)
    
    TEXT_X = LOGO_X + LOGO_W + 3   # ~43
    TEXT_Y = LOGO_Y + 2
    
    pdf.set_xy(TEXT_X, TEXT_Y)
    pdf.set_font(FONT_NAME, "B", 10)
    pdf.set_text_color(*TEXT_MAIN)
    pdf.cell(60, 5, owner_name, ln=1)
    
    pdf.set_font(FONT_NAME, "B", 8)
    pdf.set_text_color(148, 163, 184)
    pdf.set_x(TEXT_X)
    pdf.cell(60, 4, owner_role, ln=1)
    
    pdf.set_font(FONT_NAME, "", 8)
    pdf.set_x(TEXT_X)
    pdf.cell(60, 4, owner_phone, ln=1)
    
    # --- CENTRO: Tabela PIX ---
    due_date = order.created_at + timedelta(days=7)
    due_date_str = due_date.strftime("%d/%m/%Y")
    valor_fmt = f"R$ {order.suggested_price:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    
    labels_values = [
        ("Referencia:", ref_id),
        ("Pix:", pix_key),
        ("Pagar até:", due_date_str),
        ("Valor:", valor_fmt)
    ]
    
    COL_LABEL_X = 108   # início do label
    COL_VALUE_X = 142   # início do valor
    COL_VALUE_W = 20    # largura da célula de valor
    ROW_H = 5
    TABLE_Y = FOOTER_Y + 4
    
    for i, (label, value) in enumerate(labels_values):
        row_y = TABLE_Y + i * ROW_H
        
        # Label (normal, cor cinza Slate 500)
        pdf.set_xy(COL_LABEL_X, row_y)
        pdf.set_font(FONT_NAME, "", 8)
        pdf.set_text_color(100, 116, 139)
        pdf.cell(COL_VALUE_X - COL_LABEL_X, ROW_H, label, ln=0)
        
        # Valor (normal, cor escura)
        pdf.set_xy(COL_VALUE_X, row_y)
        pdf.set_font(FONT_NAME, "", 8)
        pdf.set_text_color(*TEXT_MAIN)
        pdf.cell(COL_VALUE_W, ROW_H, value, ln=0, align="R")
    
    # --- DIREITA: "Pague com Pix" + QR Code ---
    QR_X = 166
    QR_Y = FOOTER_Y + 8   # QR abaixo do texto
    QR_W = 28
    
    # Texto acima do QR
    pdf.set_xy(QR_X, FOOTER_Y + 2)
    pdf.set_font(FONT_NAME, "B", 7)
    pdf.set_text_color(*TEXT_MAIN)
    pdf.cell(QR_W, 5, "Pague com Pix", align="C")
    
    # Usar QR Code estático fornecido pelo usuário
    qr_file = os.path.join(logo_path, "qrcode_pix.png")
    if os.path.exists(qr_file):
        pdf.image(qr_file, QR_X, QR_Y, QR_W)
    else:
        print(f"Aviso: Imagem QR Code não encontrada em {qr_file}")

    # Gerar bytes do PDF
    pdf_bytes = bytes(pdf.output())

    return pdf_bytes
