import math
import logging
import requests
from datetime import datetime, timedelta
import pytz
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

TOKEN = "8970204551:AAGhNR7zOoqmpzMatxbxOptH4rCi9MxTZMI"
WEATHER_API_KEY = "f53e84bcfb68ce9facdd257edf4ac9a4"

# ==================== النموذج المستخدم ====================
FORECAST_MODEL = "ecmwf_ifs025"
FORECAST_MODEL_NAME = "ECMWF IFS 0.25°"

SYRIAN_VILLAGES_MAP = {
    "دمشق": ["المزة", "البرامكة", "الصالحية", "المهاجرين", "ركن الدين", "دمّر", "قاسيون", "باب توما", "الميدان", "التجارة"],
    "ريف دمشق": ["داريا", "معضمية الشام", "جرمانا", "التل", "يبرود", "النبك", "الزبداني", "بلودان", "دوما", "حرستا", "عقربا", "سقبا", "قطنا", "الكسوة", "زملكا", "حمورية", "قدسيا", "الهامة", "عرطوز", "صحنايا", "دير عطية", "قارة", "سرغايا"],
    "حلب": ["عفرين", "الباب", "اعزاز", "منبج", "السفيرة", "مسكنة", "دير حافر", "الأتارب", "دارة عزة", "حريتان", "نبل", "الزهراء", "عين العرب", "جرابلس", "الراعي", "خناصر"],
    "حمص": ["تدمر", "الرستن", "القصير", "تلبيسة", "تلدو", "القبو", "المخرم الفوقاني", "السخنة", "جب الجراح", "الحصن", "مرمريتا", "مهين", "القريتين", "خربة التين نور", "العريضة", "شين", "زعفرانة", "حديدة", "حب نمرة", "عناز", "مزينة", "الرقامة", "فحيلة", "الغنطو", "دير فول", "تيرمعلة", "الدار الكبيرة"],
    "حماة": ["سلمية", "محردة", "مصياف", "السقيلبية", "كفرزيتا", "اللطامنة", "حلفايا", "عقيربات", "كفرنبودة", "طيبة الإمام", "صوران", "الحمرا", "بري الشرقي", "الربيعة", "قلعة المضيق", "شطحة", "عين الكروم", "عوج", "قصية", "طاحونة الحلاوة", "الصفصافية", "جب رملة", "معردس", "حر بنفسه", "عقرب", "الشيخ حديد", "دير شميل", "كفر بهم"],
    "اللاذقية": ["جبلة", "القرداحة", "الحفة", "صلنفة", "بكسا", "بستان الباشا", "ربيعة", "كسب", "البدروسية", "الدالية", "مشقيتا", "بوقا", "قسطل معاف"],
    "إدلب": ["معرة النعمان", "أريحا", "سراقب", "جسر الشغور", "حارم", "سلقين", "خان شيخون", "بنش", "كفر تخاريم", "الدانا", "معرة مصرين", "تفتناز", "سرمدا", "أطمة", "عندان", "كفرنبل", "التمانعة", "الهبيط", "كنصفرة", "بداما", "الجانودية", "دركوش", "حزانو", "قاح", "كللي", "معرة حرمة", "أبو الظهور", "أرمناز", "محمبل", "أورم الجوز", "سنجار", "البارة", "تلمنس"],
    "طرطوس": ["بانياس", "الشيخ بدر", "الدريكيش", "صافيتا", "برمانة المشايخ", "القدموس", "مشتى الحلو", "حمام واصل", "الصفصافة", "العنازة", "بيت ياشوط"],
    "درعا": ["نوى", "بصرى الشام", "إزرع", "تسيل", "طفس", "الجيزة", "داعل", "الشيخ مسكين", "صيدا", "جاسم", "انخل", "الحراك", "سحم الجولان", "كفرناسج"],
    "السويداء": ["شهبا", "صلخد", "قنوات", "عريا", "مفعلة", "عرمان", "المشنف", "بريكة", "لاهثة", "سالح", "عريقة", "الصورة الكبرى"],
    "الرقة": ["الثورة", "تل أبيض", "المنصورة", "الحوس", "كرامة", "معدان", "السبخة", "سلوك", "عين عيسى", "الجرنية"],
    "دير الزور": ["الميادين", "البوكمال", "الشحيل", "هجين", "البصيرة", "خشام", "التبني", "موحسن", "ذيبان", "الصبيحة"],
    "الحسكة": ["القامشلي", "عامودا", "رأس العين", "المالكية", "الدرباسية", "الرميلان", "تل تمر", "الشدادي", "جوادية", "الهول", "تل براك", "تل حميس"],
    "القنيطرة": ["خان أرنبة", "فيق", "جبا", "مسعدة", "الحميدية", "البعث", "نبع الصخر", "الرفيد", "جباتا الخشب", "بقعاتا"]
}

