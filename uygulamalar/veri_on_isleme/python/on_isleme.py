"""Veri Ön İşleme Uygulaması — Python (pandas) sürümü.

Kirli bir müşteri veri setini ve ikinci bir kaynaktan gelen sipariş verisini
uçtan uca temizler, bütünleştirir, dönüştürür ve indirger. Her adım konsola
ne yaptığını ve sonucunu yazar; grafikler ../ciktilar/python/ klasörüne
kaydedilir.

Adımlar
    1. Veriyi tanıma
    2. Veri temizleme I  : gizli eksikler, metin standardizasyonu, tip dönüşümü,
                           mükerrer kayıtlar, geçersiz değerler
    3. Veri bütünleştirme: anahtar eşleme, para birimi, toplulaştırma, birleştirme,
                           fazlalık analizi (korelasyon, ki-kare)
    4. Aykırı değerler   : IQR ve z-skor, baskılama (winsorizing)
    5. Eksik değerler    : sütun/satır silme, doldurma yöntemlerinin karşılaştırılması
    6. Veri dönüştürme   : özellik türetme, log, normalizasyon, ayrıklaştırma, kodlama
    7. Veri indirgeme    : sabit sütun, PCA, tabakalı örnekleme
    8. Kaydetme ve kalite raporu

Çalıştırma (uygulama klasöründen):
    python python/on_isleme.py

Gerekli paketler: pandas, numpy, matplotlib, scipy, scikit-learn
    pip install pandas numpy matplotlib scipy scikit-learn
"""

import re
import sys
import unicodedata
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from scipy.stats import chi2_contingency  # noqa: E402
from sklearn.decomposition import PCA  # noqa: E402
from sklearn.impute import KNNImputer  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")   # Windows konsolunda Türkçe karakterler için
pd.set_option("display.width", 150)
pd.set_option("display.max_columns", 30)
pd.set_option("display.max_colwidth", 30)

KLASOR = Path(__file__).resolve().parent.parent
VERI = KLASOR / "veri"
CIKTI = KLASOR / "ciktilar" / "python"
CIKTI.mkdir(parents=True, exist_ok=True)

# "Bugün" yerine sabit bir tarih: betik hangi gün çalışırsa çalışsın aynı sonucu üretir
# (tekrar üretilebilirlik / reproducibility).
REFERANS_TARIH = pd.Timestamp("2025-12-31")   # analizin yapıldığı gün
USD_TL = 40.0                                  # sabit kabul edilen döviz kuru
GIZLI_EKSIK = ["?", "-", "N/A", "Bilinmiyor", ""]

# Grafik ayarları
MAVI, TURUNCU, YESIL, KIRMIZI, GRI, KOYU = (
    "#2a78d6", "#eb6834", "#1baf7a", "#e34948", "#a3a29d", "#1f2937")
plt.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["Segoe UI", "DejaVu Sans", "Arial"],
    "font.size": 11,
    "axes.titlesize": 12,
    "axes.titleweight": "bold",
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.edgecolor": GRI,
    "axes.grid": True,
    "grid.color": "#e7e6e2",
    "grid.linewidth": 0.8,
    "axes.axisbelow": True,
    "text.color": KOYU,
    "axes.labelcolor": KOYU,
})


def baslik(metin):
    print("\n" + "=" * 78 + f"\n{metin}\n" + "=" * 78)


def alt_baslik(metin):
    print(f"\n--- {metin} ---")


def kaydet(fig, ad):
    fig.savefig(CIKTI / ad, dpi=130, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"[grafik] ciktilar/python/{ad}")


# =============================================================================
# 1. VERİYİ TANIMA
# =============================================================================
baslik("1. VERİYİ TANIMA")

# Önce "saf" okuma: pandas sütun tiplerini kendisi tahmin etsin (tip çıkarımı).
# Bu tablo yalnızca teşhis içindir: Tek bir "?" bile sütunun tamamını metin yapar,
# böylece hangi sütunlarda sayıya benzemeyen değer olduğunu görürüz.
saf =pd.read_csv(VERI / "musteriler_kirli.csv")
alt_baslik("pandas'ın tahmin ettiği sütun tipleri")
print(saf.dtypes.to_string())
print("\nyas, gelir_aylik ve memnuniyet sayı olmalıydı ama 'object' (metin) okundu:")
print("bu sütunlarda sayıya çevrilemeyen değerler var. Bu yüzden veriyi önce METİN")
print("olarak okuyup her sütunu bilinçli olarak dönüştüreceğiz.")

# Tüm sütunları metin olarak oku; yalnızca tamamen boş hücreler NaN olsun.
# keep_default_na=False: pandas "NA", "N/A", "null" gibi ~20 metni kendiliğinden NaN
# yapmasın; gizli eksikleri 2.1'de KENDİMİZ bulup sayacağız.
ham = pd.read_csv(VERI / "musteriler_kirli.csv", dtype=str,
                  keep_default_na=False, na_values=[""])
df = ham.copy()     # ham'a dokunmuyoruz: 8. adımdaki önce/sonra raporu için saklanır

alt_baslik("Boyut ve ilk satırlar")
print(f"{df.shape[0]} satır, {df.shape[1]} sütun")
print(df.head(8).to_string())

alt_baslik("Kategorik sütunlarda kaç farklı yazım var?")
# nunique() = farklı değer sayısı (kardinalite). 6 şehir beklerken 33 görmek,
# yazım tutarsızlığının kesin işaretidir.
for s in ["cinsiyet", "sehir", "egitim", "uyelik_tipi", "kampanya_yanit"]:
    print(f"{s:15s}: {df[s].nunique():3d} farklı değer -> {sorted(df[s].dropna().unique())[:8]} ...")

alt_baslik("Hızlı kalite kontrolleri")
# duplicated() her satır için True/False döndürür; sum() True'ları sayar (True = 1).
# Tüm satıra göre ve anahtara göre sayım arasındaki fark "yarı kopyaları" gösterir.
print(f"Boş hücre sayısı (yalnızca tamamen boş olanlar): {df.isna().sum().sum()}")
print(f"Birebir aynı (mükerrer) satır sayısı          : {df.duplicated().sum()}")
print(f"Tekrarlanan musteri_id sayısı                 : {df['musteri_id'].duplicated().sum()}")

# =============================================================================
# 2. VERİ TEMİZLEME I
# =============================================================================
baslik("2. VERİ TEMİZLEME")

# --- 2.1 Boşluklar ve gizli eksik değerler ------------------------------------
alt_baslik("2.1 Baş/son boşlukları silme ve gizli eksik değerleri NaN yapma")
# Sıralama önemli: Önce boşluklar silinir, yoksa " ? " listedeki "?" ile eşleşmez.
# Listedeki "" de bu yüzden var: Yalnızca boşluktan oluşan hücre strip() sonrası "" olur.
for s in df.columns:
    df[s] = df[s].str.strip()

bos_hucre = ham.isna().sum()
gizli = df.isin(GIZLI_EKSIK).sum()
# isin() her hücre için True/False maskesi üretir; mask() True olan hücreleri NaN yapar.
# 0 ve 999 listede yok: 0 bazı sütunlarda gerçek değerdir; onları 2.5'te kurallarla yakalarız.
df = df.mask(df.isin(GIZLI_EKSIK))     # "?", "-", "N/A", "Bilinmiyor" -> NaN

eksik_tablo = pd.DataFrame({"bos_hucre": bos_hucre, "gizli_eksik": gizli})
eksik_tablo["toplam"] = eksik_tablo.sum(axis=1)
eksik_tablo["oran_%"] = (100 * eksik_tablo["toplam"] / len(df)).round(1)
eksik_tablo = eksik_tablo.sort_values("toplam", ascending=False)
print(eksik_tablo[eksik_tablo["toplam"] > 0].to_string())
print(f"Gizli eksik değerlerle birlikte toplam eksik hücre: {df.isna().sum().sum()}")

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5.5), gridspec_kw={"width_ratios": [1.3, 1]})
ax1.imshow(df.isna().to_numpy(), aspect="auto", cmap=plt.matplotlib.colors.ListedColormap(["#f1f0ec", MAVI]),
           interpolation="nearest")
