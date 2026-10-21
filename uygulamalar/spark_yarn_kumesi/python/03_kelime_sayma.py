"""Uygulama 3 — Kelime sayma: Hadoop MapReduce ile Spark'ı aynı veride yarıştırmak.

Kullanım:  spark-submit python/03_kelime_sayma.py

Aynı iş (HDFS'teki kitaplarda her kelimenin kaç kez geçtiği) üç yolla yapılır:
  1) Hadoop MapReduce: Hadoop'la gelen hazır WordCount programı (Java),
  2) Spark RDD API'si: map → reduceByKey; MapReduce'un bire bir karşılığı (Python),
  3) Spark DataFrame API'si: aynı iş SQL benzeri bildirimsel dille.
"""

import os
import re
import subprocess

from pyspark.sql import SparkSession
from pyspark.sql import functions as F

from ortak import KITAPLAR, Kronometre, hdfs_boyut, sonuc_kaydet

MR_CIKTI = "hdfs:///cikti/kelime_sayma_mapreduce"
MR_JAR = (f"{os.environ['HADOOP_HOME']}/share/hadoop/mapreduce/"
          "hadoop-mapreduce-examples-3.5.0.jar")

# 1) MapReduce. Spark oturumu açılmadan önce çalıştırılır ki YARN kaynaklarının tamamını kullanabilsin.
subprocess.run(["hdfs", "dfs", "-rm", "-r", "-f", "-skipTrash", MR_CIKTI], check=True,
               stdout=subprocess.DEVNULL)
with Kronometre("1) Hadoop MapReduce WordCount") as k_mr:
    subprocess.run(["hadoop", "jar", MR_JAR, "wordcount", KITAPLAR, MR_CIKTI], check=True,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

spark = SparkSession.builder.appName("03-kelime-sayma").getOrCreate()
sc = spark.sparkContext
print("Spark arayüzü:", sc.uiWebUrl)
boyut = hdfs_boyut(spark, KITAPLAR)
print(f"Girdi: {KITAPLAR} ({boyut / 1e6:.0f} MB)")

KELIME = re.compile(r"[^\W\d_]+")   # yalnızca harflerden oluşan diziler


# 2) RDD: map ve reduce adımlarını kendimiz yazarız
with Kronometre("2) Spark RDD (Python)") as k_rdd:
    sayimlar = (
        sc.textFile(KITAPLAR)
        .flatMap(lambda satir: KELIME.findall(satir.lower()))    # map: satır → kelimeler
        .map(lambda kelime: (kelime, 1))                          # map: kelime → (kelime, 1)
        .reduceByKey(lambda a, b: a + b)                          # reduce: aynı kelimeleri topla
    )
    en_sik_rdd = sayimlar.takeOrdered(15, key=lambda kv: -kv[1])

# 3) DataFrame: ne istediğimizi söyleriz, nasıl yapılacağını Spark planlar
with Kronometre("3) Spark DataFrame") as k_df:
    en_sik_df = (
        spark.read.text(KITAPLAR)
        .select(F.explode(F.split(F.lower("value"), r"[^\p{L}]+")).alias("kelime"))
        .where(F.col("kelime") != "")
        .groupBy("kelime").count()
        .orderBy(F.desc("count"))
        .limit(15)
        .collect()
    )

print("\nEn sık 15 kelime (RDD ↔ DataFrame):")
for (k1, n1), r in zip(en_sik_rdd, en_sik_df):
    print(f"  {k1:10s} {n1:>10,}    {r.kelime:10s} {r['count']:>10,}")

sonuc_kaydet("03_kelime_sayma", {
    "girdi_bayt": boyut,
    "mapreduce_sn": round(k_mr.sn, 1),
    "spark_rdd_sn": round(k_rdd.sn, 1),
    "spark_dataframe_sn": round(k_df.sn, 1),
})
spark.stop()