REGIONS = {
    "الشمال": ["حلب", "إدلب"],
    "الجنوب": ["دمشق", "درعا", "السويداء"],
    "الشرق": ["الحسكة", "دير الزور"],
    "الغرب": ["اللاذقية", "طرطوس"],
}

REGION_CITIES_COORDS = {
    "حلب":      (36.2021, 37.1343),
    "إدلب":     (35.9306, 36.6339),
    "دمشق":     (33.5138, 36.2765),
    "درعا":     (32.6189, 36.1021),
    "السويداء": (32.7094, 36.5692),
    "الحسكة":   (36.5025, 40.7480),
    "دير الزور": (35.3359, 40.1408),
    "اللاذقية": (35.5138, 35.7744),
    "طرطوس":    (34.8890, 35.8866),
}

ARABIC_DAYS = {0: "الاثنين", 1: "الثلاثاء", 2: "الأربعاء", 3: "الخميس", 4: "الجمعة", 5: "السبت", 6: "الأحد"}

WMO_CODES = {
    0: "☀️ صافٍ تماماً", 1: "🌤️ صافٍ غالباً", 2: "⛅ غائم جزئياً", 3: "☁️ غائم كلياً",
    45: "🌫️ ضباب", 48: "🌫️ ضباب متجمد", 51: "🌦️ رذاذ خفيف", 53: "🌦️ رذاذ متوسط", 55: "🌧️ رذاذ كثيف",
    56: "🌧️ رذاذ متجمد خفيف", 57: "🌧️ رذاذ متجمد كثيف", 61: "🌧️ مطر خفيف", 63: "🌧️ مطر متوسط",
    65: "🌧️ مطر غزير", 66: "🌧️ مطر متجمد خفيف", 67: "🌧️ مطر متجمد غزير", 71: "🌨️ ثلج خفيف",
    73: "🌨️ ثلج متوسط", 75: "❄️ ثلج كثيف", 77: "🌨️ حبيبات ثلج", 80: "🌦️ زخات مطر خفيفة",
    81: "🌧️ زخات مطر متوسطة", 82: "⛈️ زخات مطر عنيفة", 85: "🌨️ زخات ثلج خفيفة",
    86: "❄️ زخات ثلج كثيفة", 95: "⛈️ عاصفة رعدية", 96: "⛈️ رعدية مع برد خفيف", 99: "⛈️ رعدية مع برد كثيف",
}

def translate_wmo(code):
    try:
        return WMO_CODES.get(int(code), f"🌤️ ({code})")
    except Exception:
        return "🌤️"

def format_syria_time(dt_object):
    syria_tz = pytz.timezone('Asia/Damascus')
    if isinstance(dt_object, (int, float)):
        dt_syria = datetime.fromtimestamp(dt_object, tz=pytz.utc).astimezone(syria_tz)
    else:
        dt_syria = dt_object.astimezone(syria_tz)
    hour_12 = dt_syria.strftime("%I:%M").lstrip('0')
    period = "ص" if dt_syria.strftime("%p") == "AM" else "م"
    return f"{dt_syria.strftime('%Y-%m-%d')} | {ARABIC_DAYS[dt_syria.weekday()]} | {hour_12} {period}"

def format_time_12h_syria(iso_time):
    try:
        if "T" in iso_time:
            time_part = iso_time.split("T")[1][:5]
        else:
            time_part = iso_time[:5]
        h, m = map(int, time_part.split(":"))
        period = "ص" if h < 12 else "م"
        h12 = h % 12 or 12
        return f"{h12}:{m:02d} {period}"
    except Exception:
        return iso_time

