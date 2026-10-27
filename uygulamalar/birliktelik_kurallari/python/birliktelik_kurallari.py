"""Birliktelik kuralları uygulaması: Apriori ve FP-Growth (Python / mlxtend).

Weka'da Explorer > Associate sekmesinde yapılan işin Python karşılığıdır.
Aynı veri (veri/market_sepeti.csv ile veri/market_sepeti.arff aynı 1000 fiştir)
ve aynı eşikler (min_sup = 0.10, min_conf = 0.60) kullanıldığında Weka ile
aynı sık öğe kümeleri ve aynı 27 kural bulunur.

Çalıştırma (uygulamalar/birliktelik_kurallari klasöründen):
    pip install "mlxtend>=0.23" pandas
    python python/birliktelik_kurallari.py
"""

import sys
import time
from pathlib import Path

import pandas as pd
from mlxtend.frequent_patterns import apriori, association_rules, fpgrowth
from mlxtend.preprocessing import TransactionEncoder

sys.stdout.reconfigure(encoding="utf-8")   # Windows konsolunda Türkçe karakterler için
pd.set_option("display.width", 160)

KLASOR = Path(__file__).resolve().parent.parent
CIKTI = KLASOR / "ciktilar" / "python"
CIKTI.mkdir(parents=True, exist_ok=True)

MIN_SUP, MIN_CONF = 0.10, 0.60


def baslik(metin):
    print(f"\n{'=' * 70}\n{metin}\n{'=' * 70}")


def kume_yaz(kume):
    return "{" + ", ".join(sorted(kume)) + "}"


# --------------------------------------------------------------------------
# Adım 1 — Veriyi okuma: her satır bir fiş, ürünler ';' ile ayrılmış
# --------------------------------------------------------------------------
baslik("Adım 1 — Veriyi okuma")
df = pd.read_csv(KLASOR / "veri" / "market_sepeti.csv")
islemler = df["urunler"].str.split(";").tolist()
print(f"{len(islemler)} fiş okundu. İlk üç fiş:")
for fis in islemler[:3]:
    print("  ", fis)

# --------------------------------------------------------------------------
# Adım 2 — İşlem listesini ikili (one-hot) tabloya çevirme
# Weka'daki ARFF dosyası da aynı şeyi yapar: her ürün bir nitelik (sütun).
# --------------------------------------------------------------------------
baslik("Adım 2 — İkili (one-hot) tablo")
te = TransactionEncoder()
X = pd.DataFrame(te.fit(islemler).transform(islemler), columns=te.columns_)
print(f"Tablo boyutu: {X.shape[0]} fiş x {X.shape[1]} ürün")
print(X.head(3).astype(int).to_string())
print("\nÜrün destekleri (çoktan aza):")
print(X.mean().sort_values(ascending=False).round(3).to_string())

# --------------------------------------------------------------------------
# Adım 3 — Sık öğe kümeleri: Apriori ve FP-Growth
# --------------------------------------------------------------------------
baslik(f"Adım 3 — Sık öğe kümeleri (min_sup = {MIN_SUP})")
# Not: Bu küçük veride (20 ürün) mlxtend'in vektörel Apriori'si FP-Growth kadar,
# hatta ondan hızlı çalışabilir. FP-Growth'un üstünlüğü çok sayıda ürün, düşük
# destek eşiği ve uzun örüntüler olduğunda ortaya çıkar.
t0 = time.perf_counter()
sik_apriori = apriori(X, min_support=MIN_SUP, use_colnames=True)
t_apriori = time.perf_counter() - t0

t0 = time.perf_counter()
sik_fp = fpgrowth(X, min_support=MIN_SUP, use_colnames=True)
t_fp = time.perf_counter() - t0

sik_apriori["k"] = sik_apriori["itemsets"].apply(len)
print("Boyuta göre sık öğe kümesi sayısı (Weka'daki L(1), L(2), L(3)):")
print(sik_apriori["k"].value_counts().sort_index().rename("adet").to_string())

ayni = set(sik_apriori["itemsets"]) == set(sik_fp["itemsets"])
print(f"\nApriori {len(sik_apriori)} küme, FP-Growth {len(sik_fp)} küme buldu. "
      f"Kümeler aynı mı? {ayni}")
