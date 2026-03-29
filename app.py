"""
Uzay Limanı: Gelişmiş Fırlatma Simülasyon Sistemi v4
TUA Astro Hackathon
Yenilikler: Saatlik hava verisi + Uzay çöpü çarpışma risk analizi
"""

from flask import Flask, render_template, request, jsonify
import requests, math, random

app = Flask(__name__)

HANGARLAR = {
    "falcon9":  {"isim": "SpaceX Hawthorne Fabrikası", "enlem": 33.916, "boylam": -118.328},
    "starship": {"isim": "SpaceX Boca Chica Tesisi",   "enlem": 25.997, "boylam":  -97.155},
    "ariane6":  {"isim": "ArianeGroup Bremen",         "enlem": 53.047, "boylam":    8.788},
}

YEDEK_PARCALAR = {
    "falcon9": [
        {"id":"f9_merlin",    "isim":"Merlin 1D Motor",         "kg":490,   "fiyat":1000000},
        {"id":"f9_fairing",   "isim":"Payload Fairing (Burun)", "kg":1900,  "fiyat":6000000},
        {"id":"f9_grid_fin",  "isim":"Grid Fin x4",             "kg":140,   "fiyat":500000},
        {"id":"f9_octaweb",   "isim":"Octaweb Motor Bloğu",     "kg":2200,  "fiyat":3000000},
        {"id":"f9_leg",       "isim":"İniş Ayağı x4",           "kg":2100,  "fiyat":1200000},
        {"id":"f9_mvac",      "isim":"Merlin Vacuum Motor",     "kg":420,   "fiyat":1500000},
        {"id":"f9_lox_tank",  "isim":"LOX Yakıt Tankı",         "kg":3500,  "fiyat":2000000},
    ],
    "starship": [
        {"id":"ss_raptor",    "isim":"Raptor V2 Motor",         "kg":1500,  "fiyat":2000000},
        {"id":"ss_heatshield","isim":"Isı Kalkanı Kiremiti",    "kg":8000,  "fiyat":4500000},
        {"id":"ss_flap",      "isim":"Aerodinamik Flap x4",     "kg":800,   "fiyat":1200000},
        {"id":"ss_methane",   "isim":"Methan Depolama Tankı",   "kg":6000,  "fiyat":3000000},
        {"id":"ss_avionics",  "isim":"Avionik Sistem",          "kg":200,   "fiyat":5000000},
        {"id":"ss_payload",   "isim":"Payload Bay Kapısı",      "kg":3000,  "fiyat":2500000},
    ],
    "ariane6": [
        {"id":"a6_vulcain",   "isim":"Vulcain 2.1 Motor",       "kg":1800,  "fiyat":15000000},
        {"id":"a6_vinci",     "isim":"Vinci Üst Kademe Motoru", "kg":550,   "fiyat":8000000},
        {"id":"a6_fairing",   "isim":"PLF Fairing 5.4m",        "kg":2100,  "fiyat":4000000},
        {"id":"a6_p120",      "isim":"P120C Katı Roket x2",     "kg":11500, "fiyat":3000000},
        {"id":"a6_lh2_tank",  "isim":"LH2 Kriyo Tankı",         "kg":4200,  "fiyat":6000000},
        {"id":"a6_sylda",     "isim":"SYLDA Çift Yük Adaptörü", "kg":700,   "fiyat":1500000},
    ],
}

ARASTIRMA_MALZEMELERI = [
    {"id":"mik_deney",  "isim":"Mikrogravite Deney Seti",     "kg":120, "fiyat":500000},
    {"id":"bio_lab",    "isim":"Biyoloji Laboratuvarı",       "kg":85,  "fiyat":800000},
    {"id":"teleskop",   "isim":"Taşınabilir Teleskop",        "kg":200, "fiyat":2000000},
    {"id":"radyasyon",  "isim":"Radyasyon Ölçer Paketi",      "kg":30,  "fiyat":150000},
    {"id":"mal_test",   "isim":"Malzeme Test Seti",           "kg":95,  "fiyat":300000},
    {"id":"atm_sensor", "isim":"Atmosfer Sensör Dizisi",      "kg":45,  "fiyat":200000},
    {"id":"kristal",    "isim":"Kristal Büyüme Fırını",       "kg":60,  "fiyat":400000},
    {"id":"yer_goz",    "isim":"Yer Gözlem Kamerası",         "kg":180, "fiyat":1500000},
]

