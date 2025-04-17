import camelot

# tables = camelot.read_pdf('../pdfs/foo.pdf')
# tables[0].to_json('foo.json')


tables = camelot.read_pdf('../pdfs/ТТ.pdf', pages='1', flavor='lattice')  # или flavor='stream'

for i, table in enumerate(tables):
    table.to_json('TT_lattice.json')
    print(table.parsing_report)
    print(f"Таблица {i + 1}: {table._bbox} ")

    
    # if len(tables) > 0:
    #     bbox = tables[0]._bbox
    #     print(f"Координаты таблицы (x1, y1, x2, y2): {bbox}")
    #     tables[0].to_html('bbox.html')
