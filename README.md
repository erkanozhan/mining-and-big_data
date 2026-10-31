# Veri Madenciliği ve Büyük Veri — Ders Notları ve Uygulamalar

Bu depo, veri madenciliği ve büyük veri teknolojileri dersinin Türkçe ders notlarını, şekillerini ve uygulamalarını içerir. Ders iki soruya cevap arar: **Veriden nasıl bilgi çıkarılır?** ve **Veri tek bir bilgisayara sığmayacak kadar büyüdüğünde bu nasıl yapılır?**

## Ders haritası

| Dosya / klasör | İçerik |
|---|---|
| [ders_notu.md](ders_notu.md) | Ana ders notu. **Kısım I (Bölüm 0–13):** süreç modelleri, veriyi tanıma, ön işleme, veri ambarı ve OLAP, birliktelik kuralları, sınıflandırma, model değerlendirme, kümeleme, aykırı değer tespiti, ileri konular, büyük veriye köprü, etik. **Kısım II (Bölüm 14–21):** büyük veri ve 5V, Hadoop (HDFS, YARN, MapReduce), Hadoop ekosistemi (Hive, Pig, Spark, Mahout, HBase), kurulum, WordCount, Hive/Pig/Mahout ve Spark uygulamaları. |
| [spark_ders_notu.md](spark_ders_notu.md) | Ek not: Laboratuvardaki üç makineyle kurulan Hadoop + Spark kümesi; 1BRC, kelime sayma (MapReduce ve Spark), MLlib ile hiperparametre araması, ölçekleme deneyi. |
| [uygulamalar/veri_on_isleme](uygulamalar/veri_on_isleme/README.md) | Kirli bir müşteri veri setinin Python (pandas) ve R (tidyverse) ile uçtan uca temizlenmesi (Bölüm 4.6). |
| [uygulamalar/birliktelik_kurallari](uygulamalar/birliktelik_kurallari/README.md) | Pazar sepeti analizi: Weka (Apriori, FPGrowth) ve Python (`mlxtend`) (Bölüm 6.4). |
| [uygulamalar/spark_yarn_kumesi](uygulamalar/spark_yarn_kumesi/README.md) | Ek notun betikleri, küme yapılandırma dosyaları ve laboratuvarda alınan ölçüm çıktıları. |
| [scripts/sekil_uret.py](scripts/sekil_uret.py) | Ders notundaki veriye dayalı şekilleri `images/` klasörüne yeniden üretir. |
| `images/` | Ders notlarındaki bütün şekiller (SVG). |

Önerilen okuma sırası: `ders_notu.md` Kısım I → Kısım II → `spark_ders_notu.md`. Her uygulama klasörü, ilgili bölüm okunduktan sonra incelenmek üzere hazırlanmıştır.

## Kurulum

Python örnekleri ve uygulamalar için (Python 3.10 veya üstü):

```bash
pip install -r requirements.txt
```

R uygulaması için gereken paketler [uygulamalar/veri_on_isleme/README.md](uygulamalar/veri_on_isleme/README.md) dosyasında, Weka için gerekenler [uygulamalar/birliktelik_kurallari/README.md](uygulamalar/birliktelik_kurallari/README.md) dosyasında listelenmiştir. Hadoop ve Spark kurulumu ders notunun 17–21. bölümlerinde ve ek notun 5. bölümünde anlatılmıştır.

Şekilleri yeniden üretmek için:

```bash
python scripts/sekil_uret.py
```

## Yazım kuralları

* Notlar resmî (kitap dili) Türkçe ile yazılmıştır. Terimlerin İngilizce karşılığı, Latince kökenli sözcüklerde Latince kökeni, ilk geçtikleri yerde parantez içinde verilir.
* Karmaşıklık matrisinin hücreleri **Gerçek Pozitif (TP), Sahte Pozitif (FP), Gerçek Negatif (TN), Sahte Negatif (FN)** olarak adlandırılır.
* Ondalık ayırıcı olarak, kod çıktılarıyla uyumlu olması için **nokta** kullanılır (ör. 0.940, 33.2 sn).

## Terimler sözlüğü

| Türkçe | İngilizce | Bkz. |
|---|---|---|
| nitelik, öznitelik | attribute, feature | Bölüm 3.1 |
| öğe kümesi | itemset | Bölüm 6.1 |
| destek / güven | support / confidence | Bölüm 6.1 |
| aşırı öğrenme / eksik öğrenme | overfitting / underfitting | Bölüm 8.4 |
| karmaşıklık matrisi | confusion matrix | Bölüm 8.2 |
| Gerçek / Sahte Pozitif | True / False Positive | Bölüm 8.2 |
| kesinlik / duyarlılık / özgüllük | precision / recall / specificity | Bölüm 8.2 |
| kümeleme / küme merkezi | clustering / centroid | Bölüm 9 |
| aykırı değer | outlier | Bölüm 10 |
| küme (bilgisayar kümesi) / düğüm | cluster / node | Bölüm 15.1 |
| blok / replikasyon | block / replication | Bölüm 15.2 |
| meta veri | metadata | Bölüm 15.3 |
| kalp atışı / blok raporu | heartbeat / block report | Bölüm 15.3 |
| konteyner | container | Bölüm 15.4 |
| girdi parçası | input split | Bölüm 15.5 |
| karıştırma ve sıralama | shuffle and sort | Bölüm 15.5 |
| birleştirici | combiner | Bölüm 15.5 |
| sürücü / yürütücü | driver / executor | Bölüm 16.7, ek not 2.4 |
| tembel değerlendirme | lazy evaluation | Bölüm 21.4, ek not 2.2 |
| dönüşüm / eylem | transformation / action | ek not 2.2 |
| bölüm / görev / aşama / iş | partition / task / stage / job | ek not 2.3 |
| kısmi toplama | partial aggregation | Bölüm 15.5, ek not 2.3 |
| soy ağacı | lineage | ek not 2.1 |
| yavaş düğüm | straggler | ek not 11.3 |
