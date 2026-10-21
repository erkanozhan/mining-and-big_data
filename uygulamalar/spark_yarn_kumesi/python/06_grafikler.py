"""Uygulama sonuçlarını (ciktilar/sonuclar.json) SVG grafiklere dönüştürür.

Kullanım:  python python/06_grafikler.py
Gerekli:   pip install matplotlib
"""

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt  # noqa: E402

KLASOR = Path(__file__).resolve().parent.parent / "ciktilar"
S = json.loads((KLASOR / "sonuclar.json").read_text(encoding="utf-8"))

# Ders notundaki şekillerle aynı palet (scripts/sekil_uret.py)
MAVI, YESIL, TURUNCU, MOR, KIRMIZI = "#3b82f6", "#10b981", "#f59e0b", "#8b5cf6", "#ef4444"
GRI, KOYU = "#6b7280", "#1f2937"
MAKINE_RENGI = {"Gigabyte": MAVI, "Mini": YESIL, "Vento": TURUNCU}

plt.rcParams.update({
    "svg.fonttype": "none",
    "svg.hashsalt": "spark-kume",
    "font.family": "sans-serif",
    "font.sans-serif": ["Segoe UI", "DejaVu Sans", "Arial", "Helvetica"],
    "font.size": 12,
    "axes.titlesize": 14,
    "axes.titleweight": "bold",
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.edgecolor": GRI,
    "axes.labelcolor": KOYU,
    "text.color": KOYU,
    "xtick.color": KOYU,
    "ytick.color": KOYU,
})


def kaydet(fig, ad):
    yol = KLASOR / ad
    fig.savefig(yol, format="svg", facecolor="white", bbox_inches="tight", metadata={"Date": None})
    plt.close(fig)
    print("yazıldı:", yol)


def yatay_cubuk(baslik, etiketler, degerler, renkler, ad, not_metni=None):
    fig, ax = plt.subplots(figsize=(9, 0.75 * len(etiketler) + 1.6))
    cubuklar = ax.barh(etiketler, degerler, color=renkler, height=0.6)
    ax.invert_yaxis()
    ax.set_xlabel("Süre (saniye) — kısa olan daha iyi")
    ax.set_title(baslik, loc="left")
    ax.bar_label(cubuklar, labels=[f"{d:.1f} sn" for d in degerler], padding=4)
    ax.set_xlim(0, max(degerler) * 1.18)
    if not_metni:
        fig.text(0.01, -0.02, not_metni, fontsize=10, color=GRI, ha="left", va="top")
    kaydet(fig, ad)


# 1) 1BRC: aynı sorgu, üç farklı veri biçimi
b = S["02_1brc"]
yatay_cubuk(
    "1BRC sorgusu: 100 milyon satır, 3 düğüm",
    ["Düz metin (CSV)", "Parquet (sütunlu)", "Bellekte (cache)"],
    [b["csv_sn"], b["parquet_sn"], b["cache_sorgu_sn"]],
    [GRI, MAVI, YESIL],
    "g1_1brc_bicimler.svg",
    f"CSV {b['csv_bayt'] / 1e9:.2f} GB, Parquet {b['parquet_bayt'] / 1e9:.2f} GB. "
    f"Belleğe alma bir kerelik {b['cache_yukleme_sn']:.1f} sn sürdü.",
)

# 2) Kelime sayma: MapReduce ve Spark
k = S["03_kelime_sayma"]
yatay_cubuk(
    f"Kelime sayma: {k['girdi_bayt'] / 1e6:.0f} MB metin, 3 düğüm",
    ["Hadoop MapReduce (Java)", "Spark RDD (Python)", "Spark DataFrame"],
    [k["mapreduce_sn"], k["spark_rdd_sn"], k["spark_dataframe_sn"]],
    [GRI, TURUNCU, MAVI],
    "g2_kelime_sayma.svg",
)

# 3) Hiperparametre araması: küme ve tek makine
etiket, deger, renk = [], [], []
for p in (1, 4):
    if f"04_mllib_p{p}" in S:
        etiket.append(f"Spark MLlib, küme (paralellik={p})")
        deger.append(S[f"04_mllib_p{p}"]["sure_sn"])
        renk.append(MAVI if p == 1 else MOR)
if "04b_sklearn_tek_makine" in S:
    t = S["04b_sklearn_tek_makine"]
    etiket.append(f"scikit-learn, tek makine ({t['cekirdek']} iş parçacığı)")
    deger.append(t["sure_sn"])
    renk.append(YESIL)
yatay_cubuk("Rastgele Orman, 4 birleşim × 3 kat = 12 model (Covertype, 465 bin satır)",
            etiket, deger, renk, "g3_hiperparametre.svg")

# 4) Ölçekleme: süre ve hızlanma
o = S["05_olcekleme"]
n = [r["executor"] for r in o]
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4.6))
ax1.plot(n, [r["sure_sn"] for r in o], "o-", color=MAVI, lw=2.5, ms=8)
for r in o:
    ax1.annotate(f"{r['sure_sn']:.0f} sn", (r["executor"], r["sure_sn"]),
                 textcoords="offset points", xytext=(0, 9), ha="center")
ax1.set_xlabel("Executor sayısı (her biri 2 çekirdek)")
ax1.set_ylabel("Süre (sn)")
ax1.set_title("1BRC sorgusunun süresi", loc="left")
ax1.set_xticks(n)
ax1.set_ylim(0, max(r["sure_sn"] for r in o) * 1.2)
ax2.plot(n, n, "--", color=GRI, lw=1.5, label="İdeal (doğrusal) hızlanma")
ax2.plot(n, [r["hizlanma"] for r in o], "o-", color=KIRMIZI, lw=2.5, ms=8, label="Ölçülen hızlanma")
ax2.set_xlabel("Executor sayısı")
ax2.set_ylabel("Hızlanma (1 executor'a göre)")
ax2.set_title("Hızlanma (speedup)", loc="left")
ax2.set_xticks(n)
ax2.legend(frameon=False)
kaydet(fig, "g4_olcekleme.svg")

# 5) Düğümlerin gerçek hızı: 1 çekirdeğin saniyede işlediği veri
toplam = {}
for r in o:
    for ad, m in r["makineler"].items():
        t = toplam.setdefault(ad, [0, 0])
        t[0] += m["okunan_bayt"]
        t[1] += m["gorev_ms"]
adlar = [a for a in ("Gigabyte", "Mini", "Vento") if a in toplam]
hiz = [toplam[a][0] / 1e6 / (toplam[a][1] / 1000) for a in adlar]
fig, ax = plt.subplots(figsize=(8, 3.6))
cubuklar = ax.bar(adlar, hiz, color=[MAKINE_RENGI[a] for a in adlar], width=0.55)
ax.bar_label(cubuklar, labels=[f"{h:.1f} MB/sn" for h in hiz], padding=3)
ax.set_ylabel("MB/sn (çekirdek başına)")
ax.set_title("Düğüm başına işleme hızı: aynı görev, farklı makine", loc="left")
ax.set_ylim(0, max(hiz) * 1.25)
kaydet(fig, "g5_dugum_hizi.svg")
