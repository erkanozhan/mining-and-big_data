# 19. Uygulama: İlk MapReduce İşi (WordCount)

Kurulum tamamlandığında elimizde çalışan ama boş bir küme vardır. Bu bölümde HDFS'e ilk veriyi yükleyecek ve büyük veri dünyasının "Merhaba Dünya" programı sayılan **WordCount** (kelime sayma) uygulamasını çalıştıracağız.

## 19.1 Linux Dosya Sistemi ve HDFS

Önce bir kavram karışıklığını önleyelim. Ubuntu'nun kendi dosya sistemi (ext4) ile HDFS ayrı dosya sistemleridir. Masaüstünde duran bir dosyayı Hadoop doğrudan göremez; tıpkı bilgisayardaki bir fotoğrafın paylaşıma yüklenmeden başkaları tarafından görülememesi gibi. Veri önce yerel dosya sisteminden HDFS'e yüklenmelidir. HDFS komutları Linux komutlarına çok benzer; yalnızca başlarına `hdfs dfs` öneki getirilir (`hdfs dfs -ls`, `hdfs dfs -mkdir`, `hdfs dfs -cat` gibi).

## 19.2 HDFS'te Klasör Açma

HDFS'te her kullanıcının çalışma alanı `/user/<kullanıcı adı>` klasörüdür:

```bash
hdfs dfs -mkdir -p /user/hduser/giris_verisi    # -p: üst klasörleri de oluştur
```

## 19.3 Veri Hazırlığı ve Yükleme

Yerel dosya sisteminde bir metin dosyası oluşturulur:

```bash
nano deneme.txt
```

Dosyaya, tekrar eden kelimeler içeren şu satır yazılır ve dosya kaydedilir (`Ctrl+O`, `Enter`, `Ctrl+X`):

```text
Hadoop is powerful. Hadoop is open source. Big Data is future. Hadoop and Spark are friends.
```

Dosya HDFS'e yüklenir ve yüklendiği kontrol edilir; listede `deneme.txt` görülmelidir:

```bash
hdfs dfs -put deneme.txt /user/hduser/giris_verisi/
hdfs dfs -ls /user/hduser/giris_verisi/
```

## 19.4 WordCount İşini Çalıştırma

Hadoop, içinde örnek uygulamalar bulunan bir `.jar` dosyasıyla birlikte gelir. Java kodu yazmadan, bu hazır programla ilk işimizi çalıştıracağız. Komutun genel biçimi şöyledir:

`hadoop jar [jar dosyasının yeri] [programın adı] [girdi klasörü] [çıktı klasörü]`

```bash
hadoop jar $HADOOP_HOME/share/hadoop/mapreduce/hadoop-mapreduce-examples-3.5.0.jar \
    wordcount /user/hduser/giris_verisi /user/hduser/sonuc_cikti
```

> **Önemli kural:** Çıktı klasörü (`/user/hduser/sonuc_cikti`) HDFS'te **bulunmamalıdır**. Hadoop, mevcut bir sonucun yanlışlıkla üzerine yazılmasını önlemek için çıktı klasörünü kendisi oluşturur; klasör zaten varsa iş "Output directory … already exists" hatasıyla başlamadan durur. İşi yeniden çalıştırmadan önce eski çıktı `hdfs dfs -rm -r /user/hduser/sonuc_cikti` ile silinmelidir.

Komut çalışırken terminalde işin ilerleyişi izlenebilir:

* `Connecting to ResourceManager…`: İş YARN'a teslim ediliyor.
* `map 0% reduce 0%`: Görevler başlıyor.
* `map 100% reduce 0%`: Map görevleri bitti; kelimeler `(kelime, 1)` çiftlerine dönüştürüldü.
* `map 100% reduce 100%`: Shuffle ve reduce bitti; sayımlar birleştirildi.

"completed successfully" ifadesi işin başarıyla bittiğini gösterir.

## 19.5 Sonuçları Okuma

Hadoop sonuçları ekrana değil, HDFS'e dosya olarak yazar:

```bash
hdfs dfs -ls /user/hduser/sonuc_cikti
hdfs dfs -cat /user/hduser/sonuc_cikti/part-r-00000
```

Klasörde, işin başarıyla bittiğini gösteren boş bir `_SUCCESS` dosyası ve asıl sonucu içeren `part-r-00000` dosyası bulunur. Sonuç şöyledir (kelime ile sayı arasında bir sekme karakteri vardır):

```text
Big       1
Data      1
Hadoop    3
Spark     1
and       1
are       1
friends.  1
future.   1
is        3
open      1
powerful. 1
source.   1
```

Çıktının iki özelliği dikkat çeker:

* **Noktalama kelimeye yapışıktır:** Hadoop'un hazır WordCount programı metni yalnızca boşluk karakterlerinden böler. Bu yüzden `powerful.` ile `powerful` iki ayrı kelime sayılır; büyük-küçük harf de ayırt edilir. Gerçek bir analizde, Bölüm 11.5'teki metin ön işleme adımları (küçük harfe çevirme, noktalama temizliği) bu iş için yazılacak bir map fonksiyonuna eklenmelidir.
* **Sıralama:** Reduce aşamasına gelen anahtarlar bayt sırasına göre sıralanır; büyük harfle başlayan kelimeler küçük harfle başlayanlardan önce gelir. Bu sıralama, shuffle ve sort aşamasının bir yan ürünüdür.

## 19.6 Arka Planda Ne Oldu?

1. Dosya HDFS'e yüklendiğinde **NameNode** dosyanın hangi bloklardan oluştuğunu ve blokların hangi DataNode'da durduğunu kaydetti.
2. İş başlatıldığında **ResourceManager**, işin ApplicationMaster'ı için bir konteyner ayırdı; ApplicationMaster da map ve reduce görevleri için konteyner istedi.
3. Map görevi, verinin bulunduğu düğümde çalıştı (veri yerelliği) ve `(kelime, 1)` çiftleri üretti.
4. Çiftler shuffle ve sort aşamasında anahtara göre gruplandı, reduce görevi her kelimenin sayılarını topladı ve sonucu HDFS'e yazdı.

Basit bir kelime sayma işi için bile uzun komutlar yazmak ve sonucu ayrıca okumak gerekti. Bir sonraki bölümde, aynı tür analizlerin SQL'e benzer bir dille (Hive) ve adım adım bir veri akışı diliyle (Pig) nasıl kolaylaştığını göreceğiz.

---

[← 18. Hadoop Kurulumu: Tek Makinede Sözde Dağıtık Mod](18-hadoop-kurulumu.md) · [İçindekiler](../ders_notu.md) · [20. Uygulama: Hive, Pig ve Mahout →](20-hive-pig-ve-mahout.md)
