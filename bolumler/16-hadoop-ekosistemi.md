# 16. Hadoop Ekosistemi

Hadoop'un çekirdeği (HDFS, YARN ve MapReduce) güçlüdür, ama her analiz için Java ile MapReduce programı yazmak zahmetlidir. Bu yüzden çekirdeğin etrafında, işi kolaylaştıran ve yeni yetenekler kazandıran araçlardan oluşan geniş bir **ekosistem** gelişmiştir.

Bu araçları bir kütüphane benzetmesiyle düşünebiliriz. Hadoop milyonlarca kitabın durduğu devasa bir depodur; MapReduce ile çalışmak, her soru için depoya girip rafları tek tek gezmek gibidir: Güçlü ama yavaş ve zahmetli bir yöntemdir. **Hive**, sizin dilinizden anlayan bir kütüphane görevlisidir: Ona SQL'e benzer bir dille ne istediğinizi söylersiniz, o rafları sizin yerinize tarar. **Pig**, veriyi temizleyip düzenleyen bir mutfak şefine benzer: "Önce yıka, sonra doğra, en son pişir" gibi adım adım tarif edilen işlemleri uygular. **Spark**, işlemleri sürekli kâğıda yazmak yerine aklında tutan güçlü bir hesap ustasıdır. **Mahout** ise veriden tahmin modelleri çıkaran istatistikçidir.

## 16.1 Apache Hive: Veri Ambarının SQL Kapısı

**Hive**, Facebook tarafından geliştirilmiş ve sonra açık kaynak hâline getirilmiş bir veri ambarı altyapısıdır. Amacı, SQL bilen analistlerin Java yazmadan Hadoop üzerinde çalışabilmesidir. Hive, **HiveQL** (Hive Query Language) ile yazılan sorguları alır ve arka planda MapReduce, Tez veya Spark işlerine dönüştürür.

Hive gerçek zamanlı bir veritabanı değildir. OLTP işlemlerinden çok OLAP için tasarlanmıştır (Bölüm 5.1): "Bir satırı silip hemen güncelleyeyim" yerine "son 10 yılın satış verisini analiz edeyim" türünden senaryolara uygundur. Verinin şeması, veri yazılırken değil okunurken uygulanır (**schema-on-read**, Bölüm 5.4); bu da esneklik sağlar.

**Metastore.** Hive'da verinin kendisi HDFS'te durur. Tablo adları, sütun tipleri ve her tablonun HDFS'teki yeri gibi **meta veriler** ise ilişkisel bir veritabanında, **metastore** adı verilen katalogda tutulur. Bir sorgu geldiğinde Hive önce metastore'a "bu tablo nerede, sütunları neler?" diye sorar, aldığı cevaba göre veriyi HDFS'ten okur. Metastore üç biçimde kurulabilir:

| Kurulum | Meta veri nerede? | Kullanım |
|---|---|---|
| **Gömülü (embedded)** | Hive ile aynı süreçte çalışan Apache Derby veritabanında | Varsayılan; aynı anda yalnızca tek bir oturum bağlanabilir. Öğrenme ve deneme için uygundur. |
| **Yerel (local)** | MySQL veya PostgreSQL gibi ayrı bir veritabanında; metastore servisi yine Hive süreci içinde çalışır | Birden çok kullanıcı aynı anda çalışabilir. Bağlantı bilgileri `hive-site.xml` dosyasında tanımlanır. |
| **Uzak (remote)** | Ayrı bir veritabanında; metastore ayrı bir servis olarak çalışır | İstemciler (Hive, Spark vb.) metastore servisine ağ üzerinden bağlanır (varsayılan port 9083). Kurumsal kümelerde tercih edilir. |

## 16.2 Apache Pig: Veri Akışı Dili

