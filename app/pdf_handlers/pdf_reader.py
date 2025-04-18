# === FOR TEST REAL HANDLER IN MAIN.APP ===

import pdfplumber
import json

pdf_path = '../pdfs/ТТ.pdf'
output_json_path = 'output.json'

def format_text(words):

    if not words:
        return ""

    lines = []
    current_line = []
    prev_bottom = None

    for word in words:
        if prev_bottom is None:
            current_line.append(word)
            prev_bottom = word['bottom']
        else:
            if word['top'] - prev_bottom > 10:
                line_text = ""
                prev_x1 = None
                for w in current_line:
                    if prev_x1 is not None:
                        if w['x0'] - prev_x1 > 15:
                            line_text += "\t"
                        else:
                            line_text += " "
                    line_text += w['text']
                    prev_x1 = w['x1']
                lines.append(line_text)
                current_line = [word]
            else:
                current_line.append(word)
            prev_bottom = max(prev_bottom, word['bottom'])

    if current_line:
        line_text = ""
        prev_x1 = None
        for w in current_line:
            if prev_x1 is not None:
                if w['x0'] - prev_x1 > 15:
                    line_text += "\t"
                else:
                    line_text += " "
            line_text += w['text']
            prev_x1 = w['x1']
        lines.append(line_text)

    return "\n".join(lines)

result = {}

with pdfplumber.open(pdf_path) as pdf:
    for page_num, page in enumerate(pdf.pages, start=1):
        tables = page.find_tables()
        table_bboxes = [table.bbox for table in tables]
        words = page.extract_words()
        words.sort(key=lambda w: (w['top'], w['x0']))

        page_text_parts = []
        i = 0
        while i < len(words):
            word = words[i]
            in_table = False
            for bbox in table_bboxes:
                x0, top, x1, bottom = bbox
                if (word['x0'] >= x0 and word['x1'] <= x1 and
                    word['top'] >= top and word['bottom'] <= bottom):
                    in_table = True
                    break

            if in_table:
                page_text_parts.append(f"<<TABLE_PAGE_{page_num}>>")
                while i < len(words):
                    w = words[i]
                    wx0, wt, wx1, wb = w['x0'], w['top'], w['x1'], w['bottom']
                    if any(wx0 >= bx[0] and wx1 <= bx[2] and wt >= bx[1] and wb <= bx[3] for bx in table_bboxes):
                        i += 1
                    else:
                        break
            else:
                non_table_words = []
                while i < len(words):
                    w = words[i]
                    wx0, wt, wx1, wb = w['x0'], w['top'], w['x1'], w['bottom']
                    if any(wx0 >= bx[0] and wx1 <= bx[2] and wt >= bx[1] and wb <= bx[3] for bx in table_bboxes):
                        break
                    non_table_words.append(w)
                    i += 1
                formatted_text = format_text(non_table_words)
                page_text_parts.append(formatted_text)

        page_text = "\n\n".join(filter(None, page_text_parts))
        result[f"page_{page_num}"] = page_text

with open(output_json_path, 'w', encoding='utf-8') as f:
    json.dump(result, f, ensure_ascii=False, indent=4)

print(f"Результат сохранён в {output_json_path}")
