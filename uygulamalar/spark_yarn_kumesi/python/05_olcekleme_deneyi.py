"""Uygulama 5 — Ölçekleme deneyi: Executor sayısı arttıkça iş ne kadar hızlanır?

Kullanım:  spark-submit python/05_olcekleme_deneyi.py

1BRC sorgusu (CSV'den okuyup istasyonlara göre gruplama) 1, 2, 3, 4 ve 6
executor ile ayrı ayrı çalıştırılır. Her executor 2 çekirdek kullanır.
Her çalıştırmadan sonra Spark'ın REST arayüzünden hangi makinenin kaç görev
yaptığı ve görev başına ne kadar sürdüğü okunur. Böylece hem hızlanmayı
(speedup) hem de yavaş düğümün (straggler) etkisini sayılarla görürüz.
"""

import json
import time
import urllib.request
from collections import defaultdict

from pyspark.sql import SparkSession
from pyspark.sql import functions as F

from ortak import OLCUM_CSV, sonuc_kaydet

EXECUTOR_SAYILARI = [1, 2, 3, 4, 6]
TEKRAR = 2                       # her ayarda 2 ölçüm; JIT ısınması etkisini azaltmak için en kısası alınır
SEMA = "istasyon STRING, sicaklik DOUBLE"


def rest(spark, yol):
    url = f"{spark.sparkContext.uiWebUrl}/api/v1/applications/{spark.sparkContext.applicationId}/{yol}"
    with urllib.request.urlopen(url) as yanit:
        return json.load(yanit)


def makine_adi(host_port):
    ad = {"192.168.1.10": "Gigabyte", "192.168.1.11": "Mini", "192.168.1.12": "Vento"}
    return ad.get(host_port.split(":")[0], host_port)


sonuclar = []
for n in EXECUTOR_SAYILARI:
    spark = (SparkSession.builder.appName(f"05-olcekleme-{n}-executor")
             .config("spark.executor.instances", n)
             # Ölçüme, tüm executor'lar hazır olunca başla
             .config("spark.scheduler.minRegisteredResourcesRatio", "1.0")
             .config("spark.scheduler.maxRegisteredResourcesWaitingTime", "120s")
             .getOrCreate())
    spark.sparkContext.setLogLevel("WARN")

    sureler = []
    for _ in range(TEKRAR):
        # Sorgu her tekrarda yeniden kurulur. Aynı DataFrame ikinci kez çalıştırılsaydı Spark,
        # ilk çalıştırmanın shuffle çıktısını yeniden kullanıp okuma aşamasını atlardı (skipped stage).
        df = spark.read.schema(SEMA).option("sep", ";").csv(OLCUM_CSV)
        sorgu = df.groupBy("istasyon").agg(F.min("sicaklik"), F.avg("sicaklik"), F.max("sicaklik"))
        t0 = time.perf_counter()
        sorgu.collect()
        sureler.append(time.perf_counter() - t0)

    # Executor başına toplam görev sayısı, görev süresi ve okunan veri (REST API)
    makineler = defaultdict(lambda: {"executor": 0, "gorev": 0, "gorev_ms": 0, "okunan_bayt": 0})
    for e in rest(spark, "executors"):
        if e["id"] == "driver":
            continue
        m = makineler[makine_adi(e["hostPort"])]
        m["executor"] += 1
        m["gorev"] += e["totalTasks"]
        m["gorev_ms"] += e["totalDuration"]
        m["okunan_bayt"] += e["totalInputBytes"]
    for m in makineler.values():
        # 1 çekirdeğin saniyede işlediği veri: düğümün "gerçek" hızı
        m["mb_per_sn_cekirdek"] = round(m["okunan_bayt"] / 1e6 / (m["gorev_ms"] / 1000), 1)

    kayit = {"executor": n, "cekirdek": 2 * n, "sure_sn": round(min(sureler), 1),
             "makineler": dict(makineler)}
    sonuclar.append(kayit)
    print(f"{n} executor ({2 * n} çekirdek): {min(sureler):6.1f} sn   "
          + "  ".join(f"{ad}: {m['executor']} ex, {m['mb_per_sn_cekirdek']} MB/sn/çekirdek"
                      for ad, m in sorted(makineler.items())))
    spark.stop()
    time.sleep(5)                # YARN'ın konteynerleri serbest bırakması için kısa bekleme

taban = sonuclar[0]["sure_sn"]
print("\nHızlanma (1 executor'a göre):")
for s in sonuclar:
    s["hizlanma"] = round(taban / s["sure_sn"], 2)
    print(f"  {s['executor']} executor → {s['hizlanma']:.2f} kat  (ideal: {s['executor']} kat)")

sonuc_kaydet("05_olcekleme", sonuclar)
