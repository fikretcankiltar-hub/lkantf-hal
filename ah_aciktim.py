
# ====================================================================
#   PROJECT: AH+ACIKTIM Web Application (LKANT+F Technology) - Sürüm 2.5
#   FEATURES: Full PWA (Android App Mode), 4 Languages, 100 Tables
#   DEPLOYMENT: Production Ready for GitHub & Render
#   UPDATE: LKANT+F Video Intro Integrated (Safe Deploy with Autoplay)
# ====================================================================

import os
import json
import random
import string
from datetime import datetime
from flask import Flask, render_template_string, request, redirect, url_for, session, flash, jsonify
from flask_login import LoginManager, login_user, logout_user, login_required, current_user, UserMixin
from flask_bcrypt import Bcrypt
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.secret_key = os.urandom(24)

# Kalıcı veritabanı bağlantısı
db_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'ah_aciktim.db')
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'restaurant_login'

# ==========================================
#               VERİ MODELLERİ
# ==========================================

class Restaurant(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    code = db.Column(db.String(8), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now)
    tables = db.relationship('DiningTable', backref='restaurant', lazy=True, cascade="all, delete-orphan")
    orders = db.relationship('Order', backref='restaurant', lazy=True, cascade="all, delete-orphan")

class MenuItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    restaurant_id = db.Column(db.Integer, db.ForeignKey('restaurant.id'), nullable=False)
    item_number = db.Column(db.Integer, nullable=False)
    name = db.Column(db.String(100), nullable=False)

class DiningTable(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    restaurant_id = db.Column(db.Integer, db.ForeignKey('restaurant.id'), nullable=False)
    table_number = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(10), default='bos')

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    restaurant_id = db.Column(db.Integer, db.ForeignKey('restaurant.id'), nullable=False)
    table_number = db.Column(db.Integer, nullable=False)
    customer_name = db.Column(db.String(100), nullable=False)
    general_note = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(30), default='Onay Bekliyor')
    rating = db.Column(db.Integer, nullable=True)
    waiter_call = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.now)
    items = db.relationship('OrderItem', backref='order', lazy=True, cascade="all, delete-orphan")

class OrderItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
    item_number = db.Column(db.Integer, nullable=False)
    quantity = db.Column(db.Integer, default=1)
    item_note = db.Column(db.String(200), nullable=True)
    tea_quantity = db.Column(db.Integer, default=0)

@login_manager.user_loader
def load_user(user_id):
    return Restaurant.query.get(int(user_id))

def generate_unique_code():
    while True:
        code = ''.join(random.choices(string.digits, k=8))
        if not Restaurant.query.filter_by(code=code).first():
            return code

# ==========================================
#           ÇOKLU DİL SÖZLÜĞÜ (4 DİL)
# ==========================================

