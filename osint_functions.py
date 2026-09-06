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

# ===== НАСТРОЙКИ =====
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


async def search_phone_full(phone: str) -> dict:
    phone_clean, region, ok = normalize_phone(phone)
    if not ok:
        return {"Ошибка": "Неверный формат номера. Примеры: +375331234567, +79123456789"}
    
    result = {"📱 Телефон": phone}
    data_found = False
    
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
        # МТС (Беларусь)
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
        
        # Велком (Беларусь)
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
        
        # GetScam (РФ)
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
    
    # Соцсети
    result["✈️ Telegram"] = f"https://t.me/+{phone_clean}"
    result["📱 WhatsApp"] = f"https://wa.me/{phone_clean}"
    result["📞 Viber"] = f"https://viber.click/{phone_clean}"
    result["📘 VK"] = f"https://vk.com/search?c%5Bq%5D={phone_clean}"
    
    result["📊 Статус"] = "✅ Данные найдены" if data_found else "❌ Данных не найдено"
    
    return result


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
        except:
            pass
    
    return result


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
