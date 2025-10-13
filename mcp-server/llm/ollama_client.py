"""
Клиент для локальной LLM через Ollama
Используется для анализа метрик и логов
"""

import httpx
import json
from typing import Dict, List, Optional, AsyncIterator
from loguru import logger


class OllamaClient:
    """Клиент для локальной LLM через Ollama"""
    
    def __init__(
        self, 
        host: str = "http://localhost:11434",
        model: str = "llama3",
        timeout: int = 120
    ):
        """
        Инициализация клиента
        
        Args:
            host: URL Ollama сервера
            model: Название модели
            timeout: Таймаут запросов в секундах
        """
        self.host = host.rstrip('/')
        self.model = model
        self.timeout = timeout
        self.client = httpx.AsyncClient(timeout=timeout)
        logger.info(f"OllamaClient инициализирован: {self.host}, модель: {self.model}")
    
    async def generate(
        self, 
        prompt: str,
        system: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048
    ) -> str:
        """
        Генерация текста
        
        Args:
            prompt: Запрос к LLM
            system: Системный промпт
            temperature: Температура генерации (0.0-1.0)
            max_tokens: Максимум токенов в ответе
            
        Returns:
            Сгенерированный текст
        """
        url = f"{self.host}/api/generate"
        
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens
            }
        }
        
        if system:
            payload["system"] = system
        
        try:
            logger.debug(f"Запрос к Ollama: {prompt[:100]}...")
            response = await self.client.post(url, json=payload)
            response.raise_for_status()
            
            result = response.json()
            generated_text = result.get("response", "")
            
            logger.info(f"Ollama ответил ({len(generated_text)} символов)")
            return generated_text
            
        except httpx.HTTPError as e:
            logger.error(f"Ошибка при запросе к Ollama: {e}")
            return f"Ошибка: {str(e)}"
    
    async def generate_stream(
        self, 
        prompt: str,
        system: Optional[str] = None,
        temperature: float = 0.7
    ) -> AsyncIterator[str]:
        """
        Стриминг генерации (для real-time ответов)
        
        Args:
            prompt: Запрос
            system: Системный промпт
            temperature: Температура
            
        Yields:
            Части сгенерированного текста
        """
        url = f"{self.host}/api/generate"
        
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": True,
            "options": {
                "temperature": temperature
            }
        }
        
        if system:
            payload["system"] = system
        
        try:
            async with self.client.stream("POST", url, json=payload) as response:
                async for line in response.aiter_lines():
                    if line:
                        try:
                            data = json.loads(line)
                            if "response" in data:
                                yield data["response"]
                        except json.JSONDecodeError:
                            continue
                            
        except httpx.HTTPError as e:
            logger.error(f"Ошибка стриминга: {e}")
            yield f"Ошибка: {str(e)}"
    
    async def analyze_metrics(
        self, 
        metrics_data: Dict,
        context: str = ""
    ) -> str:
        """
        Анализ метрик с помощью LLM
        
        Args:
            metrics_data: Словарь с метриками
            context: Дополнительный контекст
            
        Returns:
            Анализ от LLM
        """
        system_prompt = """Ты - эксперт по мониторингу серверной инфраструктуры.
Анализируешь метрики и даешь практические рекомендации.
Отвечай кратко, по делу, на русском языке.
Если видишь проблемы - указывай их явно и предлагай решения."""
        
        # Форматирование метрик для LLM
        metrics_text = json.dumps(metrics_data, indent=2, ensure_ascii=False)
        
        prompt = f"""
Контекст: {context if context else 'Анализ текущего состояния системы'}

Метрики:
{metrics_text}

Проанализируй метрики и ответь:
1. Есть ли проблемы или аномалии?
2. Какие метрики вызывают беспокойство?
3. Что рекомендуешь сделать?

Будь конкретным и практичным.
"""
        
        return await self.generate(
            prompt=prompt,
            system=system_prompt,
            temperature=0.3  # Меньше креативности для технического анализа
        )
    
    async def analyze_logs(
        self, 
        logs: List[str],
        context: str = ""
    ) -> str:
        """
        Анализ логов
        
        Args:
            logs: Список строк логов
            context: Контекст
            
        Returns:
            Анализ логов
        """
        system_prompt = """Ты - эксперт по анализу логов и troubleshooting.
Находишь проблемы, определяешь первопричины, даешь рекомендации.
Отвечай на русском языке, кратко и по существу."""
        
        # Ограничиваем количество логов для анализа
        logs_sample = logs[:50] if len(logs) > 50 else logs
        logs_text = "\n".join(logs_sample)
        
        prompt = f"""
Контекст: {context if context else 'Анализ логов системы'}

Логи ({len(logs_sample)} строк):
{logs_text}

Проанализируй логи:
1. Какие ошибки или предупреждения присутствуют?
2. Есть ли повторяющиеся паттерны?
3. Какая вероятная первопричина проблем?
4. Что рекомендуешь сделать?
"""
        
        return await self.generate(prompt=prompt, system=system_prompt)
    
    async def detect_anomaly(
        self, 
        metric_name: str,
        current_value: float,
        historical_data: List[float],
        baseline: float
    ) -> Dict[str, any]:
        """
        Детекция аномалии с объяснением от LLM
        
        Args:
            metric_name: Название метрики
            current_value: Текущее значение
            historical_data: Исторические данные
            baseline: Базовое значение (норма)
            
        Returns:
            Словарь с флагом аномалии и объяснением
        """
        deviation = ((current_value - baseline) / baseline) * 100 if baseline != 0 else 0
        
        system_prompt = """Ты - эксперт по анализу метрик систем мониторинга.
Определяешь, является ли отклонение метрики аномалией.
Отвечай кратко, на русском."""
        
        prompt = f"""
Метрика: {metric_name}
Текущее значение: {current_value:.2f}
Базовое значение (норма): {baseline:.2f}
Отклонение: {deviation:+.1f}%

Исторические данные (последние 10 значений):
{', '.join(f'{v:.2f}' for v in historical_data[-10:])}

Это аномалия? Если да, объясни почему и что это может означать.
Если нет - укажи, что значение в норме.
"""
        
        explanation = await self.generate(
            prompt=prompt, 
            system=system_prompt,
            temperature=0.2
        )
        
        # Простая эвристика для флага аномалии
        is_anomaly = abs(deviation) > 30  # Более 30% отклонения
        
        return {
            "is_anomaly": is_anomaly,
            "deviation_percent": deviation,
            "explanation": explanation,
            "current_value": current_value,
            "baseline": baseline
        }
    
    async def generate_recommendations(
        self,
        issues: List[Dict],
        system_info: Dict
    ) -> str:
        """
        Генерация рекомендаций по устранению проблем
        
        Args:
            issues: Список обнаруженных проблем
            system_info: Общая информация о системе
            
        Returns:
            Рекомендации
        """
        system_prompt = """Ты - DevOps инженер с большим опытом.
Даешь практические рекомендации по устранению проблем в инфраструктуре.
Рекомендации должны быть конкретными и выполнимыми."""
        
        issues_text = json.dumps(issues, indent=2, ensure_ascii=False)
        system_text = json.dumps(system_info, indent=2, ensure_ascii=False)
        
        prompt = f"""
Информация о системе:
{system_text}

Обнаруженные проблемы:
{issues_text}

Предложи пошаговый план действий для устранения проблем.
Укажи:
1. Первоочередные действия
2. Команды для диагностики
3. Возможные решения
4. Меры профилактики
"""
        
        return await self.generate(prompt=prompt, system=system_prompt)
    
    async def check_health(self) -> bool:
        """
        Проверка доступности Ollama
        
        Returns:
            True если Ollama доступен
        """
        try:
            url = f"{self.host}/api/tags"
            response = await self.client.get(url, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                models = data.get("models", [])
                model_names = [m.get("name") for m in models]
                logger.info(f"Ollama: доступен ✓ (модели: {', '.join(model_names)})")
                return True
            else:
                logger.warning(f"Ollama: недоступен (status {response.status_code})")
                return False
                
        except Exception as e:
            logger.error(f"Ollama недоступен: {e}")
            return False
    
    async def close(self):
        """Закрыть соединения"""
        await self.client.aclose()
        logger.info("OllamaClient закрыт")


# Пример использования
if __name__ == "__main__":
    import asyncio
    
    async def test():
        client = OllamaClient(model="llama3")
        
        # Проверка здоровья
        is_healthy = await client.check_health()
        print(f"Ollama healthy: {is_healthy}\n")
        
        # Анализ метрик
        metrics = {
            "cpu_percent": 85.5,
            "memory_percent": 78.2,
            "disk_percent": 45.0
        }
        
        analysis = await client.analyze_metrics(metrics, "Анализ сервера production")
        print("=== Анализ метрик ===")
        print(analysis)
        print()
        
        # Детекция аномалии
        anomaly = await client.detect_anomaly(
            metric_name="CPU Usage",
            current_value=92.0,
            historical_data=[45.0, 48.0, 50.0, 47.0, 51.0, 49.0, 92.0],
            baseline=48.5
        )
        
        print("=== Детекция аномалии ===")
        print(f"Аномалия: {anomaly['is_anomaly']}")
        print(f"Отклонение: {anomaly['deviation_percent']:.1f}%")
        print(f"Объяснение: {anomaly['explanation']}")
        
        await client.close()
    
    asyncio.run(test())