translations = {
    'tr': {
        'app_name': 'AH+ACIKTIM', 'tech': 'TEKNOLOJİ', 'customer_login': 'Müşteri Girişi',
        'restaurant_code': 'Restoran Kodu (8 Haneli)', 'your_name': 'Adınız', 'enter': 'Sisteme Bağlan',
        'select_table': 'Masa Seçimi', 'order_page': 'Sipariş Ekranı', 'dish_number': 'Yemek No',
        'quantity': 'Adet', 'note': 'Müşteri Notu (Tuzsuz, şekersiz vb.)', 'tea_qty': 'Çay Adeti ☕',
        'call_waiter': 'Garson Çağır 🔔', 'submit_order': 'Siparişi Mutfağa Gönder 🚀',
        'rating_title': 'Hesap Kapatma ve Puanlama', 'send_rating': 'Hesabı Kapat & Puanı Gönder', 'login': 'Restoran Girişi',
        'register': 'Yeni Restoran Kaydı', 'email': 'E-posta Adresi', 'password': 'Şifre',
        'dashboard': 'Yönetim Paneli', 'manage_menu': 'Menü Tanımlama', 'manage_tables': '100 Masa Durumu',
        'orders': 'Gelen Canlı Siparişler', 'invalid_code': 'Hatalı kod girdin usta, kontrol et!',
        'back_to_panel': 'Panele Dön', 'add_item': '+ Yeni Kalem Yemek Ekle', 'order_status': 'Sipariş Durumu',
        'ask_bill': 'Hesap İste & Masadan Kalk 💳'
    },
    'en': {
        'app_name': 'AH+ACIKTIM', 'tech': 'TECHNOLOGY', 'customer_login': 'Customer Login',
        'restaurant_code': 'Restaurant Code (8 Digits)', 'your_name': 'Your Name', 'enter': 'Connect to System',
        'select_table': 'Select Your Table', 'order_page': 'Order Screen', 'dish_number': 'Dish No',
        'quantity': 'Qty', 'note': 'Customer Note (No salt, sugar-free etc.)', 'tea_qty': 'Tea Quantity ☕',
        'call_waiter': 'Call Waiter 🔔', 'submit_order': 'Send Order to Kitchen 🚀',
        'rating_title': 'Close Bill & Rate Experience', 'send_rating': 'Close Bill & Send Rating', 'login': 'Restaurant Login',
        'register': 'Register New Restaurant', 'email': 'Email Address', 'password': 'Password',
        'dashboard': 'Dashboard', 'manage_menu': 'Menu Setup', 'manage_tables': '100 Tables Grid',
        'orders': 'Live Orders Log', 'invalid_code': 'Invalid code, please check!',
        'back_to_panel': 'Back to Dashboard', 'add_item': '+ Add New Dish Row', 'order_status': 'Order Status',
        'ask_bill': 'Request Bill & Leave credentials 💳'
    },
    'de': {
        'app_name': 'AH+ACIKTIM', 'tech': 'TECHNOLOGIE', 'customer_login': 'Kundenlogin',
        'restaurant_code': 'Restaurantcode (8-stellig)', 'your_name': 'Ihr Name', 'enter': 'Mit System verbinden',
        'select_table': 'Tisch auswählen', 'order_page': 'Bestellbildschirm', 'dish_number': 'Gericht Nr.',
        'quantity': 'Anzahl', 'note': 'Kundenhinweis (Salzfrei, zuckerfrei usw.)', 'tea_qty': 'Tee Anzahl ☕',
        'call_waiter': 'Kellner rufen 🔔', 'submit_order': 'Bestellung an die Küche senden 🚀',
        'rating_title': 'Rechnung schließen & Bewerten', 'send_rating': 'Rechnung schließen & Senden', 'login': 'Restaurant Login',
        'register': 'Neues Restaurant registrieren', 'email': 'E-Mail-Adresse', 'password': 'Passwort',
        'dashboard': 'Dashboard', 'manage_menu': 'Menüverwaltung', 'manage_tables': '100 Tische Status',
        'orders': 'Live-Bestellungen', 'invalid_code': 'Ungültiger Code, bitte überprüfen!',
        'back_to_panel': 'Zurück zum Dashboard', 'add_item': '+ Neue Zeile hinzufügen', 'order_status': 'Bestellstatus',
        'ask_bill': 'Rechnung anfordern 💳'
    },
    'ru': {
        'app_name': 'AH+ACIKTIM', 'tech': 'ТЕХНОЛОГИЯ', 'customer_login': 'Вход для клиентов',
        'restaurant_code': 'Код ресторана (8 цифр)', 'your_name': 'Ваше имя', 'enter': 'Подключиться к системе',
        'select_table': 'Выбор стола', 'order_page': 'Экран заказа', 'dish_number': 'Номер блюда',
        'quantity': 'Кол-во', 'note': 'Заметка (Без соли, без сахара и т.д.)', 'tea_qty': 'Кол-во чая ☕',
        'call_waiter': 'Позвать официанта 🔔', 'submit_order': 'Отправить заказ на кухню 🚀',
        'rating_title': 'Закрытие счета и оценка', 'send_rating': 'Закрыть счет и отправить оценку', 'login': 'Вход для ресторанов',
        'register': 'Регистрация нового ресторана', 'email': 'Электронная почта', 'password': 'Пароль',
        'dashboard': 'Панель управления', 'manage_menu': 'Настройка меню', 'manage_tables': 'Карта на 100 столов',
        'orders': 'Живой лог заказов', 'invalid_code': 'Неверный код, проверьте еще раз!',
        'back_to_panel': 'Вернуться в исполняемую панель', 'add_item': '+ Добавить новое блюдо', 'order_status': 'Статус заказа',
        'ask_bill': 'Запросить счет 💳'
    }
}

# ==========================================
#          MİMARİ TEMPLATE MOTORU
# ==========================================

