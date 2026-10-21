# Uygulama: Spark ve YARN ile Dağıtık Veri Madenciliği

Bu klasör, [**Spark ve YARN ile Dağıtık Veri Madenciliği**](../../spark_ders_notu.md) ders notunun uygulama dosyalarını içerir. Ders notu kavramları, kurulumu ve sonuçların yorumunu anlatır. Buradaki betikler de laboratuvardaki üç makineli Hadoop + Spark kümesinde çalıştırılıp ölçülmüştür.

![Laboratuvar kümesi](../../images/sp-lab-kumesi.svg)

## Klasör yapısı

```text
uygulamalar/spark_yarn_kumesi/
├── yapilandirma/                  ← kümenin gerçek yapılandırma dosyaları
│   ├── hadoop/                    ← core-site, hdfs-site, yarn-site, mapred-site, workers, hadoop-env eki
│   ├── spark/                     ← spark-env.sh, spark-defaults.conf
│   ├── ortam.sh                   ← JAVA_HOME, HADOOP_HOME, SPARK_HOME, PATH
│   └── kume                       ← kümeyi başlatma/durdurma/durum betiği
├── betikler/veri_hazirla.sh       ← verileri indirir/üretir ve HDFS'e koyar
├── python/
│   ├── ortak.py                   ← ortak yardımcılar (HDFS yolları, süre ölçümü, sonuç kaydı)
│   ├── 00_kume_testi.py           ← her düğüm işe katılıyor mu?
│   ├── 01_olcum_verisi_uret.py    ← 100 milyon satırlık 1BRC verisini küme üzerinde üretir
│   ├── 02_1brc_spark.py           ← 1BRC: CSV, bellek (cache) ve Parquet karşılaştırması
│   ├── 03_kelime_sayma.py         ← Hadoop MapReduce ile Spark RDD/DataFrame yarışı
│   ├── 04_mllib_hiperparametre.py ← MLlib Rastgele Orman + çapraz doğrulamalı arama
│   ├── 04b_tek_makine_sklearn.py  ← aynı aramanın tek makinede scikit-learn ile yapılması
│   ├── 05_olcekleme_deneyi.py     ← 1-6 executor ile hızlanma ve yavaş düğüm ölçümü
│   └── 06_grafikler.py            ← sonuclar.json → SVG grafikler
└── ciktilar/                      ← laboratuvarda alınan çıktılar, sonuclar.json ve grafikler
```

## Çalıştırma sırası

Küme açık olmalıdır (`kume durum`; kapalıysa `kume baslat`). Komutlar herhangi bir lab makinesinde, bu klasörün içinden çalıştırılır:

```bash
source ~/bigdata/ortam.sh
spark-submit python/00_kume_testi.py              # 1 dk
bash betikler/veri_hazirla.sh                     # 3-5 dk (01 numaralı betiği de çalıştırır)
spark-submit python/02_1brc_spark.py              # 2-3 dk
spark-submit python/03_kelime_sayma.py            # 2 dk
spark-submit python/04_mllib_hiperparametre.py 1  # 6-7 dk
spark-submit python/04_mllib_hiperparametre.py 4  # 4-5 dk
spark-submit python/05_olcekleme_deneyi.py        # 6-8 dk
hdfs dfs -get /veri/covtype/covtype.data /tmp/ && python python/04b_tek_makine_sklearn.py /tmp/covtype.data
python python/06_grafikler.py                     # matplotlib gerekir
```

Her betik ölçtüğü süreleri `ciktilar/sonuclar.json` dosyasına yazar. Laboratuvarda alınan çıktılar `ciktilar/*_cikti.txt` dosyalarındadır.

Kendi kümenizi kurarken `yapilandirma/` klasöründeki dosyalarda IP adreslerini, kullanıcı adını (`/home/hduser`) ve düğüm başına bellek/çekirdek değerlerini kendi makinelerinize göre değiştirmeniz yeterlidir. Adımlar ders notunun **5. Kurulum** bölümünde açıklanmıştır.