ax1.set_xticks(range(df.shape[1]), df.columns, rotation=60, ha="right", fontsize=9)
ax1.set_ylabel("Satır (kayıt) numarası")
ax1.set_title("Eksik değer haritası (mavi = eksik)")
ax1.grid(False)
t = eksik_tablo[eksik_tablo["toplam"] > 0].iloc[::-1]
y = np.arange(len(t))
ax2.barh(y, 100 * t["bos_hucre"] / len(df), color=MAVI, label="Boş hücre", height=0.7)
ax2.barh(y, 100 * t["gizli_eksik"] / len(df), left=100 * t["bos_hucre"] / len(df),
         color=TURUNCU, label='Gizli eksik ("?", "-", "N/A", "Bilinmiyor")', height=0.7,
         edgecolor="white", linewidth=1.5)
ax2.set_yticks(y, t.index)
ax2.set_xlabel("Eksik oranı (%)")
ax2.set_title("Sütunlara göre eksik oranı")
ax2.legend(loc="lower right", fontsize=9)
for yi, v in zip(y, t["oran_%"]):
    ax2.text(v + 1, yi, f"%{v}", va="center", fontsize=9)
ax2.grid(axis="y", visible=False)
kaydet(fig, "01_eksik_degerler.png")


# --- 2.2 Metin standardizasyonu ------------------------------------------------
alt_baslik("2.2 Kategorik sütunlarda yazım birliği")


def anahtar(x):
    """Karşılaştırma anahtarı: aksanları ve noktalamayı at, küçült, boşlukları sadeleştir.

    "İstanbul", " İSTANBUL ", "Istanbul", "i̇stanbul", "İst." -> "istanbul" / "ist"
    """
    if pd.isna(x):
        return x
    x = unicodedata.normalize("NFKD", x)                       # ş -> s + çengel, İ -> I + nokta
    x = "".join(c for c in x if not unicodedata.combining(c))  # birleşik işaretleri at
    x = x.replace("ı", "i").lower()                            # ı ayrıştırılamaz, elle çevrilir
    x = re.sub(r"[^\w\s]", " ", x)                             # noktalama -> boşluk (silme değil:
                                                               # "Y.Lisans" -> "y lisans")
    return re.sub(r"\s+", " ", x).strip()


# Anahtar -> standart yazım sözlüğü. Neden bulanık eşleme (Levenshtein) değil? Bulanık
# eşleme "İst." gibi kısaltmaları ve "Altın" -> "Gold" gibi eş anlamlıları bulamaz,
# "Lise" ile "Lisans"ı yanlışlıkla birleştirebilir. Kategori sayısı az ve biliniyorsa
# elle yazılmış sözlük en güvenli ve denetlenebilir yöntemdir.
STANDART = {
    "sehir": {"istanbul": "İstanbul", "ist": "İstanbul", "ankara": "Ankara", "ankra": "Ankara",
              "izmir": "İzmir", "tekirdag": "Tekirdağ", "bursa": "Bursa", "antalya": "Antalya"},
    "egitim": {"ilkokul": "İlkokul", "lise": "Lise", "lisans": "Lisans",
               "yuksek lisans": "Yüksek Lisans", "y lisans": "Yüksek Lisans", "yl": "Yüksek Lisans",
               "doktora": "Doktora", "dr": "Doktora"},
    "uyelik_tipi": {"standart": "Standart", "gold": "Gold", "altin": "Gold",
                    "platin": "Platin", "platinum": "Platin"},
    "cinsiyet": {"e": "E", "erkek": "E", "k": "K", "kadin": "K"},
    "kampanya_yanit": {"evet": "Evet", "e": "Evet", "hayir": "Hayır", "h": "Hayır"},
}

sehir_once = df["sehir"].copy()
for sutun, sozluk in STANDART.items():
    once = df[sutun].nunique()
    anahtarlar = df[sutun].map(anahtar)
    yeni = anahtarlar.map(sozluk)          # sözlükte olmayan anahtar NaN olur -> "tanınmayan"
    taninmayan = df.loc[anahtarlar.notna() & yeni.isna(), sutun].unique()
    df[sutun] = yeni
    print(f"{sutun:15s}: {once:3d} farklı yazım -> {df[sutun].nunique()} kategori"
          + (f"  (tanınmayan: {list(taninmayan)})" if len(taninmayan) else ""))

print("\nÖrnek: şehir sütunundaki yazımlar ve standart karşılıkları")
ornek = pd.DataFrame({"ham": sehir_once, "standart": df["sehir"]}).dropna().drop_duplicates()
print(ornek.sort_values(["standart", "ham"]).head(14).to_string(index=False))


def tr_baslik(x):
    """Türkçe kurallara uygun 'Baş Harf Büyük' yazımı (ı/I ve i/İ ayrımını korur)."""
    if pd.isna(x):
        return x
    x = " ".join(x.replace("̇", "").split())            # fazla boşlukları sadeleştir
    x = x.replace("I", "ı").replace("İ", "i").lower()
    return " ".join(k[0].replace("i", "İ").replace("ı", "I").upper() + k[1:] for k in x.split(" "))


ad_once = df["ad_soyad"].copy()
df["ad_soyad"] = df["ad_soyad"].map(tr_baslik)
df["e_posta"] = df["e_posta"].str.lower()
degisen = ad_once != df["ad_soyad"]
print(f"\nad_soyad: {degisen.sum()} kayıt düzeltildi, ör. "
      + ", ".join(f"'{a}' -> '{b}'" for a, b in zip(ad_once[degisen][:3], df['ad_soyad'][degisen][:3])))
print("Not: Python'da 'YILMAZ'.title() -> 'Yilmaz' olur (yanlış). Türkçe için özel fonksiyon gerekir.")

ham_sayim = sehir_once.value_counts()
std_sayim = df["sehir"].value_counts()
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 7), gridspec_kw={"width_ratios": [1.2, 1]})
ax1.barh(range(len(ham_sayim)), ham_sayim.values[::-1], color=GRI, height=0.75)
ax1.set_yticks(range(len(ham_sayim)), [repr(v) for v in ham_sayim.index[::-1]], fontsize=8.5)
ax1.set_title(f"Önce: {len(ham_sayim)} farklı yazım")
ax1.set_xlabel("Kayıt sayısı")
ax1.grid(axis="y", visible=False)
ax2.barh(range(len(std_sayim)), std_sayim.values[::-1], color=MAVI, height=0.6)
ax2.set_yticks(range(len(std_sayim)), std_sayim.index[::-1])
for i, v in enumerate(std_sayim.values[::-1]):
    ax2.text(v + 1, i, str(v), va="center", fontsize=10)
ax2.set_title(f"Sonra: {len(std_sayim)} şehir")
ax2.set_xlabel("Kayıt sayısı")
ax2.grid(axis="y", visible=False)
fig.suptitle("Şehir sütununun standardizasyonu", fontsize=14, fontweight="bold", y=1.02)
kaydet(fig, "02_metin_standardizasyonu.png")

# --- 2.3 Veri tipi dönüşümleri ---------------------------------------------------
alt_baslik("2.3 Metin olarak saklanmış sayıları ve tarihleri dönüştürme")

yas_metin = df["yas"].copy()
# Desen: isteğe bağlı eksi (-?) + bir veya daha fazla rakam (\d+). Eksiyi bilerek yakalıyoruz:
# "-4" sessizce 4 olmasın, -4 olarak kalsın ki 2.5'teki kural onu imkânsız değer diye yakalasın.
df["yas"] = pd.to_numeric(df["yas"].str.extract(r"(-?\d+)")[0])       # "50 yaş" -> 50
print("yas         : '... yaş' biçimindekiler ->",
      yas_metin[yas_metin.str.contains("yaş", na=False)].tolist(),
      "| sayıya çevrilemeyen ->", yas_metin[yas_metin.notna() & df["yas"].isna()].tolist())