def render_lkantf_framework(main_content_html, **kwargs):
    master_layout = '''
    <!DOCTYPE html>
    <html lang="tr">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        
        <meta name="apple-mobile-web-app-capable" content="yes">
        <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
        <meta name="theme-color" content="#0c0c0e">
        <link rel="manifest" href="/manifest.json">
        
        <title>AH+ACIKTIM | LKANT+F TEKNOLOJİ</title>
        <style>
            * { box-sizing: border-box; margin: 0; padding: 0; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }
            body { background: #0c0c0e; color: #f5f5f7; display: flex; flex-direction: column; min-height: 100vh; overflow-x: hidden; }
            
            .neon-brand { text-align: center; padding: 25px 10px; font-size: 2.8rem; font-weight: 900; color: #fff; letter-spacing: 2px;
                text-shadow: 0 0 10px #00e6ff, 0 0 20px #00e6ff; animation: pulseGlow 3s infinite alternate; }
            @keyframes pulseGlow {
                0% { text-shadow: 0 0 10px #00e6ff, 0 0 20px #00e6ff; opacity: 0.9; }
                100% { text-shadow: 0 0 25px #ff0055, 0 0 50px #ff0055; opacity: 1; }
            }
            
            .lang-wrapper { text-align: center; margin-bottom: 15px; }
            .lang-wrapper button { background: #1c1c24; border: 1px solid #2d2d3d; color: #fff; padding: 6px 12px; margin: 0 4px; 
                cursor: pointer; border-radius: 6px; font-weight: 600; transition: all 0.2s ease; }
            .lang-wrapper button:hover { background: #00e6ff; color: #0c0c0e; border-color: #00e6ff; transform: translateY(-2px); }
            
            .main-frame { max-width: 650px; width: 92%; margin: 10px auto 40px auto; padding: 25px; background: #13131a; 
                border-radius: 20px; box-shadow: 0 10px 30px rgba(0, 230, 255, 0.08); border: 1px solid #1f1f2e; flex: 1; }
            
            h2 { margin-bottom: 20px; font-weight: 700; color: #fff; text-align: center; }
            input, select, textarea { width: 100%; padding: 12px 16px; margin: 10px 0; border-radius: 8px; border: 1px solid #2d2d3d; 
                background: #08080c; color: #00e6ff; font-size: 1rem; font-weight: 600; transition: all 0.2s ease; }
            input:focus, select:focus, textarea:focus { outline: none; border-color: #00e6ff; box-shadow: 0 0 8px rgba(0, 230, 255, 0.3); }
            textarea { height: 80px; resize: none; }
            
            button[type="submit"], .action-btn { background: #00e6ff; color: #0c0c0e; font-weight: 800; text-transform: uppercase; 
                letter-spacing: 1px; cursor: pointer; transition: all 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275); border: none; padding: 14px; border-radius: 8px; width: 100%; margin-top: 10px; }
            button[type="submit"]:hover, .action-btn:hover { background: #ff0055; color: #fff; transform: scale(1.02); box-shadow: 0 5px 15px rgba(255, 0, 85, 0.4); }
            
            .grid-100 { display: grid; grid-template-columns: repeat(5, 1fr); gap: 10px; margin-top: 20px; max-height: 400px; overflow-y: auto; padding-right: 5px; }
            .grid-100::-webkit-scrollbar { width: 6px; }
            .grid-100::-webkit-scrollbar-thumb { background: #2d2d3d; border-radius: 4px; }
            .grid-box { aspect-ratio: 1; display: flex; align-items: center; justify-content: center; border-radius: 10px; font-weight: 800; font-size: 1.1rem; cursor: pointer; transition: all 0.2s ease; }
            .grid-box:hover { transform: scale(1.08); filter: brightness(1.2); }
            .bos { background: linear-gradient(135deg, #2ecc71, #27ae60); color: #fff; box-shadow: 0 4px 10px rgba(46, 204, 113, 0.2); }
            .dolu { background: linear-gradient(135deg, #e74c3c, #c0392b); color: #fff; box-shadow: 0 4px 10px rgba(231, 76, 60, 0.2); }
            
            .item-row { background: #1c1c24; padding: 15px; border-radius: 12px; margin: 12px 0; border: 1px solid #2d2d3d; }
            
            .status-badge { display: inline-block; padding: 6px 12px; border-radius: 20px; font-weight: 800; font-size: 0.9rem; text-transform: uppercase; margin-top: 10px; }
            .status-waiting { background: #f39c12; color: #fff; }
            .status-cooking { background: #3498db; color: #fff; }
            .status-served { background: #2ecc71; color: #fff; }
            .status-bill { background: #9b59b6; color: #fff; }
            
            .star-rating { display: flex; justify-content: center; gap: 15px; margin: 20px 0; font-size: 2.5rem; color: #3d3d4d; }
            .star-rating span { cursor: pointer; transition: color 0.2s ease; }
            .star-rating span.gold { color: #f1c40f; text-shadow: 0 0 10px rgba(241, 196, 15, 0.4); }
            
            .order-card { background: #1c1c24; border-radius: 12px; padding: 18px; margin: 15px 0; border-left: 5px solid #00e6ff; box-shadow: 0 4px 12px rgba(0,0,0,0.2); }
            
            .ctrl-btn { background: #2c2c35; color: #fff; padding: 5px 10px; border: none; border-radius: 4px; font-weight: bold; cursor: pointer; margin: 0 5px; }
            .ctrl-btn:hover { background: #00e6ff; color: #000; }

            .lkantf-footer { text-align: center; padding: 20px; font-weight: 900; letter-spacing: 4px; font-size: 1.1rem; background: #08080c; color: #00e6ff; border-top: 1px solid #13131a; margin-top: auto; text-shadow: 0 0 8px rgba(0, 230, 255, 0.4); }
            a { color: #00e6ff; text-decoration: none; font-weight: 600; display: inline-block; margin-top: 15px; }
            a:hover { color: #ff0055; }
        </style>
    </head>
    <body>
        <div class="neon-brand"><span id="app_name">AH+ACIKTIM</span></div>
        
        <div class="lang-wrapper">
            <button onclick="switchLanguage('tr')">🇹🇷 TR</button>
            <button onclick="switchLanguage('en')">🇬🇧 EN</button>
            <button onclick="switchLanguage('de')">🇩🇪 DE</button>
            <button onclick="switchLanguage('ru')">🇷🇺 RU</button>
        </div>
        
        <div class="main-frame">
            ''' + main_content_html + '''
        </div>
        
        <div class="lkantf-footer">⚡ LKANT+F TEKNOLOJİ ⚡</div>

        <script>
            const dictionary = ''' + json.dumps(translations) + ''';
            let activeLang = localStorage.getItem('app_lang') || 'tr';
            
            function translateUI() {
                document.querySelectorAll('[data-i18n]').forEach(element => {
                    const translationKey = element.getAttribute('data-i18n');
                    if (dictionary[activeLang] && dictionary[activeLang][translationKey]) {
                        if (element.tagName === 'INPUT' || element.tagName === 'TEXTAREA') {
                            element.setAttribute('placeholder', dictionary[activeLang][translationKey]);
                        } else {
                            element.textContent = dictionary[activeLang][translationKey];
                        }
                    }
                });
                const appNameText = dictionary[activeLang]?.['app_name'] || 'AH+ACIKTIM';
                const techText = dictionary[activeLang]?.['tech'] || 'TEKNOLOJİ';
                document.getElementById('app_name').innerHTML = appNameText + ' <span style="font-size:1.2rem; display:block; color:#ff0055; font-weight:700; letter-spacing:4px;">' + techText + '</span>';
            }
            
            function switchLanguage(targetLang) {
                activeLang = targetLang;
                localStorage.setItem('app_lang', targetLang);
                translateUI();
            }
            window.addEventListener('DOMContentLoaded', translateUI);

            // PWA Android Service Worker Kaydı
            if ('serviceWorker' in navigator) {
                navigator.serviceWorker.register('/sw.js').catch(function() {});
            }
        </script>
    </body>
    </html>
    '''
    return render_template_string(master_layout, **kwargs)

