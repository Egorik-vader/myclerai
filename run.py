# run.py - ИСПРАВЛЕННЫЙ (бот + сайт)
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
from app.handlers import router

# ============================================================
# HTML СТРАНИЦА ДЛЯ САЙТА (встроена)
# ============================================================

HTML_PAGE = '''<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>OSINT Search</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #0a0a0f; color: #e0e0e0; min-height: 100vh; }
        .container { max-width: 700px; margin: 0 auto; padding: 40px 20px; }
        .header { text-align: center; padding: 40px 0; border-bottom: 1px solid #1a1a2e; }
        .header h1 { font-size: 38px; background: linear-gradient(135deg, #00d4ff, #7b2ffc); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin-bottom: 10px; }
        .header p { color: #888; font-size: 16px; }
        .search-box { background: #12121f; border-radius: 16px; padding: 30px; margin-top: 30px; border: 1px solid #1a1a2e; }
        .search-type { display: flex; gap: 10px; margin-bottom: 20px; flex-wrap: wrap; }
        .search-type button { flex: 1; padding: 10px 14px; border: 2px solid #1a1a2e; background: transparent; color: #888; border-radius: 10px; cursor: pointer; font-size: 13px; transition: all 0.3s; min-width: 70px; }
        .search-type button:hover { border-color: #00d4ff; color: #fff; }
        .search-type button.active { border-color: #7b2ffc; color: #fff; background: rgba(123, 47, 252, 0.1); }
        .search-input { display: flex; gap: 12px; }
        .search-input input { flex: 1; padding: 16px 20px; border-radius: 12px; border: 2px solid #1a1a2e; background: #0a0a12; color: #fff; font-size: 16px; outline: none; transition: border-color 0.3s; }
        .search-input input:focus { border-color: #7b2ffc; }
        .search-input input::placeholder { color: #555; }
        .search-input button { padding: 16px 40px; border: none; border-radius: 12px; background: linear-gradient(135deg, #00d4ff, #7b2ffc); color: #fff; font-size: 16px; font-weight: 600; cursor: pointer; transition: transform 0.2s; }
        .search-input button:hover { transform: scale(1.02); }
        .search-input button:disabled { opacity: 0.5; cursor: not-allowed; transform: none; }
        .results { margin-top: 30px; }
        .result-card { background: #12121f; border-radius: 12px; padding: 16px 20px; margin-bottom: 10px; border: 1px solid #1a1a2e; animation: fadeIn 0.3s ease; display: flex; gap: 12px; align-items: flex-start; }
        .result-card .key { color: #7b2ffc; font-weight: 600; font-size: 14px; min-width: 120px; flex-shrink: 0; }
        .result-card .value { color: #e0e0e0; font-size: 15px; word-break: break-all; }
        .result-card .value a { color: #00d4ff; text-decoration: none; }
        .result-card .value a:hover { text-decoration: underline; }
        .loading { text-align: center; padding: 60px 20px; color: #888; font-size: 18px; }
        .loading .spinner { width: 40px; height: 40px; border: 4px solid #1a1a2e; border-top-color: #7b2ffc; border-radius: 50%; animation: spin 0.8s linear infinite; margin: 0 auto 20px; }
        @keyframes spin { to { transform: rotate(360deg); } }
        @keyframes fadeIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
        .error { background: rgba(255,50,50,0.1); border: 1px solid #ff3333; color: #ff5555; padding: 16px 20px; border-radius: 12px; margin-top: 20px; }
        .no-results { text-align: center; color: #666; padding: 40px 20px; font-size: 16px; }
        #resultCount { background: #12121f; border-radius: 8px; padding: 10px 16px; margin-top: 20px; color: #888; font-size: 14px; border: 1px solid #1a1a2e; display: none; }
        .record-block { background: #0a0a12; border-radius: 10px; padding: 16px; margin-bottom: 12px; border-left: 3px solid #7b2ffc; }
        .record-title { color: #7b2ffc; font-weight: 600; font-size: 13px; margin-bottom: 8px; }
        @media (max-width: 600px) { .container { padding: 20px 12px; } .header h1 { font-size: 28px; } .search-type button { font-size: 11px; padding: 8px 6px; } .search-input { flex-direction: column; } .search-input button { padding: 14px; } .result-card { flex-direction: column; gap: 4px; } .result-card .key { min-width: auto; } }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔍 OSINT Search</h1>
            <p>Поиск информации в открытых источниках</p>
        </div>
        
        <div class="search-box">
            <div class="search-type" id="searchType">
                <button class="active" data-type="phone">📱 Телефон</button>
                <button data-type="russian_db">🇷🇺 РФ База</button>
                <button data-type="inn">🆔 ИНН</button>
                <button data-type="email">📧 Email</button>
                <button data-type="vk">📘 VK</button>
                <button data-type="ip">🌐 IP</button>
                <button data-type="whois">🌍 WHOIS</button>
            </div>
            
            <div class="search-input">
                <input type="text" id="queryInput" placeholder="Введите данные для поиска..." />
                <button id="searchBtn">🔍 Найти</button>
            </div>
        </div>
        
        <div id="resultCount"></div>
        <div class="results" id="resultsContainer">
            <div class="loading">
                <div class="spinner"></div>
                <p>Введите запрос для поиска</p>
            </div>
        </div>
    </div>
    
    <script>
        const searchType = document.getElementById('searchType');
        const queryInput = document.getElementById('queryInput');
        const searchBtn = document.getElementById('searchBtn');
        const resultsContainer = document.getElementById('resultsContainer');
        const resultCount = document.getElementById('resultCount');

        let currentType = 'phone';

        const placeholders = {
            phone: '+375331234567 или +79123456789',
            russian_db: '79123456789',
            inn: '1234567890',
            email: 'example@mail.com',
            vk: '123456789',
            ip: '192.168.1.1',
            whois: 'example.com'
        };

        searchType.addEventListener('click', (e) => {
            const btn = e.target.closest('button');
            if (!btn) return;
            searchType.querySelectorAll('button').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            currentType = btn.dataset.type;
            queryInput.placeholder = placeholders[currentType] || 'Введите данные...';
            queryInput.focus();
        });

        async function performSearch() {
            const query = queryInput.value.trim();
            if (!query) {
                resultsContainer.innerHTML = '<div class="no-results">Введите запрос</div>';
                resultCount.style.display = 'none';
                return;
            }
            
            resultsContainer.innerHTML = '<div class="loading"><div class="spinner"></div><p>Поиск...</p></div>';
            resultCount.style.display = 'none';
            searchBtn.disabled = true;
            
            try {
                const response = await fetch('/search', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ type: currentType, query: query })
                });
                
                const data = await response.json();
                
                if (data.error) {
                    resultsContainer.innerHTML = `<div class="error">❌ ${data.error}</div>`;
                    return;
                }
                
                if (data["✅ Найдено записей"] && data["📋 Записи"]) {
                    const records = data["📋 Записи"];
                    resultCount.textContent = `🔍 Найдено записей: ${data["✅ Найдено записей"]}`;
                    resultCount.style.display = 'block';
                    let html = '';
                    records.forEach((record, index) => {
                        html += `<div class="record-block"><div class="record-title">📋 Запись #${index + 1}</div>`;
                        for (const [key, value] of Object.entries(record)) {
                            if (value) {
                                html += `<div class="result-card"><span class="key">${key}</span><span class="value">${value}</span></div>`;
                            }
                        }
                        html += '</div>';
                    });
                    resultsContainer.innerHTML = html;
                    return;
                }
                
                const entries = Object.entries(data).filter(([k, v]) => v && String(v).trim());
                
                if (entries.length === 0) {
                    resultsContainer.innerHTML = '<div class="no-results">😕 Ничего не найдено</div>';
                    return;
                }
                
                let html = '';
                for (const [key, value] of entries) {
                    let displayValue = String(value);
                    if (displayValue.startsWith('http')) {
                        displayValue = `<a href="${displayValue}" target="_blank">${displayValue}</a>`;
                    }
                    html += `<div class="result-card"><span class="key">${key}</span><span class="value">${displayValue}</span></div>`;
                }
                resultsContainer.innerHTML = html;
                
            } catch (error) {
                resultsContainer.innerHTML = `<div class="error">❌ Ошибка: ${error.message}</div>`;
            } finally {
                searchBtn.disabled = false;
            }
        }

        searchBtn.addEventListener('click', performSearch);
        queryInput.addEventListener('keypress', (e) => { if (e.key === 'Enter') performSearch(); });
        queryInput.focus();
    </script>
</body>
</html>'''

