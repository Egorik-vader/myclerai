import asyncio
import os
import aiohttp
from aiohttp import web
from config import TOKEN

# ============================================================
# HTML СТРАНИЦА
# ============================================================

HTML_PAGE = '''<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Wekness Tool — OSINT</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, sans-serif;
            background: #0a0a12;
            color: #e8e8e8;
            padding: 20px;
            line-height: 1.6;
            min-height: 100vh;
        }
        body::before {
            content: '';
            position: fixed;
            top: -20%;
            right: -10%;
            width: 600px;
            height: 600px;
            background: radial-gradient(circle, rgba(124, 58, 237, 0.06), transparent 70%);
            pointer-events: none;
            z-index: -1;
        }
        .container { max-width: 860px; margin: 0 auto; }

        /* HEADER */
        .header {
            background: linear-gradient(135deg, rgba(20, 20, 40, 0.92), rgba(40, 20, 80, 0.6));
            backdrop-filter: blur(20px);
            border-radius: 24px;
            padding: 28px 32px;
            margin-bottom: 24px;
            border: 1px solid rgba(255,255,255,0.04);
            text-align: center;
            position: relative;
            overflow: hidden;
        }
        .header::before {
            content: '';
            position: absolute;
            top: -50%;
            right: -20%;
            width: 300px;
            height: 300px;
            background: radial-gradient(circle, rgba(124, 58, 237, 0.08), transparent 70%);
            pointer-events: none;
        }
        .header-logo {
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 16px;
            margin-bottom: 4px;
            position: relative;
            z-index: 1;
        }
        .header-logo img {
            width: 64px;
            height: 64px;
            border-radius: 16px;
            border: 1px solid rgba(255,255,255,0.06);
            box-shadow: 0 4px 20px rgba(124, 58, 237, 0.15);
            object-fit: cover;
        }
        .header-logo .logo-text {
            font-size: 32px;
            font-weight: 800;
            letter-spacing: -0.5px;
        }
        .header-logo .logo-text span {
            background: linear-gradient(135deg, #a78bfa, #7c3aed);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        .header .sub {
            color: rgba(255,255,255,0.3);
            font-size: 14px;
            position: relative;
            z-index: 1;
        }
        .header .query-box {
            display: inline-block;
            margin-top: 12px;
            background: rgba(124, 58, 237, 0.08);
            border: 1px solid rgba(124, 58, 237, 0.1);
            padding: 8px 24px;
            border-radius: 40px;
            font-size: 15px;
            font-weight: 500;
            color: #a78bfa;
            position: relative;
            z-index: 1;
        }
        .support-links {
            display: flex;
            justify-content: center;
            gap: 12px;
            margin-top: 14px;
            position: relative;
            z-index: 1;
            flex-wrap: wrap;
        }
        .support-btn {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            color: #fff;
            text-decoration: none;
            padding: 8px 20px;
            border-radius: 40px;
            font-size: 13px;
            font-weight: 600;
            transition: 0.3s;
        }
        .support-btn.boosty {
            background: linear-gradient(135deg, #f59e0b, #d97706);
            box-shadow: 0 4px 20px rgba(245, 158, 11, 0.15);
        }
        .support-btn.boosty:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 30px rgba(245, 158, 11, 0.25);
        }
        .support-btn.donate-alerts {
            background: linear-gradient(135deg, #7c3aed, #6d28d9);
            box-shadow: 0 4px 20px rgba(124, 58, 237, 0.15);
        }
        .support-btn.donate-alerts:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 30px rgba(124, 58, 237, 0.25);
        }

        /* SEARCH */
        .search-box {
            background: rgba(255,255,255,0.02);
            border-radius: 24px;
            padding: 24px 28px;
            margin-bottom: 24px;
            border: 1px solid rgba(255,255,255,0.04);
            backdrop-filter: blur(10px);
        }
        .search-type {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 8px;
            margin-bottom: 16px;
        }
        .search-type button {
            padding: 12px 8px;
            border: 2px solid rgba(255,255,255,0.04);
            background: rgba(10, 10, 18, 0.6);
            color: rgba(255,255,255,0.4);
            border-radius: 12px;
            cursor: pointer;
            font-size: 13px;
            font-weight: 600;
            transition: all 0.3s ease;
            letter-spacing: 0.3px;
        }
        .search-type button:hover {
            border-color: rgba(124, 58, 237, 0.3);
            color: rgba(255,255,255,0.7);
            transform: translateY(-1px);
        }
        .search-type button.active {
            border-color: #7c3aed;
            color: #a78bfa;
            background: rgba(124, 58, 237, 0.08);
            box-shadow: 0 0 30px rgba(124, 58, 237, 0.05);
        }
        .search-type button .icon { margin-right: 6px; }
        .search-input {
            display: flex;
            gap: 12px;
        }
        .search-input input {
            flex: 1;
            padding: 16px 20px;
            border-radius: 14px;
            border: 2px solid rgba(255,255,255,0.04);
            background: rgba(10, 10, 18, 0.6);
            color: #e8e8e8;
            font-size: 16px;
            outline: none;
            transition: all 0.3s;
        }
        .search-input input:focus {
            border-color: #7c3aed;
            box-shadow: 0 0 30px rgba(124, 58, 237, 0.05);
        }
        .search-input input::placeholder { color: rgba(255,255,255,0.15); }
        .search-input input.error { border-color: #f87171; }
        .search-input input.success { border-color: #34d399; }
        .search-input button {
            padding: 16px 40px;
            border: none;
            border-radius: 14px;
            background: linear-gradient(135deg, #7c3aed, #6d28d9);
            color: #fff;
            font-size: 16px;
            font-weight: 700;
            cursor: pointer;
            transition: all 0.3s;
            letter-spacing: 0.5px;
            white-space: nowrap;
        }
        .search-input button:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 30px rgba(124, 58, 237, 0.3);
        }
        .search-input button:disabled { opacity: 0.5; cursor: not-allowed; transform: none; }
        .validation-msg {
            margin-top: 12px;
            font-size: 13px;
            padding: 8px 16px;
            border-radius: 8px;
            display: none;
        }
        .validation-msg.error {
            display: block;
            color: #f87171;
            background: rgba(248, 113, 113, 0.06);
            border: 1px solid rgba(248, 113, 113, 0.1);
        }
        .validation-msg.success {
            display: block;
            color: #34d399;
            background: rgba(52, 211, 153, 0.04);
            border: 1px solid rgba(52, 211, 153, 0.06);
        }

        /* STATS */
        .stats {
            display: flex;
            justify-content: space-around;
            gap: 12px;
            margin-bottom: 24px;
            flex-wrap: wrap;
        }
        .stats .stat-card {
            background: rgba(255,255,255,0.02);
            border-radius: 16px;
            padding: 14px 24px;
            text-align: center;
            border: 1px solid rgba(255,255,255,0.04);
            transition: 0.3s;
            flex: 1;
            min-width: 100px;
        }
        .stats .stat-card:hover {
            border-color: rgba(124, 58, 237, 0.08);
            background: rgba(255,255,255,0.04);
        }
        .stats .stat-number {
            font-size: 28px;
            font-weight: 800;
            color: #a78bfa;
            display: block;
            letter-spacing: -0.5px;
        }
        .stats .stat-label {
            font-size: 12px;
            color: rgba(255,255,255,0.3);
            font-weight: 400;
        }

        /* CARDS */
        .card {
            background: rgba(255,255,255,0.04);
            border-radius: 24px;
            margin-bottom: 18px;
            border: 1px solid rgba(255,255,255,0.06);
            overflow: hidden;
            transition: all 0.3s;
            box-shadow: 0 4px 24px rgba(0,0,0,0.2);
        }
        .card:hover {
            transform: translateY(-3px);
            border-color: rgba(124, 58, 237, 0.15);
            box-shadow: 0 8px 32px rgba(0,0,0,0.3);
        }
        .card-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 14px 20px;
            background: rgba(255,255,255,0.02);
        }
        .card-number {
            font-weight: 600;
            font-size: 14px;
            color: rgba(255,255,255,0.3);
        }
        .copy-btn {
            background: rgba(255,255,255,0.06);
            border: 1px solid rgba(255,255,255,0.06);
            color: rgba(255,255,255,0.5);
            width: 32px;
            height: 32px;
            border-radius: 50%;
            font-size: 16px;
            cursor: pointer;
            transition: 0.3s;
            display: flex;
            align-items: center;
            justify-content: center;
            font-family: inherit;
        }
        .copy-btn:hover {
            background: rgba(124, 58, 237, 0.12);
            border-color: rgba(124, 58, 237, 0.15);
            color: #a78bfa;
        }
        .card-body {
            padding: 8px 20px 18px 20px;
        }
        .field {
            display: flex;
            justify-content: space-between;
            padding: 8px 0;
            gap: 16px;
            align-items: baseline;
            border-bottom: 1px solid rgba(255,255,255,0.03);
        }
        .field:last-child { border-bottom: none; }
        .field-label {
            color: rgba(255,255,255,0.5);
            font-size: 16px;
            white-space: nowrap;
            font-weight: 400;
        }
        .field-value {
            color: #e8e8e8;
            font-size: 17px;
            text-align: right;
            word-break: break-word;
            max-width: 60%;
            font-weight: 500;
        }
        .value-email { color: #a78bfa !important; }
        .value-phone { color: #34d399 !important; }
        .value-ip { color: #fbbf24 !important; }
        .value-status { color: #f87171 !important; font-weight: 600 !important; }
        .value-name { color: #e8e8e8 !important; font-weight: 600 !important; }
        .value-link { color: #60a5fa !important; text-decoration: none; }
        .value-link:hover { text-decoration: underline; }

        .loading {
            text-align: center;
            padding: 60px 20px;
            color: rgba(255,255,255,0.2);
        }
        .loading .spinner {
            width: 40px;
            height: 40px;
            border: 4px solid rgba(255,255,255,0.04);
            border-top-color: #7c3aed;
            border-radius: 50%;
            animation: spin 0.8s linear infinite;
            margin: 0 auto 20px;
        }
        @keyframes spin { to { transform: rotate(360deg); } }
        @keyframes fadeIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }

        .error {
            background: rgba(248, 113, 113, 0.06);
            border: 1px solid rgba(248, 113, 113, 0.1);
            color: #f87171;
            padding: 16px 20px;
            border-radius: 16px;
            margin-top: 20px;
        }
        .no-results {
            text-align: center;
            color: rgba(255,255,255,0.15);
            padding: 60px 20px;
            font-size: 16px;
        }
        #resultCount {
            background: rgba(255,255,255,0.02);
            border-radius: 12px;
            padding: 10px 16px;
            margin-top: 16px;
            color: rgba(255,255,255,0.3);
            font-size: 13px;
            border: 1px solid rgba(255,255,255,0.03);
            display: none;
        }

        .toast {
            position: fixed;
            bottom: 30px;
            left: 50%;
            transform: translateX(-50%) translateY(20px);
            background: rgba(20, 20, 40, 0.95);
            backdrop-filter: blur(20px);
            padding: 14px 28px;
            border-radius: 16px;
            border: 1px solid rgba(255,255,255,0.06);
            color: #e8e8e8;
            font-size: 15px;
            font-weight: 500;
            opacity: 0;
            transition: all 0.4s ease;
            pointer-events: none;
            z-index: 999;
            box-shadow: 0 8px 40px rgba(0,0,0,0.4);
            display: flex;
            align-items: center;
            gap: 10px;
        }
        .toast.show { opacity: 1; transform: translateX(-50%) translateY(0); pointer-events: auto; }
        .toast.error { border-color: rgba(248, 113, 113, 0.15); }

        .footer {
            text-align: center;
            margin-top: 28px;
            padding-top: 20px;
            border-top: 1px solid rgba(255,255,255,0.03);
            color: rgba(255,255,255,0.08);
            font-size: 12px;
        }
        .footer a { color: rgba(255,255,255,0.1); text-decoration: none; transition: 0.2s; }
        .footer a:hover { color: #a78bfa; }

        @media (max-width: 768px) {
            body { padding: 12px; }
            .header { padding: 20px 16px; }
            .header-logo .logo-text { font-size: 24px; }
            .header-logo img { width: 48px; height: 48px; }
            .header .query-box { font-size: 13px; padding: 6px 18px; }
            .search-type { grid-template-columns: repeat(2, 1fr); }
            .stats { flex-direction: column; gap: 8px; }
            .stats .stat-card { padding: 12px 16px; }
            .stats .stat-number { font-size: 22px; }
            .card-body { padding: 8px 16px 14px 16px; }
            .field {
                flex-direction: column;
                align-items: flex-start;
                gap: 2px;
                padding: 8px 0;
            }
            .field-value {
                text-align: left;
                max-width: 100%;
                width: 100%;
                font-size: 16px;
            }
            .field-label { font-size: 15px; }
            .search-input { flex-direction: column; }
            .search-input button { padding: 14px; }
            .support-links { flex-direction: column; align-items: center; }
            .support-btn { width: 100%; justify-content: center; }
            .copy-btn { width: 28px; height: 28px; font-size: 14px; }
            .toast { font-size: 13px; padding: 12px 20px; }
        }
        @media (max-width: 480px) {
            body { padding: 8px; }
            .header { padding: 16px 12px; border-radius: 16px; }
            .header-logo .logo-text { font-size: 20px; }
            .header-logo img { width: 40px; height: 40px; }
            .header .query-box { font-size: 11px; padding: 4px 14px; }
            .search-box { padding: 16px 16px; }
            .search-type { grid-template-columns: repeat(2, 1fr); }
            .stats .stat-card { padding: 10px 12px; }
            .stats .stat-number { font-size: 18px; }
            .card { border-radius: 18px; }
            .card-header { padding: 10px 14px; }
            .card-body { padding: 6px 14px 12px 14px; }
            .field { padding: 6px 0; }
            .field-value { font-size: 15px; }
            .field-label { font-size: 14px; }
            .copy-btn { width: 24px; height: 24px; font-size: 12px; }
            .support-btn { font-size: 12px; padding: 6px 16px; }
            .toast { font-size: 12px; padding: 10px 16px; bottom: 16px; }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="header-logo">
                <img src="https://storage.ghost.io/c/b5/22/b52265eb-d44c-4ae8-8456-954cfb01f918/content/images/2020/07/OffensiveOsint-logo-RGB-2.png" alt="Wekness Tool" onerror="this.style.display='none'">
                <div class="logo-text">⚡ <span>Wekness Tool</span></div>
            </div>
            <div class="sub">🔍 Поиск информации в открытых источниках</div>
            <div class="query-box" id="queryDisplay">📌 Введите запрос</div>
            <div class="support-links">
                <a href="https://trashbox.ru/topics/216477/wekness-tool" class="support-btn boosty" target="_blank">⬇️ Скачать</a>
                <a href="https://boosty.to/wekness" class="support-btn donate-alerts" target="_blank">❤️ Поддержать</a>
            </div>
        </div>
        
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
                <input type="text" id="queryInput" placeholder="+375331234567 или 89123456789" />
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
            ⚡ Wekness Tool • Данные из открытых источников
        </div>
    </div>
    
    <div class="toast" id="toast">
        <span id="toastIcon">✅</span>
        <span id="toastMessage">Скопировано</span>
    </div>
    
    <script>
        const searchType = document.getElementById('searchType');
        const queryInput = document.getElementById('queryInput');
        const searchBtn = document.getElementById('searchBtn');
        const resultsContainer = document.getElementById('resultsContainer');
        const resultCount = document.getElementById('resultCount');
        const validationMsg = document.getElementById('validationMsg');
        const queryDisplay = document.getElementById('queryDisplay');

        let currentType = 'phone';

        const placeholders = {
            phone: '+375331234567 или 89123456789',
            inn: '1234567890',
            email: 'example@mail.com',
            vk: '123456789',
            ip: '192.168.1.1',
            whois: 'example.com'
        };

        const typeNames = {
            phone: '📲 Телефон',
            inn: '🆔 ИНН',
            email: '📧 E-mail',
            vk: '🔵 VK',
            ip: '🏙️ IP',
            whois: '🌍 WHOIS'
        };

        function validatePhone(phone) {
            const clean = phone.replace(/[^\d+]/g, '');
            if (!clean) return { valid: false, msg: '❌ Введите номер телефона' };
            let num = clean;
            if (num.startsWith('+')) num = num.slice(1);
            const ruPattern = /^(7|8)\d{10}$/;
            const byPattern = /^375\d{9}$/;
            if (ruPattern.test(num)) return { valid: true, msg: '✅ Российский номер' };
            if (byPattern.test(num)) return { valid: true, msg: '✅ Белорусский номер' };
            if (num.length < 10) return { valid: false, msg: '❌ Слишком короткий номер' };
            if (num.length > 12) return { valid: false, msg: '❌ Слишком длинный номер' };
            return { valid: false, msg: '❌ Неверный формат. Используйте РФ (7/8...) или РБ (375...)' };
        }

        searchType.addEventListener('click', (e) => {
            const btn = e.target.closest('button');
            if (!btn) return;
            searchType.querySelectorAll('button').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            currentType = btn.dataset.type;
            queryInput.placeholder = placeholders[currentType] || 'Введите данные...';
            queryDisplay.textContent = `📌 ${typeNames[currentType]}`;
            validationMsg.className = 'validation-msg';
            validationMsg.textContent = '';
            queryInput.classList.remove('error', 'success');
            queryInput.focus();
        });

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

        function showToast(msg, isError) {
            const toast = document.getElementById('toast');
            const toastMsg = document.getElementById('toastMessage');
            const toastIcon = document.getElementById('toastIcon');
            toastMsg.textContent = msg;
            toastIcon.textContent = isError ? '❌' : '✅';
            toast.className = 'toast' + (isError ? ' error' : '');
            toast.classList.add('show');
            clearTimeout(toast._timeout);
            toast._timeout = setTimeout(() => toast.classList.remove('show'), 3500);
        }

        function copyCard(index) {
            const card = document.getElementById('card-' + index);
            if (!card) return;
            let text = '';
            const fields = card.querySelectorAll('.field');
            fields.forEach((field) => {
                const label = field.querySelector('.field-label')?.textContent?.trim() || '';
                const value = field.querySelector('.field-value')?.textContent?.trim() || '';
                if (value) {
                    text += label + ': ' + value + '\\n';
                }
            });
            if (!text) {
                showToast('Нет данных для копирования', true);
                return;
            }
            navigator.clipboard.writeText(text).then(() => {
                showToast('✅ Данные скопированы');
            }).catch(() => {
                showToast('❌ Ошибка копирования', true);
            });
        }

        function escapeHtml(text) {
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        }

        async function performSearch() {
            const query = queryInput.value.trim();
            if (!query) {
                resultsContainer.innerHTML = '<div class="no-results">Введите запрос</div>';
                resultCount.style.display = 'none';
                return;
            }
            
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
                
                // Проверяем на записи saverudata
                if (data["✅ Найдено записей"] && data["📋 Записи"]) {
                    const records = data["📋 Записи"];
                    resultCount.textContent = `🔍 Найдено записей: ${data["✅ Найдено записей"]}`;
                    resultCount.style.display = 'block';
                    
                    let html = '';
                    records.forEach((record, index) => {
                        const entries = Object.entries(record).filter(([k, v]) => v && String(v).trim());
                        
                        let fieldsHtml = '';
                        entries.forEach(([key, value]) => {
                            let cls = '';
                            const val = String(value);
                            if (key.includes('Email')) cls = 'value-email';
                            else if (key.includes('Телефон')) cls = 'value-phone';
                            else if (key.includes('IP')) cls = 'value-ip';
                            else if (key.includes('Имя')) cls = 'value-name';
                            else if (key.includes('Статус')) cls = 'value-status';
                            
                            fieldsHtml += `
                                <div class="field">
                                    <span class="field-label">${key}</span>
                                    <span class="field-value ${cls}">${escapeHtml(val)}</span>
                                </div>
                            `;
                        });
                        
                        html += `
                            <div class="card" id="card-${index}">
                                <div class="card-header">
                                    <span class="card-number">📋 Запись #${index + 1}</span>
                                    <button class="copy-btn" onclick="copyCard(${index})" title="Копировать">📋</button>
                                </div>
                                <div class="card-body">${fieldsHtml}</div>
                            </div>
                        `;
                    });
                    
                    resultsContainer.innerHTML = html;
                    return;
                }
                
                // Обычный результат
                const entries = Object.entries(data).filter(([k, v]) => v && String(v).trim());
                
                if (entries.length === 0) {
                    resultsContainer.innerHTML = '<div class="no-results">😕 Ничего не найдено</div>';
                    return;
                }
                
                resultCount.textContent = `🔍 Найдено записей: ${entries.length}`;
                resultCount.style.display = 'block';
                
                let fieldsHtml = '';
                entries.forEach(([key, value]) => {
                    let cls = '';
                    const val = String(value);
                    if (key.includes('Email')) cls = 'value-email';
                    else if (key.includes('Телефон') || key.includes('номер')) cls = 'value-phone';
                    else if (key.includes('IP')) cls = 'value-ip';
                    else if (key.includes('Имя') || key.includes('ФИО')) cls = 'value-name';
                    else if (key.includes('Статус')) cls = 'value-status';
                    
                    if (val.startsWith('http')) {
                        fieldsHtml += `
                            <div class="field">
                                <span class="field-label">${key}</span>
                                <span class="field-value"><a href="${val}" target="_blank" class="value-link">${escapeHtml(val)}</a></span>
                            </div>
                        `;
                    } else {
                        fieldsHtml += `
                            <div class="field">
                                <span class="field-label">${key}</span>
                                <span class="field-value ${cls}">${escapeHtml(val)}</span>
                            </div>
                        `;
                    }
                });
                
                const html = `
                    <div class="card" id="card-0">
                        <div class="card-header">
                            <span class="card-number">📋 Результаты поиска</span>
                            <button class="copy-btn" onclick="copyCard(0)" title="Копировать">📋</button>
                        </div>
                        <div class="card-body">${fieldsHtml}</div>
                    </div>
                `;
                
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
        queryDisplay.textContent = '📌 Телефон';
    </script>
</body>
</html>'''

# ============================================================
# ОБРАБОТЧИКИ
# ============================================================

async def handle(request):
    return web.Response(text=HTML_PAGE, content_type='text/html')

async def handle_search(request):
    try:
        data = await request.json()
        search_type = data.get('type', '')
        query = data.get('query', '')
        
        if not query:
            return web.json_response({'error': 'Введите запрос'})
        
        from osint_functions import (
            search_phone_full,
            search_inn,
            search_email,
            search_vk,
            search_ip,
            search_whois
        )
        
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
        
        result = {k: v for k, v in result.items() if v is not None}
        return web.json_response(result)
        
    except Exception as e:
        return web.json_response({'error': str(e)})

# ============================================================
# ЗАПУСК
# ============================================================

async def start_web_server():
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

if __name__ == "__main__":
    try:
        asyncio.run(start_web_server())
    except KeyboardInterrupt:
        print("⏹️ Выход...")
