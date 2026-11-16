# Veri Madenciliği ve Büyük Veri — Ders Notu

Bu not, veri madenciliği ve büyük veri teknolojileri dersinin ders notudur ve iki kısımdan oluşur. **Kısım I** veriden bilgi çıkarmanın yöntemlerini, **Kısım II** veri tek bir bilgisayara sığmayacak kadar büyüdüğünde kullanılan teknolojileri anlatır. Dersin genel planı ve önerilen okuma sırası [0. Dersin Yol Haritası](bolumler/00-dersin-yol-haritasi.md) bölümündedir.

> **Web sürümü ve PDF:** Notun web sürümü [erkanozhan.github.io/mining-and-big_data](https://erkanozhan.github.io/mining-and-big_data/) adresindedir; soldaki listeden bölümler arasında geçilir ve tüm notta arama yapılabilir. Notun tamamını yazdırmak veya PDF olarak kaydetmek için [tek sayfalık sürüm](https://erkanozhan.github.io/mining-and-big_data/yazdir.html) açılıp Ctrl+P ile "PDF olarak kaydet" seçilir. Aynı PDF, [`araclar/pdf_olustur.py`](https://github.com/erkanozhan/mining-and-big_data/blob/main/araclar/pdf_olustur.py) betiğiyle de üretilebilir.

## İçindekiler

Not, her bölüm ayrı bir sayfa olacak şekilde bölümlere ayrılmıştır. Her bölümün sonunda önceki ve sonraki bölüme geçiş bağlantıları bulunur.

### Kısım I — Veri Madenciliği: Temeller ve İleri Konular

0. [Dersin Yol Haritası](bolumler/00-dersin-yol-haritasi.md)
1. [Veri Madenciliği Nedir?](bolumler/01-veri-madenciligi-nedir.md)
2. [Bilgi Keşfi Süreç Modelleri](bolumler/02-bilgi-kesfi-surec-modelleri.md)
3. [Veriyi Tanımak](bolumler/03-veriyi-tanimak.md)
4. [Veri Ön İşleme](bolumler/04-veri-on-isleme.md)
5. [Veri Ambarı ve OLAP](bolumler/05-veri-ambari-ve-olap.md)
6. [Sık Örüntüler ve Birliktelik Kuralları](bolumler/06-birliktelik-kurallari.md)
7. [Sınıflandırma](bolumler/07-siniflandirma.md)
8. [Model Değerlendirme](bolumler/08-model-degerlendirme.md)
9. [Kümeleme](bolumler/09-kumeleme.md)
10. [Aykırı Değer Tespiti](bolumler/10-aykiri-deger-tespiti.md)
11. [Veri Madenciliğinde İleri Konular](bolumler/11-ileri-konular.md)
12. [Klasik Veri Madenciliğinden Büyük Veriye](bolumler/12-klasik-veri-madenciliginden-buyuk-veriye.md)
13. [Etik, Gizlilik ve Veri Yönetişimi](bolumler/13-etik-gizlilik-ve-veri-yonetisimi.md)

- [Kısım I Kaynakları](bolumler/kisim-1-kaynaklari.md)

### Kısım II — Büyük Veri Teknolojileri

14. [Büyük Veri Nedir?](bolumler/14-buyuk-veri-nedir.md)
15. [Hadoop'a Giriş](bolumler/15-hadoopa-giris.md)
16. [Hadoop Ekosistemi](bolumler/16-hadoop-ekosistemi.md)
17. [Kurulum Ortamının Hazırlanması](bolumler/17-kurulum-ortaminin-hazirlanmasi.md)
18. [Hadoop Kurulumu: Tek Makinede Sözde Dağıtık Mod](bolumler/18-hadoop-kurulumu.md)
19. [Uygulama: İlk MapReduce İşi (WordCount)](bolumler/19-ilk-mapreduce-isi-wordcount.md)
20. [Uygulama: Hive, Pig ve Mahout](bolumler/20-hive-pig-ve-mahout.md)
21. [Uygulama: Apache Spark Kurulumu ve PySpark](bolumler/21-apache-spark-ve-pyspark.md)

- [Kısım II Kaynakları](bolumler/kisim-2-kaynaklari.md)

### Ek not ve uygulamalar

- [Spark ve YARN ile Dağıtık Veri Madenciliği: Laboratuvar Kümesi Uygulaması](spark_ders_notu.md): Laboratuvardaki üç makineyle kurulan Hadoop + Spark kümesi (ek not)
- [Uygulama: Veri Ön İşleme (Python ve R)](uygulamalar/veri_on_isleme/README.md): Bölüm 4.6
- [Uygulama: Birliktelik Kuralları (Weka ve Python)](uygulamalar/birliktelik_kurallari/README.md): Bölüm 6.4
- [Uygulama: Spark ve YARN ile Dağıtık Veri Madenciliği](uygulamalar/spark_yarn_kumesi/README.md): ek notun betikleri, yapılandırma dosyaları ve ölçüm çıktıları
