import camelot

# tables = camelot.read_pdf('../pdfs/foo.pdf')
# tables[0].to_json('foo.json')


tables = camelot.read_pdf('../pdfs/foo.pdf', pages='1', flavor='lattice')  # или flavor='stream'

if len(tables) > 0:
    # Получение координат первой найденной таблицы
    bbox = tables[0]._bbox
    print(f"Координаты таблицы (x1, y1, x2, y2): {bbox}")
    tables[0].to_json('bbox.json')

else:
    print("net")