GIDA_LISTESI = [
    {"id":"gida_std",   "isim":"Standart Astronot Rasyon (7gün/kişi)", "kg":5.6, "fiyat":2000},
    {"id":"gida_vej",   "isim":"Vejetaryen Menü (7gün/kişi)",          "kg":4.9, "fiyat":2200},
    {"id":"gida_enj",   "isim":"Yüksek Enerji Paketi (7gün/kişi)",     "kg":3.2, "fiyat":1800},
    {"id":"su_paket",   "isim":"Su Paketi (7gün/kişi)",                "kg":11.2,"fiyat":500},
    {"id":"vitamin",    "isim":"Vitamin & Mineral Takviyesi (30gün)",   "kg":0.8, "fiyat":300},
    {"id":"acil_rasyon","isim":"Acil Durum Rasyon Seti (30gün)",        "kg":8.5, "fiyat":3500},
    {"id":"su_donusum", "isim":"Su Geri Dönüşüm Sistemi",              "kg":25.0,"fiyat":250000},
]

UZAY_ARACLARI = {
    "falcon9": {
        "isim":"Falcon 9","sirket":"SpaceX",
        "yakit_lox_ton":287,"yakit_lox_birim":270,
        "yakit_rp1_ton":92,"yakit_rp1_birim":700,
        "booster_bakim":1000000,"ust_kademe":7000000,
        "max_yuk_kg":22800,"yakit_per_kg_yuk":2720,
        "risk_baz":0.48,"max_ruzgar":14,"max_nem":85,
        "min_sicaklik":-15,"max_sicaklik":45,
        "emoji":"🚀","dusme_yaricap_km":320,
        "tasima_hizi_kmh":40,"tasima_maliyet_km":500,
        "co2_per_yakit":3.16,"soot_per_yakit":30,
        "yeniden_kullanilabilir":True,"uretim_co2_faktoru":0.3,"co2_uretim":0,
        # Orbit parameters for debris calculation
        "orbit_irtifa_km": 550, "orbit_egim_derece": 53,
    },
    "starship": {
        "isim":"Starship","sirket":"SpaceX",
        "yakit_lox_ton":2600,"yakit_lox_birim":270,
        "yakit_rp1_ton":800,"yakit_rp1_birim":400,
        "booster_bakim":2000000,"ust_kademe":0,
        "max_yuk_kg":150000,"yakit_per_kg_yuk":100,
        "risk_baz":15.0,"max_ruzgar":12,"max_nem":80,
        "min_sicaklik":-10,"max_sicaklik":40,
        "emoji":"🛸","dusme_yaricap_km":600,
        "tasima_hizi_kmh":25,"tasima_maliyet_km":1200,
        "co2_per_yakit":2.75,"soot_per_yakit":5,
        "yeniden_kullanilabilir":True,"uretim_co2_faktoru":0.1,"co2_uretim":0,
        "orbit_irtifa_km": 400, "orbit_egim_derece": 28.5,
    },
    "ariane6": {
        "isim":"Ariane 6","sirket":"ESA/ArianeGroup",
        "yakit_lox_ton":380,"yakit_lox_birim":270,
        "yakit_rp1_ton":150,"yakit_rp1_birim":6100,
        "booster_bakim":4000000,"ust_kademe":12000000,
        "max_yuk_kg":21650,"yakit_per_kg_yuk":4600,
        "risk_baz":4.6,"max_ruzgar":16,"max_nem":90,
        "min_sicaklik":-20,"max_sicaklik":50,
        "emoji":"🛩️","dusme_yaricap_km":280,
        "tasima_hizi_kmh":35,"tasima_maliyet_km":700,
        "co2_per_yakit":0.0,"soot_per_yakit":0,
        "yeniden_kullanilabilir":False,"uretim_co2_faktoru":1.0,"co2_uretim":10.5,
        "orbit_irtifa_km": 700, "orbit_egim_derece": 98,
    }
}

