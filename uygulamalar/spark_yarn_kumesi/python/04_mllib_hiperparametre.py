"""Uygulama 4 — MLlib ile dağıtık model eğitimi ve hiperparametre araması.

Kullanım:  spark-submit python/04_mllib_hiperparametre.py [paralellik]
           paralellik: aynı anda eğitilecek model sayısı (varsayılan 1)

Veri: UCI Covertype — 581.012 orman alanı, 54 nitelik, 7 orman örtüsü sınıfı.
Rastgele Orman (Random Forest) için 2 × 2 = 4 hiperparametre birleşimi,
3 katlı çapraz doğrulama ile denenir: toplam 12 model + en iyisiyle 1 son model.

İki tür paralellik vardır:
  * Her modelin İÇİNDE: ağaçlar ve veri bölümleri executor'lara dağıtılır.
  * Modeller ARASINDA: `paralellik` > 1 ise birden çok hiperparametre birleşimi
    aynı anda eğitilir (CrossValidator(parallelism=...)).
"""

import sys

from pyspark.ml import Pipeline
from pyspark.ml.classification import RandomForestClassifier
from pyspark.ml.evaluation import MulticlassClassificationEvaluator
from pyspark.ml.feature import VectorAssembler
from pyspark.ml.tuning import CrossValidator, ParamGridBuilder
from pyspark.sql import SparkSession
from pyspark.sql import functions as F

from ortak import COVTYPE, Kronometre, sonuc_kaydet

PARALELLIK = int(sys.argv[1]) if len(sys.argv) > 1 else 1

SAYISAL = ["rakim", "baki", "egim", "su_yatay_uzaklik", "su_dikey_uzaklik", "yol_uzaklik",
           "golge_09", "golge_12", "golge_15", "yangin_noktasi_uzaklik"]
NITELIKLER = SAYISAL + [f"koruma_alani_{i}" for i in range(1, 5)] + [f"toprak_{i}" for i in range(1, 41)]

spark = SparkSession.builder.appName(f"04-mllib-hiperparametre-p{PARALELLIK}").getOrCreate()
print("Spark arayüzü:", spark.sparkContext.uiWebUrl)

sema = ", ".join(f"{ad} INT" for ad in NITELIKLER + ["ortu_turu"])
veri = (spark.read.schema(sema).csv(COVTYPE)
        .withColumn("etiket", (F.col("ortu_turu") - 1).cast("double")))    # sınıflar 0..6 olmalı

egitim, test = veri.randomSplit([0.8, 0.2], seed=42)
egitim = egitim.repartition(12).cache()    # 12 bölüm: kümedeki çekirdeklere yayılır, bellekte kalır
print(f"Eğitim: {egitim.count():,} satır   Test: {test.count():,} satır")

birlestir = VectorAssembler(inputCols=NITELIKLER, outputCol="ozellikler")
orman = RandomForestClassifier(labelCol="etiket", featuresCol="ozellikler", seed=42, maxBins=64)
hat = Pipeline(stages=[birlestir, orman])

izgara = (ParamGridBuilder()
          .addGrid(orman.numTrees, [20, 40])
          .addGrid(orman.maxDepth, [10, 15])
          .build())
dogruluk = MulticlassClassificationEvaluator(labelCol="etiket", metricName="accuracy")

cv = CrossValidator(estimator=hat, estimatorParamMaps=izgara, evaluator=dogruluk,
                    numFolds=3, parallelism=PARALELLIK, seed=42)

with Kronometre(f"Çapraz doğrulamalı arama (paralellik={PARALELLIK})") as k:
    model = cv.fit(egitim)

print("\nHiperparametre birleşimleri (3 katın ortalama doğruluğu):")
satirlar = []
for parametreler, ort in zip(izgara, model.avgMetrics):
    p = {k.name: v for k, v in parametreler.items()}
    satirlar.append({**p, "dogruluk": round(ort, 4)})
    print(f"  ağaç={p['numTrees']:>3}  derinlik={p['maxDepth']:>3}  →  {ort:.4f}")

en_iyi = model.bestModel.stages[-1]
test_dogruluk = dogruluk.evaluate(model.transform(test))
print(f"\nEn iyi model: ağaç={en_iyi.getNumTrees}, derinlik={en_iyi.getOrDefault('maxDepth')}")
print(f"Test doğruluğu: {test_dogruluk:.4f}")

onem = sorted(zip(NITELIKLER, en_iyi.featureImportances.toArray()), key=lambda t: -t[1])[:8]
print("\nEn önemli 8 nitelik:")
for ad, deger in onem:
    print(f"  {ad:25s} {deger:.3f}")

sonuc_kaydet(f"04_mllib_p{PARALELLIK}", {
    "paralellik": PARALELLIK,
    "sure_sn": round(k.sn, 1),
    "izgara": satirlar,
    "test_dogruluk": round(test_dogruluk, 4),
    "onemli_nitelikler": [[ad, round(d, 3)] for ad, d in onem],
})
spark.stop()