gelir_metin = df["gelir_aylik"].copy()
# "36.500 TL": nokta binlik ayırıcıdır (veride ondalık nokta yok, önceden kontrol edildi).
# regex=False şart: düzenli ifadede "." HERHANGİ bir karakter demektir; o zaman her şey silinirdi.
df["gelir_aylik"] = pd.to_numeric(
    df["gelir_aylik"].str.replace("TL", "", regex=False).str.replace(".", "", regex=False).str.strip())
tl_li = gelir_metin.str.contains("TL", na=False)
print(f"gelir_aylik : {tl_li.sum()} değer 'TL' içeriyordu, ör.",
      [f"{a} -> {b:.0f}" for a, b in zip(gelir_metin[tl_li][:3], df["gelir_aylik"][tl_li][:3])])

for s in ["musteri_id", "gelir_yillik", "memnuniyet"]:
    df[s] = pd.to_numeric(df[s])


def tarih_coz(seri):
    """Üç farklı biçimi sırayla dener: 2023-05-14, 14/05/2023, 14.05.2023.

    Şelale (cascade) mantığı: errors="coerce" uymayan değeri hata yerine NaT yapar;
    sonraki biçim yalnızca hâlâ boş kalanlara (fillna) uygulanır. Biçimleri açıkça
    yazıyoruz, çünkü otomatik tahmin 03/08/2019'u sessizce 8 Mart sanabilir.
    """
    sonuc = pd.to_datetime(seri, format="%Y-%m-%d", errors="coerce")
    for bicim in ["%d/%m/%Y", "%d.%m.%Y"]:
        sonuc = sonuc.fillna(pd.to_datetime(seri, format=bicim, errors="coerce"))
    return sonuc


tarih_metin = df["kayit_tarihi"].copy()
df["kayit_tarihi"] = tarih_coz(df["kayit_tarihi"])
bicimler = tarih_metin.dropna().map(
    lambda t: "YYYY-AA-GG" if "-" in t else ("GG/AA/YYYY" if "/" in t else "GG.AA.YYYY"))
print("kayit_tarihi: biçim dağılımı ->", bicimler.value_counts().to_dict())
print("              çözülemeyen ->", tarih_metin[tarih_metin.notna() & df["kayit_tarihi"].isna()].tolist())
print("\nYeni sütun tipleri:")
print(df.dtypes.to_string())

# --- 2.4 Mükerrer kayıtlar -------------------------------------------------------
alt_baslik("2.4 Mükerrer (tekrarlanan) kayıtlar")
print(f"Ham veride birebir aynı satır      : {ham.duplicated().sum()}")
print(f"Standardizasyondan sonra           : {df.duplicated().sum()}  "
      "(yazım farkı yüzünden görünmeyen kopyalar ortaya çıktı)")
df = df.drop_duplicates().reset_index(drop=True)

tekrar = df[df["musteri_id"].duplicated(keep=False)].sort_values("musteri_id")
print(f"Silindikten sonra aynı musteri_id'ye sahip kayıt: {len(tekrar)} "
      f"({tekrar['musteri_id'].nunique()} müşteri). Örnek:")
print(tekrar.head(4)[["musteri_id", "ad_soyad", "sehir", "gelir_aylik", "memnuniyet"]].to_string(index=False))

# Aynı müşterinin kayıtlarından EN EKSİKSİZ olanı tut ("hayatta kalma kuralı").
# Alternatifler: ilk kayıt (keyfi), en güncel kayıt (tarih damgası gerekir), alan alan
# birleştirme (çelişki kuralı gerekir). Kopyalar yalnızca eksiklikle ayrıştığı için
# en eksiksiz kayıt bilgi kaybı olmadan seçilir.
df["_eksik"] = df.isna().sum(axis=1)                 # satırdaki eksik hücre sayısı
# Müşteri içinde az eksikli kayıt üste çıkar; kind="stable" eşitlerde orijinal sırayı
# korur, böylece sonuç her seferinde (ve R'daki arrange ile) aynıdır.
df = (df.sort_values(["musteri_id", "_eksik"], kind="stable")
        .drop_duplicates("musteri_id", keep="first")
        .drop(columns="_eksik")
        .reset_index(drop=True))
print(f"Anahtar bazlı tekilleştirmeden sonra: {len(df)} satır, "
      f"tekrarlanan musteri_id = {df['musteri_id'].duplicated().sum()}")

# --- 2.5 Geçersiz değerler (iş kuralları) ---------------------------------------
alt_baslik("2.5 Geçersiz / imkânsız değerler (alan bilgisine dayalı kurallar)")
# Pratik bir desen: kullanıcı adı @ alan adı . en az 2 harfli uzantı (tam standart RFC 5322
# çok daha karmaşıktır).
EPOSTA_DESENI = r"^[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}$"
# Her kural: açıklama -> (sütun, ihlal maskesi). Kuralları koddan ayrı bir liste olarak
# tutmak küçük bir "veri doğrulama şeması"dır: Yeni kural tek satır, alan uzmanı okuyabilir.
# "& notna()" eksik değerin ihlal sayılmasını önler: NaN.between() False, ~False ise True olurdu.
# e-postada na=True aynı işi görür (eksik e-posta "desene uyuyor" sayılır).
kurallar = {
    "yas 18-100 arasında olmalı": ("yas", ~df["yas"].between(18, 100) & df["yas"].notna()),
    "gelir_aylik 0 < g < 1.000.000": ("gelir_aylik", ~df["gelir_aylik"].between(1, 999_999) & df["gelir_aylik"].notna()),
    "gelir_yillik 0 < g < 12.000.000": ("gelir_yillik", ~df["gelir_yillik"].between(1, 11_999_999) & df["gelir_yillik"].notna()),
    "memnuniyet 1-5 ölçeğinde olmalı": ("memnuniyet", ~df["memnuniyet"].isin([1, 2, 3, 4, 5]) & df["memnuniyet"].notna()),
    "kayit_tarihi gelecekte olamaz": ("kayit_tarihi", df["kayit_tarihi"] > REFERANS_TARIH),
    "e_posta geçerli biçimde olmalı": ("e_posta", ~df["e_posta"].str.match(EPOSTA_DESENI, na=True)),
}
kurallar_oncesi = df.copy()
for aciklama, (sutun, ihlal) in kurallar.items():
    degerler = df.loc[ihlal, sutun]
    if sutun == "kayit_tarihi":
        degerler = degerler.dt.strftime("%Y-%m-%d")
    elif sutun != "e_posta":
        degerler = degerler.astype("Int64")         # 250.0 yerine 250 yazdırmak için
    print(f"{aciklama:34s}: {ihlal.sum()} ihlal -> {degerler.tolist()}")
    df.loc[ihlal, sutun] = np.nan   # geçersiz değer = bilinmeyen değer; 5. adımda ele alınacak

fig, axlar = plt.subplots(1, 2, figsize=(11, 5.5))
rng_jitter = np.random.default_rng(0)
for ax, (sutun, etiket) in zip(axlar, [("yas", "Yaş"), ("gelir_aylik", "Aylık gelir (TL)")]):
    x = kurallar_oncesi[sutun].dropna()
    hatali = x.index.isin(df.index[df[sutun].isna()])
    ax.boxplot(x, widths=0.5, showfliers=False,
               medianprops={"color": KOYU}, boxprops={"color": GRI}, whiskerprops={"color": GRI},
               capprops={"color": GRI})
    xj = 1 + rng_jitter.uniform(-0.18, 0.18, len(x))
    ax.scatter(xj[~hatali], x[~hatali], s=14, color=MAVI, alpha=0.5, label="Geçerli")
    ax.scatter(xj[hatali], x[hatali], s=60, color=KIRMIZI, edgecolor="white", linewidth=1.5,
               label="Kural ihlali", zorder=3)
    for i, (v, xx) in enumerate(zip(x[hatali], xj[hatali])):
        ax.annotate(f"{v:,.0f}".replace(",", "."), (xx, v), textcoords="offset points",
                    xytext=(12, 6 if i % 2 else -12), fontsize=9, color=KIRMIZI,
                    bbox={"boxstyle": "round,pad=0.15", "fc": "white", "ec": "none", "alpha": 0.85})
    ax.set_xticks([])
    ax.set_ylabel(etiket)
    ax.legend(loc="upper left", fontsize=9)
