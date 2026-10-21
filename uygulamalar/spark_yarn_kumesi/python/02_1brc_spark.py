"""Uygulama 2 — 1BRC'yi Spark ile çözmek: CSV, bellekte önbellek (cache) ve Parquet.

Kullanım:  spark-submit python/02_1brc_spark.py

Aynı soru üç farklı biçimde sorulur: "Her istasyonun en düşük, ortalama ve
en yüksek sıcaklığı nedir?"
  1) Düz metin (CSV) dosyadan okuyarak,
  2) Veriyi bir kez okuyup executor belleklerinde tutarak (cache),
  3) Sütunlu ve sıkıştırılmış Parquet biçiminden okuyarak.
Ayrıca Spark'ın sorguyu nasıl planladığı (explain) yazdırılır.
"""

from pyspark.sql import SparkSession
from pyspark.sql import functions as F

from ortak import OLCUM_CSV, OLCUM_PARQUET, Kronometre, hdfs_boyut, hdfs_var_mi, sonuc_kaydet

SEMA = "istasyon STRING, sicaklik DOUBLE"   # şemayı vermek, Spark'ın veriyi baştan taramasını önler


def istasyon_ozeti(df):
    return (
        df.groupBy("istasyon")
        .agg(
            F.min("sicaklik").alias("en_dusuk"),
            F.round(F.avg("sicaklik"), 1).alias("ortalama"),
            F.max("sicaklik").alias("en_yuksek"),
            F.count("*").alias("olcum_sayisi"),
        )
        .orderBy("istasyon")
    )


spark = SparkSession.builder.appName("02-1brc-spark").getOrCreate()
print("Spark arayüzü:", spark.sparkContext.uiWebUrl)

csv = spark.read.schema(SEMA).option("sep", ";").csv(OLCUM_CSV)
print(f"CSV bölüm (partition) sayısı: {csv.rdd.getNumPartitions()}")

print("\n=== Spark'ın fiziksel planı ===")
istasyon_ozeti(csv).explain()

# 1) Düz metin
with Kronometre("1) CSV'den oku + grupla") as k_csv:
    sonuc = istasyon_ozeti(csv).collect()

print("\nİlk 10 istasyon:")
for r in sonuc[:10]:
    print(f"  {r.istasyon:15s} min={r.en_dusuk:6.1f}  ort={r.ortalama:5.1f}  "
          f"max={r.en_yuksek:5.1f}  n={r.olcum_sayisi:,}")

# 2) Bellekte tutma: ilk eylem (count) veriyi okuyup executor belleklerine yerleştirir
onbellek = csv.cache()
with Kronometre("2a) Veriyi belleğe al (cache + count)") as k_yukle:
    satir = onbellek.count()
with Kronometre("2b) Bellekteki veriden grupla") as k_bellek:
    istasyon_ozeti(onbellek).collect()
onbellek.unpersist()

# 3) Parquet: bir kez dönüştür, sonra hep onu oku
if not hdfs_var_mi(spark, OLCUM_PARQUET):
    with Kronometre("CSV → Parquet dönüşümü (bir kez)"):
        csv.write.mode("overwrite").parquet(OLCUM_PARQUET)
parquet = spark.read.parquet(OLCUM_PARQUET)
with Kronometre("3) Parquet'ten oku + grupla") as k_parquet:
    istasyon_ozeti(parquet).collect()

b_csv, b_parquet = hdfs_boyut(spark, OLCUM_CSV), hdfs_boyut(spark, OLCUM_PARQUET)
print(f"\nSatır sayısı : {satir:,}")
print(f"CSV boyutu   : {b_csv / 1e9:.2f} GB")
print(f"Parquet boyut: {b_parquet / 1e9:.2f} GB  ({b_csv / b_parquet:.1f} kat küçük)")

sonuc_kaydet("02_1brc", {
    "satir": satir,
    "csv_bayt": b_csv, "parquet_bayt": b_parquet,
    "csv_sn": round(k_csv.sn, 1),
    "cache_yukleme_sn": round(k_yukle.sn, 1),
    "cache_sorgu_sn": round(k_bellek.sn, 1),
    "parquet_sn": round(k_parquet.sn, 1),
})
spark.stop()