def get_main_reply_keyboard():
    keyboard = [
        [KeyboardButton("📍 المحافظات السورية"), KeyboardButton("🌤️ طقس دمشق")],
        [KeyboardButton("📅 توقع 5 أيام للمناطق"), KeyboardButton("📅 توقع يومان للمناطق الأربع")],
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_governorate(loc_name):
    loc_name = loc_name.strip()
    if loc_name in SYRIAN_VILLAGES_MAP:
        return loc_name
    for gov, villages in SYRIAN_VILLAGES_MAP.items():
        if loc_name in villages:
            return gov
    return None

def resolve_location_om(name):
    try:
        url = f"https://geocoding-api.open-meteo.com/v1/search?name={requests.utils.quote(name)}&count=1&language=ar&format=json"
        res = requests.get(url, timeout=10).json()
        if res.get("results"):
            r = res["results"][0]
            return r["latitude"], r["longitude"], r.get("name", name)
    except Exception as e:
        logger.error(f"OM geocode: {e}")
    return None, None, name

def resolve_location(query_name):
    gov = get_governorate(query_name)
    q_str = f"{query_name}, {gov}, Syria" if gov else f"{query_name}, Syria"
    try:
        geo_url = f"https://api.openweathermap.org/geo/1.0/direct?q={requests.utils.quote(q_str)}&limit=1&appid={WEATHER_API_KEY}"
        res = requests.get(geo_url, timeout=10).json()
        if isinstance(res, list) and len(res) > 0:
            return res[0]['lat'], res[0]['lon'], query_name
    except Exception as e:
        logger.error(f"OWM geocode: {e}")
    lat, lon, nm = resolve_location_om(query_name)
    return lat, lon, query_name

# ==================== الزلازل ====================
def get_earthquakes_report():
    try:
        url = "https://earthquake.usgs.gov/fdsnws/event/1/query?format=geojson&minmagnitude=2.0&minlatitude=32.2&maxlatitude=37.5&minlongitude=35.0&maxlongitude=42.6&limit=5&orderby=time"
        res = requests.get(url, timeout=10).json()
        eqs = res.get("features", [])
        if not eqs:
            return "📴 لا توجد هزات أرضية حديثة مسجلة داخل الأراضي السورية ومحيطها."
        report = "🌋 **سجل الزلازل والهزات الأرضية في سوريا**\n━━━━━━━━━━━━━━━━━━\n"
        for eq in eqs:
            p = eq['properties']
            report += (f"🔹 **القوة:** {p.get('mag', 0)} ريختر\n"
                       f"📍 **الموقع:** {p.get('place', 'غير محدد')}\n"
                       f"🕒 **التوقيت:** {format_syria_time(p.get('time', 0) / 1000.0)}\n"
                       f"───────────────────\n")
        return report
    except Exception as e:
        logger.error(f"EQ: {e}")
        return "⚠️ حدث خطأ أثناء الاتصال بشبكة رصد الزلازل."

def get_earthquake_probability_1month():
    try:
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=365 * 5)
        url = (f"https://earthquake.usgs.gov/fdsnws/event/1/query?format=geojson"
               f"&starttime={start_date.strftime('%Y-%m-%d')}"
               f"&endtime={end_date.strftime('%Y-%m-%d')}"
               f"&minmagnitude=2.0&minlatitude=32.2&maxlatitude=37.5"
               f"&minlongitude=35.0&maxlongitude=42.6&limit=20000&orderby=time")
        features = requests.get(url, timeout=20).json().get("features", [])
        total_events = len(features)
        if total_events == 0:
            return ("📊 **احتمالية النشاط الزلزالي — الشهر القادم**\n"
                    "━━━━━━━━━━━━━━━━━━\n"
                    "لا توجد أحداث زلزالية مسجلة (قوة ≥ 2.0) في نطاق سوريا خلال آخر 5 سنوات.\n"
                    "⚠️ *هذه احتمالية إحصائية وليست تنبؤاً.*")
        mag_counts = {2: 0, 3: 0, 4: 0, 5: 0, 6: 0}
        for eq in features:
            m = eq['properties'].get('mag') or 0
            for threshold in mag_counts:
                if m >= threshold:
                    mag_counts[threshold] += 1
        report = (f"📊 **احتمالية النشاط الزلزالي — الشهر القادم**\n"
                  f"📍 **النطاق:** سوريا ومحيطها المباشر\n"
                  f"━━━━━━━━━━━━━━━━━━\n"
                  f"📅 **آخر 5 سنوات:** {total_events} حدثاً (قوة ≥ 2.0)\n\n"
                  f"📈 **الاحتمالية (خلال 30 يوماً):**\n")
        for threshold in [2, 3, 4, 5, 6]:
            rate = mag_counts[threshold] / 60.0
            p = (1 - math.exp(-rate)) * 100
            report += f"🔹 بقوة ≥ {threshold}.0: **{p:.1f}%**\n"
        report += ("\n━━━━━━━━━━━━━━━━━━\n"
                   "⚠️ **تنبيه:** احتمالات إحصائية وليست تنبؤاً.\n"
                   "📡 *المصدر: USGS*")
        return report
    except Exception as e:
        logger.error(f"EQ prob: {e}")
        return "⚠️ حدث خطأ أثناء حساب احتمالية النشاط الزلزالي."