# ==========================================
#         HTML İÇERİK BLOKLARI
# ==========================================

# GİRİŞ FORMU - VİDEO AUTOPLAY KİLİDİ KIRILDI VE STATIC YOLU TANIMLANDI
customer_index_view = '''
<div id="lkantf-intro" style="
    position: fixed; top: 0; left: 0; width: 100vw; height: 100vh; 
    background: #0c0c0e; z-index: 9999; display: flex; align-items: center; justify-content: center; 
    transition: opacity 0.8s ease; cursor: pointer;" onclick="closeIntro()">
    
    <video id="introVideo" width="100%" height="100%" style="object-fit: cover;" autoplay muted playsinline>
        <source src="/static/lkantf_intro.mp4" type="video/mp4">
        Sistem yükleniyor dostum...
    </video>

    <div style="position: absolute; top: 20px; right: 20px; background: rgba(0,0,0,0.6); 
        color: #00e6ff; padding: 8px 16px; border-radius: 20px; font-weight: bold; 
        font-size: 0.8rem; border: 1px solid #00e6ff; letter-spacing: 1px; text-transform: uppercase;">
        GEÇ ➜
    </div>
</div>

<h2 data-i18n="customer_login">Müşteri Girişi</h2>
<form action="/customer/auth" method="POST">
    <input type="text" name="code" data-i18n="restaurant_code" maxlength="8" required>
    <input type="text" name="name" data-i18n="your_name" required>
    <button type="submit" data-i18n="enter">Sisteme Bağlan</button>
</form>
<div style="text-align: center; margin-top: 25px; border-top: 1px solid #222; padding-top: 15px;">
    <a href="/restaurant/login" data-i18n="login">Restoran Girişi</a>
</div>

<script>
    const intro = document.getElementById('lkantf-intro');
    const video = document.getElementById('introVideo');

    function closeIntro() {
        if(intro) {
            intro.style.opacity = '0';
            setTimeout(() => {
                intro.style.display = 'none';
                sessionStorage.setItem('intro_seen', 'true');
            }, 800);
        }
    }

    document.addEventListener("DOMContentLoaded", function() {
        if (sessionStorage.getItem('intro_seen')) {
            if(intro) intro.style.display = 'none';
            return;
        }

        if(video) {
            video.onended = function() {
                closeIntro();
            };
            
            // Tarayıcı engelini tamamen kırmak için tetikleyici fonksiyon
            video.play().catch(function() {
                setTimeout(closeIntro, 6000);
            });
        }
    });
</script>
'''

table_selection_view = '''
<h2 data-i18n="select_table">Masa Seçimi</h2>
<p style="text-align:center; color:#a0a0b0; margin-bottom:15px;"><strong>Mekan:</strong> {{ restaurant.name }}</p>
<div class="grid-100">
    {% for table in tables %}
        <div class="grid-box {{ table.status }}" onclick="window.location='/order/screen/{{ table.id }}'">{{ table.table_number }}</div>
    {% endfor %}
</div>
'''