axlar[0].set_title("Yaş: 250, 0, -4 ve 7 imkânsız")
axlar[1].set_title("Gelir: tek bir hatalı değer (3.500.000)\ntüm ölçeği eziyor")
axlar[1].yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{v / 1e6:.1f} M"))
kaydet(fig, "03_gecersiz_degerler.png")

# =============================================================================
# 3. VERİ BÜTÜNLEŞTİRME
# =============================================================================
baslik("3. VERİ BÜTÜNLEŞTİRME (sipariş sistemi ile birleştirme)")
sip = pd.read_csv(VERI / "siparisler.csv")
print(f"siparisler.csv: {sip.shape[0]} satır. İlk satırlar:")
print(sip.head(4).to_string(index=False))

# Sıralama: mükerrerler ve para birimi TOPLULAŞTIRMADAN ÖNCE düzeltilmeli; toplamdan sonra
# iki kez sayılmış bir tutar ayırt edilemez, TL ile USD'yi toplamak da anlamsızdır.
alt_baslik("3.1 Sipariş verisindeki mükerrer kayıtlar")
print(f"Aynı siparis_no ile iki kez aktarılmış sipariş: {sip['siparis_no'].duplicated().sum()}")
sip = sip.drop_duplicates("siparis_no")

alt_baslik("3.2 Değer çakışması: farklı para birimleri")
print(sip["para_birimi"].value_counts().to_string())
# np.where(koşul, a, b): vektörel "eğer-değilse". Sabit kur bir basitleştirmedir; gerçek
# projede her sipariş, sipariş tarihindeki kurla çevrilir.
sip["tutar_tl"] = np.where(sip["para_birimi"] == "USD", sip["tutar"] * USD_TL, sip["tutar"])
print(f"USD tutarlar 1 USD = {USD_TL:.0f} TL kabulüyle TL'ye çevrildi.")

alt_baslik("3.3 Varlık tanımlama: 'C-1001' (sipariş sistemi) = 1001 (CRM)")
sip["musteri_id"] = sip["cust_id"].str.replace("C-", "", regex=False).astype(int)
# Ayrıntı düzeyini eşitle: sipariş başına satır -> müşteri başına satır. Toplulaştırmasaydık
# birleştirmeden sonra her müşteri sipariş sayısı kadar tekrarlanırdı.
# Adlandırılmış toplulaştırma: yeni_ad=(sütun, fonksiyon)
ozet = (sip.groupby("musteri_id")
           .agg(siparis_sayisi=("siparis_no", "count"), toplam_harcama_tl=("tutar_tl", "sum"))
           .reset_index())
ozet["toplam_harcama_tl"] = ozet["toplam_harcama_tl"].round(2)
print("Sipariş satırları müşteri düzeyine toplulaştırıldı (aggregation):")
print(ozet.head(4).to_string(index=False))

alt_baslik("3.4 Birleştirme (left join) ve eşleşmeyen kayıtlar")
yetim = ozet[~ozet["musteri_id"].isin(df["musteri_id"])]     # anti-join: siparişte var, CRM'de yok
print(f"CRM'de karşılığı olmayan (yetim) sipariş müşterisi: {len(yetim)} -> {yetim['musteri_id'].tolist()}")
# Neden left join? Analiz birimi CRM müşterisi ve hedef değişken yalnızca CRM'de var.
# inner join siparişsiz müşterileri kaybederdi; outer join demografisi ve hedefi olmayan
# yetimleri getirirdi. Yetimleri tabloya almıyor, yalnızca raporluyoruz.
df = df.merge(ozet, on="musteri_id", how="left")
siparissiz = df["siparis_sayisi"].isna().sum()
print(f"Hiç siparişi olmayan CRM müşterisi              : {siparissiz}")
df[["siparis_sayisi", "toplam_harcama_tl"]] = df[["siparis_sayisi", "toplam_harcama_tl"]].fillna(0)
df["siparis_sayisi"] = df["siparis_sayisi"].astype(int)
print("Bu müşterilerin eksik değeri 'bilinmiyor' değil 'sıfır sipariş' demektir -> 0 ile dolduruldu.")

alt_baslik("3.5 Fazlalık analizi: Pearson korelasyonu")
sayisal = ["yas", "gelir_aylik", "gelir_yillik", "memnuniyet", "siparis_sayisi", "toplam_harcama_tl"]
# Pearson r = cov(X, Y) / (s_X · s_Y), -1 ile +1 arası, birimden bağımsız. Eksikler çift
# bazında atlanır. |r| ≈ 1 ise bir sütun diğerinin doğrusal fonksiyonudur (fazlalık).
# Not: r yalnızca DOĞRUSAL ilişkiyi ölçer; r ≈ 0 ilişkisizlik kanıtı değildir.
kor = df[sayisal].corr()
print(kor.round(3).to_string())
ciftler = [(a, b, kor.loc[a, b]) for i, a in enumerate(sayisal) for b in sayisal[i + 1:]
           if abs(kor.loc[a, b]) > 0.95]
for a, b, r in ciftler:
    print(f"|r| > 0.95: {a} ~ {b} (r = {r:.3f}) -> biri diğerinden türetilebilir")
oran = (df["gelir_yillik"] / df["gelir_aylik"]).dropna().unique()
print(f"gelir_yillik / gelir_aylik oranı her satırda: {oran} -> gelir_yillik sütunu silindi.")

fig, ax = plt.subplots(figsize=(7.5, 6))
im = ax.imshow(kor, cmap="RdBu_r", vmin=-1, vmax=1)
ax.set_xticks(range(len(sayisal)), sayisal, rotation=40, ha="right")
ax.set_yticks(range(len(sayisal)), sayisal)
for i in range(len(sayisal)):
    for j in range(len(sayisal)):
        ax.text(j, i, f"{kor.iloc[i, j]:.2f}", ha="center", va="center", fontsize=10,
                color="white" if abs(kor.iloc[i, j]) > 0.6 else KOYU)
ax.grid(False)
fig.colorbar(im, ax=ax, shrink=0.8, label="Pearson r")
ax.set_title("Korelasyon matrisi: gelir_aylik ve gelir_yillik r = 1")
kaydet(fig, "04_korelasyon.png")
df = df.drop(columns="gelir_yillik")

alt_baslik("3.6 Kategorik nitelikler arasında ilişki: ki-kare (χ²) testi")
for nitelik in ["uyelik_tipi", "sehir"]:
    tablo = pd.crosstab(df[nitelik], df["kampanya_yanit"])     # çapraz (olumsallık) tablosu
    # Gözlenen frekansları "bağımsız olsalardı" beklenenlerle karşılaştırır:
    # χ² = Σ (G - B)² / B, sd = (satır - 1)(sütun - 1). 4. değer (beklenen tablo) kullanılmıyor: _
    # p < 0.05 -> bağımsızlık reddedilir. χ² ilişkinin VARLIĞINI söyler, gücünü değil.
    ki2, p, sd, _ = chi2_contingency(tablo)
    karar = "ilişki VAR (p < 0.05)" if p < 0.05 else "anlamlı ilişki yok"
    print(f"{nitelik} x kampanya_yanit: χ² = {ki2:.2f}, sd = {sd}, p = {p:.4f} -> {karar}")
print(pd.crosstab(df["uyelik_tipi"], df["kampanya_yanit"], normalize="index").round(2).to_string())

# =============================================================================
# 4. AYKIRI DEĞERLER
# =============================================================================
baslik("4. AYKIRI DEĞERLER")