**Pig**, Yahoo tarafından geliştirilmiştir ve **Pig Latin** adlı bir betik dili kullanır. SQL **bildirimseldir** (ne istediğinizi söylersiniz), Pig Latin ise **prosedüreldir** (nasıl yapılacağını adım adım söylersiniz): "Veriyi yükle → süz → dönüştür → kaydet." Bu yaklaşım, özellikle yapılandırılmamış veya yarı yapılandırılmış veriler üzerinde ETL işlemleri (Bölüm 5.2) yaparken kolaylık sağlar. Birbirine bağlı birkaç MapReduce işiyle yazılacak birleştirme, gruplama ve süzme zincirleri Pig'de birkaç satırla ifade edilir.

## 16.3 Apache Spark: Bellek İçi İşleme

**Spark**, Hadoop ekosistemindeki en önemli kırılma noktalarından biridir. MapReduce her işin sonucunu diske yazar ve bir sonraki iş girdisini yeniden diskten okur. Spark ise bir uygulamanın bütün adımlarını tek bir plan içinde yürütür ve ara sonuçları mümkün olduğunca işçi makinelerin belleğinde tutar. Programcı `cache()` ile istediği veriyi bellekte saklatabilir; böylece aynı veri üzerinde defalarca dönen yinelemeli algoritmalar (ör. makine öğrenmesi) diske tekrar tekrar gitmez. Spark projesi, bu tür iş yüklerinde MapReduce'a göre **100 kata kadar** hızlanma bildirir; tek geçişli işlerde fark daha küçüktür (ek nottaki kelime sayma deneyinde 2.5–3 kat ölçülmüştür).

Spark yalnızca hızlı değildir; Spark SQL, Structured Streaming (akış işleme), MLlib (makine öğrenmesi) ve GraphX (graf işleme) modüllerini tek bir çatı altında toplar. Böylece veri hazırlama, sorgulama ve model eğitimi aynı platformda yapılabilir.

> **Uygulamalı devam:** Spark'ın mimarisi, YARN üzerinde çalışması ve laboratuvardaki üç makineli kümede yapılan ölçümler ayrı bir notta anlatılmıştır: [Spark ve YARN ile Dağıtık Veri Madenciliği](../spark_ders_notu.md).

## 16.4 Apache Mahout: Hadoop Üzerinde Makine Öğrenmesi

**Mahout**, Hadoop üzerinde ölçeklenebilir makine öğrenmesi için geliştirilmiş öncü kütüphanelerden biridir. Öneri sistemleri (recommendation), kümeleme (clustering) ve sınıflandırma (classification) algoritmaları içerir. Mahout ilk çıktığında MapReduce üzerinde çalışıyordu. Ancak yinelemeli makine öğrenmesi algoritmalarında her adımın diske yazılması süreci çok yavaşlattığı için MapReduce tabanlı algoritmalar zamanla terk edildi; bu alanda bugün çoğunlukla Spark'ın kütüphanesi **MLlib** kullanılmaktadır. Mahout'u tanımak yine de dağıtık makine öğrenmesinin tarihini ve temel fikirlerini anlamak açısından yararlıdır.

## 16.5 Apache HBase: HDFS Üzerinde NoSQL Veritabanı

HDFS, büyük dosyaları baştan sona okumak için tasarlanmıştır; tek bir kaydı milisaniyeler içinde okumak veya güncellemek için uygun değildir. **HBase**, bu ihtiyacı karşılamak için Google'ın Bigtable'ından esinlenerek geliştirilmiş, HDFS üzerinde çalışan **geniş sütunlu (column-family)** bir NoSQL veritabanıdır (Bölüm 12.5).

* Her satır bir **satır anahtarıyla (row key)** tanımlanır; satırlar anahtara göre sıralı tutulur. Bu sayede belirli bir anahtara veya anahtar aralığına çok hızlı erişilir.
* Sütunlar **sütun aileleri** hâlinde gruplanır; bir satırda yalnızca dolu olan sütunlar saklandığı için çok büyük ve seyrek tablolar verimli tutulur.
* Tablolar satır aralıklarına göre **bölgelere (region)** bölünür ve bölgeler kümedeki **RegionServer** süreçleri tarafından sunulur. **HMaster** bölgelerin dağıtımını yönetir, koordinasyon için ZooKeeper kullanılır. Veri dosyaları ise HDFS'te durduğu için replikasyondan yararlanır.