# ==================== لوحات المفاتيح ====================
def build_governorates_keyboard():
    keyboard, row = [], []
    for g in SYRIAN_VILLAGES_MAP:
        row.append(InlineKeyboardButton(g, callback_data=f"gov_{g}"))
        if len(row) == 2:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)
    return InlineKeyboardMarkup(keyboard)

def build_villages_keyboard_for_gov(gov_name):
    villages = SYRIAN_VILLAGES_MAP.get(gov_name, [])
    keyboard = [[InlineKeyboardButton(f"🏙️ مركز {gov_name}", callback_data=f"center_{gov_name}")]]
    row = []
    for v in villages:
        row.append(InlineKeyboardButton(v, callback_data=f"weather_{v}"))
        if len(row) == 2:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)
    keyboard.append([InlineKeyboardButton("🔙 عودة إلى المحافظات", callback_data="back_govs")])
    return InlineKeyboardMarkup(keyboard)

def build_inline_keyboard_for_location(location_name):
    matched = get_governorate(location_name)
    if matched:
        btns = [[InlineKeyboardButton(f"🏙️ مركز {matched}", callback_data=f"center_{matched}")]]
        row = []
        for v in SYRIAN_VILLAGES_MAP[matched]:
            row.append(InlineKeyboardButton(v, callback_data=f"weather_{v}"))
            if len(row) == 2:
                btns.append(row)
                row = []
        if row:
            btns.append(row)
        btns.append([InlineKeyboardButton("🔙 عودة إلى المحافظات", callback_data="back_govs")])
        return btns
    btns, row = [], []
    for g in list(SYRIAN_VILLAGES_MAP)[:6]:
        row.append(InlineKeyboardButton(g, callback_data=f"gov_{g}"))
        if len(row) == 2:
            btns.append(row)
            row = []
    if row:
        btns.append(row)
    return btns

def build_regions_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🗺️ الشمال", callback_data="f5d_الشمال"),
         InlineKeyboardButton("🗺️ الجنوب", callback_data="f5d_الجنوب")],
        [InlineKeyboardButton("🗺️ الشرق", callback_data="f5d_الشرق"),
         InlineKeyboardButton("🗺️ الغرب", callback_data="f5d_الغرب")],
    ])

