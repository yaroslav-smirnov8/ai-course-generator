# app/__init__.py
import logging
from pathlib import Path

# Load backend/.env into os.environ early so handlers using os.environ see keys (e.g., LLM7_API_KEY)
try:
    from dotenv import load_dotenv  # type: ignore
    base_dir = Path(__file__).resolve().parent.parent  # backend/
    env_path = base_dir / ".env"
    if env_path.exists():
        # Do not override already-set environment variables
        load_dotenv(dotenv_path=env_path, override=False)
except Exception:
    # If python-dotenv is not installed, skip silently
    pass

from .core.config import settings

__version__ = settings.VERSION

# Настройка логирования
logger = logging.getLogger('app')

# Интеграция улучшенного обработчика JSON
try:
    import importlib
    from json_extractor_integration import integrate_json_extractor

    module_path = "app.services.content.generator"
    mod = importlib.import_module(module_path)
    CG = getattr(mod, "ContentGenerator", None)

    # Аккуратно выбираем доступный хук-метод — ничего не патчим, если его нет
    target_method = None
    for name in ("_process_course_response", "_clean_json_response"):
        if CG and hasattr(CG, name):
            target_method = name
            break

    if target_method:
        success = integrate_json_extractor(module_path, method_name=target_method)
        if success:
            logger.info("Улучшенный обработчик JSON успешно интегрирован с ContentGenerator")
        else:
            logger.warning("Интеграция улучшенного обработчика JSON не потребовалась или не применима")
    else:
        logger.info("Пропускаем интеграцию улучшенного обработчика JSON: подходящий хук-метод в ContentGenerator не найден")
except Exception as e:
    logger.error(f"Ошибка при интеграции улучшенного обработчика JSON: {str(e)}")
