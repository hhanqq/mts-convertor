import camelot

tables = camelot.read_pdf('../pdfs/foo.pdf')
print(tables[0].df)