import os
import aiohttp
import logging
import asyncio
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


class CodeExplainerAI:
    def __init__(self):
        self.api_key = os.getenv("HF_API_KEY", "")

    async def explain_code(self, code: str, language: str = "auto") -> str:
        """Улучшенная версия с работающими моделями"""

        if not code.strip():
            return "❌ Пожалуйста, введите код для анализа"

        # Всегда показываем локальный анализ
        local_result = self._detailed_local_analysis(code, language)

        if not self.api_key:
            return local_result + "\n\n🔑 HF_API_KEY не настроен"

        try:
            # Пробуем разные модели
            ai_result = await self._smart_ai_request(code, language)

            if ai_result and self._is_valid_response(ai_result):
                return f"🤖 **AI Анализ:**\n\n{ai_result}\n\n---\n🔍 **Детали:**\n{local_result}"
            else:
                return local_result + "\n\n⚠️ AI временно недоступен. Используется локальный анализ."

        except Exception as e:
            logger.error(f"AI ошибка: {e}")
            return local_result + f"\n\n🔧 Ошибка AI: {str(e)}"

    async def _smart_ai_request(self, code: str, language: str) -> str:
        """Умный запрос к разным моделям"""

        # Список моделей для попытки (от самых надежных)
        models = [
            {
                "name": "microsoft/DialoGPT-medium",
                "url": "https://api-inference.huggingface.co/models/microsoft/DialoGPT-medium",
                "prompt": f"Объясни этот код на {language}: {code[:500]}",
                "max_tokens": 400
            },
            {
                "name": "gpt2",
                "url": "https://api-inference.huggingface.co/models/gpt2",
                "prompt": f"Explain this {language} code: {code[:300]}",
                "max_tokens": 300
            },
            {
                "name": "facebook/blenderbot-400M-distill",
                "url": "https://api-inference.huggingface.co/models/facebook/blenderbot-400M-distill",
                "prompt": f"Please explain this {language} code: {code[:400]}",
                "max_tokens": 350
            }
        ]

        for model in models:
            try:
                result = await self._make_hf_request(
                    model["url"],
                    model["prompt"],
                    model["max_tokens"]
                )

                if result and self._is_valid_response(result):
                    logger.info(f"✅ Успешный ответ от {model['name']}")
                    return result
                else:
                    logger.info(f"❌ Пустой ответ от {model['name']}")

            except Exception as e:
                logger.warning(f"Ошибка с {model['name']}: {e}")
                continue

        return ""

    async def _make_hf_request(self, url: str, prompt: str, max_tokens: int) -> str:
        """Базовый запрос к Hugging Face"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "inputs": prompt,
            "parameters": {
                "max_new_tokens": max_tokens,
                "temperature": 0.7,
                "do_sample": True,
                "return_full_text": False
            },
            "options": {
                "wait_for_model": True
            }
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, headers=headers, timeout=30) as response:

                logger.info(f"HF Response: {response.status}")

                if response.status == 200:
                    result = await response.json()
                    return self._clean_response(result)
                elif response.status == 503:
                    # Модель загружается - ждем и пробуем другую
                    await asyncio.sleep(10)
                    return ""
                else:
                    error_text = await response.text()
                    logger.error(f"HF API Error {response.status}: {error_text}")
                    return ""

    def _clean_response(self, result) -> str:
        """Очистка ответа от HF"""
        try:
            if isinstance(result, list) and len(result) > 0:
                if 'generated_text' in result[0]:
                    text = result[0]['generated_text'].strip()
                    # Убираем повторения промпта
                    lines = text.split('\n')
                    cleaned_lines = []
                    for line in lines:
                        if not any(phrase in line for phrase in ['Объясни этот', 'Explain this', 'Please explain']):
                            cleaned_lines.append(line)
                    return '\n'.join(cleaned_lines).strip()

            # Если структура другая
            return str(result).strip()

        except Exception as e:
            logger.error(f"Error cleaning response: {e}")
            return str(result)

    def _is_valid_response(self, text: str) -> bool:
        """Проверка валидности ответа"""
        if not text:
            return False
        if text.lower() in ['null', 'none', '']:
            return False
        if len(text.strip()) < 20:  # Слишком короткий ответ
            return False
        if 'error' in text.lower() or 'exception' in text.lower():
            return False
        return True

    def _detailed_local_analysis(self, code: str, language: str) -> str:
        """Детальный локальный анализ"""
        lines = code.split('\n')
        non_empty_lines = [line for line in lines if line.strip()]

        analysis = f"""📊 **Детальный анализ кода**

**Основная информация:**
• Язык: {language}
• Всего строк: {len(lines)}
• Непустых строк: {len(non_empty_lines)} 
• Объем: {len(code)} символов

**Структура кода:**
{self._analyze_structure(code)}

**Обнаруженные элементы:**
{self._detect_elements(code)}

**Рекомендации:**
{self._get_recommendations(code, language)}

**Статистика:**
• Функции/методы: ~{self._count_functions(code)}
• Импорты: {self._count_imports(code)}
• Условия: ~{self._count_conditions(code)}
• Циклы: ~{self._count_loops(code)}"""

        return analysis

    def _analyze_structure(self, code: str) -> str:
        """Анализ структуры кода"""
        elements = []

        if 'def ' in code or 'function ' in code:
            elements.append("• Функции/методы")
        if 'class ' in code:
            elements.append("• Классы")
        if any(x in code for x in ['import ', 'require', '#include']):
            elements.append("• Импорты библиотек")
        if 'if ' in code:
            elements.append("• Условные операторы")
        if 'for ' in code or 'while ' in code:
            elements.append("• Циклы")
        if 'try:' in code or 'try{' in code:
            elements.append("• Обработка исключений")

        return '\n'.join(elements) if elements else "• Линейная структура"

    def _detect_elements(self, code: str) -> str:
        """Обнаружение элементов"""
        elements = []

        if any(x in code for x in ['print(', 'console.log', 'System.out']):
            elements.append("• Отладочный вывод")
        if 'TODO' in code or 'FIXME' in code:
            elements.append("• TODO/FIXME комментарии")
        if any(x in code.lower() for x in ['password', 'secret', 'api_key']):
            elements.append("• Возможно, чувствительные данные")
        if 'input(' in code or 'scanf' in code:
            elements.append("• Ввод данных")

        return '\n'.join(elements) if elements else "• Стандартные конструкции"

    def _get_recommendations(self, code: str, language: str) -> str:
        """Рекомендации"""
        recs = []

        if len(code) > 1000:
            recs.append("• Разбейте код на модули")
        if len(code) < 100:
            recs.append("• Добавьте больше функциональности")
        if 'def ' not in code and 'function ' not in code and len(code) > 200:
            recs.append("• Вынесите логику в функции")
        if 'TODO' in code:
            recs.append("• Решите задачи в TODO комментариях")

        return '\n'.join(recs) if recs else "• Код хорошо структурирован"

    def _count_functions(self, code: str) -> int:
        return code.count('def ') + code.count('function ')

    def _count_imports(self, code: str) -> int:
        return code.count('import ') + code.count('require') + code.count('#include')

    def _count_conditions(self, code: str) -> int:
        return code.count('if ') + code.count('else ') + code.count('switch ')

    def _count_loops(self, code: str) -> int:
        return code.count('for ') + code.count('while ') + code.count('do ')