# ==================== الطقس الحالي ====================
def get_weather_now(query_name):
    lat, lon, loc_name = resolve_location(query_name)
    if not lat or not lon:
        return f"❌ لم يتم العثور على '{query_name}'.", None
    try:
        url = (f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}"
               f"&current=temperature_2m,relative_humidity_2m,apparent_temperature,precipitation,"
               f"weather_code,wind_speed_10m,wind_gusts_10m,is_day"
               f"&hourly=precipitation_probability"
               f"&windspeed_unit=ms"
               f"&timezone=Asia%2FDamascus&forecast_days=1")
        data = requests.get(url, timeout=10).json()
        cur = data.get("current", {})
        if not cur:
            return "⚠️ تعذر جلب البيانات.", None

        now = datetime.now(pytz.timezone('Asia/Damascus'))
        hkey = now.strftime("%Y-%m-%dT%H:00")
        pop = 0
        hourly = data.get("hourly", {})
        for i, t in enumerate(hourly.get("time", [])):
            if t == hkey and i < len(hourly.get("precipitation_probability", [])):
                pop = hourly["precipitation_probability"][i] or 0
                break

        status = translate_wmo(cur.get("weather_code", 0))
        if cur.get("is_day") == 0 and cur.get("weather_code") in (0, 1):
            status = status.replace("☀️", "🌙").replace("🌤️", "🌙")

        wind_val = cur.get('wind_speed_10m') or 0
        gust_val = cur.get('wind_gusts_10m') or 0

        report = (
            f"╔══════════════════════════════╗\n"
            f"║  🌐  حالة الطقس\n"
            f"║  📍  {loc_name}\n"
            f"╚══════════════════════════════╝\n"
            f"🕒 {format_syria_time(datetime.now(pytz.utc))}\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"☁️ الحالة: {status}\n"
            f"🌡️ الحرارة: {round(cur.get('temperature_2m') or 0)}°م\n"
            f"🤔 المحسوسة: {round(cur.get('apparent_temperature') or 0)}°م\n"
            f"💧 الرطوبة: {cur.get('relative_humidity_2m') or 0}%\n"
            f"🌧️ الأمطار الآن: {cur.get('precipitation') or 0} ملم\n"
            f"🌂 احتمال الأمطار: {pop}%\n"
            f"🌬️ الرياح: {wind_val:.1f} م/ث\n"
            f"💨 الهبات: {gust_val:.1f} م/ث\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🤖 النموذج: {FORECAST_MODEL_NAME}"
        )
        btns = build_inline_keyboard_for_location(query_name)
        btns.append([InlineKeyboardButton("⏱️ 3 ساعات", callback_data=f"3h_{query_name}"),
                     InlineKeyboardButton("📅 5 أيام", callback_data=f"forecast_{query_name}")])
        return report, InlineKeyboardMarkup(btns)
    except Exception as e:
        logger.error(f"weather: {e}")
        return "⚠️ حدث خطأ أثناء الاتصال بخدمة الطقس.", None

