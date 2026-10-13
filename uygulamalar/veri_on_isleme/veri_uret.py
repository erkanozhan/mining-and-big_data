"""Veri ön işleme uygulaması için "kirli" örnek veri setlerini üretir.

İki kaynak sistem taklit edilir:

* veri/musteriler_kirli.csv : CRM sisteminden gelen müşteri kayıtları
* veri/siparisler.csv       : e-ticaret sisteminden gelen sipariş kayıtları

Veriye bilerek şu sorunlar yerleştirilir (her biri README'de bir adımda
temizlenir): eksik ve gizli eksik değerler, mükerrer ve yarı-mükerrer kayıtlar,
yazım/biçim tutarsızlıkları, metin olarak saklanmış sayılar, karışık tarih
biçimleri, geçersiz (imkânsız) değerler, aykırı değerler, gereksiz (türetilmiş)
sütun, sabit sütun, çoğunlukla boş sütun, farklı anahtar biçimi ve farklı para
birimi.

Çalıştırma (bu klasörden):
    python veri_uret.py

Sabit tohum (42) kullanıldığı için her çalıştırmada aynı dosyalar üretilir.
Öğrencinin bu betiği çalıştırması gerekmez; CSV dosyaları depoda hazırdır.
"""

import sys
from datetime import date, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

sys.stdout.reconfigure(encoding="utf-8")   # Windows konsolunda Türkçe karakterler için
rng = np.random.default_rng(42)
KLASOR = Path(__file__).resolve().parent / "veri"
KLASOR.mkdir(exist_ok=True)

N = 300

ADLAR_E = ["Ahmet", "Mehmet", "Mustafa", "Ali", "Hüseyin", "Hasan", "İbrahim", "Emre",
           "Burak", "Murat", "Okan", "Serkan", "Oğuz", "Çağlar", "Kerem", "Yusuf"]
ADLAR_K = ["Ayşe", "Fatma", "Emine", "Hatice", "Zeynep", "Elif", "Merve", "Büşra",
           "Selin", "Gizem", "Özge", "Şule", "Derya", "İrem", "Cansu", "Ece"]
SOYADLAR = ["Yılmaz", "Kaya", "Demir", "Şahin", "Çelik", "Yıldız", "Yıldırım", "Öztürk",
            "Aydın", "Özdemir", "Arslan", "Doğan", "Kılıç", "Aslan", "Çetin", "Koç",
            "Kurt", "Özkan", "Şimşek", "Polat"]

SEHIRLER = ["İstanbul", "Ankara", "İzmir", "Tekirdağ", "Bursa", "Antalya"]
SEHIR_OLASILIK = [0.34, 0.20, 0.15, 0.13, 0.10, 0.08]
SEHIR_KIRLI = {
    "İstanbul": ["istanbul", "ISTANBUL", "Istanbul", " İstanbul  ", "İst.", "İSTANBUL"],
    "Ankara": ["ankara", "ANKARA", "Ankra", "Ankara "],
    "İzmir": ["izmir", "Izmir", "IZMIR", "İzmır"],
    "Tekirdağ": ["Tekirdag", "TEKİRDAĞ", "tekirdağ", "Tekirdağ "],
    "Bursa": ["bursa", "BURSA", " Bursa"],
    "Antalya": ["antalya", "ANTALYA", "Antalya  "],
}

EGITIM = ["İlkokul", "Lise", "Lisans", "Yüksek Lisans", "Doktora"]
EGITIM_OLASILIK = [0.12, 0.33, 0.37, 0.13, 0.05]
EGITIM_MEDYAN_GELIR = {"İlkokul": 17000, "Lise": 22000, "Lisans": 35000,
                       "Yüksek Lisans": 47000, "Doktora": 58000}
EGITIM_KIRLI = {
    "İlkokul": ["ilkokul", "İLKOKUL"],
    "Lise": ["lise", "LİSE", "Lise "],
    "Lisans": ["lisans", "LİSANS", "Lisans  "],
    "Yüksek Lisans": ["Yüksek lisans", "yüksek lisans", "Y. Lisans", "YL"],
    "Doktora": ["doktora", "Dr.", "DOKTORA"],
}

UYELIK = ["Standart", "Gold", "Platin"]
UYELIK_OLASILIK = [0.58, 0.30, 0.12]
UYELIK_KIRLI = {"Standart": ["standart", "STANDART"], "Gold": ["gold", "GOLD", "Altın"],
                "Platin": ["platin", "Platinum", "PLATİN"]}