FIRLATMA_USLERI = [
    {"id":"ksc",        "isim":"Kennedy Space Center", "ulke":"ABD",        "enlem":28.573,  "boylam":-80.649,  "emoji":"🇺🇸"},
    {"id":"kourou",     "isim":"Guiana Space Centre",  "ulke":"Fransa",     "enlem":5.236,   "boylam":-52.769,  "emoji":"🇫🇷"},
    {"id":"baykonur",   "isim":"Baykonur Kosmodromu",  "ulke":"Kazakistan", "enlem":45.920,  "boylam":63.342,   "emoji":"🇰🇿"},
    {"id":"mersin",     "isim":"Mersin Uzay Limanı",   "ulke":"Türkiye",    "enlem":36.812,  "boylam":34.641,   "emoji":"🇹🇷"},
    {"id":"tanegashima","isim":"Tanegashima",          "ulke":"Japonya",    "enlem":30.400,  "boylam":130.975,  "emoji":"🇯🇵"},
    {"id":"vostochny",  "isim":"Vostochny Kozmodromu", "ulke":"Rusya",      "enlem":51.884,  "boylam":128.333,  "emoji":"🇷🇺"},
    {"id":"vandenberg", "isim":"Vandenberg SFB",       "ulke":"ABD",        "enlem":34.632,  "boylam":-120.611, "emoji":"🇺🇸"},
    {"id":"mahia",      "isim":"Mahia Peninsula",      "ulke":"NZ",         "enlem":-39.262, "boylam":177.864,  "emoji":"🇳🇿"},
]

# Bilinen büyük uzay çöpü grupları / yörünge kuşakları
DEBRIS_POPULASYONLARI = [
    {"isim": "ISS Yörüngesi",         "irtifa_km": 408,  "yogunluk": 0.85, "aciklama": "Yoğun operasyonel trafik"},
    {"isim": "Starlink Kuşağı",       "irtifa_km": 550,  "yogunluk": 0.72, "aciklama": "Binlerce küçük uydu"},
    {"isim": "Iridium Enkaz Alanı",   "irtifa_km": 780,  "yogunluk": 0.91, "aciklama": "2009 çarpışma kalıntıları"},
    {"isim": "Kosmos 1408 Enkazı",    "irtifa_km": 480,  "yogunluk": 0.78, "aciklama": "2021 ASAT testi kalıntıları"},
    {"isim": "GEO Mezarlık Kuşağı",   "irtifa_km": 700,  "yogunluk": 0.44, "aciklama": "Emekli edilmiş uydular"},
    {"isim": "Fengyun-1C Enkazı",     "irtifa_km": 850,  "yogunluk": 0.88, "aciklama": "2007 ASAT testi, 3000+ parça"},
    {"isim": "SL-16 Roket Gövdeleri", "irtifa_km": 900,  "yogunluk": 0.55, "aciklama": "Sovyet roket kalıntıları"},
]

def mesafe(lat1,lon1,lat2,lon2):
    R=6371; dl=math.radians(lat2-lat1); dn=math.radians(lon2-lon1)
    a=math.sin(dl/2)**2+math.cos(math.radians(lat1))*math.cos(math.radians(lat2))*math.sin(dn/2)**2
    return round(R*2*math.asin(math.sqrt(a)),1)

def hava_al(lat, lon):
    """Anlık hava verisi al."""
    try:
        r = requests.get(
            "https://api.open-meteo.com/v1/forecast",
            params={
                "latitude": lat, "longitude": lon,
                "current": [
                    "temperature_2m","wind_speed_10m","wind_direction_10m",
                    "precipitation","cloud_cover","surface_pressure","relative_humidity_2m"
                ],
                "wind_speed_unit": "ms"
            }, timeout=10
        )
        d = r.json().get("current", {})
        return {
            "sicaklik": round(d.get("temperature_2m", 20), 1),
            "ruzgar_hizi": round(d.get("wind_speed_10m", 5), 1),
            "ruzgar_yonu": d.get("wind_direction_10m", 0),
            "yagis": round(d.get("precipitation", 0), 1),
            "bulut": d.get("cloud_cover", 0),
            "basinc": round(d.get("surface_pressure", 1013), 1),
            "nem": d.get("relative_humidity_2m", 50)
        }
    except:
        return {
            "sicaklik": round(random.uniform(10,30),1),
            "ruzgar_hizi": round(random.uniform(2,10),1),
            "ruzgar_yonu": random.randint(0,360),
            "yagis": 0,
            "bulut": random.randint(10,50),
            "basinc": round(random.uniform(1005,1020),1),
            "nem": random.randint(30,65)
        }