def iqr_sinirlari(x):
    """Tukey kuralı: [Q1 - 1.5·IQR, Q3 + 1.5·IQR].

    1.5 katsayısı normal dağılımda yaklaşık ±2.7σ'ya denk gelir (verinin ~%0.7'si dışarıda
    kalır). Medyan/çeyrekliklere dayandığı için uç değerlerden etkilenmez (sağlam, robust).
    """
    q1, q3 = x.quantile([0.25, 0.75])
    return q1 - 1.5 * (q3 - q1), q3 + 1.5 * (q3 - q1), q1, q3


for sutun in ["gelir_aylik", "toplam_harcama_tl"]:
    x = df[sutun].dropna()
    alt_, ust, q1, q3 = iqr_sinirlari(x)
    z = (x - x.mean()) / x.std()
    print(f"\n{sutun}: Q1 = {q1:,.0f}  Q3 = {q3:,.0f}  IQR = {q3 - q1:,.0f}  "
          f"sınırlar = [{alt_:,.0f} ; {ust:,.0f}]")
    print(f"  IQR yöntemi  : {((x < alt_) | (x > ust)).sum()} aykırı -> "
          f"{sorted(x[(x < alt_) | (x > ust)].round(0).astype(int).tolist(), reverse=True)[:10]}")
    print(f"  z-skor |z|>3 : {(z.abs() > 3).sum()} aykırı -> "
          f"{sorted(x[z.abs() > 3].round(0).astype(int).tolist(), reverse=True)}")

x_hatali = kurallar_oncesi["gelir_aylik"].dropna()
z_hatali = (x_hatali - x_hatali.mean()) / x_hatali.std()
print(f"\nMaskeleme etkisi: 3.500.000 TL'lik hatalı değer silinmeseydi z-skor yalnızca "
      f"{(z_hatali.abs() > 3).sum()} aykırı bulurdu (ortalama {x_hatali.mean():,.0f}, "
      f"std {x_hatali.std():,.0f} şişerdi).")

alt_baslik("Karar")
print("gelir_aylik      : Değerler gerçek (yüksek gelirli müşteriler), silmek bilgi kaybı olur.")
print("                   IQR sınırlarına baskılandı (winsorizing / capping).")
print("toplam_harcama_tl: Sağa çarpık, doğal bir dağılım -> 6. adımda log dönüşümü uygulanacak.")
gelir_once = df["gelir_aylik"].copy()
alt_, ust, _, _ = iqr_sinirlari(df["gelir_aylik"].dropna())
# clip(): sınır dışındakileri sınıra eşitler, aradakilere ve NaN'lere dokunmaz. Tespitte
# kullandığımız sınırın aynısı (ör. %1-%99 yüzdelik değil): "aykırı" = "baskılanan".
# Alt sınır negatif olduğundan pratikte yalnızca üstten baskılanır.
df["gelir_aylik"] = df["gelir_aylik"].clip(lower=alt_, upper=ust)
print(f"Baskılanan değer sayısı: {(gelir_once != df['gelir_aylik']).sum() - gelir_once.isna().sum()}")

fig, axlar = plt.subplots(1, 2, figsize=(13, 4.5), sharey=True)
kutular = np.arange(0, 260_001, 5_000)
for ax, veri, ad in [(axlar[0], gelir_once, "Önce"), (axlar[1], df["gelir_aylik"], "Sonra (baskılama)")]:
    v = veri.dropna()
    ax.hist(v[v <= ust], bins=kutular, color=MAVI, edgecolor="white", linewidth=1, label="Sınırlar içinde")
    ax.hist(v[v > ust], bins=kutular, color=KIRMIZI, edgecolor="white", linewidth=1, label="IQR sınırı dışında")
    ax.axvline(ust, color=KOYU, linestyle="--", linewidth=1.2)
    ax.text(ust, ax.get_ylim()[1] * 0.92, f"  Q3 + 1.5·IQR\n  = {ust:,.0f} TL".replace(",", "."), fontsize=9)
    ax.set_title(ad)
    ax.set_xlabel("Aylık gelir (TL)")
    ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda val, _: f"{val / 1000:.0f} bin"))
axlar[0].set_ylabel("Müşteri sayısı")
axlar[0].legend(fontsize=9, loc="center right")
fig.suptitle("Aykırı gelir değerlerinin IQR sınırına baskılanması", fontsize=14, fontweight="bold", y=1.02)
kaydet(fig, "05_aykiri_degerler.png")

# =============================================================================
# 5. EKSİK DEĞERLER
# =============================================================================
baslik("5. EKSİK DEĞERLER")
print("Şu anki eksik değer sayıları:")
print(df.isna().sum()[df.isna().sum() > 0].to_string())

alt_baslik("5.1 Çoğunlukla boş sütunları silme (eşik %60)")
# isna().mean(): True = 1 olduğundan ortalama doğrudan eksik ORANIDIR.
# Önce sütun, sonra satır: %85'i boş sütun kalsaydı her satırın eksik oranını yapay olarak
# artırır, gereksiz satır silinmesine yol açardı. Eşikler (%60, %50) pratik seçimlerdir.
oranlar = df.isna().mean()
silinecek = oranlar[oranlar > 0.60].index.tolist()
print(f"Silinen sütun(lar): {silinecek} (eksik oranı: {[f'%{100 * oranlar[s]:.0f}' for s in silinecek]})")
df = df.drop(columns=silinecek)

alt_baslik("5.2 Çoğunlukla boş satırları silme (eşik %50)")
satir_oran = df.isna().mean(axis=1)
print(f"Değerlerinin yarısından fazlası eksik satır: {(satir_oran > 0.5).sum()} -> "
      f"{df.loc[satir_oran > 0.5, 'musteri_id'].tolist()}")
df = df[satir_oran <= 0.5]

alt_baslik("5.3 Hedef değişkeni (kampanya_yanit) eksik satırları silme")
print(f"Hedefi eksik satır: {df['kampanya_yanit'].isna().sum()} (hedefi tahmin etmeyiz, öğrenmek için kullanırız)")
df = df[df["kampanya_yanit"].notna()].reset_index(drop=True)

alt_baslik("5.4 Eksiklik rastgele mi? (gelir_aylik)")
# Eksiklik tamamen rastgele (MCAR) olsaydı geliri eksik olanların eğitim dağılımı tüm
# verininkine benzerdi; belirgin fark, eksikliğin eğitime bağlı (MAR) olduğunu gösterir.
egitim_dagilim = pd.DataFrame({
    "geliri_eksik": df.loc[df["gelir_aylik"].isna(), "egitim"].value_counts(normalize=True),
    "tum_veri": df["egitim"].value_counts(normalize=True),
}).reindex(["İlkokul", "Lise", "Lisans", "Yüksek Lisans", "Doktora"]).fillna(0).round(2)
print(egitim_dagilim.to_string())
beklenen = (df.loc[df["gelir_aylik"].isna(), "egitim"]
              .map(df.groupby("egitim")["gelir_aylik"].median()).mean())
print("Geliri eksik olanların eğitim dağılımı tüm veriden farklı: eksiklik eğitime bağlı (MAR).")
print(f"Eğitim gruplarına göre beklenen gelirleri ort. {beklenen:,.0f} TL, genel ortalama ise "
      f"{df['gelir_aylik'].mean():,.0f} TL.")
print("Genel ortalamayla doldurmak bu kişilerin gelirini olduğundan yüksek gösterir.")

alt_baslik("5.5 Kategorik sütunlar: mod (en sık değer) ile doldurma")
# Nominal nitelikte ortalama/medyan tanımsızdır, mod tek seçenektir. mode() birden fazla
# değer döndürebilir (eşit sıklık), [0] ilkini alır.
for s in ["cinsiyet", "sehir", "egitim"]:
    mod = df[s].mode()[0]
    print(f"{s:10s}: {df[s].isna().sum()} eksik -> '{mod}'")
    df[s] = df[s].fillna(mod)

