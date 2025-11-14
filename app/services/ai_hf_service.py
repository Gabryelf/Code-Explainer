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
        self.is_production = os.getenv("RENDER", False)  # Render sets this
        self.model_cache = {}

    async def explain_code(self, code: str, language: str = "auto") -> str:
        """Продакшен версия с улучшенной обработкой"""

        if not code.strip():
            return "❌ Пожалуйста, введите код для анализа"

        # Всегда быстрый локальный анализ
        local_result = self._local_analysis(code, language)

        if not self.api_key:
            return local_result

        # AI анализ с таймаутом
        try:
            ai_result = await asyncio.wait_for(
                self._production_ai_analysis(code, language),
                timeout=25.0  # Таймаут 25 секунд
            )

            if self._is_valid_ai_response(ai_result):
                return f"🤖 **AI Анализ:**\n\n{ai_result}\n\n---\n🔍 **Детали:**\n{local_result}"
            else:
                return local_result + "\n\n⚠️ AI не смог проанализировать этот код"

        except asyncio.TimeoutError:
            logger.warning("AI анализ превысил время ожидания")
            return local_result + "\n\n⏳ AI занят, попробуйте через минуту"
        except Exception as e:
            logger.error(f"AI ошибка: {e}")
            return local_result + f"\n\n🔧 Временная ошибка AI"

    async def _production_ai_analysis(self, code: str, language: str) -> str:
        """Продакшен версия AI анализа"""

        # Пробуем разные стратегии
        strategies = [
            self._try_code_llama,
            self._try_dialogpt,
            self._try_gpt2
        ]

        for strategy in strategies:
            try:
                result = await strategy(code, language)
                if self._is_valid_ai_response(result):
                    return result
            except Exception as e:
                logger.info(f"Стратегия {strategy.__name__} не сработала: {e}")
                continue

        return ""

    async def _try_code_llama(self, code: str, language: str) -> str:
        """CodeLlama - специализированная модель для кода"""
        url = "https://api-inference.huggingface.co/models/codellama/CodeLlama-7b-Instruct-hf"

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        prompt = f"[INST] Объясни этот {language} код:\n\n```{language}\n{code}\n```\n\nОбъясни что делает код, как работают функции и для чего он предназначен. [/INST]"

        payload = {
            "inputs": prompt,
            "parameters": {
                "max_new_tokens": 800,
                "temperature": 0.3,
                "do_sample": True
            }
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, headers=headers, timeout=30) as response:
                if response.status == 200:
                    result = await response.json()
                    return self._extract_text(result)
                elif response.status == 503:
                    # Модель загружается - ждем
                    await asyncio.sleep(15)
                    return await self._try_code_llama(code, language)
                else:
                    return ""

    async def _try_dialogpt(self, code: str, language: str) -> str:
        """DialoGPT - надежная модель для диалога"""
        url = "https://api-inference.huggingface.co/models/microsoft/DialoGPT-large"

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        prompt = f"Объясни этот {language} код подробно: {code[:600]}"

        payload = {
            "inputs": prompt,
            "parameters": {
                "max_new_tokens": 500,
                "temperature": 0.7,
                "do_sample": True
            }
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, headers=headers, timeout=20) as response:
                if response.status == 200:
                    result = await response.json()
                    return self._extract_text(result)
                return ""

    async def _try_gpt2(self, code: str, language: str) -> str:
        """GPT2 - базовая модель"""
        url = "https://api-inference.huggingface.co/models/gpt2"

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        prompt = f"Explain this {language} code: {code[:400]}"

        payload = {
            "inputs": prompt,
            "parameters": {
                "max_new_tokens": 300,
                "temperature": 0.7
            }
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, headers=headers, timeout=15) as response:
                if response.status == 200:
                    result = await response.json()
                    return self._extract_text(result)
                return ""

    def _extract_text(self, result) -> str:
        """Извлекаем текст из ответа HF"""
        if isinstance(result, list) and len(result) > 0:
            if 'generated_text' in result[0]:
                text = result[0]['generated_text']
                if 'Объясни этот' in text:
                    parts = text.split('Объясни этот')
                    if len(parts) > 1:
                        text = parts[1].strip()
                return text
        return ""

    def _is_valid_ai_response(self, text: str) -> bool:
        """Проверяем что ответ AI валидный"""
        if not text or text == "null":
            return False
        if len(text.strip()) < 30:
            return False
        if "error" in text.lower() or "exception" in text.lower():
            return False
        return True

    def _local_analysis(self, code: str, language: str) -> str:
        """Локальный анализ (оставляем ваш текущий)"""
        # ... ваш существующий код локального анализа ...
        return f"Локальный анализ: {len(code)} символов, {language}"