def saatlik_hava_al(lat, lon):
    """
    Sonraki 24 saatin saatlik hava verilerini Open-Meteo'dan çek.
    Fırlatma penceresi analizi için kullanılır.
    """
    try:
        r = requests.get(
            "https://api.open-meteo.com/v1/forecast",
            params={
                "latitude": lat, "longitude": lon,
                "hourly": [
                    "temperature_2m","wind_speed_10m","wind_direction_10m",
                    "precipitation_probability","precipitation","cloud_cover",
                    "relative_humidity_2m","surface_pressure","visibility"
                ],
                "wind_speed_unit": "ms",
                "forecast_days": 2,
                "timezone": "auto"
            }, timeout=12
        )
        data = r.json()
        hourly = data.get("hourly", {})
        times = hourly.get("time", [])[:48]

        saatler = []
        for i, t in enumerate(times[:24]):  # sadece ilk 24 saat
            saat_str = t[11:16] if len(t) > 10 else f"{i:02d}:00"
            saatler.append({
                "saat": saat_str,
                "sicaklik": round(hourly.get("temperature_2m", [20]*48)[i], 1),
                "ruzgar": round(hourly.get("wind_speed_10m", [5]*48)[i], 1),
                "ruzgar_yonu": round(hourly.get("wind_direction_10m", [0]*48)[i], 0),
                "yagis_olasiligi": hourly.get("precipitation_probability", [0]*48)[i],
                "yagis": round(hourly.get("precipitation", [0]*48)[i], 2),
                "bulut": hourly.get("cloud_cover", [20]*48)[i],
                "nem": hourly.get("relative_humidity_2m", [50]*48)[i],
                "basinc": round(hourly.get("surface_pressure", [1013]*48)[i], 1),
            })
        return saatler
    except Exception as e:
        # Fallback: simüle edilmiş saatlik veri
        base_temp = round(random.uniform(12, 28), 1)
        base_wind = round(random.uniform(2, 8), 1)
        saatler = []
        for i in range(24):
            saatler.append({
                "saat": f"{i:02d}:00",
                "sicaklik": round(base_temp + random.uniform(-3, 3), 1),
                "ruzgar": round(max(0, base_wind + random.uniform(-2, 4)), 1),
                "ruzgar_yonu": random.randint(0, 360),
                "yagis_olasiligi": random.randint(0, 30),
                "yagis": round(random.uniform(0, 0.5), 2),
                "bulut": random.randint(5, 60),
                "nem": random.randint(30, 70),
                "basinc": round(random.uniform(1008, 1018), 1),
            })
        return saatler

def en_iyi_firlatma_penceresi(saatlik_hava, arac_id):
    """
    Saatlik hava verilerinden en uygun fırlatma saatini belirle.
    Risk skorunu her saat için hesapla ve en düşük riski bul.
    """
    arac = UZAY_ARACLARI[arac_id]
    pencereler = []
    for s in saatlik_hava:
        saat_risk = 0
        if s["ruzgar"] > arac["max_ruzgar"]:
            saat_risk += 25
        elif s["ruzgar"] > arac["max_ruzgar"] * 0.7:
            saat_risk += 8
        if s["yagis"] > 0:
            saat_risk += 20 + s["yagis"] * 5
        if s["yagis_olasiligi"] > 50:
            saat_risk += 10
        if s["nem"] > arac["max_nem"]:
            saat_risk += 8
        if s["sicaklik"] < arac["min_sicaklik"] or s["sicaklik"] > arac["max_sicaklik"]:
            saat_risk += 12
        if s["bulut"] > 80:
            saat_risk += 5
        pencereler.append({**s, "saat_risk": round(min(saat_risk, 99), 1)})

    en_iyi = min(pencereler, key=lambda x: x["saat_risk"])
    return {"pencereler": pencereler, "en_iyi_saat": en_iyi["saat"], "en_iyi_risk": en_iyi["saat_risk"]}