order_screen_view = '''
<h2 data-i18n="order_page">Sipariş Ekranı</h2>
<p style="text-align:center; color:#00e6ff; font-weight:700; margin-bottom:15px;">Masa No: {{ table.table_number }}</p>

<div id="liveStatusContainer" style="background:#1c1c24; padding:15px; border-radius:12px; margin-bottom:20px; border:1px solid #2d2d3d; text-align:center; display:none;">
    <h3 data-i18n="order_status">Sipariş Durumu</h3>
    <div id="statusBadgeSlot"></div>
    <p style="font-size:0.9rem; color:#a0a0b0; margin-top:10px;">Sayfayı kapatmayın, durum otomatik yenilenir.</p>
    <button onclick="triggerBillRequest()" class="action-btn" style="background:#9b59b6; color:#fff; margin-top:15px;" data-i18n="ask_bill">Hesap İste & Masadan Kalk 💳</button>
</div>

<form id="kitchenOrderForm" onsubmit="processOrder(event)">
    <div id="dynamicItemsContainer">
        <div class="item-row">
            <input type="number" placeholder="Yemek No (Örn: 1)" class="dish-num" required>
            <input type="number" placeholder="Adet" class="dish-qty" value="1" min="1" required>
            <input type="text" placeholder="Not (Tuzsuz, şekersiz vb.)" class="dish-note">
            
            <div style="margin-top:10px; display:flex; align-items:center; background:#08080c; padding:8px; border-radius:6px;">
                <span data-i18n="tea_qty" style="font-weight:600; color:#a0a0b0; font-size:0.9rem;">Çay Adeti ☕</span>
                <div style="margin-left:auto; display:flex; align-items:center;">
                    <button type="button" class="ctrl-btn" onclick="adjustTea(this, -1)">-</button>
                    <input type="number" class="dish-tea-qty" value="0" min="0" style="width:50px; text-align:center; margin:0; padding:4px; background:#1c1c24;">
                    <button type="button" class="ctrl-btn" onclick="adjustTea(this, 1)">+</button>
                </div>
            </div>
        </div>
    </div>
    
    <button type="button" onclick="addNewRow()" class="action-btn" style="background:#2d2d3d; color:#fff; margin-bottom:15px;" data-i18n="add_item">+ Yeni Kalem Yemek Ekle</button>
    <textarea id="general_order_note" placeholder="Restorana iletmek istediğiniz genel not..." data-i18n="note"></textarea>
    
    <div style="display:flex; gap:10px; margin-top:10px;">
        <button type="button" onclick="triggerWaiter()" style="background:#ff0055; color:#fff; flex:1;" data-i18n="call_waiter">Garson Çağır 🔔</button>
        <button type="submit" style="flex:2;" data-i18n="submit_order">Siparişi Mutfağa Gönder 🚀</button>
    </div>
</form>

<script>
    function adjustTea(btn, amount) {
        const input = btn.parentElement.querySelector('.dish-tea-qty');
        let current = parseInt(input.value) || 0;
        current += amount;
        if(current < 0) current = 0;
        input.value = current;
    }

    function addNewRow() {
        const container = document.getElementById('dynamicItemsContainer');
        const div = document.createElement('div');
        div.className = 'item-row';
        div.innerHTML = `
            <input type="number" placeholder="Yemek No" class="dish-num" required>
            <input type="number" placeholder="Adet" class="dish-qty" value="1" min="1" required>
            <input type="text" placeholder="Not (Tuzsuz, şekersiz vb.)" class="dish-note">
            <div style="margin-top:10px; display:flex; align-items:center; background:#08080c; padding:8px; border-radius:6px;">
                <span style="font-weight:600; color:#a0a0b0; font-size:0.9rem;">${dictionary[activeLang]?.['tea_qty'] || 'Çay Adeti ☕'}</span>
                <div style="margin-left:auto; display:flex; align-items:center;">
                    <button type="button" class="ctrl-btn" onclick="adjustTea(this, -1)">-</button>
                    <input type="number" class="dish-tea-qty" value="0" min="0" style="width:50px; text-align:center; margin:0; padding:4px; background:#1c1c24;">
                    <button type="button" class="ctrl-btn" onclick="adjustTea(this, 1)">+</button>
                </div>
            </div>
        `;
        container.appendChild(div);
    }

    async function processOrder(e) {
        e.preventDefault();
        const itemsList = [];
        document.querySelectorAll('.item-row').forEach(row => {
            itemsList.push({
                number: row.querySelector('.dish-num').value,
                quantity: row.querySelector('.dish-qty').value,
                note: row.querySelector('.dish-note').value,
                tea_qty: row.querySelector('.dish-tea-qty').value
            });
        });
        const note = document.getElementById('general_order_note').value;
        
        const response = await fetch('/api/v1/submit_order', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ table_id: {{ table.id }}, items: itemsList, general_note: note })
        });
        const result = await response.json();
        if(result.order_id) {
            localStorage.setItem('lkantf_active_order', result.order_id);
            checkOrderStateLoop();
            document.getElementById('kitchenOrderForm').reset();
            alert(activeLang === 'tr' ? 'Sipariş iletildi, takibe alındı kanka.' : 'Order sent!');
        }
    }

    async function triggerWaiter() {
        await fetch('/api/v1/call_waiter', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ table_id: {{ table.id }} })
        });
        alert('Garson çağrıldı!');
    }

    async function checkOrderStateLoop() {
        const orderId = localStorage.getItem('lkantf_active_order');
        if(!orderId) return;

        document.getElementById('liveStatusContainer').style.display = 'block';
        const response = await fetch('/api/v1/order_status/' + orderId);
        const data = await response.json();
        const slot = document.getElementById('statusBadgeSlot');

        if(data.status === 'Onay Bekliyor') {
            slot.innerHTML = '<span class="status-badge status-waiting">⏳ Onay Bekliyor</span>';
        } else if(data.status === 'Hazırlanıyor') {
            slot.innerHTML = '<span class="status-badge status-cooking">🔥 Hazırlanıyor</span>';
        } else if(data.status === 'Masaya Geldi') {
            slot.innerHTML = '<span class="status-badge status-served">✅ Masaya Geldi</span>';
        } else if(data.status === 'Hesap İstendi') {
            slot.innerHTML = '<span class="status-badge status-bill">💵 Hesap Bekleniyor...</span>';
        } else if(data.status === 'Kapatıldı') {
            window.location = '/experience/rating/' + orderId;
            return;
        }
        setTimeout(checkOrderStateLoop, 4000);
    }

    function triggerBillRequest() {
        const orderId = localStorage.getItem('lkantf_active_order');
        if(!orderId) return;
        fetch('/api/v1/request_bill', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ order_id: orderId })
        });
    }

    if(localStorage.getItem('lkantf_active_order')) {
        checkOrderStateLoop();
    }
</script>
'''

