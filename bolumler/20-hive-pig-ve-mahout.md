# 20. Uygulama: Hive, Pig ve Mahout

Bu bölümdeki araçlar Hadoop'tan ayrı olarak indirilip kurulur. Her biri belirli Hadoop ve Java sürümleriyle uyumludur.

> **Sürüm uyumluluğu:** Bir aracı indirmeden önce, projenin sürüm notlarında hangi Hadoop ve Java sürümlerini desteklediği kontrol edilmelidir. Aşağıdaki komutlarda sürüm numarası `HIVE_SURUM` ve `PIG_SURUM` değişkenleriyle verilmiştir ve bu notun yazıldığı tarihteki en son sürümler (Hive 4.2.1, Pig 0.18.0) kullanılmıştır. Bu sürümlerin kurulu Hadoop 3.5 ve Java 17 ile birlikte sınanmadığı unutulmamalıdır; bir uyumsuzluk görülürse değişkene projenin sürüm notlarında uyumlu olduğu belirtilen sürüm yazılmalıdır. Uyumlu bir sürüm bulunamazsa uygulamalar, aynı işi yapan Spark SQL ve PySpark ile yapılabilir (Bölüm 21).

## 20.1 Apache Hive ile Sınav Analizi

**Kurulum.** Hive indirilir, kısa yolu ve ortam değişkenleri tanımlanır, HDFS'te Hive'ın kullanacağı klasörler açılır ve gömülü (Derby) metastore'un şeması `schematool` ile oluşturulur:

```bash
HIVE_SURUM=4.2.1      # yazım tarihindeki en son sürüm
cd ~/bigdata
wget https://archive.apache.org/dist/hive/hive-$HIVE_SURUM/apache-hive-$HIVE_SURUM-bin.tar.gz
tar xzf apache-hive-$HIVE_SURUM-bin.tar.gz
ln -s apache-hive-$HIVE_SURUM-bin hive
echo 'export HIVE_HOME=$HOME/bigdata/hive; export PATH=$HIVE_HOME/bin:$PATH' >> ~/bigdata/ortam.sh
source ~/bigdata/ortam.sh

hdfs dfs -mkdir -p /tmp /user/hive/warehouse     # geçici klasör ve tabloların duracağı ambar klasörü
hdfs dfs -chmod g+w /tmp /user/hive/warehouse
cd ~ && schematool -dbType derby -initSchema     # metastore şemasını oluştur (bir kez)
```

Gömülü Derby veritabanı, `schematool` komutunun çalıştırıldığı klasörde `metastore_db` adıyla oluşturulur. Hive her zaman aynı klasörden (burada ev dizini) başlatılmalıdır; aksi hâlde yeni ve boş bir metastore arar.

**Adım 1 — Veriyi hazırlama.** Yerel dosya sisteminde (`nano notlar.txt` ile) `notlar.txt` dosyası oluşturulur. Biçim: öğrenci numarası, ders, not:

```text
101,Matematik,80
102,Matematik,90
101,Fizik,45
103,Matematik,60
102,Fizik,70
```

**Adım 2 — Hive'a bağlanma.** Eski Hive sürümlerinde terminale `hive` yazmak yeterlidir. Hive 4 ve sonrasında eski komut satırı istemcisinin yerini **Beeline** almıştır; gömülü modda `beeline -u jdbc:hive2://` komutuyla bağlanılır.

**Adım 3 — Tabloyu oluşturma.** Tıpkı ilişkisel bir veritabanında olduğu gibi:

```sql
CREATE TABLE sinav_sonuclari (
    ogrenci_id INT,
    ders STRING,
    puan INT
)
ROW FORMAT DELIMITED
FIELDS TERMINATED BY ',';
```

Bu tanım Hive'a, virgülle ayrılmış bir metin dosyası okuyacağını ve sütunların neler olduğunu söyler.

**Adım 4 — Veriyi yükleme.** `LOCAL` sözcüğü dosyanın yerel dosya sisteminden okunacağını belirtir; Hive dosyayı tablonun HDFS'teki ambar klasörüne kendisi kopyalar. Bu yüzden dosyanın önceden HDFS'e yüklenmesi gerekmez:

```sql
LOAD DATA LOCAL INPATH '/home/hduser/notlar.txt' INTO TABLE sinav_sonuclari;
```

**Adım 5 — Sorgulama.**

```sql
SELECT ders, AVG(puan) FROM sinav_sonuclari GROUP BY ders;
```

Hive bu sorguyu bir veya birkaç dağıtık işe dönüştürür, YARN'a gönderir ve sonucu getirir. Beklenen sonuç şudur (görünüm istemciye göre değişebilir):

```text
Fizik       57.5
Matematik   76.66666666666667
```

Fizik'te iki not vardır: (45 + 70) / 2 = 57.5. Matematik'te üç not vardır: (80 + 90 + 60) / 3 ≈ 76.67. Java kodu yazılmadan, yalnızca SQL ile dağıtık bir hesap yapılmıştır.

## 20.2 Apache Pig ile Filtreleme

**Kurulum.** Pig de aynı yolla kurulur:

```bash
PIG_SURUM=0.18.0      # yazım tarihindeki en son sürüm
cd ~/bigdata
wget https://archive.apache.org/dist/pig/pig-$PIG_SURUM/pig-$PIG_SURUM.tar.gz
tar xzf pig-$PIG_SURUM.tar.gz
ln -s pig-$PIG_SURUM pig
echo 'export PIG_HOME=$HOME/bigdata/pig; export PATH=$PIG_HOME/bin:$PATH' >> ~/bigdata/ortam.sh
source ~/bigdata/ortam.sh
```

Pig iki kipte çalışır. **Yerel kipte (`pig -x local`)** dosyalar yerel dosya sisteminden okunur ve iş tek makinede yürütülür; küçük denemeler için idealdir. **MapReduce kipinde (`pig`)** göreli dosya yolları HDFS'teki kullanıcı klasörüne (`/user/hduser`) göre çözülür ve iş kümede çalışır.

**Amaç:** Bir önceki bölümdeki not dosyasından, puanı 50'den yüksek olan kayıtları adım adım süzmek. `notlar.txt` ev dizininde durduğu için Pig yerel kipte, ev dizininden başlatılır:

```bash
cd ~
pig -x local           # grunt> istemi görülür
```

MapReduce kipinde çalışmak için önce dosyanın HDFS'e yüklenmesi gerekir: `hdfs dfs -put notlar.txt /user/hduser/` ve ardından `pig`. Aynı betik iki kipte de çalışır; değişen yalnızca `'notlar.txt'` yolunun hangi dosya sisteminde arandığıdır.

```pig
-- 1. Veriyi yükle
notlar = LOAD 'notlar.txt' USING PigStorage(',') AS (id:int, ders:chararray, puan:int);

-- 2. Süz: puanı 50'den büyük olanlar
gecenler = FILTER notlar BY puan > 50;

-- 3. Sonucu ekrana yaz (hesaplama bu satırda başlar)
DUMP gecenler;
```

Pig de Spark gibi **tembel değerlendirme (lazy evaluation)** kullanır: İlk iki satır yalnızca bir plan oluşturur; hesaplama, sonuç isteyen `DUMP` (veya `STORE`) komutu geldiğinde başlar. Beklenen çıktı:

```text
(101,Matematik,80)
(102,Matematik,90)
(103,Matematik,60)
(102,Fizik,70)
```

45 puanlı kayıt süzülmüştür. Pig, özellikle veri temizleme ve dönüştürme (ETL) işlerinde birkaç satırlık betiklerle uzun MapReduce zincirlerinin yerini tutar.

## 20.3 Apache Mahout ile Öneri Sistemi (Gösterim)

> **Not:** Bu bölüm bir **gösterimdir**. Aşağıdaki MapReduce tabanlı komut yalnızca Mahout'un eski (0.x) sürümlerinde bulunur ve bu sürümler, notta kullanılan Hadoop 3.5 ve Java 17 ile birlikte çalışmak üzere tasarlanmamıştır. Aynı tür bir öneri sistemi bugün Spark MLlib'in `ALS` (Alternating Least Squares) algoritmasıyla kurulur.

