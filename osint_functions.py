# osint_functions.py - Добавляем saverudata в search_phone_full

import re
import aiohttp
import phonenumbers
from phonenumbers import timezone, geocoder, carrier
import vk_api
import whois
from bs4 import BeautifulSoup
import os
import base64
import random
from faker import Faker
from datetime import datetime

# ============================================================
# НАСТРОЙКИ
# ============================================================

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "application/json, text/plain, */*",
    "Referer": "https://www.google.com/"
}

def decode_token(enc: str) -> str:
    return base64.b64decode(enc).decode()[::-1]

enc_vk = "NWJkNzViNTVmNmFiOTA5MTZmMTg3ZmExNDI5ODY3Mzc2NzM3N2VkNzI4NDA3YWQ0Mjk4NjczNzQyOTg2NzM3NDI5ODY3Mzc="
VK_TOKEN = decode_token(enc_vk)
vk_session = vk_api.VkApi(token=VK_TOKEN)
vk = vk_session.get_api()
fake = Faker()

# ============================================================
# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# ============================================================

def normalize_phone(phone: str):
    raw = phone.replace('+', '').replace(' ', '').replace('-', '').replace('(', '').replace(')', '')
    if raw.startswith('375') and len(raw) == 12:
        return raw, "BY", True
    if len(raw) == 9 and raw.isdigit():
        return '375' + raw, "BY", True
    if raw.startswith('7') and len(raw) == 11:
        return raw, "RU", True
    if raw.startswith('8') and len(raw) == 11:
        return '7' + raw[1:], "RU", True
    if len(raw) == 10 and raw.isdigit():
        return '7' + raw, "RU", True
    return raw, None, False