print(f"Süre: Apriori {t_apriori * 1000:.1f} ms, FP-Growth {t_fp * 1000:.1f} ms")

print("\n3-öğe kümeleri (Weka'daki L(3)):")
for _, r in sik_apriori[sik_apriori["k"] == 3].iterrows():
    print(f"  {kume_yaz(r['itemsets']):<32} destek = {r['support']:.3f}"
          f"  ({round(r['support'] * len(X))} fiş)")

# --------------------------------------------------------------------------
# Adım 4 — Kural üretme (Weka'daki "Best rules found" listesi)
# --------------------------------------------------------------------------
baslik(f"Adım 4 — Kurallar (min_conf = {MIN_CONF})")
kurallar = association_rules(sik_fp, num_itemsets=len(X),
                             metric="confidence", min_threshold=MIN_CONF)
kurallar = kurallar.sort_values(["confidence", "lift"], ascending=False).reset_index(drop=True)
print(f"{len(kurallar)} kural bulundu (Weka da 27 kural bulur).\n")

tablo = pd.DataFrame({
    "kural": kurallar["antecedents"].apply(kume_yaz) + " => " + kurallar["consequents"].apply(kume_yaz),
    "destek": kurallar["support"].round(3),
    "güven": kurallar["confidence"].round(2),
    "lift": kurallar["lift"].round(2),
    "leverage": kurallar["leverage"].round(3),
    "conviction": kurallar["conviction"].round(2),
})
tablo.index += 1
print(tablo.to_string())

# --------------------------------------------------------------------------
# Adım 5 — Lift ile yorumlama: Yüksek güven her zaman ilişki demek değildir
# --------------------------------------------------------------------------
baslik("Adım 5 — Güven yüksek ama lift ≈ 1 olan kurallar")
tuzak = tablo[tablo["lift"].between(0.9, 1.2)]
print(f"Ekmeğin desteği {X['ekmek'].mean():.3f}. Fişlerin çoğunda zaten ekmek var;")
print("bu yüzden '... => {ekmek}' kurallarının güveni yüksek ama lift değeri 1'e yakın:\n")
print(tuzak.to_string())

print("\nGerçekten ilginç kurallar (lift > 2), lift değerine göre:")
print(tablo[tablo["lift"] > 2].sort_values("lift", ascending=False).to_string())

# --------------------------------------------------------------------------
# Adım 6 — Destek eşiğini düşürmek: nadir ama güçlü kurallar
# --------------------------------------------------------------------------
baslik("Adım 6 — min_sup = 0.05 ile yeniden deneme")
sik_005 = fpgrowth(X, min_support=0.05, use_colnames=True)
kurallar_005 = association_rules(sik_005, num_itemsets=len(X),
                                 metric="confidence", min_threshold=MIN_CONF)
print(f"{len(sik_005)} sık öğe kümesi, {len(kurallar_005)} kural.")
yeni = kurallar_005[kurallar_005["antecedents"].apply(
    lambda s: bool(s & {"deterjan", "yumusatici", "cips", "kola", "kiyma"}))
    & (kurallar_005["lift"] > 2)]
print("0.10 eşiğinde görünmeyen, lift > 2 olan kurallardan bazıları:")
for _, r in yeni.sort_values("lift", ascending=False).iterrows():
    print(f"  {kume_yaz(r['antecedents'])} => {kume_yaz(r['consequents'])}"
          f"  destek={r['support']:.3f}  güven={r['confidence']:.2f}  lift={r['lift']:.2f}")

# --------------------------------------------------------------------------
# Kaydetme
# --------------------------------------------------------------------------
tablo.to_csv(CIKTI / "kurallar.csv", index_label="sira", encoding="utf-8")
sik_apriori.assign(itemsets=sik_apriori["itemsets"].apply(kume_yaz)) \
    .drop(columns="k").to_csv(CIKTI / "sik_oge_kumeleri.csv", index=False, encoding="utf-8")
print(f"\nKurallar ve sık öğe kümeleri {CIKTI.relative_to(KLASOR)} klasörüne kaydedildi.")
