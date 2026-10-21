"""Uygulama 0 — Küme ayakta mı? Her düğüm işe katılıyor mu?

Kullanım:  spark-submit python/00_kume_testi.py

Kümedeki her executor'a küçük görevler gönderir ve görevlerin hangi makinede
çalıştığını raporlar. Üç makinenin adını da görüyorsanız küme hazırdır.
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

# 600 küçük görev, 60 bölüme (partition) dağıtılır
sayac = Counter(sc.parallelize(range(600), 60).map(gorev_bilgisi).collect())
print("\nGörevlerin çalıştığı makineler:")
for (makine, py), adet in sorted(sayac.items()):
    print(f"  {makine:12s} Python {py}  → {adet} görev")

spark.stop()
