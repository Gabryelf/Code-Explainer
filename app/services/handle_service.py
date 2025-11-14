import logging

logger = logging.getLogger(__name__)


class SimpleCodeAnalyzer:
    def __init__(self):
        self.language_patterns = {
            "python": ["def ", "import ", "from ", "print(", "class "],
            "javascript": ["function", "const ", "let ", "var ", "console.log", "export "],
            "java": ["public ", "class ", "void ", "System.out.", "import "],
            "html": ["<!DOCTYPE", "<html", "<head", "<body", "<div", "<script"],
            "css": ["{", "}", "@import", "@media", ":"],
            "cpp": ["#include", "using namespace", "int main", "cout ", "cin "]
        }

    async def explain_code(self, code: str, language: str = "auto") -> str:

        detected_lang = self._detect_language(code, language)
        analysis = self._analyze_code(code, detected_lang)

        return f"""🔍 **Анализ кода**

**Язык программирования:** {detected_lang}
**Размер кода:** {len(code)} символов, {code.count(chr(10)) + 1} строк

**Структура кода:**
{analysis}

**Статистика:**
- Функции/методы: ~{self._count_functions(code, detected_lang)}
- Импорты: {self._count_imports(code)}
- Условия: ~{self._count_conditions(code)}
- Циклы: ~{self._count_loops(code)}

**Рекомендации:**
{self._get_recommendations(code, detected_lang)}

*Для AI-анализа настройте Yandex GPT API*"""

    def _detect_language(self, code: str, hint: str) -> str:
        if hint != "auto":
            return hint

        for lang, patterns in self.language_patterns.items():
            if any(pattern in code for pattern in patterns):
                return lang
        return "unknown"

    def _analyze_code(self, code: str, language: str) -> str:
        lines = code.split('\n')
        analysis = []

        if any("def " in line for line in lines):
            analysis.append("• Содержит функции")
        if any("class " in line for line in lines):
            analysis.append("• Содержит классы")
        if any("import " in line or "require" in line for line in lines):
            analysis.append("• Есть импорты библиотек")
        if any("if " in line for line in lines):
            analysis.append("• Есть условные операторы")
        if any("for " in line or "while " in line for line in lines):
            analysis.append("• Есть циклы")
        if any("=" in line for line in lines):
            analysis.append("• Есть присваивания переменных")

        return '\n'.join(analysis) if analysis else "• Базовая структура программы"

    def _count_functions(self, code: str, language: str) -> int:
        if language == "python":
            return code.count("def ")
        elif language == "javascript":
            return code.count("function")
        else:
            return code.count("def ") + code.count("function")

    def _count_imports(self, code: str) -> int:
        return code.count("import ") + code.count("require") + code.count("#include")

    def _count_conditions(self, code: str) -> int:
        return code.count("if ") + code.count("else ") + code.count("switch ")

    def _count_loops(self, code: str) -> int:
        return code.count("for ") + code.count("while ") + code.count("do ")

    def _get_recommendations(self, code: str, language: str) -> str:
        recs = []

        if len(code) > 1000:
            recs.append("• Код довольно большой, рассмотрите разбиение на модули")

        if "TODO" in code or "FIXME" in code:
            recs.append("• Обнаружены комментарии TODO/FIXME")

        if language == "python" and "print(" in code:
            recs.append("• Используется вывод для отладки")

        return '\n'.join(recs) if recs else "• Код выглядит структурированно"
