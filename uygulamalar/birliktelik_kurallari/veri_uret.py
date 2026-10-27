"""Birliktelik kuralları uygulaması için sentetik market sepeti verisini üretir.

Bir mahalle marketinin 1000 alışveriş fişi taklit edilir. Her fiş, birkaç
"alışveriş senaryosu"nun (kahvaltı, bebek bakımı, çamaşır, akşam yemeği,
film gecesi) ve rastgele "dolgu" ürünlerin birleşimidir. Senaryolar veriye
bilerek gömülmüş birliktelik kurallarıdır; algoritmaların bunları geri
bulması beklenir:

* bebek bakımı : bez        -> mama, islak_mendil
* çamaşır      : deterjan   -> yumusatici
* akşam yemeği : makarna    -> domates_sosu, kiyma
* kahvaltı     : peynir, zeytin, yumurta, cay -> (cay -> seker)
* film gecesi  : cips       -> kola

Ekmek ise senaryolardan bağımsız olarak fişlerin yaklaşık %60'ında bulunur.
Bu yüzden "X -> ekmek" biçimindeki kuralların güveni yüksek, lift değeri ise
1'e yakın çıkar (güvenin tek başına yanıltıcı olabileceğini gösterir).

Üretilen dosyalar (aynı 1000 fişin iki farklı gösterimi):

* veri/market_sepeti.arff : Weka için; her ürün tek değerli {t} niteliğidir,
                            ürün fişte yoksa değer '?' (eksik) olur.
* veri/market_sepeti.csv  : Python için; her satır bir fiş, ürünler ';' ile
                            ayrılmış.
* veri/ornek_5_islem.arff : ders notundaki 5 fişlik elle hesaplama örneği.

Çalıştırma (bu klasörden):
    python veri_uret.py

Sabit tohum (42) kullanıldığı için her çalıştırmada aynı dosyalar üretilir.
Yalnızca Python standart kütüphanesi kullanılır.
"""

import random
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")   # Windows konsolunda Türkçe karakterler için
rng = random.Random(42)
KLASOR = Path(__file__).resolve().parent / "veri"
KLASOR.mkdir(exist_ok=True)

N = 1000

# Weka'da Türkçe karakter sorunu yaşanmaması için ürün adları ASCII yazıldı.
URUNLER = [
    "ekmek", "sut", "peynir", "zeytin", "yumurta", "cay", "seker",
    "bez", "mama", "islak_mendil",
    "deterjan", "yumusatici",
    "makarna", "domates_sosu", "kiyma",
    "cips", "kola",
    "su", "muz", "kahve",
]

# Her fişe senaryodan bağımsız eklenen ürünler ve olasılıkları
DOLGU = {
    "ekmek": 0.60, "su": 0.30, "sut": 0.25, "muz": 0.15, "kahve": 0.08,
    "peynir": 0.05, "yumurta": 0.06, "cay": 0.05, "makarna": 0.04,
    "cips": 0.05, "kola": 0.06, "seker": 0.04,
}

# senaryo: (fişte görülme olasılığı, {ürün: senaryo içindeki olasılık})
SENARYOLAR = {
    "kahvalti":     (0.30, {"peynir": 0.85, "zeytin": 0.70, "yumurta": 0.50, "cay": 0.55}),
    "bebek":        (0.15, {"bez": 1.00, "mama": 0.80, "islak_mendil": 0.70}),
    "camasir":      (0.10, {"deterjan": 1.00, "yumusatici": 0.75}),
    "aksam_yemegi": (0.18, {"makarna": 1.00, "domates_sosu": 0.70, "kiyma": 0.40}),
    "film_gecesi":  (0.12, {"cips": 0.90, "kola": 0.80}),
}


def fis_uret():
    sepet = set()
    for urun, p in DOLGU.items():
        if rng.random() < p:
            sepet.add(urun)
    for p_senaryo, urunler in SENARYOLAR.values():
        if rng.random() < p_senaryo:
            for urun, p in urunler.items():
                if rng.random() < p:
                    sepet.add(urun)
    # Çay alanların çoğu şeker de alır (kahvaltı dışında da geçerli bir kural)
    if "cay" in sepet and rng.random() < 0.65:
        sepet.add("seker")
    if not sepet:                      # boş fiş olmasın
        sepet.add(rng.choice(["ekmek", "su", "sut"]))
    return sepet


def arff_yaz(dosya, iliski, urunler, fisler, aciklama):
    satirlar = [f"% {s}" for s in aciklama]
    satirlar += ["", f"@relation {iliski}", ""]
    satirlar += [f"@attribute {u} {{t}}" for u in urunler]
    satirlar += ["", "@data"]
    satirlar += [",".join("t" if u in fis else "?" for u in urunler) for fis in fisler]
    dosya.write_text("\n".join(satirlar) + "\n", encoding="utf-8")


fisler = [fis_uret() for _ in range(N)]

# 1) Weka için ARFF
arff_yaz(KLASOR / "market_sepeti.arff", "market_sepeti", URUNLER, fisler, [
    "Sentetik market sepeti verisi: 1000 fiş, 20 ürün (veri_uret.py ile üretildi).",
    "Her nitelik bir üründür: 't' = ürün fişte var, '?' = yok.",
])

# 2) Python için işlem (fiş) listesi
with open(KLASOR / "market_sepeti.csv", "w", encoding="utf-8", newline="\n") as f:
    f.write("fis_no,urunler\n")
    for i, fis in enumerate(fisler, start=1):
        f.write(f"{i},{';'.join(u for u in URUNLER if u in fis)}\n")

# 3) Ders notundaki 5 fişlik örnek (Bölüm 6.1)
ornek = [
    {"ekmek", "sut"},
    {"ekmek", "bez", "mama", "yumurta"},
    {"sut", "bez", "mama", "kola"},
    {"ekmek", "sut", "bez", "mama"},
    {"ekmek", "sut", "bez", "kola"},
]
arff_yaz(KLASOR / "ornek_5_islem.arff", "ornek_5_islem",
         ["ekmek", "sut", "bez", "mama", "kola", "yumurta"], ornek, [
    "Ders notu Bölüm 6.1-6.2'deki 5 fişlik elle hesaplama örneği.",
])

ortalama = sum(len(f) for f in fisler) / N
print(f"{N} fiş üretildi, fiş başına ortalama {ortalama:.2f} ürün.")
for u in URUNLER:
    print(f"  {u:<13} destek = {sum(u in f for f in fisler) / N:.3f}")