def uzay_copu_analizi(arac_id):
    """
    Aracın hedef yörünge irtifasına göre uzay çöpü çarpışma riski analiz et.
    Gerçek zamanlı Space-Track.org verisine erişim olmadığından,
    bilinen popülasyon yoğunluklarına ve irtifa örtüşmesine göre model.
    """
    arac = UZAY_ARACLARI[arac_id]
    hedef_irtifa = arac["orbit_irtifa_km"]
    hedef_egim   = arac["orbit_egim_derece"]

    tehdit_listesi = []
    toplam_risk_puani = 0.0

    for pop in DEBRIS_POPULASYONLARI:
        irtifa_fark = abs(pop["irtifa_km"] - hedef_irtifa)

        # İrtifa yakınlığına göre risk ağırlığı (±150 km içinde tehlike)
        if irtifa_fark <= 50:
            irtifa_katsayi = 1.0
        elif irtifa_fark <= 100:
            irtifa_katsayi = 0.6
        elif irtifa_fark <= 150:
            irtifa_katsayi = 0.25
        else:
            irtifa_katsayi = 0.0

        if irtifa_katsayi == 0.0:
            continue

        # Yörünge eğim uyumsuzluğu faktörü (kutupsal vs ekvatoryal)
        egim_fark = min(abs(hedef_egim - 53), 90) / 90  # normalize
        egim_katsayi = 1.0 - egim_fark * 0.4

        # Ham risk puanı
        ham_risk = pop["yogunluk"] * irtifa_katsayi * egim_katsayi * 100

        # Nispi hız (bileşke hız ≈ 7.8 km/s, çarpışma hızı artışı)
        if irtifa_fark < 30:
            hiz_carpani = 1.3
        else:
            hiz_carpani = 1.1

        nihai_risk = min(ham_risk * hiz_carpani, 95)
        toplam_risk_puani += nihai_risk * 0.15  # katkı ağırlığı

        if nihai_risk > 8:
            seviye = "YÜKSEK" if nihai_risk > 55 else ("ORTA" if nihai_risk > 25 else "DÜŞÜK")
            tehdit_listesi.append({
                "isim":        pop["isim"],
                "irtifa_km":   pop["irtifa_km"],
                "irtifa_fark": round(irtifa_fark, 1),
                "risk_puani":  round(nihai_risk, 1),
                "seviye":      seviye,
                "aciklama":    pop["aciklama"],
                "yogunluk_pct": round(pop["yogunluk"] * 100, 0),
            })

    tehdit_listesi.sort(key=lambda x: x["risk_puani"], reverse=True)
    toplam_risk = round(min(toplam_risk_puani, 92), 1)

    # Çarpışma olasılığı (10^-4 mertebesinde, NASA/ESA standart yaklaşımı)
    carpişma_olasiligi_per_gun = round(toplam_risk * 0.000012, 7)

    if toplam_risk < 15:
        genel_seviye = "DÜŞÜK"
        genel_renk   = "green"
        oneri = "Yörünge irtifası görece temiz. Standart kaçınma manevrası protokolü yeterli."
    elif toplam_risk < 40:
        genel_seviye = "ORTA"
        genel_renk   = "orange"
        oneri = "Artırılmış gözetim önerilir. Otomatik çarpışma kaçınma sistemi aktif tutulmalı."
    else:
        genel_seviye = "YÜKSEK"
        genel_renk   = "red"
        oneri = "Kritik risk! Yörünge irtifası değişikliği veya görev başlangıcının ertelenmesi değerlendirilmeli."

    return {
        "hedef_irtifa_km":   hedef_irtifa,
        "hedef_egim":        hedef_egim,
        "toplam_risk":       toplam_risk,
        "genel_seviye":      genel_seviye,
        "genel_renk":        genel_renk,
        "tehdit_sayisi":     len(tehdit_listesi),
        "tehditler":         tehdit_listesi[:5],  # en tehlikeli 5
        "carpişma_olasiligi_per_gun": carpişma_olasiligi_per_gun,
        "oneri":             oneri,
        "toplam_takip_nesnesi_tahmini": random.randint(21000, 27000),
        "kacinma_kapasitesi": "Otomatik" if arac_id in ["falcon9","starship"] else "Manuel",
    }