GIZLI_EKSIK = ["?", "-", "N/A", "Bilinmiyor"]


def kirlet(deger, sozluk, oran):
    """Değeri verilen olasılıkla kirli varyantlarından biriyle değiştirir."""
    if rng.random() < oran:
        return rng.choice(sozluk[deger])
    return deger


def ascii_yap(metin):
    return metin.translate(str.maketrans("çğıöşüÇĞİÖŞÜ", "cgiosuCGIOSU")).lower()


def tr_buyuk(metin):
    return metin.replace("i", "İ").replace("ı", "I").upper()


def tr_kucuk(metin):
    return metin.replace("I", "ı").replace("İ", "i").lower()


def rastgele_indeks(n, haric=()):
    """Daha önce kirletilmemiş satırlardan n tanesini seçer."""
    adaylar = np.setdiff1d(np.arange(N), np.array(list(haric), dtype=int))
    return rng.choice(adaylar, size=n, replace=False)


# --- 1) Temiz "gerçek" veri ----------------------------------------------------
cinsiyet = rng.choice(["E", "K"], size=N)
ad = [rng.choice(ADLAR_E if c == "E" else ADLAR_K) for c in cinsiyet]
soyad = rng.choice(SOYADLAR, size=N)
yas = np.clip(rng.normal(41, 12, N), 18, 78).round().astype(int)
sehir = rng.choice(SEHIRLER, size=N, p=SEHIR_OLASILIK)
egitim = rng.choice(EGITIM, size=N, p=EGITIM_OLASILIK)
uyelik = rng.choice(UYELIK, size=N, p=UYELIK_OLASILIK)

baslangic = date(2018, 1, 1)
gun_araligi = (date(2025, 6, 30) - baslangic).days
kayit = [baslangic + timedelta(days=int(g)) for g in rng.integers(0, gun_araligi, N)]

gelir = np.array([EGITIM_MEDYAN_GELIR[e] for e in egitim]) * rng.lognormal(0, 0.28, N)
gelir = gelir * (1 + (yas - 41) * 0.006)                     # yaşla hafif artış
gelir = (gelir / 100).round() * 100

memnuniyet = np.clip(rng.normal(3.6, 1.0, N).round(), 1, 5).astype(int)

skor = (-2.6 + 0.000035 * gelir + 0.45 * (memnuniyet - 3)
        + np.select([uyelik == "Gold", uyelik == "Platin"], [1.0, 1.7], 0))
kampanya = np.where(rng.random(N) < 1 / (1 + np.exp(-skor)), "Evet", "Hayır")

musteri_id = np.arange(1001, 1001 + N)
e_posta = [f"{ascii_yap(a)}.{ascii_yap(s)}{i % 97}@ornek.com"
           for a, s, i in zip(ad, soyad, musteri_id)]

df = pd.DataFrame({
    "musteri_id": musteri_id,
    "ad_soyad": [f"{a} {s}" for a, s in zip(ad, soyad)],
    "cinsiyet": cinsiyet,
    "yas": yas.astype(object),
    "sehir": sehir.astype(object),
    "egitim": egitim.astype(object),
    "uyelik_tipi": uyelik.astype(object),
    "kayit_tarihi": [k.isoformat() for k in kayit],
    "gelir_aylik": gelir.astype(int).astype(object),
    "gelir_yillik": gelir * 12,
    "memnuniyet": memnuniyet.astype(object),
    "e_posta": e_posta,
    "ulke": "Türkiye",
    "referans_kodu": np.where(rng.random(N) < 0.12,
                              [f"REF{x:04d}" for x in rng.integers(1, 9999, N)], None),
    "kampanya_yanit": kampanya.astype(object),
})

# --- 2) Kirletme ---------------------------------------------------------------
kullanildi = set()

# 2.1 Yazım / büyük-küçük harf / boşluk tutarsızlıkları
df["sehir"] = [kirlet(s, SEHIR_KIRLI, 0.30) for s in df["sehir"]]
df["egitim"] = [kirlet(e, EGITIM_KIRLI, 0.20) for e in df["egitim"]]
df["uyelik_tipi"] = [kirlet(u, UYELIK_KIRLI, 0.15) for u in df["uyelik_tipi"]]
df["cinsiyet"] = [kirlet(c, {"E": ["Erkek", "erkek", "e", "ERKEK"],
                             "K": ["Kadın", "kadın", "k", "KADIN", "Kadin"]}, 0.25)
                  for c in df["cinsiyet"]]