# ==================== 3 ساعات ====================
def get_forecast_3hours(query_name):
    lat, lon, _ = resolve_location(query_name)
    if not lat:
        return f"❌ لم يتم العثور على '{query_name}'."
    try:
        url = (f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}"
               f"&hourly=temperature_2m,apparent_temperature,precipitation,"
               f"precipitation_probability,weather_code,wind_speed_10m"
               f"&windspeed_unit=ms"
               f"&models={FORECAST_MODEL}"
               f"&timezone=Asia%2FDamascus&forecast_days=2")
        hourly = requests.get(url, timeout=10).json().get("hourly", {})
        times = hourly.get("time", [])
        if not times:
            return "⚠️ تعذر جلب التوقعات."
        now_key = datetime.now(pytz.timezone('Asia/Damascus')).strftime("%Y-%m-%dT%H:00")
        start = next((i for i, t in enumerate(times) if t >= now_key), 0)

        report = (
            f"╔══════════════════════════════╗\n"
            f"║  ⏱️  توقعات 3 ساعات\n"
            f"║  📍  {query_name}\n"
            f"╚══════════════════════════════╝\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        )
        for i in range(start, min(start + 3, len(times))):
            dt = datetime.fromisoformat(times[i]).replace(tzinfo=pytz.timezone('Asia/Damascus'))
            wind = hourly['wind_speed_10m'][i] or 0
            report += (
                f"\n📆 **{ARABIC_DAYS[dt.weekday()]} — "
                f"{dt.strftime('%I:%M').lstrip('0')} "
                f"{'ص' if dt.strftime('%p') == 'AM' else 'م'}**\n"
                f"     ☁️ الحالة: {translate_wmo(hourly['weather_code'][i])}\n"
                f"     🌡️ الحرارة: {round(hourly['temperature_2m'][i] or 0)}°م\n"
                f"     🤔 المحسوسة: {round(hourly['apparent_temperature'][i] or 0)}°م\n"
                f"     🌧️ احتمال الأمطار: {hourly['precipitation_probability'][i] or 0}%\n"
                f"     💧 كمية الأمطار: {hourly['precipitation'][i] or 0} ملم\n"
                f"     🌬️ الرياح: {wind:.1f} م/ث\n"
                f"     ─────────────────────\n"
            )
        return report + f"\n🤖 النموذج: {FORECAST_MODEL_NAME}"
    except Exception as e:
        logger.error(f"3h: {e}")
        return "⚠️ حدث خطأ."

# ==================== 5 أيام لموقع واحد ====================
def get_forecast_5days(query_name):
    lat, lon, _ = resolve_location(query_name)
    if not lat:
        return f"❌ لم يتم العثور على '{query_name}'."
    try:
        url = (f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}"
               f"&daily=weather_code,temperature_2m_max,temperature_2m_min,"
               f"precipitation_sum,precipitation_probability_max,"
               f"wind_speed_10m_max,wind_gusts_10m_max,"
               f"sunrise,sunset,uv_index_max"
               f"&windspeed_unit=ms"
               f"&models={FORECAST_MODEL}"
               f"&timezone=Asia%2FDamascus&forecast_days=5")
        daily = requests.get(url, timeout=10).json().get("daily", {})
        times = daily.get("time", [])
        if not times:
            return "⚠️ تعذر جلب التوقعات."

        report = (
            f"╔══════════════════════════════╗\n"
            f"║  📅  توقع 5 أيام\n"
            f"║  📍  {query_name}\n"
            f"╚══════════════════════════════╝\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        )
        for i in range(min(5, len(times))):
            dt = datetime.fromisoformat(times[i]).replace(tzinfo=pytz.timezone('Asia/Damascus'))
            sr = format_time_12h_syria(daily["sunrise"][i])
            ss = format_time_12h_syria(daily["sunset"][i])
            wind = daily['wind_speed_10m_max'][i] or 0
            gust = daily['wind_gusts_10m_max'][i] or 0

            report += (
                f"\n📆 **{ARABIC_DAYS[dt.weekday()]} — {dt.strftime('%d/%m')}**\n"
                f"     ☁️ الحالة: {translate_wmo(daily['weather_code'][i])}\n"
                f"     🌡️ الحرارة: {round(daily['temperature_2m_min'][i] or 0)}° ← "
                f"{round(daily['temperature_2m_max'][i] or 0)}°م\n"
                f"     🌧️ احتمال الأمطار: {daily['precipitation_probability_max'][i] or 0}%\n"
                f"     💧 كمية الأمطار: {daily['precipitation_sum'][i] or 0} ملم\n"
                f"     🌬️ الرياح: {wind:.1f} م/ث\n"
                f"     💨 الهبات: {gust:.1f} م/ث\n"
                f"     ☀️ الأشعة فوق البنفسجية: {round(daily['uv_index_max'][i] or 0)}\n"
                f"     🌅 الشروق: {sr}\n"
                f"     🌇 الغروب: {ss}\n"
                f"     ─────────────────────\n"
            )
        return report + f"\n🤖 النموذج: {FORECAST_MODEL_NAME}"
    except Exception as e:
        logger.error(f"5d: {e}")
        return "⚠️ حدث خطأ أثناء جلب التوقعات."

# ==================== توقع 5 أيام للمناطق ====================
def _fetch_5days_daily(lat, lon):
    url = (f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}"
           f"&daily=weather_code,temperature_2m_max,temperature_2m_min,"
           f"precipitation_probability_max,wind_speed_10m_max"
           f"&windspeed_unit=ms&models={FORECAST_MODEL}"
           f"&timezone=Asia%2FDamascus&forecast_days=5")
    return requests.get(url, timeout=10).json().get("daily", {})

def _fetch_2days_daily(lat, lon):
    url = (f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}"
           f"&daily=weather_code,temperature_2m_max,temperature_2m_min,"
           f"precipitation_sum,precipitation_probability_max,wind_speed_10m_max"
           f"&windspeed_unit=ms&models={FORECAST_MODEL}"
           f"&timezone=Asia%2FDamascus&forecast_days=2")
    return requests.get(url, timeout=10).json().get("daily", {})

