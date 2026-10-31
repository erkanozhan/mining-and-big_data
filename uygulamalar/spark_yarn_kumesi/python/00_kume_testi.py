"""Uygulama 0 — Küme ayakta mı? Her düğüm işe katılıyor mu?

Kullanım:  spark-submit python/00_kume_testi.py

Kümedeki executor'lara 60 küçük görev gönderir ve görevlerin (ve işledikleri
elemanların) hangi makinede çalıştığını raporlar. Üç makinenin adını da görüyorsanız küme hazırdır.
"""

from collections import Counter

from pyspark.sql import SparkSession


def gorev_bilgisi(_):
    # Bu fonksiyon sürücüde değil, executor'larda (worker makinelerde) çalışır
    import platform
    import socket

    return (socket.gethostname(), platform.python_version())


spark = SparkSession.builder.appName("00-kume-testi").getOrCreate()
sc = spark.sparkContext
print("Spark sürümü     :", spark.version)
print("Uygulama kimliği :", sc.applicationId)
print("Spark arayüzü    :", sc.uiWebUrl)

# 600 eleman 60 bölüme (partition) ayrılır; her bölüm bir görevdir (task) ve 10 eleman işler
ELEMAN, BOLUM = 600, 60
sayac = Counter(sc.parallelize(range(ELEMAN), BOLUM).map(gorev_bilgisi).collect())
print(f"\nElemanların işlendiği makineler (her görev {ELEMAN // BOLUM} eleman işler):")
for (makine, py), adet in sorted(sayac.items()):
    print(f"  {makine:12s} Python {py}  → {adet} eleman ({adet // (ELEMAN // BOLUM)} görev)")

spark.stop()