df["kampanya_yanit"] = [kirlet(k, {"Evet": ["evet", "E", "EVET"],
                                   "Hayır": ["hayır", "hayir", "H", "HAYIR"]}, 0.12)
                        for k in df["kampanya_yanit"]]

# Ad-soyad: fazladan boşluklar ve tutarsız harf büyüklüğü
idx = rastgele_indeks(25)
df.loc[idx, "ad_soyad"] = [f"  {tr_buyuk(x)} " if i % 2 else tr_kucuk(x).replace(" ", "   ")
                           for i, x in enumerate(df.loc[idx, "ad_soyad"])]
# E-posta: büyük harfle girilmiş adresler (aynı adres, farklı yazım)
idx = rastgele_indeks(15)
df.loc[idx, "e_posta"] = df.loc[idx, "e_posta"].str.title()

# 2.2 Karışık tarih biçimleri: ISO (YYYY-AA-GG), GG/AA/YYYY ve GG.AA.YYYY
for i in range(N):
    r = rng.random()
    yil, ay, gun = df.at[i, "kayit_tarihi"].split("-")
    if r < 0.15:
        df.at[i, "kayit_tarihi"] = f"{gun}/{ay}/{yil}"
    elif r < 0.30:
        df.at[i, "kayit_tarihi"] = f"{gun}.{ay}.{yil}"

# 2.3 Metin olarak saklanmış sayılar
idx = rastgele_indeks(40)
df.loc[idx, "gelir_aylik"] = [f"{int(g):,} TL".replace(",", ".") if i % 2 else f"{int(g)} TL"
                              for i, g in enumerate(df.loc[idx, "gelir_aylik"])]
idx = rastgele_indeks(4)
df.loc[idx, "yas"] = [f"{y} yaş" for y in df.loc[idx, "yas"]]

# 2.4 Geçersiz / imkânsız değerler (alan bilgisiyle yakalanır)
idx = rastgele_indeks(14)
kullanildi.update(idx)
df.loc[idx[0], "yas"] = 250
df.loc[idx[1], "yas"] = -4
df.loc[idx[2], "yas"] = 0
df.loc[idx[3], "yas"] = 7                    # 18 yaş altı müşteri olamaz
df.loc[idx[4], "yas"] = "otuz beş"           # sayıya çevrilemez
df.loc[idx[5], "gelir_aylik"] = -25000
df.loc[idx[6], "gelir_aylik"] = -18000
df.loc[idx[7], "gelir_aylik"] = 3_500_000     # veri girişi hatası (fazladan sıfırlar)
df.loc[idx[8], "memnuniyet"] = 9              # 1-5 ölçeğinin dışında
df.loc[idx[9], "memnuniyet"] = 0
df.loc[idx[10], "memnuniyet"] = 55
df.loc[idx[11], "kayit_tarihi"] = "2029-04-01"  # gelecekteki tarih
df.loc[idx[12], "kayit_tarihi"] = "31.02.2022"  # takvimde olmayan tarih
df.loc[idx[13], "e_posta"] = "ayse.kaya@"
for i, hatali in zip(rastgele_indeks(3, kullanildi), ["mehmet.demir.ornek.com",
                                                      "selin@ornek", "kerem koc@ornek.com"]):
    df.loc[i, "e_posta"] = hatali
df["gelir_yillik"] = pd.to_numeric(df["gelir_aylik"], errors="coerce") * 12
df.loc[df["gelir_yillik"].isna(), "gelir_yillik"] = (
    df.loc[df["gelir_yillik"].isna(), "gelir_aylik"]
    .str.replace(r"[^\d]", "", regex=True).astype(float) * 12)

# 2.5 Gerçek ama aşırı yüksek gelirler (geçerli aykırı değerler)
idx = rastgele_indeks(5, kullanildi)
kullanildi.update(idx)
yuksek = [185000, 210000, 245000, 160000, 230000]
df.loc[idx, "gelir_aylik"] = yuksek
df.loc[idx, "gelir_yillik"] = np.array(yuksek) * 12
df.loc[idx, "egitim"] = ["Doktora", "Yüksek Lisans", "Doktora", "Lisans", "Yüksek Lisans"]