def rakim_al(lat,lon):
    try:
        r=requests.get("https://api.opentopodata.org/v1/srtm90m",params={"locations":f"{lat},{lon}"},timeout=8)
        return r.json()["results"][0]["elevation"]
    except:
        return random.randint(0,200)

def tasima_hesapla(arac_id, us_id):
    arac=UZAY_ARACLARI[arac_id]; hangar=HANGARLAR[arac_id]
    us=next(u for u in FIRLATMA_USLERI if u["id"]==us_id)
    km=mesafe(hangar["enlem"],hangar["boylam"],us["enlem"],us["boylam"])
    if km<500:   yontem="🚛 Kara (Özel Konvoy)";  hiz=arac["tasima_hizi_kmh"]; mkm=arac["tasima_maliyet_km"]
    elif km<8000:yontem="🚢 Deniz (Kargo Gemisi)"; hiz=35; mkm=120
    else:        yontem="✈️ Uçak + Deniz Kombine"; hiz=400; mkm=250
    sure_saat = km/hiz + (48 if km>=8000 else 0)
    ara_noktalar=[]
    for i in [0.25,0.5,0.75]:
        al=hangar["enlem"]+(us["enlem"]-hangar["enlem"])*i
        ao=hangar["boylam"]+(us["boylam"]-hangar["boylam"])*i
        ah=hava_al(al,ao)
        ara_noktalar.append({"enlem":round(al,2),"boylam":round(ao,2),"sicaklik":ah["sicaklik"],"ruzgar":ah["ruzgar_hizi"],"yagis":ah["yagis"]})
    return {"hangar":hangar["isim"],"hangar_enlem":hangar["enlem"],"hangar_boylam":hangar["boylam"],"us_isim":us["isim"],"us_enlem":us["enlem"],"us_boylam":us["boylam"],"mesafe_km":km,"yontem":yontem,"sure_gun":round(sure_saat/24,1),"maliyet":round(km*mkm),"ara_noktalar":ara_noktalar}

def risk_hesapla(arac_id,hava,rakim):
    a=UZAY_ARACLARI[arac_id]; risk=a["risk_baz"]
    if hava["ruzgar_hizi"]>a["max_ruzgar"]: risk+=15+(hava["ruzgar_hizi"]-a["max_ruzgar"])*2
    elif hava["ruzgar_hizi"]>a["max_ruzgar"]*0.7: risk+=5
    if hava["yagis"]>0: risk+=20+hava["yagis"]*3
    if hava["nem"]>a["max_nem"]: risk+=8
    elif hava["nem"]>a["max_nem"]*0.85: risk+=3
    if hava["sicaklik"]<a["min_sicaklik"] or hava["sicaklik"]>a["max_sicaklik"]: risk+=12
    elif hava["sicaklik"]<a["min_sicaklik"]+5 or hava["sicaklik"]>a["max_sicaklik"]-5: risk+=4
    if rakim>1500: risk-=1.5
    return round(min(risk,98),1)

def maliyet_hesapla(arac_id,hava,yuk_kg):
    a=UZAY_ARACLARI[arac_id]
    temel=(a["yakit_lox_ton"]*a["yakit_lox_birim"])+(a["yakit_rp1_ton"]*a["yakit_rp1_birim"])
    yuk_ek=yuk_kg*a["yakit_per_kg_yuk"]
    ruzgar_c=1+(hava["ruzgar_hizi"]*0.008); nem_c=1+(hava["nem"]*0.0005)
    yakit=round((temel+yuk_ek)*ruzgar_c*nem_c)
    parca_t=a["booster_bakim"]+a["ust_kademe"]
    risk=risk_hesapla(arac_id,hava,100)
    parca=round(parca_t*(1+risk/150))
    return {"temel_yakit":round(temel),"yuk_ek":round(yuk_ek),"yakit":yakit,"yedek_parca":parca,"toplam":yakit+parca}

