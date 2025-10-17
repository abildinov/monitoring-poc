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
        timeout: int = 300  # 5 минут для больших моделей
    ):
        """
        Инициализация клиента
        
        Args:
            host: URL Ollama сервера
            model: Название модели
            timeout: Таймаут запросов в секундах (по умолчанию 300 = 5 минут)
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
        system_prompt = """Ты - опытный DevOps инженер и эксперт по мониторингу серверной инфраструктуры.

Твоя задача:
1. Анализировать метрики серверов (CPU, память, диски, сеть, процессы)
2. Определять проблемы и их критичность
3. Давать конкретные, выполнимые рекомендации

Уровни критичности:
- КРИТИЧНО (>95%): Требует немедленных действий
- ВНИМАНИЕ (>80%): Требует внимания в ближайшее время  
- НОРМА (<80%): Все в порядке

ВАЖНО: Отвечай ТОЛЬКО на русском языке. Будь конкретным и практичным."""
        
        # Форматирование метрик для LLM
        metrics_text = json.dumps(metrics_data, indent=2, ensure_ascii=False)
        
        prompt = f"""
Контекст: {context if context else 'Анализ текущего состояния системы'}

Метрики системы:
{metrics_text}

КРИТИЧЕСКИ ВАЖНО! Пороги для оценки:
- CPU: НОРМА <80%, ВНИМАНИЕ 80-95%, КРИТИЧНО >95%
- Memory: НОРМА <85%, ВНИМАНИЕ 85-95%, КРИТИЧНО >95%
- Disk: НОРМА <90%, ВНИМАНИЕ 90-95%, КРИТИЧНО >95%

ПРАВИЛО АНАЛИЗА (ОБЯЗАТЕЛЬНО СЛЕДУЙ):
- Если CPU = 6% → это НИЖЕ 80% → НОРМА ✅
- Если Memory = 23% → это НИЖЕ 85% → НОРМА ✅
- Если Disk = 45% → это НИЖЕ 90% → НОРМА ✅

ЗАПРЕЩЕНО:
- НЕ говори "запас до порогов 15%" если CPU = 6% (это неправильно!)
- НЕ говори "запас 10%" если Memory = 23% (это неправильно!)
- НЕ говори "запас 5%" если Disk = 45% (это неправильно!)

ПРАВИЛЬНО:
- CPU 6% = "отличная ситуация, используется только 6% из 100%"
- Memory 23% = "достаточно свободной памяти, используется 23% из 100%"
- Disk 45% = "половина диска свободна, используется 45% из 100%"

Проанализируй и ответь структурированно:

1. СТАТУС: Общая оценка состояния (КРИТИЧНО/ВНИМАНИЕ/НОРМА)

2. ПРОБЛЕМЫ (если есть):
   - Метрика и текущее значение
   - Уровень критичности
   - Почему это проблема

3. РЕКОМЕНДАЦИИ (конкретные действия):
   - Что сделать СЕЙЧАС (если критично)
   - Что проверить
   - Как предотвратить в будущем

4. ПРОГНОЗ: Что может произойти при текущей нагрузке

