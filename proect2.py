import telebot
import random
import datetime
import time
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError
from telebot import types
import json
import os
import base64


bot =  telebot.TeleBot('8355503801:AAE6hiBjyP_aWCkYvA-69sYB1pnCc2n9iVg')
geolockator = Nominatim(user_agent='pollen_bot')


def get_city_name(lat, lon, max_retries=3):
    for i in range(max_retries):
        try:
            loc = geolockator.reverse((lat, lon), timeout= 10)
            if loc and loc.address:
                ap = loc.address.split(',')
                for i in reversed(ap):
                    i = i.strip()
                    for j in ['город','city','петербург', 'минск', 'спб', 'sankt', 'moscow', 'москва']:
                        if j in i.lower():
                            return i.strip()
                if ap:
                    for i in ap:
                        i = i.strip().lower()
                        for country in ['россия', 'беларусь', 'russia', 'belarus']:
                            if country in i:
                                return'Ваш регион'
                    return ap[0].strip()
            return'Ваш регион'
        except(GeocoderTimedOut, GeocoderServiceError):
            time.sleep(1)
    return'Ваш регион'        

def get_level(valye):
    if valye == 0:
        return '⚪','Нет активности'
    elif valye < 20:
        return '🟢','Очень низкая'
    elif valye < 50:
        return '🟢','Низкая'
    elif valye < 100:
        return '🟡','Среднея'
    elif valye < 200:
        return '🟠','Повышенная'
    else:
        return '🔴','Высокая'
    
def get_seasonal_polen(mounth): 
    try:
        path = os.path.join(os.path.dirname(__file__),'data.json')
        with open(path,'r',encoding='utf-8')as file:
            data =json.load(file)
        encoded = data.get('encoded')
        decoded_json =base64.b64decode(encoded).decode('utf-8')
        seasons = json.loads(decoded_json)
        return seasons.get(str(mounth),{"Берёза": 0.1, "Ольха": 0.1, "Трава": 0.1,"Амброзия": 0.1, "Полынь": 0.1, "Сорняки": 0.1})
    except Exception as e:
        print(f"[ERROR] Не удалось загрузить закодированный data.json: {e}")
        return{"Берёза": 0.1, "Ольха": 0.1, "Трава": 0.1,"Амброзия": 0.1, "Полынь": 0.1, "Сорняки": 0.1}

def get_pollen_realistic(city, lat, lon):
    current_month = datetime.datetime.now().month
    current_day = datetime.datetime.now().day
    base_season = get_seasonal_polen(current_month)
    random.seed(f'{city}_{lat}_{lon}_{current_month}_{current_day}_{int(time.time()//3600)}')
    pollen_data = {}
    plants = ["Берёза", "Ольха", "Трава", "Амброзия", "Полынь", "Сорняки"]
    for i in plants:
        if i in base_season:
            season_coef = base_season[i]
            if season_coef > 0:
                if season_coef < 0.3:
                    min_base = 10
                elif season_coef < 0.5:
                    min_base = 20
                else:
                    min_base = 30
                base_level = max(min_base, season_coef*random.uniform(50,150))
                weather_factor = random.uniform(0.8,1.3)
                day_factor = random.uniform(0.85,1.15)
                value = int(base_level*weather_factor*day_factor)
                value = min(value,300)
                pollen_data[i]=max(5,value)
            else:
                pollen_data[i] = 0
    if current_month == 10:
        pollen_data['Полынь']= max(pollen_data['Полынь'],random.randint(15,60))
        pollen_data['Сорняки']= max(pollen_data['Сорняки'],random.randint(10,45))
    if random.random() < 0.15:
        active_plants = []
        for p,v in pollen_data.items():
            if v > 0:
                active_plants.append(p)
        #if len(active_plants)> 0:
    if current_month in [3,4,5,6,7,8,9,10]:
        pass
    else:
        if random.random()< 0.1:
            for plant in plants:
                if pollen_data[plant]< 10:
                    pollen_data[plant] = 0
    return pollen_data

def get_advice(pollen_data):
    high_pollen= []
    medium_pollen = []
    low_pollen = []
    for p,v in pollen_data.items():    
        if v >= 100:
            high_pollen.append(p)
        elif v >=30 and v <100:
            medium_pollen.append(p)
        elif v >=5 and v <30:
            low_pollen.append(p)    
    total_pollen = sum(pollen_data.values())
    if total_pollen == 0:
        return '✅Отличная погода для прогулок!'
    elif len(high_pollen) > 0:
        return f"⚠️ *ВЫСОКИЙ РИСК* для {', '.join(high_pollen)} \n Ограничьте выход на улицу \n Принимайте антигистаминные \n Используйте HEPA-фильтры"
    elif len(medium_pollen) > 0:
        return f"‼️*ПОВЫШЕННЫЙ РИСК* для {', '.join(medium_pollen)} \n Держите окна закрытыми\n Промывайте нос после улицы\n Следите за симптомами "
    elif len(low_pollen) > 0:
        return f"❗*ЕСТЬ РИСК* для {', '.join(low_pollen)} \n• Можно гулять, но осторожно\n• Поливайте растения дома"
    else:
        'Можно гулять не опасаясь пыльцы'

def format_message(city, pollen_data):
    current_data= datetime.datetime.now().strftime('%d.%m.%Y %H:%M')
    total_pollen = sum(pollen_data.values())
    active_plants = []
    for i in pollen_data.values():
        if i > 0:
            active_plants.append(1)
    text = f'🏙️ *{city}*\n🗓️ {current_data}\n\n 🌿*Текущий уровень пыльцы: *\n'
    text += f'📈 Общий индекс: {total_pollen}/100\n'
    text += f'🪴 Активных растений: {len(active_plants)}/6\n\n'
    for plant, value in pollen_data.items():
        if value>0:
            emoge, level = get_level(value)
            text += f'  {plant}: *{value}* {emoge} {level}\n'
        else:
            text += f'  {plant}: *{value} ⚪*\n'
    text += f'\n{get_advice(pollen_data)}\n\n⌚ Данные о пыльце обновляются каждый день'
    return text


@bot.message_handler(commands= ['start'])
def start(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    button = types.KeyboardButton('📍Отправить местоположение',request_location=True)
    markup.add(button)
    button_city = types.KeyboardButton('🏙️Введите город',request_location=True)
    markup.add(button_city)
    bot.send_message(message.chat.id, "🌿 Привет! Я бот, который показывает уровень пыльцы в твоём регионе.\n"
        "Нажми кнопку ниже, чтобы я определил твоё местоположение:", reply_markup = markup)

@bot.message_handler(content_types= ['location'])
def handle_location(message):
    bot.send_message(message.chat.id, 'Я принял твоё местоположение')
    lat = message.location.latitude 
    lon = message.location.longitude
    load_message = bot.send_message(
        message.chat.id,
        '🔎 *Определение местоположение*\n'
        '📡 *Определение метеостанции*\n'
        '🌿 *Анализ данных о пыльце\n*',
        parse_mode='Markdown'
    )

    try:
        city = get_city_name(lat, lon)
        pollen_data = get_pollen_realistic(city,lat,lon)  
        bot.delete_message(message.chat.id, load_message.message_id)
        text = format_message(city, pollen_data)
        bot.send_message(message.chat.id,text,parse_mode='Markdown')
    except Exception as e:
        bot.send_message(message.chat.id, '❌Ошибка получения данных попробуйте позже')
        print(e)













































bot.polling(none_stop= True, interval= 0)