alt_baslik("5.6 gelir_aylik için doldurma yöntemlerinin karşılaştırılması")
EGITIM_SIRA = {"İlkokul": 0, "Lise": 1, "Lisans": 2, "Yüksek Lisans": 3, "Doktora": 4}
UYELIK_SIRA = {"Standart": 0, "Gold": 1, "Platin": 2}
eksik_gelir = df["gelir_aylik"].isna()
# Dört yöntem aynı eksik veriden ayrı ayrı hesaplanır, tabloya henüz yazılmaz; adil
# karşılaştırmadan sonra seçilen yöntem tek satırla uygulanır (aşağıda).
# transform("median"), agg'den farklı olarak tabloyu küçültmez: her satıra kendi grubunun
# medyanını yazar, böylece doğrudan fillna()'ya verilebilir.
yontemler = {
    "Ortalama": df["gelir_aylik"].fillna(df["gelir_aylik"].mean()),
    "Medyan": df["gelir_aylik"].fillna(df["gelir_aylik"].median()),
    "Eğitim grubunun medyanı": df["gelir_aylik"].fillna(
        df.groupby("egitim")["gelir_aylik"].transform("median")),
}
# k-NN: benzer müşterilerin (yaş, eğitim, üyelik, harcama) gelir ortalaması
knn_girdi = pd.DataFrame({
    "yas": df["yas"], "egitim": df["egitim"].map(EGITIM_SIRA),
    "uyelik": df["uyelik_tipi"].map(UYELIK_SIRA), "harcama": df["toplam_harcama_tl"],
    "gelir": df["gelir_aylik"]})
olcek = knn_girdi.drop(columns="gelir")
olcek = (olcek - olcek.min()) / (olcek.max() - olcek.min())       # uzaklık için ölçekleme şart
knn = KNNImputer(n_neighbors=5).fit_transform(olcek.assign(gelir=knn_girdi["gelir"]))
yontemler["k-NN (k = 5)"] = pd.Series(knn[:, -1], index=df.index)

print(f"Eksik gelir sayısı: {eksik_gelir.sum()}")
print(f"{'Yöntem':26s} {'ortalama':>10s} {'std':>10s} {'doldurulan değerlerin ort.':>28s}")
print(f"{'(Gözlenen değerler)':26s} {df['gelir_aylik'].mean():10,.0f} {df['gelir_aylik'].std():10,.0f}")
for ad, seri in yontemler.items():
    print(f"{ad:26s} {seri.mean():10,.0f} {seri.std():10,.0f} {seri[eksik_gelir].mean():28,.0f}")
print("Ortalama/medyan ile doldurma tüm eksiklere AYNI değeri verir: varyans yapay olarak düşer.")
print("Seçilen yöntem: eğitim grubunun medyanı (sınıf bazında doldurma).")
# Neden? MAR yapısını hesaba katar, basit ve açıklanabilirdir. Hepsi "tekli atama"dır:
# doldurulan değerin belirsizliğini gizler; ileri yöntem çoklu atamadır (multiple imputation).

fig, axlar = plt.subplots(2, 2, figsize=(13, 7.5), sharex=True, sharey=True)
kutular = np.arange(0, 80_001, 2_500)
for ax, (ad, seri) in zip(axlar.flat, yontemler.items()):
    ax.hist([seri[~eksik_gelir], seri[eksik_gelir]], bins=kutular, stacked=True,
            color=[MAVI, TURUNCU], edgecolor="white", linewidth=0.8, label=["Gözlenen", "Doldurulan"])
    ax.set_title(f"{ad}  (std = {seri.std():,.0f})".replace(",", "."))
    ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda val, _: f"{val / 1000:.0f} bin"))
axlar[0, 0].legend(fontsize=9)
for ax in axlar[1]:
    ax.set_xlabel("Aylık gelir (TL)")
for ax in axlar[:, 0]:
    ax.set_ylabel("Müşteri sayısı")
fig.suptitle("Eksik gelir değerlerini doldurma yöntemleri", fontsize=14, fontweight="bold", y=1.02)
kaydet(fig, "06_eksik_doldurma.png")

df["gelir_aylik"] = yontemler["Eğitim grubunun medyanı"]

alt_baslik("5.7 Diğer sayısal sütunlar")
print(f"yas         : {df['yas'].isna().sum()} eksik -> medyan = {df['yas'].median():.0f}")
df["yas"] = df["yas"].fillna(df["yas"].median())
print(f"memnuniyet  : {df['memnuniyet'].isna().sum()} eksik -> medyan = {df['memnuniyet'].median():.0f} "
      "(sıralı ölçek: ortalama 3.6 gibi ara değer anlamsız)")
df["memnuniyet"] = df["memnuniyet"].fillna(df["memnuniyet"].median())
medyan_tarih = df["kayit_tarihi"].median().floor("D")     # çift sayıda kayıtta öğlen 12:00 çıkabilir
print(f"kayit_tarihi: {df['kayit_tarihi'].isna().sum()} eksik -> medyan tarih = {medyan_tarih:%Y-%m-%d}")
df["kayit_tarihi"] = df["kayit_tarihi"].fillna(medyan_tarih)
print(f"e_posta     : {df['e_posta'].isna().sum()} eksik -> DOLDURULMADI (iletişim bilgisi tahmin edilemez, "
      "modelde kullanılmayacak)")

alt_baslik("Kalan eksik değerler")
print(df.isna().sum()[df.isna().sum() > 0].to_string())

# =============================================================================
# 6. VERİ DÖNÜŞTÜRME
# =============================================================================
baslik("6. VERİ DÖNÜŞTÜRME")
temiz = df.copy()     # okunabilir, temizlenmiş tablo (kodlanmamış hâli) ayrıca kaydedilecek

alt_baslik("6.1 Özellik türetme (feature construction)")
# Tarih farkı bir süre (timedelta); .dt.days gün sayısı. 365.25: artık yılların ortalaması.
# Sıfıra bölme: pandas'ta 0/0 = NaN, x/0 = inf; siparişi olmayanlara doğrudan 0 yazıyoruz.
# Bu türetilmiş nitelikler pazarlamadaki RFM (Recency, Frequency, Monetary) fikrine dayanır.
df["uyelik_suresi_yil"] = ((REFERANS_TARIH - df["kayit_tarihi"]).dt.days / 365.25).round(2)
df["ort_siparis_tl"] = np.where(df["siparis_sayisi"] > 0,
                                df["toplam_harcama_tl"] / df["siparis_sayisi"].replace(0, 1), 0).round(2)
print(df[["musteri_id", "kayit_tarihi", "uyelik_suresi_yil", "siparis_sayisi",
          "toplam_harcama_tl", "ort_siparis_tl"]].head(5).to_string(index=False))


def carpiklik(x):
    """Çarpıklık: 3. standart moment. 0 simetrik, > 0 sağa çarpık; |g| > 1 güçlü çarpık."""
    x = np.asarray(x, dtype=float)
    return np.mean((x - x.mean()) ** 3) / np.std(x) ** 3


alt_baslik("6.2 Log dönüşümü (sağa çarpık dağılımlar için)")
# Log çarpımsal farkları toplamsala çevirir (1.000 -> 10.000 ile 10.000 -> 100.000 aynı uzaklık).
# Alternatifler: karekök (daha hafif), Box-Cox / Yeo-Johnson (üssü veriden tahmin eder).
df["log_harcama"] = np.log1p(df["toplam_harcama_tl"]).round(4)      # log(1 + x): sıfırlar için güvenli
pozitif = df["toplam_harcama_tl"] > 0
cark_once = carpiklik(df.loc[pozitif, "toplam_harcama_tl"])
cark_sonra = carpiklik(df.loc[pozitif, "log_harcama"])
print(f"Siparişi olan müşterilerde çarpıklık: {cark_once:.2f} -> log1p sonrası {cark_sonra:.2f}")
print(f"Dikkat: {(~pozitif).sum()} müşterinin harcaması 0; log1p(0) = 0 olduğu için bunlar ayrı bir")
print("yığın oluşturur. Çarpıklık ölçüsü bu yığından çok etkilenir, bu yüzden pozitifler üzerinden raporlandı.")

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 4.5))
ax1.hist(df["toplam_harcama_tl"], bins=30, color=MAVI, edgecolor="white")
ax1.set_title(f"Ham harcama (çarpıklık* = {cark_once:.2f})")
ax1.set_xlabel("Toplam harcama (TL)")
ax1.set_ylabel("Müşteri sayısı")
ax1.xaxis.set_major_formatter(plt.FuncFormatter(lambda val, _: f"{val / 1000:.0f} bin"))
ax2.hist(df["log_harcama"], bins=30, color=YESIL, edgecolor="white")
ax2.set_title(f"log(1 + harcama) (çarpıklık* = {cark_sonra:.2f})")
ax2.set_xlabel("log(1 + toplam harcama)")
ax2.annotate("Hiç siparişi olmayanlar\n(log(1 + 0) = 0)", xy=(0.3, (df["log_harcama"] == 0).sum()),
             xytext=(1.5, (df["log_harcama"] == 0).sum() + 12), fontsize=9,
             arrowprops={"arrowstyle": "->", "color": GRI})