def karbon_hesapla(arac_id,hava):
    a=UZAY_ARACLARI[arac_id]; yt=a["yakit_rp1_ton"]
    yanma=round(yt*a["co2_per_yakit"]*(1+hava["ruzgar_hizi"]*0.008)*(1+hava["nem"]*0.0005),1)
    uretim=round(yt*a["co2_uretim"]*a["uretim_co2_faktoru"],1)
    soot=round(yt*a["soot_per_yakit"]*0.05,1)
    toplam=round(yanma+uretim+soot,1)
    skor=round(max(0,min(100,(1-toplam/5000)*100)),1)
    yakit_tipi="RP-1/Kerosene" if arac_id=="falcon9" else ("Methan/LNG" if arac_id=="starship" else "LH2/Hidrojen")
    return {"yanma_co2_ton":yanma,"uretim_co2_ton":uretim,"soot_co2_esdeger_ton":soot,"toplam_co2_ton":toplam,"surdurulebilirlik_skoru":skor,"yeniden_kullanilabilir":a["yeniden_kullanilabilir"],"yakit_tipi":yakit_tipi}

def dusme_hesapla(lat,lon,arac_id,ryonu,rhizi):
    a=UZAY_ARACLARI[arac_id]; yr=a["dusme_yaricap_km"]
    drift=rhizi*1.5; ar=math.radians(ryonu)
    de=(drift/111)*math.cos(ar); db=(drift/(111*math.cos(math.radians(lat))))*math.sin(ar)
    res=[]
    for ac,isim,risk in [(0,"Kuzey","Orta"),(90,"Dogu","Dusuk"),(180,"Guney","Orta"),(270,"Bati","Yuksek")]:
        rad=math.radians(ac); mes=yr*(0.7+random.uniform(0,0.6))
        res.append({"isim":isim+" Bölgesi","enlem":round(lat+de+(mes/111)*math.cos(rad),3),"boylam":round(lon+db+(mes/(111*math.cos(math.radians(lat))))*math.sin(rad),3),"mesafe_km":round(mes,1),"risk":risk})
    return res

@app.route("/")
def anasayfa():
    return render_template("index.html")

@app.route("/api/usler")
def usler():
    return jsonify(FIRLATMA_USLERI)

@app.route("/api/malzemeler/<arac_id>")
def malzemeler(arac_id):
    return jsonify({"yedek_parcalar":YEDEK_PARCALAR.get(arac_id,[]),"arastirma":ARASTIRMA_MALZEMELERI,"gida":GIDA_LISTESI})