def search_in_mts_file(phone_clean: str) -> dict:
    result = {}
    if not os.path.exists("MTS.txt"):
        return result
    try:
        with open("MTS.txt", "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                if phone_clean in line or phone_clean[-7:] in line:
                    parts = line.split(';')
                    if len(parts) >= 1:
                        result["Номер в базе"] = parts[0]
                    if len(parts) >= 2:
                        result["ФИО (МТС)"] = parts[1]
                    if len(parts) >= 3:
                        result["Доп. информация"] = parts[2]
                    if len(parts) >= 4:
                        result["Адрес"] = parts[3]
                    break
    except:
        pass
    return result


# ============================================================
# 1. ПОИСК ПО РФ БАЗЕ (saverudata)
# ============================================================

async def search_russian_db(phone: str) -> dict:
    """Поиск по российской базе saverudata"""
    clean = ''.join(filter(str.isdigit, phone))
    if not clean:
        return {"Ошибка": "Введите номер телефона"}
    
    if len(clean) < 10:
        return {"Ошибка": "Слишком короткий номер"}
    
    prefix = clean[:6]
    digits = '/'.join(prefix)
    target_url = f"https://saverudata.org/db/{digits}/00000-99999.json"
    cdx_url = f"https://web.archive.org/cdx/search/cdx?url={target_url}&output=json&fl=timestamp,original,mimetype,statuscode,digest,length"
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(cdx_url) as response:
                if response.status != 200:
                    return {}
                
                data = await response.json()
                if len(data) <= 1:
                    return {}
                
                latest = data[-1]
                timestamp = latest[0]
                url = latest[1]
                download_url = f"https://web.archive.org/web/{timestamp}/{url}"
                
                async with session.get(download_url) as json_response:
                    if json_response.status != 200:
                        return {}
                    
                    json_data = await json_response.json()
                    search_phone = clean
                    found_records = []
                    
                    for item in json_data:
                        if len(item) > 0:
                            phone_in_json = ''.join(filter(str.isdigit, item[0]))
                            if phone_in_json == search_phone:
                                record = {
                                    "Телефон": item[0] if len(item) > 0 else None,
                                    "Город": item[1] if len(item) > 1 and item[1] else None,
                                    "Улица": item[2] if len(item) > 2 and item[2] else None,
                                    "Дом": item[3] if len(item) > 3 and item[3] else None,
                                    "Подъезд": item[4] if len(item) > 4 and item[4] else None,
                                    "Этаж": item[5] if len(item) > 5 and item[5] else None,
                                    "Квартира": item[6] if len(item) > 6 and item[6] else None,
                                    "Имя": item[7] if len(item) > 7 and item[7] else None,
                                    "Email": item[8] if len(item) > 8 and item[8] else None,
                                    "Короткое имя": item[9] if len(item) > 9 and item[9] else None,
                                    "Дополнительно": item[10] if len(item) > 10 and item[10] else None,
                                }
                                record = {k: v for k, v in record.items() if v}
                                if record:
                                    found_records.append(record)
                    
                    if found_records:
                        return {
                            "✅ Найдено записей (saverudata)": len(found_records),
                            "📋 Записи": found_records
                        }
                    return {}
                        
        except Exception as e:
            return {"Ошибка saverudata": str(e)}


# ============================================================
# 2. ПОИСК ПО НОМЕРУ (ПОЛНЫЙ - С ВСЕМИ БАЗАМИ)
# ============================================================

async def search_phone_full(phone: str) -> dict:
    """ПОЛНЫЙ поиск по номеру телефона (ВСЕ БАЗЫ)"""
    phone_clean, region, ok = normalize_phone(phone)
    if not ok:
        return {"Ошибка": "Неверный формат номера. Примеры: +375331234567, +79123456789"}
    
    result = {"📱 Телефон": phone}
    data_found = False
    
    # ===== 1. Базовая информация =====
    try:
        parsed = phonenumbers.parse(phone_clean, region)
        result["✅ Валидный"] = "Да" if phonenumbers.is_valid_number(parsed) else "Нет"
        result["📡 Оператор"] = carrier.name_for_number(parsed, "ru") or "Неизвестно"
        result["🌍 Страна"] = geocoder.description_for_number(parsed, "ru") or "Неизвестно"
        tz = timezone.time_zones_for_number(parsed)
        result["🕐 Часовой пояс"] = tz[0] if tz else "Неизвестно"
    except:
        pass
    
    async with aiohttp.ClientSession() as session:
        # ===== 2. МТС =====
        try:
            link = f'https://spravochnik109.link/byelarus/mobilnaya-svyaz/mTS-mobilnyj-opyerator/mTS-mobilnyye-tyelyefony?phone={phone_clean[-7:]}'
            async with session.get(link, headers=HEADERS) as resp:
                if resp.status == 200:
                    html = await resp.text()
                    soup = BeautifulSoup(html, 'html.parser')
                    fio_elem = soup.find('td', class_='fio')
                    if fio_elem:
                        result["👤 ФИО (МТС)"] = fio_elem.text.strip()
                        data_found = True
                    addr_elem = soup.find('td', class_='adr')
                    if addr_elem:
                        result["📍 Адрес (МТС)"] = addr_elem.text.strip()
                        data_found = True
        except:
            pass
        
        # ===== 3. Велком =====
        try:
            link = f'https://spravochnik109.link/byelarus/mobilnaya-svyaz/vyelkom-mobilnyj-opyerator/vyelkom-mobilnyye-tyelyefony?phone=%2B{phone_clean}'
            async with session.get(link, headers=HEADERS) as resp:
                if resp.status == 200:
                    html = await resp.text()
                    soup = BeautifulSoup(html, 'html.parser')
                    addr = soup.find('td', class_='adr')
                    if addr:
                        result["📍 Адрес (Велком)"] = addr.text.strip()
                        data_found = True
                    fio_elem = soup.find(class_='res')
                    if fio_elem:
                        fio_text = fio_elem.text.replace("Телефоны", "").strip()
                        name_user = re.sub(r'[^\w\s]+|[\d]+', r'', fio_text)
                        if name_user:
                            result["👤 ФИО (Велком)"] = name_user.replace(' XXX', '').strip()
                            data_found = True
        except:
            pass
        
        # ===== 4. MTS.txt =====
        mts_file = search_in_mts_file(phone_clean)
        for k, v in mts_file.items():
            result[k] = v
            data_found = True
        
        # ===== 5. GetScam (РФ) =====
        if phone_clean.startswith('7'):
            try:
                url = f'https://getscam.com/{phone_clean}'
                async with session.get(url, headers=HEADERS) as resp:
                    if resp.status == 200:
                        html = await resp.text()
                        soup = BeautifulSoup(html, 'html.parser')
                        ip_elem = soup.find(class_='top__info-item')
                        if ip_elem:
                            ip_match = re.search(r'IP адрес\s*([\d\.]+)', ip_elem.text)
                            if ip_match:
                                result["🌐 IP адрес"] = ip_match.group(1)
                                data_found = True
                
                tinkoff_url = f'https://www.tbank.ru/oleg/who-called/info/{phone_clean}/'
                async with session.get(tinkoff_url, headers=HEADERS) as tresp:
                    if tresp.status == 200:
                        thtml = await tresp.text()
                        tsoup = BeautifulSoup(thtml, 'html.parser')
                        comp = tsoup.find(class_='abtnK6gFv')
                        if comp:
                            result["🏢 Организация"] = comp.text.strip()
                            data_found = True
            except:
                pass
            
            # ===== 6. Saverudata (РФ база) =====
            try:
                saveresult = await search_russian_db(phone_clean)
                for k, v in saveresult.items():
                    if k == "📋 Записи":
                        # Добавляем записи с префиксом
                        for i, record in enumerate(v, 1):
                            for rk, rv in record.items():
                                result[f"📋 Saverudata #{i} {rk}"] = rv
                                data_found = True
                    elif k != "Ошибка saverudata":
                        result[k] = v
                        data_found = True
            except:
                pass
    
    # ===== 7. Соцсети =====
    result["✈️ Telegram"] = f"https://t.me/+{phone_clean}"
    result["📱 WhatsApp"] = f"https://wa.me/{phone_clean}"
    result["📞 Viber"] = f"https://viber.click/{phone_clean}"
    result["📘 VK"] = f"https://vk.com/search?c%5Bq%5D={phone_clean}"
    
    result["📊 Статус"] = "✅ Данные найдены" if data_found else "❌ Данных не найдено"
    
    return result


# ============================================================
# 3. ПОИСК ПО ИНН
# ============================================================

async def search_inn(inn_text: str) -> dict:
    if not inn_text:
        return {"Ошибка": "ИНН не может быть пустым"}
    
    inn_clean = inn_text.strip().replace(' ', '').replace('-', '')
    
    if not inn_clean.isdigit():
        return {"Ошибка": "ИНН должен содержать только цифры"}
    
    if len(inn_clean) not in [9, 10, 12]:
        return {"Ошибка": f"Неверная длина ИНН: {len(inn_clean)}"}
    
    result = {"🔢 ИНН": inn_clean}
    
    if len(inn_clean) in [10, 12]:
        try:
            async with aiohttp.ClientSession() as session:
                headers = {
                    'Content-Type': 'application/json',
                    'Accept': 'application/json',
                    'Authorization': 'Token 8c801352aa28b2066f4df99a3a50e28f8da3f14e'
                }
                url = 'https://suggestions.dadata.ru/suggestions/api/4_1/rs/findById/party'
                payload = {'query': inn_clean}
                
                async with session.post(url, json=payload, headers=headers, timeout=10) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        if data.get('suggestions'):
                            item = data['suggestions'][0].get('data', {})
                            if item.get('name'):
                                name = item['name']
                                if isinstance(name, dict):
                                    if name.get('full_with_opf'):
                                        result["🏢 Полное наименование"] = name['full_with_opf']
                            if item.get('address'):
                                result["📍 Адрес"] = item['address'].get('value', '')
                            if item.get('kpp'):
                                result["🏷️ КПП"] = str(item['kpp'])
                            if item.get('ogrn'):
                                result["🔑 ОГРН"] = str(item['ogrn'])
                            if item.get('state'):
                                status_map = {'ACTIVE': 'Действующее', 'LIQUIDATED': 'Ликвидировано'}
                                status = item['state'].get('status') if isinstance(item['state'], dict) else None
                                if status:
                                    result["⚡ Статус"] = status_map.get(status, status)
        except:
            pass
    
    return result


# ============================================================
# 4. ПОИСК ПО EMAIL
# ============================================================

async def search_email(email: str) -> dict:
    if not email:
        return {"Ошибка": "Email не может быть пустым"}
    
    email_clean = email.strip().lower()
    
    if '@' not in email_clean:
        return {"Ошибка": "Неверный формат email"}
    
    username = email_clean.split('@')[0]
    domain = email_clean.split('@')[1]
    
    result = {"📧 Email": email_clean, "👤 Username": username, "🌐 Домен": domain}
    
    async with aiohttp.ClientSession() as session:
        try:
            url = f'https://getscam.com/email/{email_clean}'
            async with session.get(url, headers=HEADERS) as resp:
                if resp.status == 200:
                    html = await resp.text()
                    soup = BeautifulSoup(html, 'html.parser')
                    info_block = soup.find('div', class_='pt-[16px] border-t border-t-gray-300')
                    if info_block:
                        city_tag = info_block.find('a', href=lambda x: x and 'find-city' in x)
                        if city_tag:
                            result["🏙️ Город"] = city_tag.text.strip()
                        ip_tag = info_block.find('a', href=lambda x: x and '/ip/' in x)
                        if ip_tag:
                            result["🌐 IP"] = ip_tag.text.strip()
        except:
            pass
        
        try:
            breach_url = f'https://haveibeenpwned.com/api/v3/breachedaccount/{email_clean}'
            headers_hibp = {'hibp-api-key': '', 'User-Agent': 'OSINT-Tool/1.0'}
            async with session.get(breach_url, headers=headers_hibp) as resp:
                if resp.status == 200:
                    breaches = await resp.json()
                    if breaches:
                        breach_names = [b.get('Name', 'Unknown') for b in breaches[:5]]
                        result["🔐 Утечки"] = ", ".join(breach_names)
        except:
            pass
    
    return result


# ============================================================
# 5. ПОИСК ПО VK ID
# ============================================================

async def search_vk(vk_id: str) -> dict:
    result = {"📘 VK ID": vk_id}
    try:
        user = vk.users.get(
            user_ids=vk_id,
            fields='first_name,last_name,bdate,city,sex,online,last_seen,relation,education,about,followers_count,verified'
        )[0]
        result["👤 Имя"] = user.get('first_name', 'Неизвестно')
        result["👤 Фамилия"] = user.get('last_name', 'Неизвестно')
        result["🔗 Ссылка"] = f"https://vk.com/id{vk_id}"
        if user.get('bdate'):
            result["📅 Дата рождения"] = user['bdate']
        if user.get('city'):
            result["🏙️ Город"] = user['city'].get('title', 'Неизвестно')
        if user.get('about'):
            result["📝 О себе"] = user['about'][:200]
        if user.get('followers_count'):
            result["👥 Подписчиков"] = user['followers_count']
    except Exception as e:
        result["❌ Ошибка"] = str(e)
    return result


# ============================================================
# 6. ПОИСК ПО IP
# ============================================================

async def search_ip(ip: str) -> dict:
    result = {"🌐 IP": ip}
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f'http://ip-api.com/json/{ip}') as resp:
                if resp.status == 200:
                    data = await resp.json()
                    if data.get('status') == 'success':
                        result["🌍 Страна"] = data.get('country', 'Неизвестно')
                        result["🏙️ Город"] = data.get('city', 'Неизвестно')
                        result["🏢 Провайдер"] = data.get('isp', 'Неизвестно')
                        result["📌 Широта"] = data.get('lat', 'Неизвестно')
                        result["📌 Долгота"] = data.get('lon', 'Неизвестно')
                    else:
                        result["❌ Ошибка"] = "IP не найден"
    except Exception as e:
        result["❌ Ошибка"] = str(e)
    return result


# ============================================================
# 7. WHOIS ПОИСК
# ============================================================

async def search_whois(domain: str) -> dict:
    result = {"🌐 Домен": domain}
    try:
        w = whois.whois(domain)
        if w.registrar:
            result["🏢 Регистратор"] = w.registrar
        if w.creation_date:
            if isinstance(w.creation_date, list):
                result["📅 Создан"] = str(w.creation_date[0])
            else:
                result["📅 Создан"] = str(w.creation_date)
        if w.expiration_date:
            if isinstance(w.expiration_date, list):
                result["📅 Истекает"] = str(w.expiration_date[0])
            else:
                result["📅 Истекает"] = str(w.expiration_date)
        if w.name_servers:
            ns = w.name_servers
            if isinstance(ns, list):
                result["📡 NS серверы"] = ", ".join(ns[:3])
        if w.emails:
            result["📧 Контакты"] = ", ".join(w.emails[:3])
    except Exception as e:
        result["❌ Ошибка"] = str(e)
    return result
