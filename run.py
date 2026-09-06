# run.py - Бот + Красивый сайт (только нужные кнопки: Телефон, ИНН, Email, VK, IP, WHOIS)
import aiogram
import logging
from aiogram import Bot, Dispatcher
import asyncio
import os
import aiohttp
import re

# Принудительно используем ThreadedResolver вместо aiodns
try:
    aiohttp.resolver.DefaultResolver = aiohttp.resolver.ThreadedResolver
except:
    pass

from aiohttp import web
from config import TOKEN
from app.handlers import router

# ============================================================
# HTML СТРАНИЦА (ТОЛЬКО НУЖНЫЕ КНОПКИ)
# ============================================================

HTML_PAGE = '''<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Wekness Tool - OSINT Search</title>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&display=swap');
        
        * { margin: 0; padding: 0; box-sizing: border-box; }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: #0a0a0f;
            color: #e0e0e0;
            min-height: 100vh;
            background-image: 
                radial-gradient(ellipse at 10% 20%, rgba(123, 47, 252, 0.05) 0%, transparent 50%),
                radial-gradient(ellipse at 90% 80%, rgba(0, 212, 255, 0.05) 0%, transparent 50%);
        }
        
        .container { max-width: 750px; margin: 0 auto; padding: 30px 20px; }
        
        .header {
            text-align: center;
            padding: 30px 0 25px;
            border-bottom: 2px solid rgba(123, 47, 252, 0.2);
            position: relative;
        }
        
        .header::after {
            content: '';
            position: absolute;
            bottom: -2px;
            left: 50%;
            transform: translateX(-50%);
            width: 200px;
            height: 2px;
            background: linear-gradient(90deg, transparent, #7b2ffc, #00d4ff, transparent);
        }
        
        .logo-container {
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 20px;
            margin-bottom: 10px;
        }
        
        .logo {
            width: 70px;
            height: 70px;
            border-radius: 50%;
            background: linear-gradient(135deg, #7b2ffc, #00d4ff);
            padding: 3px;
            animation: pulse 2s ease-in-out infinite;
        }
        
        .logo img {
            width: 100%;
            height: 100%;
            border-radius: 50%;
            object-fit: cover;
            background: #0a0a0f;
        }
        
        @keyframes pulse {
            0%, 100% { transform: scale(1); box-shadow: 0 0 20px rgba(123, 47, 252, 0.3); }
            50% { transform: scale(1.03); box-shadow: 0 0 40px rgba(123, 47, 252, 0.5); }
        }
        
        .header h1 {
            font-family: 'Orbitron', 'Segoe UI', sans-serif;
            font-size: 32px;
            font-weight: 900;
            background: linear-gradient(135deg, #7b2ffc, #00d4ff);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            letter-spacing: 2px;
        }
        
        .header h1 .tool {
            color: #00d4ff;
            -webkit-text-fill-color: #00d4ff;
        }
        
        .header .subtitle {
            color: #666;
            font-size: 14px;
            margin-top: 5px;
            letter-spacing: 1px;
        }
        
        .header .subtitle span {
            color: #7b2ffc;
        }
        
        .download-badge {
            display: inline-block;
            margin-top: 12px;
            padding: 8px 24px;
            background: linear-gradient(135deg, rgba(123, 47, 252, 0.2), rgba(0, 212, 255, 0.2));
            border: 1px solid rgba(123, 47, 252, 0.3);
            border-radius: 20px;
            color: #aaa;
            font-size: 13px;
            transition: all 0.3s;
            text-decoration: none;
        }
        
        .download-badge:hover {
            background: linear-gradient(135deg, rgba(123, 47, 252, 0.3), rgba(0, 212, 255, 0.3));
            border-color: #7b2ffc;
            color: #fff;
            transform: translateY(-2px);
            box-shadow: 0 5px 25px rgba(123, 47, 252, 0.2);
        }
        
        .search-box {
            background: rgba(18, 18, 31, 0.9);
            border-radius: 16px;
            padding: 30px;
            margin-top: 30px;
            border: 1px solid rgba(26, 26, 46, 0.8);
            backdrop-filter: blur(10px);
            box-shadow: 0 10px 50px rgba(0, 0, 0, 0.5);
        }
        
        .search-type {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 8px;
            margin-bottom: 20px;
        }
        
        .search-type button {
            padding: 12px 8px;
            border: 2px solid rgba(26, 26, 46, 0.8);
            background: rgba(10, 10, 18, 0.8);
            color: #666;
            border-radius: 10px;
            cursor: pointer;
            font-size: 13px;
            font-weight: 600;
            transition: all 0.3s ease;
            letter-spacing: 0.5px;
        }
        
        .search-type button:hover {
            border-color: rgba(123, 47, 252, 0.4);
            color: #aaa;
            transform: translateY(-2px);
        }
        
        .search-type button.active {
            border-color: #7b2ffc;
            color: #fff;
            background: rgba(123, 47, 252, 0.15);
            box-shadow: 0 0 30px rgba(123, 47, 252, 0.1);
        }
        
        .search-type button .icon { margin-right: 6px; }
        
        .search-input {
            display: flex;
            gap: 12px;
        }
        
        .search-input input {
            flex: 1;
            padding: 16px 20px;
            border-radius: 12px;
            border: 2px solid rgba(26, 26, 46, 0.8);
            background: rgba(10, 10, 18, 0.8);
            color: #fff;
            font-size: 15px;
            outline: none;
            transition: all 0.3s;
        }
        
        .search-input input:focus {
            border-color: #7b2ffc;
            box-shadow: 0 0 30px rgba(123, 47, 252, 0.1);
        }
        
        .search-input input::placeholder { color: #444; }
        .search-input input.error { border-color: #ff3333; }
        .search-input input.success { border-color: #00ff88; }
        
        .search-input button {
            padding: 16px 35px;
            border: none;
            border-radius: 12px;
            background: linear-gradient(135deg, #7b2ffc, #00d4ff);
            color: #fff;
            font-size: 15px;
            font-weight: 700;
            cursor: pointer;
            transition: all 0.3s;
            letter-spacing: 0.5px;
            white-space: nowrap;
        }
        
        .search-input button:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 30px rgba(123, 47, 252, 0.3);
        }
        
        .search-input button:disabled {
            opacity: 0.5;
            cursor: not-allowed;
            transform: none;
        }
        
        .validation-msg {
            margin-top: 12px;
            font-size: 13px;
            padding: 8px 16px;
            border-radius: 8px;
            display: none;
        }
        
        .validation-msg.error {
            display: block;
            color: #ff5555;
            background: rgba(255, 50, 50, 0.1);
            border: 1px solid rgba(255, 50, 50, 0.2);
        }
        
        .validation-msg.success {
            display: block;
            color: #00ff88;
            background: rgba(0, 255, 136, 0.05);
            border: 1px solid rgba(0, 255, 136, 0.1);
        }
        
        .results { margin-top: 30px; }
        
        .result-card {
            background: rgba(18, 18, 31, 0.9);
            border-radius: 12px;
            padding: 16px 20px;
            margin-bottom: 10px;
            border: 1px solid rgba(26, 26, 46, 0.8);
            animation: fadeIn 0.3s ease;
            display: flex;
            gap: 12px;
            align-items: flex-start;
            backdrop-filter: blur(5px);
        }
        
        .result-card .key {
            color: #7b2ffc;
            font-weight: 600;
            font-size: 13px;
            min-width: 110px;
            flex-shrink: 0;
        }
        
        .result-card .value {
            color: #e0e0e0;
            font-size: 14px;
            word-break: break-all;
        }
        
        .result-card .value a {
            color: #00d4ff;
            text-decoration: none;
        }
        
        .result-card .value a:hover { text-decoration: underline; }
        
        .loading {
            text-align: center;
            padding: 60px 20px;
            color: #555;
            font-size: 16px;
        }
        
        .loading .spinner {
            width: 40px;
            height: 40px;
            border: 4px solid rgba(26, 26, 46, 0.8);
            border-top-color: #7b2ffc;
            border-radius: 50%;
            animation: spin 0.8s linear infinite;
            margin: 0 auto 20px;
        }
        
        @keyframes spin { to { transform: rotate(360deg); } }
        @keyframes fadeIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
        
        .error {
            background: rgba(255, 50, 50, 0.1);
            border: 1px solid rgba(255, 50, 50, 0.2);
            color: #ff5555;
            padding: 16px 20px;
            border-radius: 12px;
            margin-top: 20px;
        }
        
        .no-results {
            text-align: center;
            color: #444;
            padding: 40px 20px;
            font-size: 15px;
        }
        
        #resultCount {
            background: rgba(18, 18, 31, 0.9);
            border-radius: 8px;
            padding: 10px 16px;
            margin-top: 20px;
            color: #666;
            font-size: 13px;
            border: 1px solid rgba(26, 26, 46, 0.8);
            display: none;
        }
        
        .record-block {
            background: rgba(10, 10, 18, 0.8);
            border-radius: 10px;
            padding: 16px;
            margin-bottom: 12px;
            border-left: 3px solid #7b2ffc;
        }
        
        .record-title {
            color: #7b2ffc;
            font-weight: 600;
            font-size: 12px;
            margin-bottom: 8px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        
        .footer {
            text-align: center;
            padding: 30px 0 20px;
            color: #333;
            font-size: 12px;
            border-top: 1px solid rgba(26, 26, 46, 0.5);
            margin-top: 30px;
        }
        
        .footer a {
            color: #555;
            text-decoration: none;
        }
        
        .footer a:hover { color: #7b2ffc; }
        
        @media (max-width: 600px) {
            .container { padding: 15px 12px; }
            .header h1 { font-size: 22px; }
            .logo { width: 50px; height: 50px; }
            .search-type { grid-template-columns: repeat(2, 1fr); }
            .search-type button { font-size: 11px; padding: 10px 6px; }
            .search-input { flex-direction: column; }
            .search-input button { padding: 14px; }
            .result-card { flex-direction: column; gap: 4px; }
            .result-card .key { min-width: auto; }
            .logo-container { gap: 12px; }
        }
    </style>
</head>
<body>
    <div class="container">
        <!-- HEADER -->
        <div class="header">
            <div class="logo-container">
                <div class="logo">
                    <img src="https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRLj8GYGEmx3A6wfcAAWcP8kkrsoM02IydeP4GVn-aY_g&s=10" alt="Wekness Tool Logo">
                </div>
                <div>
                    <h1>Wekness <span class="tool">Tool</span></h1>
                    <div class="subtitle">🔍 <span>OSINT</span> Search Engine</div>
                </div>
            </div>
            <a href="https://trashbox.ru/topics/216477/wekness-tool" class="download-badge" target="_blank">
                ⬇️ Скачать Wekness Tool
            </a>
        </div>
        
        <!-- SEARCH -->
        <div class="search-box">
            <div class="search-type" id="searchType">
                <button class="active" data-type="phone"><span class="icon">📲</span> Телефон</button>
                <button data-type="inn"><span class="icon">🆔</span> ИНН</button>
                <button data-type="email"><span class="icon">📧</span> E-mail</button>
                <button data-type="vk"><span class="icon">🔵</span> VK</button>
                <button data-type="ip"><span class="icon">🏙️</span> IP</button>
                <button data-type="whois"><span class="icon">🌍</span> WHOIS</button>
            </div>
            
            <div class="search-input">
                <input type="text" id="queryInput" placeholder="Введите данные для поиска..." />
                <button id="searchBtn">🔍 Найти</button>
            </div>
            
            <div class="validation-msg" id="validationMsg"></div>
        </div>
        
        <div id="resultCount"></div>
        <div class="results" id="resultsContainer">
            <div class="loading">
                <div class="spinner"></div>
                <p>Введите запрос для поиска</p>
            </div>
        </div>
        
        <div class="footer">
            <p>Wekness Tool &copy; 2026 | <a href="https://trashbox.ru/topics/216477/wekness-tool" target="_blank">Скачать</a></p>
        </div>
    </div>
    
    <script>
        const searchType = document.getElementById('searchType');
        const queryInput = document.getElementById('queryInput');
        const searchBtn = document.getElementById('searchBtn');
        const resultsContainer = document.getElementById('resultsContainer');
        const resultCount = document.getElementById('resultCount');
        const validationMsg = document.getElementById('validationMsg');

        let currentType = 'phone';

        const placeholders = {
            phone: '+375331234567 или 89123456789',
            inn: '1234567890',
            email: 'example@mail.com',
            vk: '123456789',
            ip: '192.168.1.1',
            whois: 'example.com'
        };

        // Валидация телефона (РФ и РБ)
        function validatePhone(phone) {
            const clean = phone.replace(/[^\d+]/g, '');
            if (!clean) return { valid: false, msg: '❌ Введите номер телефона' };
            
            let num = clean;
            if (num.startsWith('+')) num = num.slice(1);
            
            // РФ: 7 или 8 + 10 цифр
            const ruPattern = /^(7|8)\d{10}$/;
            // РБ: 375 + 9 цифр
            const byPattern = /^375\d{9}$/;
            
            if (ruPattern.test(num)) return { valid: true, msg: '✅ Российский номер' };
            if (byPattern.test(num)) return { valid: true, msg: '✅ Белорусский номер' };
            
            if (num.length < 10) return { valid: false, msg: '❌ Слишком короткий номер' };
            if (num.length > 12) return { valid: false, msg: '❌ Слишком длинный номер' };
            
            return { valid: false, msg: '❌ Неверный формат. Используйте РФ (7/8...) или РБ (375...)' };
        }

        // Выбор типа
        searchType.addEventListener('click', (e) => {
            const btn = e.target.closest('button');
            if (!btn) return;
            searchType.querySelectorAll('button').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            currentType = btn.dataset.type;
            queryInput.placeholder = placeholders[currentType] || 'Введите данные...';
            validationMsg.className = 'validation-msg';
            validationMsg.textContent = '';
            queryInput.classList.remove('error', 'success');
            queryInput.focus();
        });

        // Валидация при вводе (только для телефона)
        queryInput.addEventListener('input', () => {
            if (currentType === 'phone') {
                const result = validatePhone(queryInput.value);
                if (result.valid) {
                    validationMsg.className = 'validation-msg success';
                    validationMsg.textContent = result.msg;
                    queryInput.classList.remove('error');
                    queryInput.classList.add('success');
                } else if (queryInput.value.length > 0) {
                    validationMsg.className = 'validation-msg error';
                    validationMsg.textContent = result.msg;
                    queryInput.classList.remove('success');
                    queryInput.classList.add('error');
                } else {
                    validationMsg.className = 'validation-msg';
                    validationMsg.textContent = '';
                    queryInput.classList.remove('error', 'success');
                }
            }
        });

        async function performSearch() {
            const query = queryInput.value.trim();
            if (!query) {
                resultsContainer.innerHTML = '<div class="no-results">Введите запрос</div>';
                resultCount.style.display = 'none';
                return;
            }
            
            // Валидация для телефона
            if (currentType === 'phone') {
                const result = validatePhone(query);
                if (!result.valid) {
                    validationMsg.className = 'validation-msg error';
                    validationMsg.textContent = result.msg;
                    queryInput.classList.add('error');
                    return;
                }
            }
            
            resultsContainer.innerHTML = '<div class="loading"><div class="spinner"></div><p>🔍 Поиск данных...</p></div>';
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
# ОБРАБОТЧИКИ ВЕБ-ЗАПРОСОВ
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
            search_whois
        )
        
        # Выбираем функцию
        if search_type == 'phone':
            result = await search_phone_full(query)
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
    print(f"🌐 Wekness Tool запущен на порту {port}")
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
