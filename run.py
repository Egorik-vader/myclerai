import aiogram
import logging
from aiogram import Bot, Dispatcher
import asyncio
import os
import aiohttp

# Принудительно используем ThreadedResolver вместо aiodns
try:
    aiohttp.resolver.DefaultResolver = aiohttp.resolver.ThreadedResolver
except:
    pass

from aiohttp import web
from config import TOKEN
from app.handlers import router  # только один раз

async def handle(request):
    return web.Response(text="Bot is live")

async def start_web_server():
    app = web.Application()
    app.router.add_get("/", handle)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.getenv("PORT", 10000))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    print(f"Web server started on port {port}")

bot = Bot(token=TOKEN)
dp = Dispatcher()

async def main():
    # Подключаем роутер только один раз
    dp.include_router(router)
    await start_web_server()
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Exit")
    # Убираем дублирующий вызов asyncio.run(main())