@app.route("/api/simulasyon", methods=["POST"])
def simulasyon():
    data=request.get_json()
    us_id=data.get("us_id","ksc"); arac_id=data.get("arac_id","falcon9")
    tarih=data.get("tarih","2026-01-01"); secimler=data.get("malzemeler",[])

    us=next(u for u in FIRLATMA_USLERI if u["id"]==us_id)
    arac=UZAY_ARACLARI[arac_id]

    tum=([(p,"parca") for p in YEDEK_PARCALAR.get(arac_id,[])]+[(a,"arastirma") for a in ARASTIRMA_MALZEMELERI]+[(g,"gida") for g in GIDA_LISTESI])
    yuk_kg=0; mal_fiyat=0; mal_detay=[]
    for s in secimler:
        item=next((m for m,_ in tum if m["id"]==s["id"]),None)
        if item:
            mik=int(s.get("miktar",1)); kg=item["kg"]*mik; f=item["fiyat"]*mik
            yuk_kg+=kg; mal_fiyat+=f
            mal_detay.append({"isim":item["isim"],"miktar":mik,"kg":round(kg,1),"fiyat":f})

    kapasite_asimi=yuk_kg>arac["max_yuk_kg"]
    hava=hava_al(us["enlem"],us["boylam"])
    rakim=rakim_al(us["enlem"],us["boylam"])

    # YENİ: Saatlik hava analizi
    saatlik = saatlik_hava_al(us["enlem"], us["boylam"])
    firlatma_penceresi = en_iyi_firlatma_penceresi(saatlik, arac_id)

    # YENİ: Uzay çöpü analizi
    uzay_copu = uzay_copu_analizi(arac_id)

    risk=risk_hesapla(arac_id,hava,rakim)
    maliyet=maliyet_hesapla(arac_id,hava,yuk_kg)
    maliyet["malzeme_fiyat"]=mal_fiyat; maliyet["genel_toplam"]=maliyet["toplam"]+mal_fiyat
    tasima=tasima_hesapla(arac_id,us_id)
    karbon=karbon_hesapla(arac_id,hava)
    dusme=dusme_hesapla(us["enlem"],us["boylam"],arac_id,hava["ruzgar_yonu"],hava["ruzgar_hizi"])

    # Ucuz taşıma önerisi
    ucuz=None; en_dusuk_tasima=tasima["maliyet"]
    for u in FIRLATMA_USLERI:
        if u["id"]==us_id: continue
        t=tasima_hesapla(arac_id,u["id"])
        if t["maliyet"]<en_dusuk_tasima*0.8:
            en_dusuk_tasima=t["maliyet"]; ucuz={"tip":"us","us":u["isim"],"emoji":u["emoji"],"maliyet":t["maliyet"],"sure":t["sure_gun"],"fark":round(tasima["maliyet"]-t["maliyet"])}
    for aid,ac in UZAY_ARACLARI.items():
        if aid==arac_id: continue
        t=tasima_hesapla(aid,us_id)
        if t["maliyet"]<en_dusuk_tasima*0.8:
            en_dusuk_tasima=t["maliyet"]; ucuz={"tip":"arac","arac":ac["isim"],"emoji":ac["emoji"],"maliyet":t["maliyet"],"sure":t["sure_gun"],"fark":round(tasima["maliyet"]-t["maliyet"])}

    # Risk önerisi
    risk_on=None; en_dusuk_risk=risk
    for u in FIRLATMA_USLERI:
        if u["id"]==us_id: continue
        h=hava_al(u["enlem"],u["boylam"])
        for aid in UZAY_ARACLARI:
            r=risk_hesapla(aid,h,100)
            if r<en_dusuk_risk-5:
                en_dusuk_risk=r; risk_on={"us":u["isim"],"us_emoji":u["emoji"],"arac":UZAY_ARACLARI[aid]["isim"],"arac_emoji":UZAY_ARACLARI[aid]["emoji"],"risk":r,"fark":round(risk-r,1)}

    # Karbon önerisi
    karbon_on=None; en_dusuk_co2=karbon["toplam_co2_ton"]
    nh={"ruzgar_hizi":5,"nem":50,"sicaklik":20,"yagis":0}
    for aid,ac in UZAY_ARACLARI.items():
        if aid==arac_id: continue
        k=karbon_hesapla(aid,nh)
        if k["toplam_co2_ton"]<en_dusuk_co2*0.85:
            en_dusuk_co2=k["toplam_co2_ton"]; karbon_on={"arac":ac["isim"],"emoji":ac["emoji"],"co2_ton":k["toplam_co2_ton"],"yakit_tipi":k["yakit_tipi"],"fark_ton":round(karbon["toplam_co2_ton"]-k["toplam_co2_ton"],1),"yuzde":round((1-k["toplam_co2_ton"]/karbon["toplam_co2_ton"])*100,1)}

    risk_durum="DÜŞÜK" if risk<15 else ("ORTA" if risk<35 else "YÜKSEK")
    risk_renk="green" if risk<15 else ("orange" if risk<35 else "red")

    return jsonify({
        "us": us, "arac": {**arac,"id":arac_id}, "tarih": tarih,
        "hava": hava, "rakim": rakim,
        "saatlik_hava": firlatma_penceresi,   # YENİ
        "uzay_copu": uzay_copu,               # YENİ
        "risk": {"yuzde":risk,"durum":risk_durum,"renk":risk_renk},
        "maliyet": maliyet,
        "yuk": {"toplam_kg":round(yuk_kg,1),"max_kg":arac["max_yuk_kg"],"kapasite_asimi":kapasite_asimi,"detay":mal_detay},
        "tasima": tasima,
        "ucuz_tasima": ucuz,
        "dusme_bolgeleri": dusme,
        "karbon": karbon,
        "karbon_oneri": karbon_on,
        "risk_oneri": risk_on,
    })

if __name__=="__main__":
    app.run(debug=True)