fig.suptitle("Log dönüşümü sağa çarpık dağılımı simetrikleştirir", fontsize=14, fontweight="bold", y=1.02)
fig.text(0.5, -0.03, "* Çarpıklık yalnızca siparişi olan müşteriler üzerinden hesaplandı.",
         ha="center", fontsize=9, color="#52514e")
kaydet(fig, "07_log_donusumu.png")

alt_baslik("6.3 Normalizasyon: min-maks ve z-skor")
ornek = pd.DataFrame({"yas": df["yas"], "gelir_aylik": df["gelir_aylik"]})
# İkisi de dağılımın BİÇİMİNİ değiştirmez, yalnızca ekseni kaydırıp gerer.
# min-maks: [0, 1], sınırlı aralık gerektiğinde; tek bir uç değer herkesi sıkıştırır.
# z-skor  : ort. 0, std 1; PCA, doğrusal modeller, kümeleme için standart seçim.
minmaks =(ornek - ornek.min()) / (ornek.max() - ornek.min())
zskor = (ornek - ornek.mean()) / ornek.std()        # pandas std: n-1 (R'daki sd/scale ile aynı)
print(pd.concat([ornek.add_prefix("ham_"), minmaks.add_prefix("minmaks_").round(3),
                 zskor.add_prefix("z_").round(3)], axis=1).head(5).to_string(index=False))
print(f"min-maks aralığı: [{minmaks.min().min():.0f}, {minmaks.max().max():.0f}]   "
      f"z-skor: ortalama ≈ {zskor.mean().abs().max():.0f}, std = {zskor.std().mean():.0f}")

fig, axlar = plt.subplots(1, 3, figsize=(14, 4.5))
for ax, veri, ad in [(axlar[0], ornek, "Ham değerler"), (axlar[1], minmaks, "Min-maks [0, 1]"),
                     (axlar[2], zskor, "z-skor (ort. 0, std 1)")]:
    ax.boxplot([veri["yas"], veri["gelir_aylik"]], widths=0.55, patch_artist=True,
               boxprops={"facecolor": "#dbe8f8", "edgecolor": MAVI}, medianprops={"color": KOYU},
               whiskerprops={"color": MAVI}, capprops={"color": MAVI},
               flierprops={"markerfacecolor": TURUNCU, "markeredgecolor": "white", "markersize": 6})
    ax.set_xticks([1, 2], ["yas", "gelir_aylik"])
    ax.set_title(ad)
    ax.grid(axis="x", visible=False)
axlar[0].yaxis.set_major_formatter(plt.FuncFormatter(lambda val, _: f"{val / 1000:.0f} bin"))
axlar[0].annotate("yaş bu ölçekte\ngörünmüyor", xy=(1, 2_000), xytext=(1.1, 40_000), fontsize=9,
                  arrowprops={"arrowstyle": "->", "color": GRI})
fig.suptitle("Ölçekleme: farklı birimlerdeki nitelikleri karşılaştırılabilir kılar",
             fontsize=14, fontweight="bold", y=1.04)
kaydet(fig, "08_olcekleme.png")

alt_baslik("6.4 Ayrıklaştırma: yaşı aralıklara bölme")
df["yas_esit_genislik"] = pd.cut(df["yas"], bins=4)        # min-maks arası 4 eşit uzunlukta aralık
df["yas_esit_frekans"] = pd.qcut(df["yas"], q=4)           # çeyrekliklerde böl: kovalarda benzer sayı
# Alan bilgisiyle: aralıklar (17, 29] biçimindedir (sol açık, sağ kapalı); 18'in "Genç"e
# girmesi için ilk sınır 17.
df["yas_grubu"] =pd.cut(df["yas"], bins=[17, 29, 49, 100], labels=["Genç", "Orta yaş", "Olgun"])
for s in ["yas_esit_genislik", "yas_esit_frekans", "yas_grubu"]:
    print(f"{s}:\n{df[s].value_counts(sort=False).to_string()}\n")
medyan_yas = df["yas"].median()
print(f"Eşit frekansta kovalar tam eşit değil: {(df['yas'] == medyan_yas).sum()} müşterinin yaşı tam "
      f"{medyan_yas:.0f} (çoğu medyanla doldurulanlar); aynı değer iki kovaya bölünemez.")

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 4.2), sharey=True)
for ax, s, ad, renk in [(ax1, "yas_esit_genislik", "Eşit genişlik: aralıklar aynı boyda", MAVI),
                        (ax2, "yas_esit_frekans", "Eşit frekans: kovalarda benzer sayıda kayıt", YESIL)]:
    sayim = df[s].value_counts(sort=False)
    ax.bar(range(len(sayim)), sayim.values, color=renk, width=0.7)
    ax.set_xticks(range(len(sayim)), [f"({a.left:.1f}, {a.right:.1f}]" for a in sayim.index], fontsize=9)
    for i, v in enumerate(sayim.values):
        ax.text(i, v + 2, str(v), ha="center", fontsize=10)
    ax.set_title(ad)
    ax.set_xlabel("Yaş aralığı")
    ax.grid(axis="x", visible=False)
ax1.set_ylabel("Müşteri sayısı")
fig.suptitle("Ayrıklaştırma: yaş niteliğini 4 kovaya bölme", fontsize=14, fontweight="bold", y=1.02)
kaydet(fig, "09_ayriklastirma.png")

alt_baslik("6.5 Kategorik nitelikleri kodlama")
df["egitim_kod"] = df["egitim"].map(EGITIM_SIRA)              # sıralı (ordinal) kodlama
df["uyelik_kod"] = df["uyelik_tipi"].map(UYELIK_SIRA)         # sıralı: Standart < Gold < Platin
df["cinsiyet_K"] = (df["cinsiyet"] == "K").astype(int)        # ikili (binary) kodlama
df["kampanya_yanit"] = (df["kampanya_yanit"] == "Evet").astype(int)
# Şehre sıralı kod verilseydi model "İstanbul = 4 × Ankara" gibi anlamsız bir sıra öğrenirdi.
# Altı sütunun toplamı her satırda 1'dir (kukla değişken tuzağı); doğrusal modellerde bir
# sütun atılır (drop_first=True). Okunabilirlik için hepsini tutuyoruz.
sehir_dummy = pd.get_dummies(df["sehir"], prefix="sehir", dtype=int)   # one-hot (nominal)
sehir_dummy = sehir_dummy[sorted(sehir_dummy.columns)]                 # R ile aynı sütun sırası
df = pd.concat([df, sehir_dummy], axis=1)
print("egitim  ->", EGITIM_SIRA)
print("uyelik  ->", UYELIK_SIRA)
print("One-hot kodlanmış şehir sütunları:", sehir_dummy.columns.tolist())
print(pd.concat([df[["sehir"]], sehir_dummy], axis=1).head(4).to_string(index=False))

# =============================================================================
# 7. VERİ İNDİRGEME
# =============================================================================
baslik("7. VERİ İNDİRGEME")

