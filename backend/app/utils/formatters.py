# app/utils/formatters.py
import re
from typing import Optional

def clean_text(text: str) -> str:
    # Очистка текста от специальных символов
    return re.sub(r'[^\x00-\x7F]+', '', text)

def format_telegram_username(username: Optional[str]) -> Optional[str]:
    if not username:
        return None
    # Удаляем @ если есть в начале
    return username.lstrip('@')

def format_markdown(text: str) -> str:
    # Экранирование специальных символов для Markdown
    special_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
    for char in special_chars:
        text = text.replace(char, f'\\{char}')
    return text