HBase, kullanıcı profilleri, sensör zaman serileri veya mesajlaşma kayıtları gibi milyarlarca satıra **rastgele ve gerçek zamanlı** okuma/yazma gereken durumlarda kullanılır. Toplu analiz için ise Hive veya Spark daha uygundur. CAP teoremi açısından HBase, tutarlılığı erişilebilirliğe tercih eden bir **CP** sistemidir (Bölüm 12.4).

## 16.6 Tamamlayıcı Araçlar: ZooKeeper, Sqoop ve Flume

* **ZooKeeper:** Dağıtık sistemlerde koordinasyonu sağlar. Hangi sunucunun ayakta olduğu, hangisinin lider olduğu ve ortak yapılandırma bilgilerinin nerede tutulduğu gibi soruların cevabı ZooKeeper'dadır. Bir trafik polisine benzetilebilir.
* **Sqoop:** İlişkisel veritabanları (MySQL, Oracle vb.) ile Hadoop arasında toplu veri aktarımı sağlar. Proje 2021'de Apache bünyesinde emekliye ayrılmıştır; bugün aynı iş çoğunlukla Spark'ın JDBC bağlantısıyla yapılır.
* **Flume:** Log dosyaları gibi sürekli üretilen verileri toplayıp HDFS'e aktarmak için tasarlanmıştır. Günümüzde bu alanda Apache Kafka da yaygın olarak kullanılır (Bölüm 12.6).

## 16.7 Bileşenler Nasıl Birlikte Çalışır?

Bu araçlar birbirinden bağımsız adalar değildir. Hepsi aynı dosya sistemini (HDFS) ve aynı kaynak yöneticisini (YARN) paylaşır ve birbirlerinin yapılandırma dosyalarını okuyarak haberleşir.

* **Ortam değişkenleri:** İşletim sisteminin `hdfs`, `spark-submit` gibi komutları bulabilmesi için `JAVA_HOME`, `HADOOP_HOME`, `SPARK_HOME` gibi değişkenlerin ve `PATH`'in tanımlanması gerekir (Bölüm 17.3).
* **Yapılandırma dosyaları:** Hadoop'un davranışı `$HADOOP_HOME/etc/hadoop` altındaki XML dosyalarıyla belirlenir: `core-site.xml` (varsayılan dosya sistemi, yani NameNode'un adresi), `hdfs-site.xml` (kopya sayısı, veri klasörleri), `yarn-site.xml` (ResourceManager'ın adresi, düğüm kaynakları) ve `mapred-site.xml` (MapReduce'un YARN üzerinde çalışması). Spark ve Hive, HDFS'in ve YARN'ın nerede olduğunu bu dosyalardan öğrenir; bunun için `HADOOP_CONF_DIR` değişkeninin bu klasörü göstermesi yeterlidir.
* **Spark ve YARN:** Bir Spark uygulaması `spark-submit` ile başlatıldığında YARN'dan kaynak ister. Uygulamanın planını yapan sürece **driver (sürücü)**, işçi makinelerde görevleri yürüten süreçlere **executor (yürütücü)** denir. `--num-executors` ve `--executor-memory` gibi parametreler hem işin hızını hem de kümenin diğer işlere bırakacağı kaynağı belirler: Kümenin kapasitesinden fazla kaynak istenirse iş kuyrukta bekler, gereğinden az istenirse kaynaklar boşa kalır.
* **Spark ve Hive:** Spark, Hive tablolarını doğrudan okuyabilir. Bunun için `hive-site.xml` dosyası Spark'ın `conf` klasörüne kopyalanır ve Spark oturumu Hive desteğiyle (`enableHiveSupport()`) başlatılır. Böylece Hive'ın kataloğundaki tablolar Spark SQL ile, Spark'ın hızından yararlanılarak sorgulanabilir.

---

[← 15. Hadoop'a Giriş](15-hadoopa-giris.md) · [İçindekiler](../ders_notu.md) · [17. Kurulum Ortamının Hazırlanması →](17-kurulum-ortaminin-hazirlanmasi.md)
