"""
HTTP клиент для Prometheus
Получает метрики с удаленного сервера
"""

import httpx
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from loguru import logger


class PrometheusClient:
    """HTTP клиент для удаленного Prometheus"""
    
    def __init__(self, base_url: str, timeout: int = 30):
        """
        Инициализация клиента
        
        Args:
            base_url: URL Prometheus сервера (например, http://147.45.157.2:9090)
            timeout: Таймаут запросов в секундах
        """
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.client = httpx.AsyncClient(timeout=timeout)
        logger.info(f"PrometheusClient инициализирован: {self.base_url}")
    
    async def query(self, promql: str) -> Dict[str, Any]:
        """
        Выполнить PromQL запрос (мгновенный снимок)
        
        Args:
            promql: PromQL выражение
            
        Returns:
            Результат запроса
        """
        url = f"{self.base_url}/api/v1/query"
        params = {"query": promql}
        
        try:
            response = await self.client.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            if data.get("status") != "success":
                logger.error(f"Prometheus query error: {data}")
                return {"status": "error", "data": {}}
            
            logger.debug(f"Query успешен: {promql[:50]}...")
            return data
            
        except httpx.HTTPError as e:
            logger.error(f"HTTP ошибка при запросе к Prometheus: {e}")
            return {"status": "error", "error": str(e), "data": {}}
    
    async def query_range(
        self, 
        promql: str,
        start: datetime,
        end: datetime,
        step: str = "15s"
    ) -> Dict[str, Any]:
        """
        Запрос метрик за период времени
        
        Args:
            promql: PromQL выражение
            start: Начало периода
            end: Конец периода
            step: Шаг между точками данных
            
        Returns:
            Временной ряд данных
        """
        url = f"{self.base_url}/api/v1/query_range"
        params = {
            "query": promql,
            "start": int(start.timestamp()),
            "end": int(end.timestamp()),
            "step": step
        }
        
        try:
            response = await self.client.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            if data.get("status") != "success":
                logger.error(f"Prometheus query_range error: {data}")
                return {"status": "error", "data": {}}
            
            logger.debug(f"Query range успешен: {promql[:50]}...")
            return data
            
        except httpx.HTTPError as e:
            logger.error(f"HTTP ошибка при query_range: {e}")
            return {"status": "error", "error": str(e), "data": {}}
    
    async def get_current_cpu(self) -> Optional[float]:
        """
        Получить текущую нагрузку CPU (%)
        
        Returns:
            Процент загрузки CPU или None при ошибке
        """
        query = '100 - (avg(rate(node_cpu_seconds_total{mode="idle"}[5m])) * 100)'
        result = await self.query(query)
        
        if result.get("status") == "success" and result["data"].get("result"):
            value = float(result["data"]["result"][0]["value"][1])
            logger.info(f"CPU usage: {value:.2f}%")
            return value
        
        return None
    
    async def get_current_memory(self) -> Optional[Dict[str, float]]:
        """
        Получить текущее использование памяти
        
        Returns:
            Словарь с метриками памяти (used, total, percent) или None
        """
        # Запросы для памяти
        total_query = "node_memory_MemTotal_bytes"
        available_query = "node_memory_MemAvailable_bytes"
        
        total_result = await self.query(total_query)
        available_result = await self.query(available_query)
        
        if (total_result.get("status") == "success" and 
            available_result.get("status") == "success"):
            
            total_bytes = float(total_result["data"]["result"][0]["value"][1])
            available_bytes = float(available_result["data"]["result"][0]["value"][1])
            used_bytes = total_bytes - available_bytes
            percent = (used_bytes / total_bytes) * 100
            
            memory_info = {
                "total_gb": total_bytes / (1024**3),
                "used_gb": used_bytes / (1024**3),
                "available_gb": available_bytes / (1024**3),
                "percent": percent
            }
            
            logger.info(f"Memory: {memory_info['percent']:.2f}% used")
            return memory_info
        
        return None
    
    async def get_disk_usage(self) -> Optional[List[Dict[str, Any]]]:
        """
        Получить использование дисков
        
        Returns:
            Список дисков с метриками или None
        """
        query = '''
        100 - (node_filesystem_avail_bytes{fstype!="tmpfs",fstype!="ramfs"} 
        / node_filesystem_size_bytes{fstype!="tmpfs",fstype!="ramfs"} * 100)
        '''
        
        result = await self.query(query)
        
        if result.get("status") == "success" and result["data"].get("result"):
            disks = []
            for item in result["data"]["result"]:
                disk_info = {
                    "device": item["metric"].get("device", "unknown"),
                    "mountpoint": item["metric"].get("mountpoint", "/"),
                    "percent": float(item["value"][1])
                }
                disks.append(disk_info)
            
            logger.info(f"Disk usage получен для {len(disks)} дисков")
            return disks
        
        return None
    
    async def check_health(self) -> bool:
        """
        Проверка доступности Prometheus
        
        Returns:
            True если Prometheus доступен
        """
        try:
            url = f"{self.base_url}/-/healthy"
            response = await self.client.get(url, timeout=5)
            is_healthy = response.status_code == 200
            
            if is_healthy:
                logger.info("Prometheus: здоров ✓")
            else:
                logger.warning(f"Prometheus: нездоров (status {response.status_code})")
            
            return is_healthy
            
        except Exception as e:
            logger.error(f"Prometheus недоступен: {e}")
            return False
    
    async def close(self):
        """Закрыть соединения"""
        await self.client.aclose()
        logger.info("PrometheusClient закрыт")


# Пример использования
if __name__ == "__main__":
    import asyncio
    
    async def test():
        client = PrometheusClient("http://147.45.157.2:9090")
        
        # Проверка здоровья
        is_healthy = await client.check_health()
        print(f"Prometheus healthy: {is_healthy}")
        
        # CPU
        cpu = await client.get_current_cpu()
        print(f"CPU: {cpu}%")
        
        # Memory
        memory = await client.get_current_memory()
        print(f"Memory: {memory}")
        
        # Disk
        disks = await client.get_disk_usage()
        print(f"Disks: {disks}")
        
        await client.close()
    
    asyncio.run(test())