customer_rating_view = '''
<h2 data-i18n="rating_title">Hesap Kapatma ve Puanlama</h2>
<div class="star-rating">
    <span onclick="setStars(1)">☆</span><span onclick="setStars(2)">☆</span><span onclick="setStars(3)">☆</span><span onclick="setStars(4)">☆</span><span onclick="setStars(5)">☆</span>
</div>
<button onclick="commitRating()" class="action-btn" data-i18n="send_rating">Hesabı Kapat & Puanı Gönder</button>

<script>
    let globalRating = 0;
    function setStars(score) {
        globalRating = score;
        const stars = document.querySelectorAll('.star-rating span');
        stars.forEach((star, index) => {
            star.textContent = index < score ? '★' : '☆';
            star.classList.toggle('gold', index < score);
        });
    }
    async function commitRating() {
        if(globalRating === 0) { alert('Puan seç kanka!'); return; }
        await fetch('/api/v1/submit_rate', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ order_id: {{ order_id }}, score: globalRating })
        });
        localStorage.removeItem('lkantf_active_order');
        window.location = '/';
    }
</script>
'''

restaurant_login_view = '''
<h2 data-i18n="login">Restoran Girişi</h2>
<form method="POST">
    <input type="email" name="email" data-i18n="email" required>
    <input type="password" name="password" data-i18n="password" required>
    <button type="submit" data-i18n="login">Giriş</button>
</form>
<center><a href="/restaurant/register" data-i18n="register">Yeni Restoran Kaydı</a></center>
'''

restaurant_register_view = '''
<h2 data-i18n="register">Yeni Restoran Kaydı</h2>
<form method="POST">
    <input type="text" name="name" placeholder="Mekan Adı" required>
    <input type="email" name="email" data-i18n="email" required>
    <input type="password" name="password" data-i18n="password" required>
    <button type="submit" data-i18n="register">Kayıt Ol ve Masaları Kur</button>
</form>
'''

restaurant_dashboard_view = '''
<h2 data-i18n="dashboard">Yönetim Paneli</h2>
<div style="background:#1c1c24; padding:15px; border-radius:12px; text-align:center; margin-bottom:20px; border:1px solid #2d2d3d;">
    <p>Mekan: <strong>{{ current_user.name }}</strong></p>
    <p style="color:#00e6ff; font-size:1.8rem; font-weight:900; letter-spacing:2px; margin-top:5px;">{{ current_user.code }}</p>
</div>
<a href="/restaurant/tables_grid"><button class="action-btn" data-i18n="manage_tables" style="background:#2ecc71; color:#fff;">100 Masa Durumu</button></a>
<a href="/restaurant/live_orders"><button class="action-btn" data-i18n="orders">Gelen Canlı Siparişler</button></a>
<a href="/restaurant/menu_setup"><button class="action-btn" data-i18n="manage_menu">Menü Tanımlama</button></a>
<center><a href="/logout" style="color:#ff0055;">Çıkış</a></center>
'''

restaurant_tables_view = '''
<h2 data-i18n="manage_tables">100 Masa Durumu</h2>
<div class="grid-100">
    {% for table in tables %}
        <div class="grid-box {{ table.status }}" onclick="switchTableState({{ table.id }})">{{ table.table_number }}</div>
    {% endfor %}
</div>
<script>
    async function switchTableState(id) {
        await fetch('/api/v1/toggle_table/' + id);
        location.reload();
    }
</script>
'''

restaurant_menu_view = '''
<h2 data-i18n="manage_menu">Menü Tanımlama</h2>
<form method="POST">
    <input type="number" name="item_number" placeholder="Yemek Numarası" required>
    <input type="text" name="name" placeholder="Yemek Adı" required>
    <button type="submit">Menüye Sabitle</button>
</form>
{% for item in menu %}
    <p>No {{ item.item_number }}: {{ item.name }} <a href="/restaurant/menu/delete/{{ item.id }}" style="color:#ff0055;">[Sil]</a></p>
{% endfor %}
'''