Если все в норме - скажи это четко. НЕ используй фразы типа "запас до порогов" - это технически неверно.
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
        system_prompt = """Ты - эксперт по анализу логов и troubleshooting серверных систем.

Твоя задача:
1. Классифицировать ошибки по severity (ERROR > WARN > INFO)
2. Находить паттерны и повторяющиеся проблемы
3. Определять первопричину (root cause)
4. Давать конкретные решения

ВАЖНО: Отвечай ТОЛЬКО на русском языке. Приоритизируй проблемы."""
        
        # Ограничиваем количество логов для анализа
        logs_sample = logs[:50] if len(logs) > 50 else logs
        logs_text = "\n".join(logs_sample)
        total_logs = len(logs)
        shown_logs = len(logs_sample)
        
        prompt = f"""
Контекст: {context if context else 'Анализ логов системы'}

Логи системы ({total_logs} строк, показаны {shown_logs}):
{logs_text}

Проанализируй структурированно:

1. СТАТИСТИКА:
   - Сколько ERROR, WARN, INFO
   - Есть ли повторяющиеся ошибки
   - Временные паттерны (всплески)

2. КРИТИЧНЫЕ ПРОБЛЕМЫ (ERROR):
   - Текст ошибки
   - Вероятная причина
   - Влияние на систему

3. ПРЕДУПРЕЖДЕНИЯ (WARN):
   - Что может привести к проблемам
   - Нужны ли действия

4. ROOT CAUSE:
   - Основная первопричина проблем
   - Связь между ошибками

5. ДЕЙСТВИЯ:
   - Что проверить в первую очередь
   - Как исправить
   - Как предотвратить

Если логи чистые - скажи это и отметь стабильность системы.
"""
        
        return await self.generate(prompt=prompt, system=system_prompt, temperature=0.3)
    
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
        
        # Вычисляем статистику
        min_value = min(historical_data) if historical_data else baseline
        max_value = max(historical_data) if historical_data else baseline
        
        # Определяем тренд
        if len(historical_data) >= 3:
            recent_avg = sum(historical_data[-3:]) / 3
            older_avg = sum(historical_data[-6:-3]) / 3 if len(historical_data) >= 6 else baseline
            if recent_avg > older_avg * 1.1:
                trend = "растет"
            elif recent_avg < older_avg * 0.9:
                trend = "падает"
            else:
                trend = "стабильно"
        else:
            trend = "недостаточно данных"
        
        system_prompt = """Ты - эксперт по детекции аномалий в системах мониторинга.

Твоя задача:
1. Определить, является ли значение аномальным
2. Учесть контекст и тренды
3. Объяснить причину и последствия

Критерии аномалии:
- Резкий скачок (>30% за короткое время)
- Выход за исторические пределы
- Необычный паттерн для времени суток

ВАЖНО: Отвечай ТОЛЬКО на русском языке."""
        
        # Форматируем исторические данные как мини-график
        history_chart = ' → '.join(f'{v:.1f}' for v in historical_data[-10:])
        
        prompt = f"""
Метрика: {metric_name}

Текущее значение: {current_value:.2f}
Базовое значение (среднее): {baseline:.2f}
Отклонение: {deviation:+.1f}%

Исторические данные (последние 10 измерений):
{history_chart}

Статистика:
- Минимум: {min_value:.2f}
- Максимум: {max_value:.2f}
- Тренд: {trend}

Проанализируй:

1. АНОМАЛИЯ?: Да/Нет и почему
   
2. СЕРЬЕЗНОСТЬ:
   - Незначительное отклонение
   - Требует внимания
   - Критическая аномалия

3. ПРИЧИНА:
   - Почему произошло
   - Паттерн или случайность

4. ДЕЙСТВИЯ:
   - Нужно ли реагировать
   - Что проверить

5. ПРОГНОЗ: Куда движется метрика
"""
        
        explanation = await self.generate(
            prompt=prompt, 
            system=system_prompt,
            temperature=0.2
        )
        
        # Улучшенная эвристика для флага аномалии
        is_anomaly = (
            abs(deviation) > 30 or  # Более 30% отклонения
            current_value > max_value * 1.2 or  # Превышает исторический максимум на 20%
            current_value < min_value * 0.8  # Ниже исторического минимума на 20%
        )
        
        return {
            "is_anomaly": is_anomaly,
            "deviation_percent": deviation,
            "explanation": explanation,
            "current_value": current_value,
            "baseline": baseline,
            "trend": trend,
            "min_value": min_value,
            "max_value": max_value
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
    
    async def analyze_system_health(
        self,
        all_metrics: Dict,
        active_alerts: List[Dict],
        error_logs_count: int
    ) -> str:
        """
        Комплексный анализ здоровья всей системы
        
        Args:
            all_metrics: Все метрики системы (CPU, memory, disk, network)
            active_alerts: Список активных алертов
            error_logs_count: Количество ошибок в логах за последний час
            
        Returns:
            Комплексный анализ здоровья системы
        """
        system_prompt = """Ты - старший DevOps инженер, проводящий полную проверку системы.

Дай комплексную оценку здоровья сервера, учитывая все метрики, алерты и логи.

ВАЖНО: Отвечай ТОЛЬКО на русском языке."""
        
        # Извлекаем основные метрики
        cpu = all_metrics.get('cpu_percent', 0)
        memory = all_metrics.get('memory_percent', 0)
        disk = all_metrics.get('disk_percent', 0)
        network_status = all_metrics.get('network_status', 'unknown')
        active_alerts_count = len(active_alerts)
        
        # Форматируем алерты
        alerts_text = "\n".join([f"  - {alert.get('name', 'Unknown')}: {alert.get('message', '')}" 
                                 for alert in active_alerts[:5]]) if active_alerts else "  Нет активных алертов"
        
        prompt = f"""
ПОЛНАЯ ПРОВЕРКА СИСТЕМЫ

Метрики:
- CPU: {cpu:.1f}% (порог: Warning >80%, Critical >95%)
- Memory: {memory:.1f}% (порог: Warning >85%, Critical >95%)
- Disk: {disk:.1f}% (порог: Warning >90%, Critical >95%)
- Network: {network_status}

Алерты: {active_alerts_count} активных
{alerts_text}

Ошибки в логах: {error_logs_count} за последний час

Проведи комплексный анализ:

1. ОБЩАЯ ОЦЕНКА: (оцени от 1 до 5 звезд)
   - Состояние системы одним словом

2. ОСНОВНЫЕ ПРОБЛЕМЫ:
   - Самые критичные вопросы
   - Взаимосвязи между проблемами

3. РИСКИ:
   - Что может сломаться
   - Узкие места системы

4. ПРИОРИТЕТНЫЕ ДЕЙСТВИЯ:
   - Топ-3 действия ПРЯМО СЕЙЧАС
   - Мониторинг на ближайшие часы

5. ДОЛГОСРОЧНЫЕ РЕКОМЕНДАЦИИ:
   - Что улучшить в архитектуре
   - Как оптимизировать

Если все отлично - похвали систему и укажи запас прочности.
"""
        
        return await self.generate(
            prompt=prompt,
            system=system_prompt,
            temperature=0.3
        )
    
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

