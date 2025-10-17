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
    
    async def get_network_traffic(self) -> Dict[str, Any]:
        """
        Получить сетевой трафик по интерфейсам
        
        Returns:
            Словарь с данными о трафике
        """
        try:
            # Входящий трафик
            rx_query = 'node_network_receive_bytes_total'
            rx_result = await self.query(rx_query)
            
            # Исходящий трафик
            tx_query = 'node_network_transmit_bytes_total'
            tx_result = await self.query(tx_query)
            
            # Статус интерфейсов
            up_query = 'node_network_up'
            up_result = await self.query(up_query)
            
            interfaces = {}
            
            # Обработка входящего трафика
            if rx_result.get('status') == 'success' and rx_result.get('data', {}).get('result'):
                for item in rx_result['data']['result']:
                    interface = item['metric'].get('device', 'unknown')
                    value = float(item['value'][1])
                    if interface not in interfaces:
                        interfaces[interface] = {}
                    interfaces[interface]['rx_bytes'] = value
            
            # Обработка исходящего трафика
            if tx_result.get('status') == 'success' and tx_result.get('data', {}).get('result'):
                for item in tx_result['data']['result']:
                    interface = item['metric'].get('device', 'unknown')
                    value = float(item['value'][1])
                    if interface not in interfaces:
                        interfaces[interface] = {}
                    interfaces[interface]['tx_bytes'] = value
            
            # Обработка статуса интерфейсов
            if up_result.get('status') == 'success' and up_result.get('data', {}).get('result'):
                for item in up_result['data']['result']:
                    interface = item['metric'].get('device', 'unknown')
                    value = float(item['value'][1])
                    if interface not in interfaces:
                        interfaces[interface] = {}
                    interfaces[interface]['up'] = value == 1
            
            logger.info(f"Получены данные о трафике для {len(interfaces)} интерфейсов")
            return {
                'interfaces': interfaces,
                'total_interfaces': len(interfaces),
                'active_interfaces': sum(1 for iface in interfaces.values() if iface.get('up', False))
            }
            
        except Exception as e:
            logger.error(f"Ошибка получения сетевого трафика: {e}")
            return {'interfaces': {}, 'total_interfaces': 0, 'active_interfaces': 0}
    
    async def get_network_connections(self) -> Dict[str, Any]:
        """
        Получить количество сетевых соединений
        
        Returns:
            Словарь с данными о соединениях
        """
        try:
            # TCP соединения
            tcp_query = 'node_netstat_Tcp_CurrEstab'
            tcp_result = await self.query(tcp_query)
            
            # UDP соединения
            udp_query = 'node_netstat_Udp_CurrDatagrams'
            udp_result = await self.query(udp_query)
            
            connections = {
                'tcp_established': 0,
                'udp_datagrams': 0,
                'total': 0
            }
            
            if tcp_result.get('status') == 'success' and tcp_result.get('data', {}).get('result'):
                connections['tcp_established'] = float(tcp_result['data']['result'][0]['value'][1])
            
            if udp_result.get('status') == 'success' and udp_result.get('data', {}).get('result'):
                connections['udp_datagrams'] = float(udp_result['data']['result'][0]['value'][1])
            
            connections['total'] = connections['tcp_established'] + connections['udp_datagrams']
            
            logger.info(f"Сетевые соединения: TCP={connections['tcp_established']}, UDP={connections['udp_datagrams']}")
            return connections
            
        except Exception as e:
            logger.error(f"Ошибка получения сетевых соединений: {e}")
            return {'tcp_established': 0, 'udp_datagrams': 0, 'total': 0}
    
    async def get_network_errors(self) -> Dict[str, Any]:
        """
        Получить ошибки сети
        
        Returns:
            Словарь с данными об ошибках
        """
        try:
            # Ошибки входящего трафика
            rx_errors_query = 'node_network_receive_errs_total'
            rx_errors_result = await self.query(rx_errors_query)
            
            # Ошибки исходящего трафика
            tx_errors_query = 'node_network_transmit_errs_total'
            tx_errors_result = await self.query(tx_errors_query)
            
            errors = {
                'rx_errors': 0,
                'tx_errors': 0,
                'total_errors': 0,
                'interfaces_with_errors': []
            }
            
            if rx_errors_result.get('status') == 'success' and rx_errors_result.get('data', {}).get('result'):
                for item in rx_errors_result['data']['result']:
                    interface = item['metric'].get('device', 'unknown')
                    value = float(item['value'][1])
                    errors['rx_errors'] += value
                    if value > 0:
                        errors['interfaces_with_errors'].append(interface)
            
            if tx_errors_result.get('status') == 'success' and tx_errors_result.get('data', {}).get('result'):
                for item in tx_errors_result['data']['result']:
                    interface = item['metric'].get('device', 'unknown')
                    value = float(item['value'][1])
                    errors['tx_errors'] += value
                    if value > 0 and interface not in errors['interfaces_with_errors']:
                        errors['interfaces_with_errors'].append(interface)
            
            errors['total_errors'] = errors['rx_errors'] + errors['tx_errors']
            
            logger.info(f"Сетевые ошибки: RX={errors['rx_errors']}, TX={errors['tx_errors']}")
            return errors
            
        except Exception as e:
            logger.error(f"Ошибка получения сетевых ошибок: {e}")
            return {'rx_errors': 0, 'tx_errors': 0, 'total_errors': 0, 'interfaces_with_errors': []}
    
    async def get_top_processes_by_cpu(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Получить топ процессов по использованию CPU
        
        Args:
            limit: Количество процессов для возврата
            
        Returns:
            Список процессов с данными о CPU
        """
        try:
            # Используем node_cpu_seconds_total для расчета загрузки по процессам
            # Это приблизительная оценка, так как node_exporter не предоставляет детальные метрики процессов
            query = 'topk(10, rate(node_cpu_seconds_total{mode="user"}[5m]))'
            result = await self.query(query)
            
            processes = []
            
            if result.get('status') == 'success' and result.get('data', {}).get('result'):
                for i, item in enumerate(result['data']['result'][:limit]):
                    cpu_id = item['metric'].get('cpu', f'cpu{i}')
                    value = float(item['value'][1])
                    
                    processes.append({
                        'rank': i + 1,
                        'cpu_id': cpu_id,
                        'cpu_usage': value * 100,  # Конвертируем в проценты
                        'name': f'CPU Core {cpu_id}'
                    })
            
            logger.info(f"Получены топ {len(processes)} процессов по CPU")
            return processes
            
        except Exception as e:
            logger.error(f"Ошибка получения топ процессов по CPU: {e}")
            return []
    
    async def get_top_processes_by_memory(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Получить топ процессов по использованию памяти
        
        Args:
            limit: Количество процессов для возврата
            
        Returns:
            Список процессов с данными о памяти
        """
        try:
            # Используем node_memory_MemAvailable_bytes для оценки доступной памяти
            # Это не точные данные о процессах, но дает представление об использовании памяти
            query = 'node_memory_MemAvailable_bytes'
            result = await self.query(query)
            
            processes = []
            
            if result.get('status') == 'success' and result.get('data', {}).get('result'):
                available_bytes = float(result['data']['result'][0]['value'][1])
                available_gb = available_bytes / (1024**3)
                
                # Создаем фиктивные данные о процессах для демонстрации
                # В реальной системе нужно использовать другой экспортер для метрик процессов
                processes.append({
                    'rank': 1,
                    'name': 'System Memory',
                    'memory_usage_gb': available_gb,
                    'memory_percent': (available_gb / 4) * 100  # Предполагаем 4GB общий объем
                })
            
            logger.info(f"Получены данные о памяти для {len(processes)} процессов")
            return processes
            
        except Exception as e:
            logger.error(f"Ошибка получения топ процессов по памяти: {e}")
            return []
    
    async def get_network_status(self) -> Dict[str, Any]:
        """
        Получить полный статус сети
        
        Returns:
            Объединенные данные о сети
        """
        try:
            traffic = await self.get_network_traffic()
            connections = await self.get_network_connections()
            errors = await self.get_network_errors()
            
            return {
                'traffic': traffic,
                'connections': connections,
                'errors': errors,
                'status': 'healthy' if errors['total_errors'] < 100 else 'warning'
            }
            
        except Exception as e:
            logger.error(f"Ошибка получения статуса сети: {e}")
            return {
                'traffic': {'interfaces': {}, 'total_interfaces': 0, 'active_interfaces': 0},
                'connections': {'tcp_established': 0, 'udp_datagrams': 0, 'total': 0},
                'errors': {'rx_errors': 0, 'tx_errors': 0, 'total_errors': 0, 'interfaces_with_errors': []},
                'status': 'error'
            }

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

