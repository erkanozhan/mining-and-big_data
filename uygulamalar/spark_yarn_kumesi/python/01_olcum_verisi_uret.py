"""Uygulama 1 — 1BRC tarzı sıcaklık ölçümü verisini küme üzerinde üretip HDFS'e yazar.

Kullanım:  spark-submit python/01_olcum_verisi_uret.py [satır_sayısı]
           (varsayılan 100 milyon satır, yaklaşık 1.28 GB düz metin)

Ders notundaki 12.7 vakasında 10 milyon satırlık dosyayı tek bilgisayarda
Python ile üretmiştik. Burada üretimin kendisi de dağıtıktır: Her executor
kendi bölümündeki (partition) satırları üretir ve HDFS'e kendi parça
dosyasını (part-0000x) yazar. Hiçbir makine verinin tamamını görmez.
"""

import sys

from pyspark.sql import SparkSession
from pyspark.sql import functions as F

from ortak import OLCUM_CSV, Kronometre, hdfs_boyut, sonuc_kaydet

# 81 il ve yaklaşık yıllık ortalama sıcaklıkları (°C, öğretim amaçlı yuvarlanmış)
ISTASYONLAR = [
    ("Adana", 19.1), ("Adıyaman", 17.0), ("Afyonkarahisar", 11.3), ("Ağrı", 6.2),
    ("Amasya", 13.6), ("Ankara", 11.9), ("Antalya", 18.7), ("Artvin", 12.3),
    ("Aydın", 17.6), ("Balıkesir", 14.6), ("Bilecik", 12.4), ("Bingöl", 12.1),
    ("Bitlis", 9.4), ("Bolu", 10.6), ("Burdur", 13.2), ("Bursa", 14.6),
    ("Çanakkale", 15.0), ("Çankırı", 11.2), ("Çorum", 10.8), ("Denizli", 16.0),
    ("Diyarbakır", 15.8), ("Edirne", 13.7), ("Elazığ", 13.0), ("Erzincan", 10.9),
    ("Erzurum", 5.7), ("Eskişehir", 11.0), ("Gaziantep", 15.4), ("Giresun", 14.6),
    ("Gümüşhane", 9.3), ("Hakkari", 9.9), ("Hatay", 18.2), ("Isparta", 12.1),
    ("Mersin", 19.0), ("İstanbul", 14.6), ("İzmir", 17.9), ("Kars", 4.8),
    ("Kastamonu", 9.8), ("Kayseri", 10.6), ("Kırklareli", 13.2), ("Kırşehir", 11.5),
    ("Kocaeli", 14.8), ("Konya", 11.6), ("Kütahya", 10.8), ("Malatya", 13.9),
    ("Manisa", 16.9), ("Kahramanmaraş", 16.7), ("Mardin", 16.1), ("Muğla", 15.1),
    ("Muş", 9.8), ("Nevşehir", 10.8), ("Niğde", 11.2), ("Ordu", 14.4),
    ("Rize", 14.3), ("Sakarya", 14.7), ("Samsun", 14.5), ("Siirt", 16.0),
    ("Sinop", 14.2), ("Sivas", 8.9), ("Tekirdağ", 14.0), ("Tokat", 12.4),
    ("Trabzon", 14.8), ("Tunceli", 12.6), ("Şanlıurfa", 18.5), ("Uşak", 12.6),
    ("Van", 9.3), ("Yozgat", 9.1), ("Zonguldak", 13.6), ("Aksaray", 12.2),
    ("Bayburt", 6.9), ("Karaman", 11.9), ("Kırıkkale", 12.5), ("Batman", 16.4),
    ("Şırnak", 16.4), ("Bartın", 12.9), ("Ardahan", 3.8), ("Iğdır", 12.1),
    ("Yalova", 14.9), ("Karabük", 13.0), ("Kilis", 17.2), ("Osmaniye", 18.4),
    ("Düzce", 13.4),
]

N = int(sys.argv[1]) if len(sys.argv) > 1 else 100_000_000
BOLUM = max(8, N // 2_500_000)  # her bölüm ~2.5 milyon satır (~32 MB)

spark = SparkSession.builder.appName("01-olcum-verisi-uret").getOrCreate()
print("Spark arayüzü:", spark.sparkContext.uiWebUrl)

istasyon = spark.createDataFrame(
    [(i, ad, ort) for i, (ad, ort) in enumerate(ISTASYONLAR)], "no INT, istasyon STRING, ort DOUBLE"
)

olcumler = (
    spark.range(N, numPartitions=BOLUM)                                 # 0..N-1, BOLUM parçaya bölünmüş
    .withColumn("no", (F.rand(42) * len(ISTASYONLAR)).cast("int"))      # rastgele bir istasyon seç
    .join(F.broadcast(istasyon), "no")                                  # küçük tablo her executor'a kopyalanır
    .select("istasyon", F.round(F.col("ort") + F.randn(7) * 8, 1).alias("sicaklik"))
)

with Kronometre(f"{N:,} satır üret + HDFS'e yaz") as k:
    olcumler.write.mode("overwrite").option("sep", ";").csv(OLCUM_CSV)

boyut = hdfs_boyut(spark, OLCUM_CSV)
print(f"HDFS'e yazıldı: {OLCUM_CSV}  ({boyut / 1e9:.2f} GB, {BOLUM} parça dosya)")
print("Örnek satırlar:")
for satir in spark.read.text(OLCUM_CSV).limit(5).collect():
    print("  ", satir.value)

sonuc_kaydet("01_veri_uretimi", {"satir": N, "bolum": BOLUM, "bayt": boyut, "sure_sn": round(k.sn, 1)})
spark.stop()