def _format_5days_detailed(city_name, daily):
    times = daily.get("time", [])
    if not times:
        return f"\n🏙️ **{city_name}**\n   ❌ البيانات غير متاحة\n"
    codes = daily.get('weather_code', [0] * 5)
    tmaxs = daily.get('temperature_2m_max', [0] * 5)
    tmins = daily.get('temperature_2m_min', [0] * 5)
    rains = daily.get('precipitation_probability_max', [0] * 5)
    winds = daily.get('wind_speed_10m_max', [0] * 5)

    out = (
        f"\n╔══════════════════════════════╗\n"
        f"║  🏙️  {city_name}\n"
        f"╚══════════════════════════════╝\n"
    )
    for i in range(min(5, len(times))):
        dt = datetime.fromisoformat(times[i]).replace(tzinfo=pytz.timezone('Asia/Damascus'))
        day_name = ARABIC_DAYS[dt.weekday()]
        status = translate_wmo(codes[i])
        tmin = round(tmins[i] or 0)
        tmax = round(tmaxs[i] or 0)
        rain = rains[i] or 0
        wind = winds[i] or 0
        out += (
            f"\n📆 **{day_name} — {dt.strftime('%d/%m')}**\n"
            f"     ☁️ الحالة: {status}\n"
            f"     🌡️ الحرارة: {tmin}° ← {tmax}°م\n"
            f"     🌧️ احتمال الأمطار: {rain}%\n"
            f"     🌬️ الرياح: {wind:.1f} م/ث\n"
            f"     ─────────────────────\n"
        )
    return out

# ==================== أوامر البوت (Handlers) ====================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "أهلاً بك في بوت طقس سوريا! 🇸🇾\nاختر من القائمة أدناه أو اكتب اسم مدينتك:",
        reply_markup=get_main_reply_keyboard()
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    
    if text == "📍 المحافظات السورية":
        await update.message.reply_text("اختر المحافظة:", reply_markup=build_governorates_keyboard())
        
    elif text == "🌤️ طقس دمشق":
        report, markup = get_weather_now("دمشق")
        await update.message.reply_text(report, reply_markup=markup, parse_mode="Markdown")
        
    elif text == "📅 توقع 5 أيام للمناطق":
        await update.message.reply_text("اختر المنطقة:", reply_markup=build_regions_keyboard())
        
    elif text == "📅 توقع يومان للمناطق الأربع":
        # تمثيل مبدئي، يمكنك إضافة دالة مخصصة لهذا الخيار
        await update.message.reply_text("هذا الخيار قيد التطوير.")
        
    else:
        # البحث عن المدينة أو القرية
        report, markup = get_weather_now(text)
        await update.message.reply_text(report, reply_markup=markup, parse_mode="Markdown")

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "back_govs":
        await query.edit_message_text("اختر المحافظة:", reply_markup=build_governorates_keyboard())
        
    elif data.startswith("gov_"):
        gov = data.split("_", 1)[1]
        await query.edit_message_text(f"اختر القرية أو المدينة في {gov}:", reply_markup=build_villages_keyboard_for_gov(gov))
        
    elif data.startswith("center_"):
        loc = data.split("_", 1)[1]
        report, markup = get_weather_now(loc)
        await query.edit_message_text(report, reply_markup=markup, parse_mode="Markdown")
        
    elif data.startswith("weather_"):
        loc = data.split("_", 1)[1]
        report, markup = get_weather_now(loc)
        await query.edit_message_text(report, reply_markup=markup, parse_mode="Markdown")
        
    elif data.startswith("3h_"):
        loc = data.split("_", 1)[1]
        report = get_forecast_3hours(loc)
        await query.edit_message_text(report, parse_mode="Markdown")
        
    elif data.startswith("forecast_"):
        loc = data.split("_", 1)[1]
        report = get_forecast_5days(loc)
        await query.edit_message_text(report, parse_mode="Markdown")
        
    elif data.startswith("f5d_"):
        region = data.split("_", 1)[1]
        # مثال مبسط لجلب توقعات المنطقة
        await query.edit_message_text(f"توقعات 5 أيام لمنطقة {region} قيد التطوير.")

def main():
    application = Application.builder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(CallbackQueryHandler(handle_callback))

    logger.info("Bot is running...")
    application.run_polling()

if __name__ == '__main__':
    main()