# 2.6 Eksik değerler (boş hücre) ve gizli eksik değerler ("?", "-", "N/A" ...)
eksik_oranlari = {"yas": 0.05, "sehir": 0.04, "egitim": 0.04, "gelir_aylik": 0.10,
                  "memnuniyet": 0.06, "e_posta": 0.03, "cinsiyet": 0.02}
for sutun, oran in eksik_oranlari.items():
    idx = rastgele_indeks(int(N * oran), kullanildi)
    yarisi = len(idx) // 2
    df.loc[idx[:yarisi], sutun] = None
    df.loc[idx[yarisi:], sutun] = rng.choice(GIZLI_EKSIK, size=len(idx) - yarisi)
    if sutun == "gelir_aylik":
        df.loc[idx, "gelir_yillik"] = None
# Eğitimi düşük olanlar gelirini daha sık boş bırakıyor (rastgele olmayan eksiklik)
idx = [i for i in rastgele_indeks(40, kullanildi) if df.at[i, "egitim"] in ("İlkokul", "Lise")][:8]
df.loc[idx, ["gelir_aylik", "gelir_yillik"]] = None
# Hedef değişkeni eksik iki kayıt
df.loc[rastgele_indeks(2, kullanildi), "kampanya_yanit"] = None
# Neredeyse tamamen boş üç kayıt
idx = rastgele_indeks(3, kullanildi)
df.loc[idx, ["cinsiyet", "yas", "sehir", "egitim", "gelir_aylik", "gelir_yillik",
             "memnuniyet", "e_posta", "kayit_tarihi"]] = None

# 2.7 Mükerrer kayıtlar
tam_kopya = df.loc[rng.choice(N, 10, replace=False)]          # birebir aynı satırlar
yari_kopya = df.loc[rng.choice(N, 6, replace=False)].copy()   # aynı müşteri, farklı yazım
yari_kopya["ad_soyad"] = "  " + yari_kopya["ad_soyad"].map(tr_buyuk)
# Python'un str.lower() metodu "İ" harfini "i̇" (i + birleşik nokta) yapar: gerçek hayattaki bir tuzak
yari_kopya["sehir"] = yari_kopya["sehir"].map(lambda s: s.lower() if isinstance(s, str) else s)
yari_kopya.loc[yari_kopya.index[:3], "memnuniyet"] = None     # daha eksik kopya
df = pd.concat([df, tam_kopya, yari_kopya], ignore_index=True)
df = df.sample(frac=1, random_state=42).reset_index(drop=True)

df["gelir_yillik"] = pd.to_numeric(df["gelir_yillik"]).round().astype("Int64")
df.to_csv(KLASOR / "musteriler_kirli.csv", index=False, encoding="utf-8")

# --- 3) İkinci kaynak: sipariş sistemi ------------------------------------------
siparis = []
for mid, g, u in zip(musteri_id, gelir, uyelik):
    adet = rng.poisson(1.5 + g / 20000 + {"Standart": 0, "Gold": 1.5, "Platin": 3}[u])
    if rng.random() < 0.07:
        adet = 0                                       # hiç sipariş vermemiş müşteri
    for _ in range(adet):
        tl = rng.lognormal(np.log(250 + g * 0.02), 0.6)
        if rng.random() < 0.3:
            siparis.append((f"C-{mid}", round(tl / 40, 2), "USD"))
        else:
            siparis.append((f"C-{mid}", round(tl, 2), "TL"))
for _ in range(12):                                    # CRM'de karşılığı olmayan müşteriler
    siparis.append((f"C-{rng.integers(1401, 1450)}", round(rng.lognormal(6, 0.5), 2), "TL"))

sip = pd.DataFrame(siparis, columns=["cust_id", "tutar", "para_birimi"])
sip = sip.sample(frac=1, random_state=7).reset_index(drop=True)
sip.insert(0, "siparis_no", [f"S{100000 + i}" for i in range(len(sip))])
sip = pd.concat([sip, sip.sample(8, random_state=3)], ignore_index=True)   # çift aktarılmış siparişler
sip.to_csv(KLASOR / "siparisler.csv", index=False, encoding="utf-8")

print(f"musteriler_kirli.csv: {df.shape[0]} satır, {df.shape[1]} sütun")
print(f"siparisler.csv     : {sip.shape[0]} satır, {sip.shape[1]} sütun")