restaurant_orders_view = '''
<h2 data-i18n="orders">Gelen Canlı Siparişler</h2>
{% for order in orders if order.status != 'Kapatıldı' %}
    <div class="order-card" style="border-left-color: {% if order.status == 'Hesap İstendi' %}#9b59b6{% elif order.status == 'Hazırlanıyor' %}#3498db{% elif order.status == 'Masaya Geldi' %}#2ecc71{% else %}#00e6ff{% endif %};">
        <strong>Masa {{ order.table_number }}</strong> - {{ order.customer_name }} [{{ order.status }}]
        {% if order.waiter_call %}<p style="color:#ff0055;">🔔 GARSON ÇAĞIRIYOR!</p>{% endif %}
        <ul>
        {% for item in order.items %}
            <li>No {{ item.item_number }} - Adet: {{ item.quantity }} {% if item.tea_quantity > 0 %}[☕ {{ item.tea_quantity }} Çay]{% endif %} ({{ item.item_note or '' }})</li>
        {% endfor %}
        </ul>
        <p>Not: {{ order.general_note or 'Yok' }}</p>
        <button onclick="updateStatus({{ order.id }}, 'Hazırlanıyor')" style="background:#3498db; color:#fff; padding:5px; border:none; margin-right:5px;">Mutfakta Hazırla</button>
        <button onclick="updateStatus({{ order.id }}, 'Masaya Geldi')" style="background:#2ecc71; color:#fff; padding:5px; border:none; margin-right:5px;">Masaya Gönder</button>
        <button onclick="updateStatus({{ order.id }}, 'Kapatıldı')" style="background:#e74c3c; color:#fff; padding:5px; border:none;">Masayı Kapat</button>
    </div>
{% endfor %}
<script>
    async function updateStatus(orderId, nextState) {
        await fetch('/api/v1/update_order_state', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ order_id: orderId, status: nextState })
        });
        location.reload();
    }
</script>
'''

# ==========================================
#                   ROTALAR
# ==========================================

@app.route('/')
def customer_home():
    return render_lkantf_framework(customer_index_view)

@app.route('/manifest.json')
def manifest():
    pwa_data = {
        "short_name": "AH+ACIKTIM",
        "name": "AH+ACIKTIM Web Application",
        "icons": [{"src": "https://cdn-icons-png.flaticon.com/512/3443/3443338.png", "type": "image/png", "sizes": "512x512"}],
        "start_url": "/",
        "background_color": "#0c0c0e",
        "theme_color": "#0c0c0e",
        "display": "standalone",
        "orientation": "portrait"
    }
    return jsonify(pwa_data)

@app.route('/sw.js')
def service_worker():
    js_code = "self.addEventListener('fetch', function(event) { event.respondWith(fetch(event.request)); });"
    return app.response_class(js_code, mimetype='application/javascript')

@app.route('/customer/auth', methods=['POST'])
def customer_auth():
    code = request.form.get('code')
    name = request.form.get('name')
    restaurant = Restaurant.query.filter_by(code=code).first()
    if not restaurant:
        return "<h3>Girdiğin kod veritabanımızda kayıtlı değil kanka!</h3>"
    session['customer_name'] = name
    session['target_restaurant_id'] = restaurant.id
    return redirect(url_for('customer_tables'))

@app.route('/customer/tables')
def customer_tables():
    if 'target_restaurant_id' not in session:
        return redirect(url_for('customer_home'))
    restaurant = Restaurant.query.get(session['target_restaurant_id'])
    tables = DiningTable.query.filter_by(restaurant_id=restaurant.id).all()
    return render_lkantf_framework(table_selection_view, restaurant=restaurant, tables=tables)

@app.route('/order/screen/<int:table_id>')
def order_screen(table_id):
    if 'target_restaurant_id' not in session:
        return redirect(url_for('customer_home'))
    table = DiningTable.query.get(table_id)
    return render_lkantf_framework(order_screen_view, table=table)

# ==========================================
#                 API ROTALARI
# ==========================================

@app.route('/api/v1/submit_order', methods=['POST'])
def api_submit_order():
    data = request.json
    table_id = data['table_id']
    table = DiningTable.query.get(table_id)
    restaurant_id = session.get('target_restaurant_id')
    
    new_order = Order(
        restaurant_id=restaurant_id,
        table_number=table.table_number,
        customer_name=session.get('customer_name', 'Müşteri'),
        general_note=data.get('general_note'),
        status='Onay Bekliyor'
    )
    db.session.add(new_order)
    db.session.flush()
    
    for row in data['items']:
        item = OrderItem(
            order_id=new_order.id,
            item_number=int(row['number']),
            quantity=int(row['quantity']),
            item_note=row.get('note'),
            tea_quantity=int(row.get('tea_qty', 0))
        )
        db.session.add(item)
        
    table.status = 'dolu'
    db.session.commit()
    return jsonify({'order_id': new_order.id})

@app.route('/api/v1/order_status/<int:order_id>')
def api_order_status(order_id):
    order = Order.query.get(order_id)
    if order:
        return jsonify({'status': order.status})
    return jsonify({'status': 'Kapatıldı'})

@app.route('/api/v1/request_bill', methods=['POST'])
def api_request_bill():
    data = request.json
    order = Order.query.get(data['order_id'])
    if order:
        order.status = 'Hesap İstendi'
        db.session.commit()
    return jsonify({'success': True})

