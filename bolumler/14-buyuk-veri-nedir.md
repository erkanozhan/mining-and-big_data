# 14. Büyük Veri Nedir?

> **Kısım II — Büyük Veri Teknolojileri.** Kısım I'in son bölümünde klasik algoritmaların tek bir makinede neden tıkandığını gördük. Bu kısımda, bu sorunu çözmek için geliştirilmiş teknolojileri tanıyacak ve onları kendi bilgisayarımıza kuracağız. Kurulum adımları, laboratuvar kümesinin anlatıldığı ek notla ([Spark ve YARN ile Dağıtık Veri Madenciliği](../spark_ders_notu.md)) aynı sürümleri ve aynı klasör düzenini kullanır. Böylece tek makinede öğrenilen her adım, çok makineli kümeye doğrudan taşınabilir.

## 14.1 Tanım

En basit hâliyle başlayalım. Elinizde tek bir kitaptan oluşan bir bilgi kaynağı olduğunu düşünün. İçindeki bilgileri bulmak ve analiz etmek oldukça kolaydır. Şimdi, o tek kitap yerine dünyanın en büyük kütüphanesindeki bütün kitapların, dergilerin, ses kayıtlarının ve videoların bir anda önünüze yığıldığını hayal edin. Üstelik bu kütüphaneye her saniye binlerce yeni materyal ekleniyor. İşte bu devasa, karmaşık ve sürekli büyüyen bilgi yığınına **büyük veri (big data)** denir.

Geleneksel yöntemler, yani tek bir bilgisayar ve sıradan programlar, bu kütüphaneyi anlamlandırmakta yetersiz kalır: Bir sorunun cevabı saatler, hatta günler sürebilir. Büyük veri alanı, tam da bu sorunu çözmek için vardır. Birbirinden farklı kaynaklardan (sosyal medya, sensörler, web siteleri, banka işlemleri vb.) gelen devasa veri koleksiyonlarını **depolamaya, işlemeye ve analiz etmeye** adanmış bir alandır.

Büyük verinin temel amacı, bu veri yığınının içindeki **değeri**, yani anlamı ortaya çıkarmaktır. Kısım I'de veri madenciliği için kullandığımız madencilik benzetmesi burada da geçerlidir: Tonlarca toprak elenerek değerli maden bulunur; büyük veri de işlenerek değerli bilgilere ve öngörülere ulaşılır.

## 14.2 Büyük Verinin Getirdiği Kazanımlar

Büyük veriyi işlemenin kurumlara sağladığı başlıca kazanımlar şunlardır:

* **Operasyonel iyileştirme:** Bir fabrikanın üretim hattındaki sensör verileri analiz edilerek arızalar önceden tespit edilebilir ve üretim daha verimli hâle getirilebilir.
* **Eyleme dönüştürülebilir bilgi:** Müşteri davranışları analiz edilerek her müşteriye uygun ürün, uygun zamanda sunulabilir.
* **Yeni pazarların belirlenmesi:** Toplumdaki yeni eğilimler ve ihtiyaçlar erken fark edilerek yeni iş fırsatları yaratılabilir.
* **Daha isabetli tahminler:** Hava durumundan talep tahminine kadar geçmiş verilerden geleceğe dair daha isabetli öngörüler üretilebilir.
* **Hata ve sahtekârlık tespiti:** Bankacılıkta olağan dışı işlem örüntüleri anında tespit edilerek sahtekârlık önlenebilir.
* **Veriye dayalı karar verme:** Sezgiler veya sınırlı bilgiler yerine somut verilere dayanan kararlar alınabilir.
* **Bilimsel keşifler:** Genom analizinden uzay araştırmalarına kadar pek çok alanda yeni keşiflere imkân tanır.

## 14.3 Veri Analitiğinin Dört Türü

Ham veriden anlamlı sonuçlar çıkarmak için kullanılan yöntemlerin, tekniklerin ve araçların tümüne **veri analitiği (data analytics)** denir. Veri analitiği, sorduğu soruya göre dört türe ayrılır. Bu ayrımı bir hekimin bir hastayla ilgili yürüttüğü süreç üzerinden düşünmek kolaylık sağlar:

| Tür | Sorusu | Hekim örneği | İş dünyasından örnek |
|---|---|---|---|
| **Betimleyici (descriptive)** | Ne oldu? | "Hastanın ateşi 39 derece." | "Geçen ay ne kadar satış yaptık?" |
| **Tanısal (diagnostic)** | Neden oldu? | "Tahlillere göre ateşin sebebi bakteriyel bir enfeksiyon." | "İkinci çeyrek satışları neden ilk çeyrekten düşük kaldı?" |
| **Tahmine dayalı (predictive)** | Ne olacak? | "Bu enfeksiyon genellikle 3 gün içinde tedaviyle kontrol altına alınır." | "Bu müşterinin kredisini ödememe olasılığı nedir?" |
| **Yönlendirici (prescriptive)** | Ne yapmalıyız? | "En iyi sonuç için bu antibiyotik günde iki kez alınmalı." | "Talebi karşılamak için hangi depodan hangi mağazaya ne kadar ürün gönderilmeli?" |

Betimleyici analitik en temel türdür; yönlendirici analitik ise yalnızca ne olacağını söylemekle kalmaz, en iyi sonuca ulaşmak için ne yapılması gerektiğini de önerir. Kısım I'de gördüğümüz sınıflandırma ve regresyon tahmine dayalı analitiğin, kümeleme ve birliktelik kuralları ise betimleyici analitiğin araçlarıdır.

## 14.4 Büyük Verinin 5 Temel Özelliği (5V)

Bir veri setinin büyük veri sayılması için genellikle İngilizce adları "V" harfiyle başlayan beş özelliğe sahip olması beklenir:

1. **Hacim (Volume):** Verinin miktarı terabaytlar, hatta petabaytlar düzeyindedir. Sosyal medya platformlarına her gün yüz milyonlarca fotoğraf ve video yüklenir.
2. **Hız (Velocity):** Verinin üretilme ve işlenmesi gereken hız. Bir yangın hortumundan akan su gibi düşünülebilir: borsadaki anlık işlemler, bir uçak motorundan gelen sensör verileri, sosyal medyada saniyede paylaşılan binlerce ileti.
3. **Çeşitlilik (Variety):** Verinin farklı tür ve biçimlerde olması. Düzenli tablolar (**yapılandırılmış** veri), XML ve JSON dosyaları (**yarı yapılandırılmış** veri) ve metinler, e-postalar, görüntüler, ses kayıtları (**yapılandırılmamış** veri) bir arada bulunur.
4. **Doğruluk (Veracity):** Verinin kalitesi ve güvenilirliği. Veri eksik, hatalı veya tutarsız olabilir; analizden önce temizlenmesi gerekir (Bölüm 4).
5. **Değer (Value):** En önemli özelliktir. İşlenen veri bir fayda sağlamıyor, bir sorunu çözmüyor veya bir karara yardımcı olmuyorsa, onu toplamanın ve işlemenin anlamı yoktur.

---

[← Kısım I Kaynakları](kisim-1-kaynaklari.md) · [İçindekiler](../ders_notu.md) · [15. Hadoop'a Giriş →](15-hadoopa-giris.md)
