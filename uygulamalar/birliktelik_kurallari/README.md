# Uygulama: Birliktelik Kuralları (Weka ve Python)

Bu uygulama, ders notunun **6. Sık Örüntüler ve Birliktelik Kuralları** bölümünde anlatılan **Apriori** ve **FP-Growth** algoritmalarını sentetik bir market verisi üzerinde uygular. Aynı analiz iki ayrı araçla yapılır: **Weka** (grafik arayüz, kod yazmadan) ve **Python** (`mlxtend`). Aynı veri ve aynı eşiklerle iki araç **aynı sık öğe kümelerini ve aynı kuralları** bulur.

**Senaryo.** Bir mahalle marketi, raf düzenini ve kampanyalarını yeniden planlamak istiyor. Elinde son dönemin 1000 alışveriş fişi var. Soru: *Hangi ürünler birlikte alınıyor ve bu birlikteliklerden hangileri gerçekten anlamlı?*

## İçindekiler

0. [Klasör yapısı](#0-klasör-yapısı)
1. [Veri seti](#1-veri-seti)
2. [Isınma: Ders notundaki 5 fişi Weka'da doğrulamak](#2-isınma-ders-notundaki-5-fişi-wekada-doğrulamak)
3. [Weka ile Apriori](#3-weka-ile-apriori)
4. [Weka ile FP-Growth](#4-weka-ile-fp-growth)
5. [Sonuçları yorumlamak](#5-sonuçları-yorumlamak)
6. [Python karşılığı](#6-python-karşılığı)
7. [Weka ↔ Python karşılık tablosu](#7-weka--python-karşılık-tablosu)
8. [Alıştırmalar](#8-alıştırmalar)

---

## 0. Klasör yapısı

```text
uygulamalar/birliktelik_kurallari/
├── veri/
│   ├── market_sepeti.arff         ← Weka için: 1000 fiş, 20 ürün
│   ├── market_sepeti.csv          ← Python için: aynı 1000 fiş (ürünler ';' ile ayrılmış)
│   └── ornek_5_islem.arff         ← ders notundaki 5 fişlik elle hesaplama örneği
├── python/birliktelik_kurallari.py ← Python (mlxtend) sürümü
├── ciktilar/
│   ├── weka/                      ← Weka'nın ürettiği çıktılar (karşılaştırma için)
│   └── python/                    ← Python'un konsol çıktısı ve CSV dosyaları
└── veri_uret.py                   ← sentetik veriyi üreten betik (yalnızca öğretici için)
```

**Weka:** [Weka'nın resmî sayfasından](https://ml.cms.waikato.ac.nz/weka) 3.8.x sürümünü indirip kurun. Windows kurulum paketi Java'yı da içerir.

**Python** (3.9 veya üstü):

```bash
pip install pandas "mlxtend>=0.23"
cd uygulamalar/birliktelik_kurallari
python python/birliktelik_kurallari.py
```

**Veriyi yeniden üretmek** (gerekmez, dosyalar depoda hazırdır): `python veri_uret.py`. Sabit tohum (42) kullanıldığı için her seferinde aynı dosyalar üretilir.

---

## 1. Veri seti

Her fiş, birkaç "alışveriş senaryosunun" ve rastgele eklenen ürünlerin birleşimidir. Senaryolar, veriye **bilerek gömülmüş** birlikteliklerdir. Algoritmaların bunları geri bulmasını bekliyoruz:

| Senaryo | Fişlerin yaklaşık oranı | Birlikte alınan ürünler |
|---|---|---|
| Kahvaltı | %30 | peynir, zeytin, yumurta, çay |
| Bebek bakımı | %15 | bez, mama, ıslak mendil |
| Akşam yemeği | %18 | makarna, domates sosu, kıyma |
| Film gecesi | %12 | cips, kola |
| Çamaşır | %10 | deterjan, yumuşatıcı |

Ayrıca çay alanların çoğu şeker de alır. **Ekmek** ise senaryolardan bağımsız olarak fişlerin yaklaşık %60'ında bulunur. Bu, Bölüm 6.1'deki "Neden lift?" uyarısını gerçek veride görmemizi sağlayacak.

Ürün adları, Weka'da Türkçe karakter sorunu yaşanmaması için ASCII yazılmıştır (`sut`, `cay`, `seker`, `islak_mendil`, `domates_sosu`, `yumusatici`, `kiyma`).

**ARFF biçimi.** Weka'nın kendi dosya biçimidir. Her ürün bir niteliktir ve tek bir değer alabilir: `t` (true, ürün fişte var). Ürün fişte yoksa değer `?` (eksik) yazılır:

```text
@relation market_sepeti

@attribute ekmek {t}
@attribute sut {t}
...
@attribute kahve {t}

@data
?,?,t,t,?,t,?,?,?,?,?,?,t,t,t,t,?,t,?,?
t,t,?,?,?,?,?,?,?,?,?,?,?,?,?,t,t,t,?,?
...
```

> **Neden `{t}` ve `?`, neden `{0, 1}` değil?** `{0, 1}` kullanılsaydı Weka, "ürün yok" (`=0`) değerini de bir öğe sayar ve `ekmek=0 ⇒ kahve=0` gibi işe yaramaz kurallarla ekranı doldururdu. Tek değerli `{t}` niteliklerde eksik değer "ürün yok" anlamına gelir ve kurallarda yer almaz. Weka ile gelen `supermarket.arff` örneği de bu biçimi kullanır.

---

## 2. Isınma: Ders notundaki 5 fişi Weka'da doğrulamak

Önce elle hesapladığımız küçük örneği Weka'ya çözdürelim.

1. Weka'yı açın, **Explorer** düğmesine tıklayın.
2. **Preprocess** sekmesinde **Open file…** ile `veri/ornek_5_islem.arff` dosyasını açın. Solda 6 nitelik (ekmek, sut, bez, mama, kola, yumurta), üstte *Instances: 5* görünmelidir.
3. **Associate** sekmesine geçin. **Choose** ile `Apriori` seçili olsun.
4. Algoritma adının üzerine (beyaz kutuya) tıklayıp parametre penceresini açın ve şunları ayarlayın:

   | Parametre | Değer | Anlamı |
   |---|---|---|
   | `lowerBoundMinSupport` | 0.6 | min_sup = %60 (3 fiş) |
   | `minMetric` | 0.7 | min_conf = %70 |
   | `numRules` | 20 | En fazla 20 kural göster |
   | `outputItemSets` | True | Sık öğe kümelerini de yazdır |

5. **OK**, ardından **Start**.

Çıktının özeti ([ciktilar/weka/ornek_5_islem_apriori_cikti.txt](ciktilar/weka/ornek_5_islem_apriori_cikti.txt)):

```text
Minimum support: 0.6 (3 instances)
Minimum metric <confidence>: 0.7

Large Itemsets L(1):           Large Itemsets L(2):
ekmek=t 4                      ekmek=t sut=t 3
sut=t 4                        ekmek=t bez=t 3
bez=t 4                        sut=t bez=t 3
mama=t 3                       bez=t mama=t 3

Best rules found:
 1. mama=t 3 ==> bez=t 3    <conf:(1)> lift:(1.25) ...
 2. sut=t 4 ==> ekmek=t 3    <conf:(0.75)> lift:(0.94) ...
 ...
 8. bez=t 4 ==> mama=t 3    <conf:(0.75)> lift:(1.25) ...
```

$L_1$, $L_2$ ve 8 kural, ders notundaki (Bölüm 6.2) elle hesaplanan tabloyla birebir aynıdır. Kola ve Yumurta 1. taramada elenmiş, 3-öğe kümesi bulunamamıştır.

---

## 3. Weka ile Apriori

1. **Preprocess** sekmesinde `veri/market_sepeti.arff` dosyasını açın. *Instances: 1000*, *Attributes: 20* görünmelidir. Bir niteliğe (ör. `ekmek`) tıklayınca sağda *Missing: 376 (38%)* görürsünüz: Ekmek 624 fişte var, 376 fişte yok.
2. **Associate** sekmesinde `Apriori` seçin ve parametreleri ayarlayın:

   | Parametre | Varsayılan | Bizim değer | Açıklama |
   |---|---|---|---|
   | `lowerBoundMinSupport` | 0.1 | **0.1** | min_sup = %10 (100 fiş) |
   | `minMetric` | 0.9 | **0.6** | min_conf = %60 |
   | `numRules` | 10 | **100** | Kural sayısı sınırı (aşağıdaki nota bakın) |
   | `metricType` | Confidence | Confidence | Kuralları güvene göre sırala |
   | `outputItemSets` | False | **True** | Sık öğe kümelerini de yazdır |

3. **Start**. Sonuç ([ciktilar/weka/apriori_cikti.txt](ciktilar/weka/apriori_cikti.txt)):

```text
Minimum support: 0.1 (100 instances)
Minimum metric <confidence>: 0.6
Number of cycles performed: 18

Size of set of large itemsets L(1): 16
Size of set of large itemsets L(2): 20
Size of set of large itemsets L(3): 3

Best rules found:

  1. mama=t 128 ==> bez=t 128    <conf:(1)> lift:(6.17) lev:(0.11) [107] conv:(107.26)
  2. domates_sosu=t 126 ==> makarna=t 126    <conf:(1)> lift:(4.52) lev:(0.1) [98] conv:(98.15)
  3. islak_mendil=t 117 ==> bez=t 117    <conf:(1)> lift:(6.17) lev:(0.1) [98] conv:(98.05)
  4. peynir=t seker=t 110 ==> cay=t 102    <conf:(0.93)> lift:(4.85) lev:(0.08) [80] conv:(9.89)
  5. ekmek=t zeytin=t 120 ==> peynir=t 106    <conf:(0.88)> lift:(3.18) lev:(0.07) [72] conv:(5.78)
  6. zeytin=t 203 ==> peynir=t 175    <conf:(0.86)> lift:(3.1) lev:(0.12) [118] conv:(5.05)
  ...
 16. seker=t 168 ==> ekmek=t 115    <conf:(0.68)> lift:(1.1) lev:(0.01) [10] conv:(1.17)
  ...
 27. yumurta=t 207 ==> ekmek=t 125    <conf:(0.6)> lift:(0.97) lev:(-0) [-4] conv:(0.94)
```

**Bir kural satırı nasıl okunur?** `mama=t 128 ==> bez=t 128 <conf:(1)> lift:(6.17) lev:(0.11) [107] conv:(107.26)`

| Parça | Anlamı |
|---|---|
| `mama=t 128` | Sol taraf (X): Mama 128 fişte var |
| `bez=t 128` | X ve Y'nin birlikte geçtiği fiş sayısı: 128 → destek = 128/1000 = 0.128 |
| `conf:(1)` | Güven = 128/128 = 1.00: Mama alan herkes bez de almış |
| `lift:(6.17)` | Lift = 1.00 / 0.162 (bezin desteği) = 6.17 |
| `lev:(0.11) [107]` | Leverage = P(X∪Y) − P(X)·P(Y) = 0.128 − 0.128·0.162 ≈ 0.107. Köşeli parantezdeki 107, bunun fiş sayısı karşılığıdır: "Bağımsızlık durumuna göre 107 fiş fazla" |
| `conv:(107.26)` | Conviction = (1 − destek(Y)) / (1 − güven). Kuralın ne kadar az yanıldığını ölçer; 1 bağımsızlık demektir. Bu kural hiç yanılmadığı için çok büyüktür (Bölüm 6'daki nota bakın) |

Ders notunda tanımlanan destek, güven ve lift'e ek olarak Weka iki ölçü daha verir. **Leverage**, birlikte görülme oranının bağımsızlık durumunda beklenenden ne kadar *fazla* olduğudur (lift oranı, leverage farkı ölçer). **Conviction** ise kuralın yanılma oranını, X ve Y bağımsız olsaydı beklenecek yanılma oranıyla karşılaştırır.

> **"Number of cycles performed: 18" ne demek?** Weka'nın Apriori'si destek eşiğini doğrudan kullanmaz. `upperBoundMinSupport` (1.0) değerinden başlar, eşiği her turda `delta` (0.05) kadar düşürür ve `numRules` sayıda kural bulunca durur. Eşik `lowerBoundMinSupport` değerinin altına inemez. Burada 0.95 → 0.90 → … → 0.10 arasında 18 tur yapılmıştır. `numRules` değerini 100 yaptığımız için Weka 27 kuralla yetinmeyip 0.10'a kadar inmiştir. Varsayılan `numRules = 10` ile bıraksaydınız, Weka 10 kural bulduğu ilk eşikte duracaktı ve sonuç, eşiği tam 0.10 olan Python sonucuyla karşılaştırılamazdı.

---

## 4. Weka ile FP-Growth

1. Aynı veri açıkken **Associate** sekmesinde **Choose → FPGrowth** seçin.
2. Parametreler:

   | Parametre | Varsayılan | Bizim değer | Açıklama |
   |---|---|---|---|
   | `lowerBoundMinSupport` | 0.1 | **0.1** | min_sup |
   | `minMetric` | 0.9 | **0.6** | min_conf |
   | `findAllRulesForSupportLevel` | False | **True** | Eşiği adım adım düşürme; doğrudan 0.1 ile tüm kuralları bul |
   | `positiveIndex` | 2 | 2 | `{t}` gibi tek değerli niteliklerde etkisizdir |

3. **Start**. Sonuç ([ciktilar/weka/fpgrowth_cikti.txt](ciktilar/weka/fpgrowth_cikti.txt)):

```text
FPGrowth found 27 rules

 1. [domates_sosu=t]: 126 ==> [makarna=t]: 126   <conf:(1)> lift:(4.52) lev:(0.1) conv:(98.15)
 2. [mama=t]: 128 ==> [bez=t]: 128   <conf:(1)> lift:(6.17) lev:(0.11) conv:(107.26)
 3. [islak_mendil=t]: 117 ==> [bez=t]: 117   <conf:(1)> lift:(6.17) lev:(0.1) conv:(98.05)
 4. [peynir=t, seker=t]: 110 ==> [cay=t]: 102   <conf:(0.93)> lift:(4.85) lev:(0.08) conv:(9.89)
 ...
```

FPGrowth da **aynı 27 kuralı** bulur. Yalnızca yazım biçimi farklıdır (öğeler köşeli parantez içinde). Güveni eşit olan kuralların sırası iki algoritmada farklı olabilir. Bu, kuralların kendisini etkilemez.

> **FPGrowth'un iki kullanışlı parametresi:** `rulesMustContain` (ör. `bez`) yalnızca bu ürünü içeren kuralları gösterir. `transactionsMustContain` ise analizi yalnızca bu ürünü içeren fişlerle sınırlar. Kalabalık bir çıktıda belirli bir ürünü incelemek için idealdir.

**Komut satırından (isteğe bağlı).** Weka kurulum klasöründeki `weka.jar` ile aynı sonuçlar şu komutlarla da alınabilir:

```bash
java -cp weka.jar weka.associations.Apriori  -t veri/market_sepeti.arff -N 100 -C 0.6 -M 0.1 -I
java -cp weka.jar weka.associations.FPGrowth -t veri/market_sepeti.arff -C 0.6 -M 0.1 -S
```

---

## 5. Sonuçları yorumlamak

27 kuralın hepsi aynı değerde değildir. Bunları üç gruba ayırabiliriz:

**a) Gömülü örüntüler bulundu (lift ≫ 1).** Bebek bakımı (lift 6.17), akşam yemeği (4.52), çay–şeker (4.14) ve kahvaltı (peynir–zeytin 3.10) senaryoları başarıyla geri bulundu. Bu kurallar raf düzeni ve kampanya için kullanılabilir. Örneğin mama alan herkes bez de alıyor, ama bez alanların ancak %79'u mama alıyor. Mama alanlara bez önermek ek satış getirmez, çünkü zaten alıyorlar. Asıl fırsat, bez alıp mama almayan %21'lik gruptadır: Bez reyonunun yanında yapılacak bir mama kampanyası bu gruba ulaşır.

**b) Güven yüksek ama ilişki yok (lift ≈ 1).** 7 kuralın sağ tarafı `ekmek`:

| Kural | Güven | Lift |
|---|---|---|
| {seker} ⇒ {ekmek} | 0.68 | 1.10 |
| {cay} ⇒ {ekmek} | 0.66 | 1.07 |
| {makarna} ⇒ {ekmek} | 0.66 | 1.05 |
| {kola} ⇒ {ekmek} | 0.63 | 1.01 |
| {peynir} ⇒ {ekmek} | 0.62 | 0.99 |
| {peynir, zeytin} ⇒ {ekmek} | 0.61 | 0.97 |
| {yumurta} ⇒ {ekmek} | 0.60 | 0.97 |

Güvenleri %60'ın üzerinde, ama ekmek zaten fişlerin %62.4'ünde var. Bu ürünleri almak, ekmek alma olasılığını değiştirmiyor. Bu kurallara dayanarak "peynir alanlara ekmek önerelim" demek anlamsızdır. **Kuralları yalnızca güvene göre değil, lift'e göre de süzün.** Weka'da `metricType = Lift` ve örneğin `minMetric = 1.5` seçerek bunu doğrudan yapabilirsiniz.

**c) Bulunamayanlar.** Deterjan–yumuşatıcı (lift 11.8!) ve cips–kola ilişkileri listede yok. Neden? Yumuşatıcı yalnızca 61, {cips, kola} ise 87 fişte geçiyor. İkisi de min_sup = 100 fiş eşiğinin altında kalıyor. Destek eşiği, **nadir ama güçlü** ilişkileri gözden kaçırmamıza yol açabilir (Alıştırma 1).

---

## 6. Python karşılığı

[python/birliktelik_kurallari.py](python/birliktelik_kurallari.py) betiği, Weka'da yapılanları adım adım yapar. Tam konsol çıktısı: [ciktilar/python/konsol_cikti.txt](ciktilar/python/konsol_cikti.txt).

**Adım 1–2: Fişleri okuyup ikili tabloya çevirme.** CSV'de her satır bir fiştir. `TransactionEncoder`, bu listeyi her ürünün bir sütun olduğu True/False tablosuna çevirir. Weka'daki ARFF dosyasının yaptığı iş de budur.

```python
import pandas as pd
from mlxtend.preprocessing import TransactionEncoder
from mlxtend.frequent_patterns import apriori, fpgrowth, association_rules

df = pd.read_csv("veri/market_sepeti.csv")
islemler = df["urunler"].str.split(";").tolist()   # [['peynir', 'zeytin', ...], ...]

te = TransactionEncoder()
X = pd.DataFrame(te.fit(islemler).transform(islemler), columns=te.columns_)
# X.shape → (1000, 20)
```

**Adım 3: Sık öğe kümeleri.** İki algoritmanın çağrısı aynıdır:

```python
sik_apriori = apriori(X, min_support=0.10, use_colnames=True)
sik_fp      = fpgrowth(X, min_support=0.10, use_colnames=True)
```

```text
Boyuta göre sık öğe kümesi sayısı (Weka'daki L(1), L(2), L(3)):
1    16
2    20
3     3

Apriori 39 küme, FP-Growth 39 küme buldu. Kümeler aynı mı? True
```

**Adım 4: Kurallar.**

```python
kurallar = association_rules(sik_fp, num_itemsets=len(X),
                             metric="confidence", min_threshold=0.60)
```

```text
27 kural bulundu (Weka da 27 kural bulur).

                            kural  destek  güven  lift  leverage  conviction
1                 {mama} => {bez}   0.128   1.00  6.17     0.107         inf
2         {islak_mendil} => {bez}   0.117   1.00  6.17     0.098         inf
3     {domates_sosu} => {makarna}   0.126   1.00  4.52     0.098         inf
4        {peynir, seker} => {cay}   0.102   0.93  4.85     0.081       11.12
5     {ekmek, zeytin} => {peynir}   0.106   0.88  3.18     0.073        6.19
6            {zeytin} => {peynir}   0.175   0.86  3.10     0.119        5.23
...
```

**Adım 5** lift değeri 1'e yakın "ekmek kurallarını" ve lift > 2 olan ilginç kuralları ayrı ayrı listeler. **Adım 6** destek eşiğini 0.05'e düşürür ve 0.10'da kaybolan deterjan–yumuşatıcı, kıyma–domates sosu ve cips–kola kurallarını gösterir. Kurallar ve sık öğe kümeleri `ciktilar/python/` altına CSV olarak kaydedilir.

> **Conviction neden farklı?** Güveni 1 olan kurallarda conviction'ın paydası $1 - \text{güven} = 0$ olur. Python bu durumda `inf` (sonsuz) yazar. Weka ise paydaya 1 fiş ekleyerek düzeltme yapar ve sonlu ama çok büyük bir sayı (107.26) verir. Diğer kurallarda da bu düzeltme yüzünden iki aracın conviction değerleri biraz farklıdır (ör. 9.89 ve 11.12). Destek, güven, lift ve leverage ise birebir aynıdır.

> **Hız karşılaştırması hakkında.** Betik iki algoritmanın sürelerini de yazdırır. Bu küçük veride (20 ürün, 1000 fiş) `mlxtend`'in Apriori'si FP-Growth kadar, hatta ondan hızlı çalışabilir, çünkü vektörel (numpy) hesap kullanır. FP-Growth'un üstünlüğü yüzlerce/binlerce ürün, milyonlarca fiş ve düşük destek eşiğinde ortaya çıkar. Bu yüzden Spark MLlib büyük veri için Apriori'yi değil, FP-Growth'u sunar.

---

## 7. Weka ↔ Python karşılık tablosu

| İş | Weka (Explorer) | Python (mlxtend) |
|---|---|---|
| Veri biçimi | ARFF, her ürün `{t}` niteliği, yok = `?` | Fiş listesi → `TransactionEncoder` → True/False tablo |
| Apriori | Associate → `Apriori` | `apriori(X, min_support=...)` |
| FP-Growth | Associate → `FPGrowth` | `fpgrowth(X, min_support=...)` |
| min_sup | `lowerBoundMinSupport` | `min_support` |
| min_conf | `minMetric` (metricType = Confidence) | `association_rules(..., metric="confidence", min_threshold=...)` |
| Lift ile süzme | `metricType = Lift`, `minMetric = 1.5` | `metric="lift", min_threshold=1.5` |
| Sık kümeleri görme | `outputItemSets = True` | `apriori(...)` / `fpgrowth(...)` sonucu |
| Belirli ürünü içeren kurallar | FPGrowth → `rulesMustContain` | `kurallar[kurallar.antecedents.apply(lambda s: "bez" in s)]` |
| Kural sayısı sınırı | `numRules` / `numRulesToFind` | `kurallar.head(n)` |

---

## 8. Alıştırmalar

1. **Destek eşiğini düşürün.** Weka'da `lowerBoundMinSupport = 0.05` yapın (FPGrowth'ta `findAllRulesForSupportLevel = True` kalsın). Kaç kural bulunuyor? Deterjan–yumuşatıcı ve cips–kola kuralları görünüyor mu? Python'da Adım 6 aynı deneyi yapar; iki aracın kural sayılarını karşılaştırın.
2. **Lift ile sıralayın.** Weka'da `metricType = Lift`, `minMetric = 1.5` seçin. "Ekmek kuralları" listede kalıyor mu? En yüksek lift değerli kural hangisi ve neden?
3. **Yönlülük.** `{mama} ⇒ {bez}` ile `{bez} ⇒ {mama}` kurallarının destek, güven ve lift değerlerini karşılaştırın. Hangileri aynı, hangisi farklı? Neden?
4. **3'lü kurallar.** `{peynir, seker} ⇒ {cay}` kuralının güveni (0.93), `{seker} ⇒ {cay}` kuralının güveninden (0.79) yüksek. Bu, market için ne anlama gelir?
5. **Kendi verinizi üretin.** `veri_uret.py` içindeki `SENARYOLAR` sözlüğüne yeni bir senaryo ekleyin (ör. "piknik": mangal kömürü, sucuk, ayran). Veriyi yeniden üretin, Weka ve Python'da yeni kuralı bulun. Senaryonun olasılığını düşürdükçe kural hangi destek eşiğinde kayboluyor?
6. **(İleri) FP-ağacını elle çizin.** `ornek_5_islem.arff` için ders notundaki (Bölüm 6.3) FP-ağacını, öğe sırasını *Mama, Bez, Ekmek, Süt* olarak değiştirip yeniden çizin. Ağaç değişir mi? Bulunan sık kümeler değişir mi?