Mahout'un en bilinen kullanım alanı **öneri sistemleridir (recommendation engines)**: "Bu filmi izleyenler şunları da izledi" veya "Bu ürünü alanlar şunları da aldı" önerileri bu tür sistemlerin ürünüdür. Mahout'un öneri komutları, her satırı `kullanıcı,öğe,puan` biçiminde olan bir girdi bekler (`film_puanlari.txt`):

```text
1,101,5.0
1,102,3.0
2,101,5.0
2,103,4.5
```

| Satır | Anlamı |
|---|---|
| `1,101,5.0` | 1 numaralı kullanıcı 101 numaralı filme 5 puan verdi |
| `1,102,3.0` | 1 numaralı kullanıcı 102 numaralı filme 3 puan verdi |
| `2,101,5.0` | 2 numaralı kullanıcı 101 numaralı filme 5 puan verdi |
| `2,103,4.5` | 2 numaralı kullanıcı 103 numaralı filme 4.5 puan verdi |

Dosya HDFS'e yüklendikten sonra öğe tabanlı öneri işi şöyle başlatılır:

```bash
hdfs dfs -put film_puanlari.txt /user/hduser/
mahout recommenditembased \
    --input /user/hduser/film_puanlari.txt \
    --output /user/hduser/oneriler \
    --similarityClassname SIMILARITY_COOCCURRENCE
```

`recommenditembased`, **öğe tabanlı (item-based)** bir öneri algoritmasıdır; kullanıcıları değil, **öğeleri** birbiriyle karşılaştırır:

1. **Öğe benzerliklerini hesaplar:** Aynı kullanıcılar tarafından birlikte puanlanan öğeler birbirine benzer sayılır. Örnekte 2 numaralı kullanıcı hem 101'i hem 103'ü puanlamıştır; bu yüzden 101 ile 103 numaralı filmler arasında bir benzerlik oluşur. Bu küçük örnekte benzerlik ölçüsü olarak birlikte görülme sayısı (`SIMILARITY_COOCCURRENCE`) seçilmiştir; Pearson korelasyonu gibi ölçüler, iki öğeyi birlikte puanlayan en az iki kullanıcı olmadan hesaplanamaz.
2. **Önerileri üretir:** 1 numaralı kullanıcı 101 numaralı filmi beğenmiştir (5 puan) ve 103 numaralı filmi henüz puanlamamıştır. 103, 101'e benzediği için 1 numaralı kullanıcıya 103 önerilir.

Kullanıcı tabanlı (user-based) yaklaşım ise aynı soruyu kullanıcılar üzerinden sorar: "1 ve 2 numaralı kullanıcılar benzer zevklere sahip mi?" Öğeler arasındaki benzerlikler kullanıcılar arasındakilere göre daha kararlı olduğu ve önceden hesaplanabildiği için büyük sistemlerde öğe tabanlı yaklaşım yaygındır. Mahout bu hesapları matris işlemleri olarak ifade eder ve MapReduce işleriyle kümeye dağıtır; yavaştır ama çok büyük verilerde de çalışır.

## 20.4 Özet

| Araç | Rolü |
|---|---|
| **HDFS + MapReduce** | Kümenin temeli ve işleme motoru |
| **Hive** | SQL ile sorgulama ve raporlama |
| **Pig** | Adım adım veri akışları, temizlik ve dönüştürme |
| **Mahout** | Hadoop üzerinde makine öğrenmesi (bugün yerini büyük ölçüde Spark MLlib'e bırakmıştır) |

Bu araçların MapReduce üzerinde çalışan sürümleri, her işin sonucunu diske yazar ve sonraki işe diskten okur. Bir sonraki bölümde ara sonuçları bellekte tutarak bu maliyeti azaltan Spark kurulacaktır.

---

[← 19. Uygulama: İlk MapReduce İşi (WordCount)](19-ilk-mapreduce-isi-wordcount.md) · [İçindekiler](../ders_notu.md) · [21. Uygulama: Apache Spark Kurulumu ve PySpark →](21-apache-spark-ve-pyspark.md)
