import http.server
import socketserver
import json
import sqlite3
from urllib.parse import parse_qs, unquote
import os


# --- VERİTABANI MOTORU (BOZMADAN DEVAM) ---
def db_kur():
    conn = sqlite3.connect('halci_plus_f.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS halciler 
                 (kod TEXT PRIMARY KEY, unvan TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS talepler 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, ad TEXT, kod TEXT, kasa INTEGER, 
                  islem TEXT, konum TEXT, durum TEXT DEFAULT 'Bekliyor', tarih TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    conn.commit()
    conn.close()

db_kur()

# --- ARTTIRILMIŞ HAFIZALI VE TARİHLİ ARAYÜZ ---
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>HALCİ+F PRO V2</title>
    <style>
        :root { --ana: #2c3e50; --vurgu: #27ae60; --kasa: #e67e22; --konum: #2980b9; --iptal: #c0392b; }
        body { font-family: 'Segoe UI', Arial, sans-serif; background: #f1f2f6; margin: 0; padding: 10px; display: flex; flex-direction: column; align-items: center; min-height: 100vh; }
        .container { max-width: 550px; width: 100%; background: white; padding: 20px; border-radius: 15px; box-shadow: 0 10px 25px rgba(0,0,0,0.1); box-sizing: border-box; margin-top: 10px; }
        h1 { text-align: center; color: var(--ana); font-weight: 900; margin: 0; font-size: 28px; }
        h2 { text-align: center; color: #7f8c8d; font-size: 13px; margin-top: 5px; margin-bottom: 20px; }
        .Grup { display: flex; gap: 5px; margin-bottom: 25px; }
        .Grup button { flex: 1; padding: 12px; border: 2px solid var(--ana); background: none; font-weight: bold; cursor: pointer; border-radius: 8px; font-size: 14px; }
        .aktif { background: var(--ana) !important; color: white; }
        input, button.ana-btn { width: 100%; padding: 14px; margin: 8px 0; border-radius: 8px; border: 1px solid #ccc; font-size: 16px; box-sizing: border-box; }
        button.ana-btn { background: var(--ana); color: white; border: none; font-weight: bold; cursor: pointer; }
        .islem-btn { width: 100%; padding: 18px; font-size: 16px; font-weight: bold; border: none; border-radius: 10px; cursor: pointer; color: white; margin: 8px 0; display: block; text-align: center; }
        .btn-konum { background: var(--konum); }
        .btn-kasa { background: var(--kasa); }
        .btn-hazir { background: var(--vurgu); }
        .gizli { display: none; }
        .kart { background: #f8f9fa; border-left: 6px solid var(--ana); padding: 15px; margin: 12px 0; border-radius: 8px; box-shadow: 0 2px 5px rgba(0,0,0,0.05); overflow: hidden; }
        .onay-btn { background: var(--vurgu); color: white; border: none; padding: 8px 15px; border-radius: 5px; font-weight: bold; cursor: pointer; float: right; }
        .durum-bar { background: #dfe6e9; padding: 10px; border-radius: 8px; font-weight: bold; text-align: center; margin-bottom: 15px; color: var(--ana); }
        .harita-link { display: inline-block; margin-top: 5px; color: var(--konum); font-weight: bold; text-decoration: none; }
        .tarih-etiket { font-size: 11px; color: #7f8c8d; font-weight: bold; display: block; margin-top: 8px; background: #eeded0; padding: 3px 6px; border-radius: 4px; width: fit-content; }
        .imza { text-align: center; font-weight: 900; color: #b2bec3; letter-spacing: 2px; font-size: 14px; margin-top: auto; padding: 20px; }
    </style>
</head>
<body>

<div class="container">
    <h1>HALCİ+F</h1>
    <h2>LKANT+F Akıllı Lojistik Sistemi</h2>

    <div id="modEkrani" class="Grup">
        <button id="mMod" class="aktif" onclick="modSec('mustahsil')">Müstahsil (Giriş)</button>
        <button id="hMod" onclick="modSec('halci')">Halci / Şoför Panel</button>
    </div>

    <div id="mGrisForm">
        <input type="text" id="mAd" placeholder="Adınız Soyadınız">
        <input type="text" id="mKod" placeholder="8 Haneli Hal Kodu" maxlength="8">
        <button class="ana-btn" onclick="mustahsilGiris()">SİSTEME BAĞLAN</button>
    </div>

    <div id="mIslemPaneli" class="gizli">
        <div class="durum-bar" id="mUstBilgi">Müstahsil: - | Kod: -</div>
        <div id="canliDurumBildirimi" style="background:#ffeaa7; padding:10px; border-radius:8px; margin-bottom:15px; text-align:center; font-weight:bold; display:none;"></div>
        
        <button class="islem-btn btn-konum" id="gpsBtn" onclick="konumYakala()">📍 1. BUTON: MEVCUT KONUMU GÖNDER</button>
        
        <div style="background:#f5f6fa; padding:10px; border-radius:8px; margin:10px 0; border:1px solid #ddd;">
            <label style="font-weight:bold; color:var(--ana)">Boş Kasa Sayısı:</label>
            <input type="number" id="mKasaAdet" value="150" min="1" style="width:100%; padding:10px; margin-top:5px;">
            <button class="islem-btn btn-kasa" onclick="mustahsilTalepGonder('Boş Kasa İstiyor')">📦 2. BUTON: BOŞ KASA İSTE</button>
        </div>
        
        <button class="islem-btn btn-hazir" onclick="mustahsilTalepGonder('Mal Hazır Gelin Alın')">🚜 3. BUTON: MAL HAZIR GELİN ALIN</button>
        <button class="ana-btn" style="background:#7f8c8d; margin-top:20px;" onclick="temizleVeCikis()">Kullanıcıyı Değiştir (Çıkış)</button>
    </div>

    <div id="hPanel" class="gizli">
        <div id="hAuth">
            <input type="text" id="hUnvan" placeholder="Yazıhane Adı (Kayıt İçin)">
            <input type="text" id="hKod" placeholder="8 Haneli Giriş Kodu" maxlength="8">
            <button class="ana-btn" onclick="halciEylemi('giris')">GİRİŞ YAP</button>
            <button class="ana-btn" style="background:#95a5a6;" onclick="halciEylemi('kayit')">YAZIHANEYİ ÖMÜRLÜK KAYDET</button>
        </div>
        
        <div id="hTakip" class="gizli">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:15px;">
                <b id="hPanelBaslik" style="color:var(--ana); font-size:18px;">Lojistik Ekranı</b>
                <button onclick="location.reload()" style="padding:6px 12px; background:var(--iptal); color:white; border:none; border-radius:5px; cursor:pointer; font-weight:bold;">Çıkış</button>
            </div>
            <div id="canliTaleplerKutusu">
                <p style="text-align:center; color:#95a5a6;">Müşteri aranıyor, sistem tetikte...</p>
            </div>
        </div>
    </div>
</div>

<div class="imza">LKANT+F TEKNOLOJİ</div>

<script>
    let gonderilenKonum = "Konum Paylaşılmadı";
    let mAdSoyad = "";
    let mHalKodu = "";
    let hOturumKodu = "";

    // SİSTEM AÇILDIĞINDA HAFIZAYI KONTROL ET (MÜŞTERİ BİR DAHA GİRİŞ YAPMASIN)
    window.onload = function() {
        const hafizaAd = localStorage.getItem('lkantf_ad');
        const hafizaKod = localStorage.getItem('lkantf_kod');
        
        if(hafizaAd && hafizaKod) {
            mAdSoyad = hafizaAd;
            mHalKodu = hafizaKod;
            // Otomatik bağlanmayı tetikle
            otoBaglan();
        }
    }

    function modSec(mod) {
        document.getElementById('mGrisForm').classList.toggle('gizli', mod==='halci');
        document.getElementById('hPanel').classList.toggle('gizli', mod==='mustahsil');
        document.getElementById('mMod').classList.toggle('aktif', mod==='mustahsil');
        document.getElementById('hMod').classList.toggle('aktif', mod==='halci');
    }

    function mustahsilGiris() {
        mAdSoyad = document.getElementById('mAd').value.trim();
        mHalKodu = document.getElementById('mKod').value.trim();
        if(!mAdSoyad || !mHalKodu) return alert("Bilgileri doldur kanka!");

        const data = new URLSearchParams();
        data.append('a', 'kod_kontrol'); data.append('kod', mHalKodu);
        
        fetch('/api', { method: 'POST', body: data }).then(r=>r.json()).then(res=>{
            if(res.s === 'ok') {
                // VERİLERİ ÖMÜRLÜK HAFIZAYA AL
                localStorage.setItem('lkantf_ad', mAdSoyad);
                localStorage.setItem('lkantf_kod', mHalKodu);
                
                paneliAc(res.u);
            } else { alert(res.m); }
        });
    }

    function otoBaglan() {
        const data = new URLSearchParams();
        data.append('a', 'kod_kontrol'); data.append('kod', mHalKodu);
        fetch('/api', { method: 'POST', body: data }).then(r=>r.json()).then(res=>{
            if(res.s === 'ok') { paneliAc(res.u); }
        });
    }

    function paneliAc(unvan) {
        document.getElementById('mUstBilgi').innerText = `Müstahsil: ${mAdSoyad} | Hal: ${unvan}`;
        document.getElementById('mGrisForm').classList.add('gizli');
        document.getElementById('modEkrani').classList.add('gizli');
        document.getElementById('mIslemPaneli').classList.remove('gizli');
        setInterval(mustahsilDurumKontrol, 3000);
    }

    function temizleVeCikis() {
        localStorage.removeItem('lkantf_ad');
        localStorage.removeItem('lkantf_kod');
        location.reload();
    }

    function konumYakala() {
        if (navigator.geolocation) {
            navigator.geolocation.getCurrentPosition(pos => {
                gonderilenKonum = `https://www.google.com/maps?q=${pos.coords.latitude},${pos.coords.longitude}`;
                document.getElementById('gpsBtn').innerText = "✅ KONUM ALINDI VE GÖNDERİLDİ";
                document.getElementById('gpsBtn').style.background = "#2ecc71";
                mustahsilTalepGonder('Sadece Konum Paylaştı');
            }, () => alert("GPS İzni Ver kanka!"));
        }
    }

    function mustahsilTalepGonder(islemTuru) {
        const kasaAdet = document.getElementById('mKasaAdet').value || 0;
        const data = new URLSearchParams();
        data.append('a', 'talep_at'); data.append('ad', mAdSoyad); data.append('kod', mHalKodu);
        data.append('kasa', kasaAdet); data.append('islem', islemTuru); data.append('konum', gonderilenKonum);

        fetch('/api', { method: 'POST', body: data }).then(r=>r.json()).then(res=>{ alert(res.m); });
    }

    function mustahsilDurumKontrol() {
        fetch(`/get-durum?ad=${encodeURIComponent(mAdSoyad)}&kod=${mHalKodu}`)
        .then(r=>r.json()).then(res=>{
            const kutu = document.getElementById('canliDurumBildirimi');
            if(res.durum && res.durum !== 'Bekliyor') {
                kutu.innerText = `🚨 ONAYLANDI: ${res.islem} Talebiniz Halci Tarafından Onaylandı kanka!`;
                kutu.style.display = 'block'; kutu.style.background = '#2ecc71'; kutu.style.color = 'white';
            }
        });
    }

    function halciEylemi(tip) {
        const kod = document.getElementById('hKod').value.trim();
        const unvan = document.getElementById('hUnvan').value.trim();
        if(!kod) return alert("Kodu gir kanka!");

        const data = new URLSearchParams();
        data.append('a', tip); data.append('kod', kod); data.append('unvan', unvan);

        fetch('/api', { method: 'POST', body: data }).then(r=>r.json()).then(res=>{
            alert(res.m);
            if(res.s === 'ok' && tip === 'giris') {
                hOturumKodu = kod;
                document.getElementById('hAuth').classList.add('gizli');
                document.getElementById('modEkrani').classList.add('gizli');
                document.getElementById('hTakip').classList.remove('gizli');
                document.getElementById('hPanelBaslik').innerText = `${res.u} Lojistik Üssü`;
                halciVeriYukle();
                setInterval(halciVeriYukle, 3000);
            }
        });
    }

    function halciVeriYukle() {
        if(!hOturumKodu) return;
        fetch('/get-talepler?kod=' + hOturumKodu).then(r=>r.json()).then(data=>{
            const kutu = document.getElementById('canliTaleplerKutusu');
            if(data.length === 0) {
                kutu.innerHTML = '<p style="text-align:center; color:#95a5a6;">Henüz işlem yapan müşteri yok kanka.</p>';
                return;
            }
            kutu.innerHTML = '';
            // En yeni talepler en üstte gözüksün diye ters çeviriyoruz
            data.reverse().forEach(t=>{
                // t[0]:id, t[1]:ad, t[2]:kod, t[3]:kasa, t[4]:islem, t[5]:konum, t[6]:durum, t[7]:tarih
                let btn = t[6] === 'Bekliyor' ? `<button class="onay-btn" onclick="talepOnayla(${t[0]})">👍 ONAYLA</button>` : `<span style="float:right; color:#27ae60; font-weight:bold;">✅ ONAYLI</span>`;
                
                // Tarih formatını güzelleştiriyoruz
                let temizTarih = t[7] ? t[7].replace('T', ' ').substring(0, 19) : 'Bilinmiyor';

                kutu.innerHTML += `
                    <div class="kart">
                        ${btn}
                        <p style="margin:0 0 5px 0;"><b>Müşteri:</b> ${t[1]}</p>
                        <p style="margin:0 0 5px 0;"><b>İstek:</b> ${t[4]}</p>
                        <p style="margin:0 0 5px 0;"><b>Kasa Adedi:</b> <span style="color:#e67e22; font-weight:bold;">${t[3]} Adet</span></p>
                        ${t[5] !== 'Konum Paylaşılmadı' ? `<a href="${t[5]}" target="_blank" class="harita-link">📍 Haritada Konumu Gör</a>` : ''}
                        <span class="tarih-etiket">📅 İşlem Zamanı: ${temizTarih}</span>
                    </div>
                `;
            });
        });
    }

    function talepOnayla(id) {
        const data = new URLSearchParams();
        data.append('a', 'onayla'); data.append('id', id);
        fetch('/api', { method: 'POST', body: data }).then(r=>r.json()).then(res=>{ if(res.s === 'ok') halciVeriYukle(); });
    }
</script>
</body>
</html>
"""

class LKANTF_SERVER_V2(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path.startswith('/get-talepler'):
            kod = parse_qs(self.path.split('?')[-1]).get('kod', [''])[0]
            db = sqlite3.connect('halci_plus_f.db')
            res = db.execute("SELECT * FROM talepler WHERE kod=?", (kod,)).fetchall()
            db.close()
            self.send_response(200); self.send_header('Content-type', 'application/json'); self.end_headers()
            self.wfile.write(json.dumps(res).encode('utf-8'))
        elif self.path.startswith('/get-durum'):
            params = parse_qs(self.path.split('?')[-1])
            ad = unquote(params.get('ad', [''])[0])
            kod = params.get('kod', [''])[0]
            db = sqlite3.connect('halci_plus_f.db')
            res = db.execute("SELECT islem, durum FROM talepler WHERE ad=? AND kod=? ORDER BY id DESC LIMIT 1", (ad, kod)).fetchone()
            db.close()
            veri = {"islem": res[0], "durum": res[1]} if res else {}
            self.send_response(200); self.send_header('Content-type', 'application/json'); self.end_headers()
            self.wfile.write(json.dumps(veri).encode('utf-8'))
        else:
            self.send_response(200); self.send_header('Content-type', 'text/html; charset=utf-8'); self.end_headers()
            self.wfile.write(HTML_TEMPLATE.encode('utf-8'))

    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        p = parse_qs(self.rfile.read(content_length).decode('utf-8'))
        action = p.get('a', [''])[0]
        db = sqlite3.connect('halci_plus_f.db')
        yanit = {"s": "hata", "m": "Hata"}

        if action == 'kod_kontrol':
            kod = p.get('kod', [''])[0]
            h = db.execute("SELECT unvan FROM halciler WHERE kod=?", (kod,)).fetchone()
            yanit = {"s": "ok", "u": h[0]} if h else {"s": "hata", "m": "Böyle bir Hal Kodu kayıtlı değil kanka!"}
        elif action == 'kayit':
            try:
                db.execute("INSERT INTO halciler VALUES (?,?)", (p['kod'][0], p['unvan'][0]))
                db.commit(); yanit = {"s": "ok", "m": "Yazıhane başarıyla kaydedildi kanka!"}
            except: yanit = {"s": "hata", "m": "Bu kod zaten alınmış!"}
        elif action == 'giris':
            h = db.execute("SELECT unvan FROM halciler WHERE kod=?", (p['kod'][0],)).fetchone()
            yanit = {"s": "ok", "m": "Giriş Başarılı!", "u": h[0]} if h else {"s": "hata", "m": "Kod bulunamadı!"}
        elif action == 'talep_at':
            db.execute("INSERT INTO talepler (ad, kod, kasa, islem, konum) VALUES (?,?,?,?,?)",
                       (p['ad'][0], p['kod'][0], int(p['kasa'][0]), p['islem'][0], p['konum'][0]))
            db.commit(); yanit = {"s": "ok", "m": "Talebiniz başarıyla halciye iletildi!"}
        elif action == 'onayla':
            db.execute("UPDATE talepler SET durum='Onaylandi' WHERE id=?", (p['id'][0],))
            db.commit(); yanit = {"s": "ok", "m": "Onaylandı!"}

        db.close()
        self.send_response(200); self.send_header('Content-type', 'application/json'); self.end_headers()
        self.wfile.write(json.dumps(yanit).encode('utf-8'))

# Kodun en altındaki o son 4 satırı sil, aynen bunu yapıştır kanka:

PORT = int(os.environ.get("PORT", 8080))

socketserver.TCPServer.allow_reuse_address = True
with socketserver.TCPServer(("", PORT), LKANTF_SERVER_V2) as httpd:
    print(f"🚀 [LKANT+F RENDER READY] Sistem Aktif Port: {PORT}")
    httpd.serve_forever()
