import pdfplumber
import camelot
import io
from typing import Optional
from collections import OrderedDict


def process_pdf_to_html(pdf_content: bytes, output_html_path: Optional[str] = None) -> str:
    """Конвертирует PDF из бинарных данных в HTML"""

    # HTML шаблон
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>PDF Conversion</title>
        <style>
            body { font-family: Arial, sans-serif; line-height: 1.5; }
            table { border-collapse: collapse; margin: 20px 0; }
            th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
            th { background-color: #f2f2f2; }
            .page { page-break-after: always; margin-bottom: 50px; }
            .page-number { font-weight: bold; margin-top: 20px; }
        </style>
    </head>
    <body>
    """

    # Создаем файлоподобный объект из бинарных данных
    pdf_file = io.BytesIO(pdf_content)

    try:
        with pdfplumber.open(pdf_file) as pdf:
            for page_num, page in enumerate(pdf.pages, start=1):
                html_content += f'<div class="page" id="page-{page_num}">'
                html_content += f'<div class="page-number">Page {page_num}</div>'

                # Обработка таблиц с помощью Camelot
                tables = camelot.read_pdf(pdf_file, pages=str(page_num), flavor='lattice')
                for table in tables:
                    html_content += table_to_html(table)

                # Обработка текста
                words = page.extract_words()
                if words:
                    formatted_text = format_text(words)
                    html_content += f'<div class="text">{formatted_text}</div>'

                html_content += '</div>'

    except Exception as e:
        raise ValueError(f"PDF processing error: {str(e)}")

    html_content += """
    </body>
    </html>
    """

    # Сохранение в файл (если нужно)
    if output_html_path:
        with open(output_html_path, 'w', encoding='utf-8') as f:
            f.write(html_content)

    return html_content


def table_to_html(table):
    """Конвертирует таблицу camelot в HTML"""
    html = '<table>'
    for row in table.data:
        html += '<tr>'
        for cell in row:
            html += f'<td>{cell}</td>'
        html += '</tr>'
    html += '</table>'
    return html


def format_text(words):
    """Форматирует список слов в читаемый текст"""
    words = sorted(words, key=lambda w: (w['top'], w['x0']))

    lines = []
    current_line = []
    current_top = None

    for word in words:
        if current_top is None or abs(word['top'] - current_top) < 5:
            current_line.append(word)
            current_top = word['top']
        else:
            lines.append(format_line(current_line))
            current_line = [word]
            current_top = word['top']

    if current_line:
        lines.append(format_line(current_line))

    return "<br>".join(lines)


def format_line(words):
    """Форматирует строку текста"""
    line_text = ""
    prev_x1 = None

    for word in sorted(words, key=lambda w: w['x0']):
        if prev_x1 and word['x0'] - prev_x1 > 10:
            line_text += "    "
        elif prev_x1:
            line_text += " "
        line_text += word['text']
        prev_x1 = word['x1']

    return line_text