@app.route('/api/v1/update_order_state', methods=['POST'])
def api_update_order_state():
    data = request.json
    order = Order.query.get(data['order_id'])
    if order:
        order.status = data['status']
        if data['status'] == 'Kapatıldı':
            table = DiningTable.query.filter_by(restaurant_id=order.restaurant_id, table_number=order.table_number).first()
            if table: table.status = 'bos'
        db.session.commit()
    return jsonify({'success': True})

@app.route('/api/v1/call_waiter', methods=['POST'])
def api_call_waiter():
    data = request.json
    table = DiningTable.query.get(data['table_id'])
    restaurant_id = session.get('target_restaurant_id')
    
    waiter_alert = Order(
        restaurant_id=restaurant_id,
        table_number=table.table_number,
        customer_name=session.get('customer_name', 'Müşteri'),
        waiter_call=True,
        status='Garson Çağrısı'
    )
    db.session.add(waiter_alert)
    db.session.commit()
    return jsonify({'success': True})

@app.route('/experience/rating/<int:order_id>')
def experience_rating(order_id):
    return render_lkantf_framework(customer_rating_view, order_id=order_id)

@app.route('/api/v1/submit_rate', methods=['POST'])
def api_submit_rate():
    data = request.json
    order = Order.query.get(data['order_id'])
    if order:
        order.rating = int(data['score'])
        order.status = 'Kapatıldı'
        table = DiningTable.query.filter_by(restaurant_id=order.restaurant_id, table_number=order.table_number).first()
        if table: table.status = 'bos'
        db.session.commit()
    return jsonify({'success': True})

# ==========================================
#           RESTORAN YETKİLİ ROTALARI
# ==========================================

@app.route('/restaurant/login', methods=['GET', 'POST'])
def restaurant_login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        restaurant = Restaurant.query.filter_by(email=email).first()
        if restaurant and bcrypt.check_password_hash(restaurant.password_hash, password):
            login_user(restaurant)
            return redirect(url_for('restaurant_dashboard'))
    return render_lkantf_framework(restaurant_login_view)

@app.route('/restaurant/register', methods=['GET', 'POST'])
def restaurant_register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        
        if Restaurant.query.filter_by(email=email).first():
            return "Bu e-posta zaten kullanımda!"
            
        code = generate_unique_code()
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        new_restaurant = Restaurant(name=name, email=email, password_hash=hashed_password, code=code)
        db.session.add(new_restaurant)
        db.session.commit()
        
        for number in range(1, 101):
            db.session.add(DiningTable(restaurant_id=new_restaurant.id, table_number=number, status='bos'))
        db.session.commit()
        
        login_user(new_restaurant)
        return redirect(url_for('restaurant_dashboard'))
    return render_lkantf_framework(restaurant_register_view)

@app.route('/restaurant/dashboard')
@login_required
def restaurant_dashboard():
    return render_lkantf_framework(restaurant_dashboard_view)

@app.route('/restaurant/tables_grid')
@login_required
def restaurant_tables_grid():
    tables = DiningTable.query.filter_by(restaurant_id=current_user.id).all()
    return render_lkantf_framework(restaurant_tables_view, tables=tables)

@app.route('/api/v1/toggle_table/<int:table_id>')
@login_required
def api_toggle_table(table_id):
    table = DiningTable.query.get(table_id)
    if table and table.restaurant_id == current_user.id:
        table.status = 'bos' if table.status == 'dolu' else 'dolu'
        db.session.commit()
    return jsonify({'success': True})

@app.route('/restaurant/menu_setup', methods=['GET', 'POST'])
@login_required
def restaurant_menu_setup():
    if request.method == 'POST':
        num = request.form['item_number']
        name = request.form['name']
        db.session.add(MenuItem(restaurant_id=current_user.id, item_number=int(num), name=name))
        db.session.commit()
        return redirect(url_for('restaurant_menu_setup'))
    menu = MenuItem.query.filter_by(restaurant_id=current_user.id).all()
    return render_lkantf_framework(restaurant_menu_view, menu=menu)

@app.route('/restaurant/menu/delete/<int:item_id>')
@login_required
def restaurant_menu_delete(item_id):
    item = MenuItem.query.get(item_id)
    if item and item.restaurant_id == current_user.id:
        db.session.delete(item)
        db.session.commit()
    return redirect(url_for('restaurant_menu_setup'))

@app.route('/restaurant/live_orders')
@login_required
def restaurant_live_orders():
    orders = Order.query.filter_by(restaurant_id=current_user.id).order_by(Order.created_at.desc()).all()
    return render_lkantf_framework(restaurant_orders_view, orders=orders)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    session.clear()
    return redirect(url_for('customer_home'))

# ==========================================
#         RENDER VE GITHUB LİMAN AYARLARI
# ==========================================

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        if not Restaurant.query.filter_by(code='07076789').first():
            test_rest = Restaurant(
                name='LKANT+F Merkez Restoran',
                email='center@lkantf.com',
                password_hash=bcrypt.generate_password_hash('123456').decode('utf-8'),
                code='07076789'
            )
            db.session.add(test_rest)
            db.session.commit()
            for i in range(1, 101):
                db.session.add(DiningTable(restaurant_id=test_rest.id, table_number=i, status='bos'))
            db.session.commit()
            
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