alt_baslik("7.1 Bilgi taşımayan sütunlar")
# Tek değerli sütun hiçbir kaydı diğerinden ayıramaz (varyans = entropi = 0). Sütun adı
# yazmak yerine kural tanımladığımız için yeni bir sabit sütun da kendiliğinden yakalanır.
sabit = [s for s in df.columns if df[s].nunique() == 1]
print(f"Tek bir değer alan (sabit) sütunlar: {sabit} -> silindi")
df = df.drop(columns=sabit)
print("Kimlik/iletişim sütunları (musteri_id, ad_soyad, e_posta) model matrisine alınmaz.")

alt_baslik("7.2 Model için hazır tablo")
OZELLIKLER = ["yas", "gelir_aylik", "memnuniyet", "uyelik_suresi_yil", "siparis_sayisi", "log_harcama"]
model = df[["musteri_id"]].copy()
model[OZELLIKLER] = ((df[OZELLIKLER] - df[OZELLIKLER].mean()) / df[OZELLIKLER].std()).round(4)
model[["egitim_kod", "uyelik_kod", "cinsiyet_K"] + sehir_dummy.columns.tolist() + ["kampanya_yanit"]] = \
    df[["egitim_kod", "uyelik_kod", "cinsiyet_K"] + sehir_dummy.columns.tolist() + ["kampanya_yanit"]]
print(f"{model.shape[0]} satır, {model.shape[1]} sütun")
print(model.head(3).to_string(index=False))

alt_baslik("7.3 Temel Bileşenler Analizi (PCA)")
# Bileşen sayısı verilmedi: önce TÜM bileşenleri görüp sonra karar vereceğiz. fit() kovaryans
# matrisinin özvektörlerini (varyansın en büyük, birbirine dik yönleri) bulur. Girdi z-skorla
# ölçeklendi (7.2); yoksa varyansı milyonlarca olan gelir PC1'i tek başına ele geçirirdi.
pca = PCA().fit(model[OZELLIKLER])
aciklanan = pca.explained_variance_ratio_      # her özdeğer / toplam özdeğer
kumulatif = np.cumsum(aciklanan)
for i, (a, k) in enumerate(zip(aciklanan, kumulatif), 1):
    print(f"PC{i}: açıklanan varyans %{100 * a:5.1f}   kümülatif %{100 * k:5.1f}")
gerekli = int(np.argmax(kumulatif >= 0.90) + 1)
print(f"Varyansın %90'ı için {gerekli} bileşen gerekiyor ({len(OZELLIKLER)} nitelik -> {gerekli} bileşen).")
print("Nitelikler birbiriyle zayıf ilişkili olduğundan PCA burada boyutu fazla azaltamıyor;")
print("PCA, güçlü korelasyonlu nitelikler (ör. siparis_sayisi ~ log_harcama) olduğunda daha etkilidir.")
yukler = pd.DataFrame(pca.components_[:2].T, index=OZELLIKLER, columns=["PC1", "PC2"]).round(3)
print("PC1 ve PC2 yükleri (işaretler yazılıma göre ters çıkabilir):")
print(yukler.to_string())

skorlar = pca.transform(model[OZELLIKLER])
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 4.8))
ax1.bar(range(1, len(aciklanan) + 1), 100 * aciklanan, color=MAVI, width=0.6, label="Bileşen başına")
ax1.plot(range(1, len(aciklanan) + 1), 100 * kumulatif, color=TURUNCU, marker="o", linewidth=2,
         markersize=8, label="Kümülatif")
ax1.axhline(90, color=GRI, linestyle="--", linewidth=1)
ax1.text(0.6, 91.5, "%90", color=GRI, fontsize=9)
ax1.set_xticks(range(1, len(aciklanan) + 1), [f"PC{i}" for i in range(1, len(aciklanan) + 1)])
ax1.set_ylabel("Açıklanan varyans (%)")
ax1.set_ylim(0, 105)
ax1.set_title("Açıklanan varyans (scree grafiği)")
ax1.legend(loc="center right", fontsize=9)
ax1.grid(axis="x", visible=False)
for deger, renk, ad in [(0, MAVI, "Hayır"), (1, TURUNCU, "Evet")]:
    m = model["kampanya_yanit"] == deger
    ax2.scatter(skorlar[m, 0], skorlar[m, 1], s=22, color=renk, alpha=0.75, edgecolor="white",
                linewidth=0.6, label=f"Kampanyaya yanıt: {ad}")
ax2.set_xlabel(f"PC1 (%{100 * aciklanan[0]:.1f})")
ax2.set_ylabel(f"PC2 (%{100 * aciklanan[1]:.1f})")
ax2.set_title("Müşteriler ilk iki bileşen düzleminde")
ax2.legend(fontsize=9)
fig.suptitle(f"PCA: {len(OZELLIKLER)} sayısal nitelik", fontsize=14, fontweight="bold", y=1.02)
kaydet(fig, "10_pca.png")

alt_baslik("7.4 Örnekleme: basit rastgele ve tabakalı (%30)")
# Tek bir örnek şanslı/şanssız çıkabilir; 1000 tekrar, yöntemin örnekleme dağılımını gösterir.
# random_state (tohum) "rastgele" örneği tekrar üretilebilir kılar.
# Tabakalı: groupby(hedef) ile her sınıftan AYRI AYRI %30 çekilir, sınıf oranı korunur.
basit_oranlar = np.array([model.sample(frac=0.30, random_state=i)["kampanya_yanit"].mean()
                          for i in range(1000)])
tabakali = model.groupby("kampanya_yanit", group_keys=False).sample(frac=0.30, random_state=1)
print(f"Tüm verideki 'Evet' oranı      : {model['kampanya_yanit'].mean():.3f}")
print(f"Tabakalı örnek (n = {len(tabakali)})        : {tabakali['kampanya_yanit'].mean():.3f}")
print(f"1000 basit rastgele örnek (n = {round(0.3 * len(model))}): "
      f"en düşük {basit_oranlar.min():.3f}, en yüksek {basit_oranlar.max():.3f}, std {basit_oranlar.std():.3f}")
print("Tabakalı örnekleme sınıf oranını her seferinde korur; basit örnekte oran şansa bağlı oynar.")

# =============================================================================
# 8. KAYDETME VE KALİTE RAPORU
# =============================================================================
baslik("8. KAYDETME VE KALİTE RAPORU")
temiz = temiz.drop(columns=[s for s in ["ulke"] if s in temiz.columns])
temiz["kayit_tarihi"] = temiz["kayit_tarihi"].dt.strftime("%Y-%m-%d")
temiz["gelir_aylik"] = temiz["gelir_aylik"].round(2)
for s in ["yas", "memnuniyet", "musteri_id"]:
    temiz[s] = temiz[s].astype(int)
temiz.to_csv(CIKTI / "musteriler_temiz.csv", index=False, encoding="utf-8")
model.to_csv(CIKTI / "musteriler_model.csv", index=False, encoding="utf-8")
print("Kaydedildi: ciktilar/python/musteriler_temiz.csv (okunabilir, temizlenmiş tablo)")
print("Kaydedildi: ciktilar/python/musteriler_model.csv (kodlanmış + ölçeklenmiş, modele hazır)")

rapor = pd.DataFrame({
    "Ham veri": [len(ham), ham.shape[1], int(ham.isna().sum().sum() + gizli.sum()),
                 int(ham.duplicated().sum()), int(ham["musteri_id"].duplicated().sum()),
                 ham["sehir"].nunique()],
    "Temiz veri": [len(temiz), temiz.shape[1], int(temiz.isna().sum().sum()),
                   int(temiz.duplicated().sum()), int(temiz["musteri_id"].duplicated().sum()),
                   temiz["sehir"].nunique()],
}, index=["Satır", "Sütun", "Eksik hücre (gizli eksikler dahil)", "Birebir mükerrer satır",
          "Tekrarlanan musteri_id", "Farklı şehir yazımı"])
print()
print(rapor.to_string())
print("Temiz veride kalan eksikler yalnızca e_posta sütunundadır (bilinçli olarak doldurulmadı).")
