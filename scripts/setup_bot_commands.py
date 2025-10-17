#!/usr/bin/env python3
"""
Скрипт для настройки команд бота в Telegram
Регистрирует команды в меню бота через BotFather
"""

import asyncio
import sys
from pathlib import Path

# Добавляем путь к mcp-server для импорта модулей
sys.path.insert(0, str(Path(__file__).parent.parent / "mcp-server"))

from config import settings
import httpx


async def setup_bot_commands():
    """Настройка команд бота"""
    
    if not settings.telegram_enabled or not settings.telegram_bot_token:
        print("❌ Telegram не настроен!")
        print("Запустите: python setup_telegram_bot.py")
        return False
    
    bot_token = settings.telegram_bot_token
    base_url = f"https://api.telegram.org/bot{bot_token}"
    
    print("🤖 Настройка команд бота...")
    print(f"🔑 Token: {bot_token[:10]}...")
    
    # Команды для меню бота
    commands = [
        {
            "command": "start",
            "description": "🏠 Приветствие и главное меню"
        },
        {
            "command": "help", 
            "description": "❓ Справка по командам"
        },
        {
            "command": "menu",
            "description": "📋 Показать меню с кнопками"
        },
        {
            "command": "analyze",
            "description": "🎓 Полный анализ системы через LLM"
        },
        {
            "command": "status",
            "description": "📊 Статус системы"
        },
        {
            "command": "health",
            "description": "🏥 Здоровье компонентов"
        },
        {
            "command": "alerts",
            "description": "🚨 Активные алерты"
        },
        {
            "command": "chat",
            "description": "💬 Задать вопрос LLM"
        }
    ]
    
    async with httpx.AsyncClient(timeout=30) as client:
        try:
            # Устанавливаем команды
            url = f"{base_url}/setMyCommands"
            data = {
                "commands": commands
            }
            
            print(f"📤 Отправляем команды в Telegram...")
            response = await client.post(url, json=data)
            response.raise_for_status()
            
            result = response.json()
            
            if result.get("ok"):
                print(f"✅ Команды успешно установлены!")
                print(f"📋 Установлено команд: {len(commands)}")
                
                # Показываем установленные команды
                print(f"\n📝 Установленные команды:")
                for cmd in commands:
                    print(f"  /{cmd['command']} - {cmd['description']}")
                
                return True
            else:
                print(f"❌ Ошибка установки команд: {result.get('description', 'Unknown error')}")
                return False
                
        except Exception as e:
            print(f"❌ Ошибка установки команд: {e}")
            return False


async def get_bot_info():
    """Получить информацию о боте"""
    
    if not settings.telegram_enabled or not settings.telegram_bot_token:
        print("❌ Telegram не настроен!")
        return False
    
    bot_token = settings.telegram_bot_token
    base_url = f"https://api.telegram.org/bot{bot_token}"
    
    async with httpx.AsyncClient(timeout=30) as client:
        try:
            # Получаем информацию о боте
            url = f"{base_url}/getMe"
            
            response = await client.get(url)
            response.raise_for_status()
            
            result = response.json()
            
            if result.get("ok"):
                bot_info = result.get("result", {})
                print(f"🤖 Информация о боте:")
                print(f"  Имя: {bot_info.get('first_name', 'Unknown')}")
                print(f"  Username: @{bot_info.get('username', 'Unknown')}")
                print(f"  ID: {bot_info.get('id', 'Unknown')}")
                print(f"  Поддерживает команды: {bot_info.get('can_join_groups', False)}")
                return True
            else:
                print(f"❌ Ошибка получения информации: {result.get('description', 'Unknown error')}")
                return False
                
        except Exception as e:
            print(f"❌ Ошибка получения информации: {e}")
            return False


async def get_current_commands():
    """Получить текущие команды бота"""
    
    if not settings.telegram_enabled or not settings.telegram_bot_token:
        print("❌ Telegram не настроен!")
        return False
    
    bot_token = settings.telegram_bot_token
    base_url = f"https://api.telegram.org/bot{bot_token}"
    
    async with httpx.AsyncClient(timeout=30) as client:
        try:
            # Получаем текущие команды
            url = f"{base_url}/getMyCommands"
            
            response = await client.get(url)
            response.raise_for_status()
            
            result = response.json()
            
            if result.get("ok"):
                commands = result.get("result", [])
                print(f"📋 Текущие команды бота ({len(commands)}):")
                
                if commands:
                    for cmd in commands:
                        print(f"  /{cmd.get('command', 'unknown')} - {cmd.get('description', 'No description')}")
                else:
                    print("  Команды не установлены")
                
                return True
            else:
                print(f"❌ Ошибка получения команд: {result.get('description', 'Unknown error')}")
                return False
                
        except Exception as e:
            print(f"❌ Ошибка получения команд: {e}")
            return False


async def main():
    """Главная функция"""
    print("NASTROYKA KOMAND TELEGRAM BOTA")
    print("=" * 50)
    
    # Получаем информацию о боте
    print("\n1. Poluchenie informacii o bote...")
    await get_bot_info()
    
    # Показываем текущие команды
    print("\n2. Tekushchie komandy bota...")
    await get_current_commands()
    
    # Устанавливаем новые команды
    print("\n3. Ustanovka komand...")
    success = await setup_bot_commands()
    
    if success:
        print("\nKomandy uspeshno ustanovleny!")
        print("\nTeper' v Telegram:")
        print("  1. Otkroyte chat s botom")
        print("  2. Nazhmite na knopku menu ryadom s polem vvoda")
        print("  3. Vyberite nuzhnuyu komandu iz spiska")
        print("\nKomandy takzhe mozhno vvodit' vruchnuyu: /analyze, /status i t.d.")
    else:
        print("\nOshibka ustanovki komand!")
        print("Prover'te nastroyki v .env fayle")
    
    return 0 if success else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
