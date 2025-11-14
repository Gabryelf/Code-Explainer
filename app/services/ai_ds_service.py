import os
import aiohttp
import logging
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


class CodeExplainerAI:
    def __init__(self):
        self.api_key = os.getenv("DEEPSEEK_API_KEY", "")

    async def explain_code(self, code: str, language: str = "auto") -> str:
        """Упрощенная версия с приоритетом на локальный анализ"""

        if not code.strip():
            return "❌ Введите код для анализа"

        # Сначала пробуем AI если есть ключ
        if self.api_key:
            try:
                result = await self._simple_ai_call(code, language)
                if result and result != "null":
                    return f"🤖 **AI Анализ:**\n\n{result}"
            except Exception as e:
                logger.info(f"AI не сработал: {e}")

        # Всегда возвращаем локальный анализ
        return self._detailed_local_analysis(code, language)

    async def _simple_ai_call(self, code: str, language: str) -> str:
        """Простой AI запрос"""
        url = "https://api.deepseek.com/v1/chat/completions"

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }

        prompt = f"Объясни этот {language} код: {code[:1000]}"

        payload = {
            "model": "deepseek-chat",
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 1000
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, headers=headers, timeout=15) as response:
                if response.status == 200:
                    result = await response.json()
                    return result.get("choices", [{}])[0].get("message", {}).get("content", "")
                return ""

    def _detailed_local_analysis(self, code: str, language: str) -> str:
        """Детальный локальный анализ"""
        lines = code.split('\n')

        analysis = f"""🤖 **Детальный анализ кода**

📋 **Общая информация:**
• Язык: {language}
• Строк кода: {len(lines)}
• Символов: {len(code)}

🔍 **Структурный анализ:**
{self._analyze_structure(code)}

📝 **Первые 3 строки кода:**
{chr(10).join(['• ' + line.strip() for line in lines[:3] if line.strip()])}

💡 **Советы по улучшению:**
{self._get_improvement_tips(code, language)}"""

        return analysis

    def _analyze_structure(self, code: str) -> str:
        analysis = []

        # Анализ функций
        functions = [line for line in code.split('\n') if 'def ' in line or 'function ' in line]
        if functions:
            analysis.append(f"• Функции: {len(functions)}")
            for func in functions[:2]:  # Показываем первые 2
                analysis.append(f"  - {func.strip()}")

        # Анализ классов
        classes = [line for line in code.split('\n') if 'class ' in line]
        if classes:
            analysis.append(f"• Классы: {len(classes)}")

        # Анализ импортов
        imports = [line for line in code.split('\n') if any(x in line for x in ['import ', 'require', '#include'])]
        if imports:
            analysis.append(f"• Импорты: {len(imports)}")

        return '\n'.join(analysis) if analysis else "• Простая структура"

    def _get_improvement_tips(self, code: str, language: str) -> str:
        tips = []

        if not any(x in code for x in ['def ', 'function ', 'class ']):
            tips.append("• Добавьте функции для лучшей организации")

        if 'TODO' in code or 'FIXME' in code:
            tips.append("• Решите задачи в TODO/FIXME комментариях")

        if len(code) > 500:
            tips.append("• Разбейте код на несколько файлов")

        if language == "python" and '    ' not in code and 'def ' in code:
            tips.append("• Проверьте отступы в Python коде")

        return '\n'.join(tips) if tips else "• Код хорошо организован"
