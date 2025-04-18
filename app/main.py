from io import BytesIO

import camelot
import pdfplumber
from fastapi import FastAPI, Depends, HTTPException, status, UploadFile, File
from fastapi.security import OAuth2PasswordRequestForm
from typing import Annotated
from datetime import timedelta, datetime
import uvicorn
from sqlalchemy.orm import Session

import logging

from fastapi.responses import StreamingResponse, HTMLResponse

from app.models.pdf import PDFFile
from app.models.user import User
from app.database import Base, engine, get_db
from app.schemas.pdf_resp import PDFResponse
from app.schemas.user import UserCreate, UserOut
from app.schemas.token import Token
# from app.pdf_handlers.pdf_reader_camelot_plumber import process_pdf_to_html
from app.authorization.auth_user import (
    authenticate_user,
    create_access_token,
    ACCESS_TOKEN_EXPIRE_MINUTES,
    get_password_hash,
    get_current_active_user
)


app = FastAPI()

Base.metadata.create_all(bind=engine)


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)



@app.post("/register", response_model=UserOut)
async def register(
    user_data: UserCreate,
    db: Session = Depends(get_db)
):
    db_user = db.query(User).filter(User.email == user_data.email).first()
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email уже зарегестрирован"
        )

    if user_data.tg_id:
        db_user_tg = db.query(User).filter(User.tg_id == user_data.tg_id).first()
        if db_user_tg:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Telegram ID уже зарегестрирован"
            )

    hashed_password = get_password_hash(user_data.password)
    db_user = User(
        email=user_data.email,
        first_name=user_data.first_name,
        last_name=user_data.last_name,
        surname=user_data.surname,
        hashed_password=hashed_password,
        tg_id=user_data.tg_id,
        disabled=user_data.disabled
    )

    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@app.post("/login", response_model=Token)
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Session = Depends(get_db)
) -> Token:
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"email": user.email},
        expires_delta=access_token_expires
    )
    return Token(access_token=access_token, token_type="bearer")

@app.get("/users/me", response_model=UserOut)
async def read_users_me(
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    return current_user


@app.get("/users/", response_model=list[UserOut])
async def get_users(
        db: Session = Depends(get_db)
):
    users = db.query(User).all()
    return users


@app.post("/upload-pdf/", response_model=PDFResponse)
async def upload_pdf(file: UploadFile = File(...), db: Session = Depends(get_db)):
    # Проверка типа файла
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")

    try:
        # Чтение файла
        contents = await file.read()
        file_size = len(contents)

        # Подготовка данных для сохранения
        db_pdf = PDFFile(
            filename=file.filename,
            content=contents,
            upload_date=datetime.now().isoformat(),
            file_size=file_size
        )

        # Сохранение в базу
        db.add(db_pdf)
        db.commit()
        db.refresh(db_pdf)

        # Формирование ответа
        response_data = {
            "id": db_pdf.id,
            "filename": db_pdf.filename,
            "upload_date": db_pdf.upload_date,
            "file_size": db_pdf.file_size
        }

        return response_data
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error saving PDF: {str(e)}")



@app.get("/pdf-info/{pdf_id}", response_model=PDFResponse)
async def get_pdf_info(pdf_id: int, db: Session = Depends(get_db)):
    pdf_file = db.query(PDFFile).get(pdf_id)
    if not pdf_file:
        raise HTTPException(status_code=404, detail="PDF не найден")
    return StreamingResponse(
        BytesIO(pdf_file.content),
        media_type="application/pdf",
        headers={"Content-Disposition": f"inline; filename={pdf_file.filename}"}
    )


@app.get("/pdf/redactor/{pdf_str}", response_class=HTMLResponse)
async def get_pdf_for_redactor(pdf_str: str, db: Session = Depends(get_db)):
    try:
        pdf_record = db.query(PDFFile).filter(PDFFile.filename == pdf_str).first()
        if not pdf_record:
            raise HTTPException(status_code=404, detail="PDF not found")
        if not pdf_record.content:
            raise HTTPException(status_code=404, detail="PDF content is empty")

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
                .text-content { margin: 10px 0; }
            </style>
        </head>
        <body>
        """

        pdf_file = BytesIO(pdf_record.content)

        with pdfplumber.open(pdf_file) as pdf:
            for page_num, page in enumerate(pdf.pages, start=1):
                html_content += f'<div class="page" id="page-{page_num}">'
                html_content += f'<div class="page-number">Page {page_num}</div>'

                page_width = page.width
                page_height = page.height

                tables = camelot.read_pdf(pdf_file, pages=str(page_num), flavor='lattice')

                table_bboxes = []
                for table in tables:
                    x1, y1, x2, y2 = table._bbox
                    bbox = (x1, page_height - y2, x2, page_height - y1)
                    table_bboxes.append(bbox)

                    html_content += '<table>'
                    for row in table.data:
                        html_content += '<tr>'
                        for cell in row:
                            html_content += f'<td>{cell}</td>'
                        html_content += '</tr>'
                    html_content += '</table>'

                words = page.extract_words()
                if words:
                    filtered_words = []
                    for word in words:
                        word_bbox = (word['x0'], word['top'], word['x1'], word['bottom'])
                        in_table = False
                        for table_bbox in table_bboxes:
                            if bbox_overlap(word_bbox, table_bbox):
                                in_table = True
                                break
                        if not in_table:
                            filtered_words.append(word)

                    if filtered_words:
                        formatted_text = format_text(filtered_words)
                        html_content += f'<div class="text-content">{formatted_text}</div>'

                html_content += '</div>'

        html_content += """
        </body>
        </html>
        """

        return HTMLResponse(content=html_content)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing PDF: {str(e)}"
        )


def bbox_overlap(bbox1, bbox2):
    """Проверяет пересекаются ли два bounding box"""
    x1_1, y1_1, x2_1, y2_1 = bbox1
    x1_2, y1_2, x2_2, y2_2 = bbox2

    # Проверка на пересечение по x и y
    overlap_x = x1_1 < x2_2 and x2_1 > x1_2
    overlap_y = y1_1 < y2_2 and y2_1 > y1_2

    return overlap_x and overlap_y


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


@app.get("/pdf/all", response_model=list[PDFResponse])
async def get_all_pdf(db: Session = Depends(get_db)):
    pdfs = db.query(PDFFile).all()
    return pdfs


@app.delete("/pdf/{pdf_id}")
async def delete_pdf(pdf_id: int, db: Session = Depends(get_db)):
    try:
        pdf_file = db.query(PDFFile).filter(PDFFile.id == pdf_id).first()

        if not pdf_file:
            raise HTTPException(status_code=404, detail="PDF not found")

        db.delete(pdf_file)
        db.commit()

        return {"message": "PDF deleted successfully"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))



if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        reload=True
    )