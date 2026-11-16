# 21. Uygulama: Apache Spark Kurulumu ve PySpark

MapReduce her işlemde veriyi diske yazar ve diskten okur; disk ise bilgisayarın en yavaş bileşenlerinden biridir. Spark'ın yaklaşımı, veriyi mecbur kalmadıkça diske indirmemek ve ara sonuçları bellekte tutmaktır. Bir benzetmeyle: Her durakta yükü depoya indirip yeniden yükleyen bir kamyon yerine, yükü aracın üzerinde tutarak yola devam etmek. Bu bölümde Spark kurulacak ve Python arayüzü **PySpark** ile ilk işler çalıştırılacaktır.

## 21.1 Hazırlık ve İndirme

Spark'ın çalışması için Java (Bölüm 17.2'de kuruldu) ve Python gerekir. Ubuntu Python 3 ile birlikte gelir (`python3 --version` ile kontrol edilebilir). HDFS'teki veriler okunacağı için Hadoop servisleri de çalışıyor olmalıdır:

```bash
start-dfs.sh
start-yarn.sh
```

Spark, Hadoop 3 için önceden derlenmiş paket olarak indirilir:

```bash
cd ~/bigdata/indirilen
wget https://archive.apache.org/dist/spark/spark-4.1.3/spark-4.1.3-bin-hadoop3.tgz
cd ~/bigdata
tar xzf indirilen/spark-4.1.3-bin-hadoop3.tgz
ln -s spark-4.1.3-bin-hadoop3 spark
```

## 21.2 Ortam Değişkenleri

`SPARK_HOME`, `PYSPARK_PYTHON` ve Spark'ın `bin` klasörü, Bölüm 17.3'te `ortam.sh` dosyasına zaten eklenmiştir. `PYSPARK_PYTHON=python3` satırı, Spark'ın işçi süreçlerinde Python 3 kullanmasını sağlar; driver ile executor'ların Python sürümleri farklı olursa PySpark hata verir. Yeni bir terminalde `which pyspark` komutu `/home/hduser/bigdata/spark/bin/pyspark` yolunu göstermelidir.

## 21.3 Spark'ı Hadoop'a Bağlamak

Spark, HDFS'in ve YARN'ın nerede olduğunu `HADOOP_CONF_DIR` değişkeninin gösterdiği klasördeki yapılandırma dosyalarından öğrenir. Bu değişken `ortam.sh` dosyasında tanımlıdır. Spark'ın kendi başlatma betikleri de okusun diye aynı satır Spark'ın yapılandırma dosyasına eklenir:

```bash
cd $SPARK_HOME/conf
cp spark-env.sh.template spark-env.sh
echo 'export HADOOP_CONF_DIR=$HOME/bigdata/hadoop/etc/hadoop' >> spark-env.sh
```

Böylece Spark, `hdfs:///...` biçimindeki yolları `core-site.xml`'deki NameNode adresine göre çözer.

## 21.4 PySpark Kabuğu: İlk RDD

```bash
pyspark
```

Bir süre sonra ekranda Spark'ın logosu ve `>>>` istemi görülür. Kabuk, Spark'a bağlanmak için hazır bir `sc` (SparkContext) ve `spark` (SparkSession) nesnesi sunar. Spark'ın temel veri yapısı olan **RDD (Resilient Distributed Dataset, dayanıklı dağıtık veri kümesi)**, kümedeki makinelere bölünmüş, değiştirilemez bir kayıt koleksiyonudur. Bir parçası kaybolursa, o parçanın nasıl üretildiğinin kaydından (soy ağacı, lineage) yeniden hesaplanır (ek not, Bölüm 2.1).

```python
# 1'den 5'e kadar sayılardan bir RDD oluştur
rakamlar = sc.parallelize([1, 2, 3, 4, 5])

# Dönüşüm (transformation): her sayının karesi
kareler = rakamlar.map(lambda x: x * x)

# Eylem (action): sonucu getir
kareler.collect()
```

Çıktı `[1, 4, 9, 16, 25]` olur. `map` satırı çalıştırıldığında hiçbir hesaplama yapılmaz; Spark yalnızca planı kaydeder. Hesaplama, sonuç isteyen `collect()` eylemi geldiğinde başlar. Bu davranışa **tembel değerlendirme (lazy evaluation)** denir. Kabuktan çıkmak için `exit()` yazılır veya `Ctrl+D` tuşlarına basılır.

## 21.5 Spark ile WordCount

Bölüm 19'da hazır jar dosyasıyla çalıştırılan kelime sayma işi, PySpark kabuğunda birkaç satırla ve aynı HDFS dosyası üzerinde yapılabilir:

```python
# 1. HDFS'teki dosyayı oku
satirlar = sc.textFile("hdfs:///user/hduser/giris_verisi/deneme.txt")

# 2. Say: flatMap satırları kelimelere böler, map her kelimeye (kelime, 1) değerini verir,
#    reduceByKey aynı kelimenin 1'lerini toplar
sayimlar = (satirlar.flatMap(lambda satir: satir.split())
                    .map(lambda kelime: (kelime, 1))
                    .reduceByKey(lambda a, b: a + b))

# 3. Sonuçları sıralayıp yazdır
for kelime, adet in sorted(sayimlar.collect()):
    print(f"{kelime}: {adet}")
```

`split()` metni Hadoop'un WordCount programı gibi boşluk karakterlerinden böldüğü için sonuç, Bölüm 19.5'teki 12 kelime ve sayılarla aynıdır (örneğin `Hadoop: 3`, `is: 3`). Kod; derleme, jar dosyası ve ayrı bir çıktı klasörü gerektirmez. `flatMap` ve `map` adımları MapReduce'un map aşamasına, `reduceByKey` ise birleştirici (combiner) ile reduce aşamasına karşılık gelir.

## 21.6 Genel Değerlendirme

Bu kısmın sonunda tek bir bilgisayarda (veya sanal makinede) şu katmanlar çalışır durumdadır:

1. **Linux (Ubuntu):** İşletim sistemi.
2. **HDFS:** Dağıtık depolama katmanı.
3. **YARN:** Kaynak yöneticisi.
4. **MapReduce, Hive ve Pig:** Diskten diske çalışan toplu (batch) işleme ve sorgulama araçları.
5. **Spark:** Ara sonuçları bellekte tutan toplu işleme motoru; Structured Streaming modülüyle akış işleme de yapabilir (Bölüm 12.6).

Bu yapı, büyük ölçekli veri platformlarının küçük bir modelidir.

Araçlar hızla değişir; ama işi parçalara bölmek, hesaplamayı verinin bulunduğu yere götürmek ve ara sonuçları birleştirmek fikri (MapReduce mantığı) kalıcıdır. Bu fikri kavrayan biri, hangi araç gelirse gelsin onu hızla öğrenebilir. Kurulum sırasında karşılaşılan hata mesajları da öğrenmenin bir parçasıdır: Günlük dosyalarını dikkatle okumak, dağıtık sistemlerde en değerli alışkanlıktır. Aynı yapının üç makineli gerçek bir kümede nasıl kurulduğu ve ölçüldüğü ek notta anlatılmıştır: [Spark ve YARN ile Dağıtık Veri Madenciliği](../spark_ders_notu.md).

---

[← 20. Uygulama: Hive, Pig ve Mahout](20-hive-pig-ve-mahout.md) · [İçindekiler](../ders_notu.md) · [Kısım II Kaynakları →](kisim-2-kaynaklari.md)