# ============================================================
# ОБРАБОТЧИК ВЕБ-ЗАПРОСОВ
# ============================================================

async def handle(request):
    """Главная страница - отдает HTML интерфейс"""
    return web.Response(text=HTML_PAGE, content_type='text/html')

async def handle_search(request):
    """Обработка поисковых запросов через AJAX"""
    try:
        data = await request.json()
        search_type = data.get('type', '')
        query = data.get('query', '')
        
        if not query:
            return web.json_response({'error': 'Введите запрос'})
        
        # Импортируем функции поиска
        from osint_functions import (
            search_phone_full,
            search_inn,
            search_email,
            search_vk,
            search_ip,
            search_whois,
            search_russian_db
        )
        
        # Выбираем функцию
        if search_type == 'phone':
            result = await search_phone_full(query)
        elif search_type == 'russian_db':
            result = await search_russian_db(query)
        elif search_type == 'inn':
            result = await search_inn(query)
        elif search_type == 'email':
            result = await search_email(query)
        elif search_type == 'vk':
            result = await search_vk(query)
        elif search_type == 'ip':
            result = await search_ip(query)
        elif search_type == 'whois':
            result = await search_whois(query)
        else:
            return web.json_response({'error': 'Неизвестный тип поиска'})
        
        # Очищаем от None
        result = {k: v for k, v in result.items() if v is not None}
        
        return web.json_response(result)
        
    except Exception as e:
        return web.json_response({'error': str(e)})

async def start_web_server():
    """Запуск веб-сервера"""
    app = web.Application()
    app.router.add_get("/", handle)
    app.router.add_post("/search", handle_search)
    
    runner = web.AppRunner(app)
    await runner.setup()
    
    port = int(os.getenv("PORT", 10000))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    print(f"🌐 Веб-сайт запущен на порту {port}")
    print(f"🔗 Открой: http://localhost:{port}")

# ============================================================
# БОТ
# ============================================================

bot = Bot(token=TOKEN)
dp = Dispatcher()
dp.include_router(router)

async def main():
    """Запуск бота и веб-сервера одновременно"""
    await start_web_server()
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("⏹️ Выход...")
