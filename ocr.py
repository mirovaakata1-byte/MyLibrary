import pytesseract
from PIL import Image
import re
from typing import Optional
import io

# Укажи путь к Tesseract (если не в PATH)
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"


def extract_text_from_image(image_bytes: bytes) -> str:
    """Извлекает текст из изображения с помощью Tesseract OCR (русский + английский)."""
    image = Image.open(io.BytesIO(image_bytes))
    text = pytesseract.image_to_string(image, lang="rus+eng")
    return text


def find_isbn(text: str) -> Optional[str]:
    """
    Ищет ISBN-10 или ISBN-13 в тексте.
    Поддерживает форматы: 1234567890, 123-4-56-789012-3, 978-1234567890, ISBN 978-0-7475-3269-9 и т.д.
    """
    # Убираем "ISBN" или "ISBN-13" в начале
    text = re.sub(r'(?i)isbn[-: ]?(13)?', '', text)

    # Ищем 10 или 13 цифр подряд (с возможными дефисами/пробелами)
    pattern = r'(?:\d[\-\s]?){9,13}\d'
    matches = re.findall(pattern, text)

    if not matches:
        return None

    # Берём первый найденный и оставляем только цифры
    isbn = re.sub(r'[^0-9]', '', matches[0])

    # Проверяем длину (должна быть 10 или 13)
    if len(isbn) == 10 or len(isbn) == 13:
        return isbn
    return None