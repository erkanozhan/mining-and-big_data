# 13. Etik, Gizlilik ve Veri Yönetişimi

Veri madenciliği güçlü bir araçtır. Her güçlü araç gibi yanlış kullanıldığında ciddi zararlara yol açabilir. Witten ve arkadaşları, Han ve arkadaşları ve Erl ve arkadaşları, kitaplarında bu konuya ayrı bölümler ayırır. Bu da konunun teknik konular kadar önemli olduğunu gösterir.

**Gizlilik ve yasal çerçeve.** Kişisel verilerin işlenmesi Türkiye'de **6698 sayılı Kişisel Verilerin Korunması Kanunu (KVKK)**, Avrupa Birliği'nde **Genel Veri Koruma Tüzüğü (GDPR)** ile düzenlenir. Temel ilkeler şunlardır:

* **Amaçla sınırlılık:** Veri yalnızca toplandığı belirli ve meşru amaç için işlenebilir.
* **Veri minimizasyonu:** Amaç için gerekenden fazla veri toplanmamalıdır. Bu ilke, "her şeyi topla, belki ileride lazım olur" büyük veri yaklaşımıyla doğrudan çatışır.
* **Açık rıza ve aydınlatma:** İlgili kişi, verisinin nasıl işleneceği konusunda bilgilendirilmelidir.
* **Unutulma hakkı:** Kişi, verisinin silinmesini talep edebilir.
* **Otomatik karar verme:** GDPR, yalnızca otomatik işlemeye dayanan ve kişiyi önemli ölçüde etkileyen kararlara (ör. kredi reddi) itiraz ve açıklama hakkı tanır.

**Anonimleştirme yeterli mi?** Kimlik numarası ve isim gibi doğrudan tanımlayıcıları silmek çoğu zaman yetmez. Latanya Sweeney'in ünlü çalışmasına göre ABD nüfusunun yaklaşık **%87'si** yalnızca *posta kodu, doğum tarihi ve cinsiyet* üçlüsüyle tekil olarak tanımlanabilir. Netflix'in 2006'da bir yarışma için yayımladığı "anonim" film puanlama verisi de 2008'de araştırmacılar tarafından IMDb'deki herkese açık puanlarla eşleştirilmiş ve bazı kullanıcıların kimlikleri ortaya çıkarılmıştır. Bu tür **yeniden tanımlama (re-identification)** saldırılarına karşı geliştirilen yöntemler şunlardır:

* **k-anonimlik:** Her kaydın, tanımlayıcı niteliklerde en az *k−1* başka kayıtla aynı olması (genelleştirme ve bastırma ile).
* **Diferansiyel gizlilik (differential privacy):** Sorgu sonuçlarına kontrollü gürültü eklenerek, tek bir kişinin veri setinde bulunup bulunmamasının sonucu fark edilir biçimde değiştirmemesi sağlanır.
* **Gizliliği koruyan veri madenciliği (privacy-preserving data mining)** ve verinin merkeze taşınmadan cihazlarda model eğitildiği **federe öğrenme (federated learning)**.

**Algoritmik önyargı ve adalet.** Modeller geçmiş veriden öğrenir; geçmiş veri ise toplumdaki önyargıları yansıtabilir. Sık anılan bir örnek, büyük bir teknoloji şirketinin işe alım modelidir. Geçmişte çoğunlukla erkeklerin işe alındığı verilerle eğitilen model, "kadın" kelimesi geçen özgeçmişleri sistematik olarak düşük puanlamıştır. Hassas bir niteliği (cinsiyet, etnik köken) modelden çıkarmak da yetmez, çünkü posta kodu veya okul gibi **vekil (proxy)** değişkenler aynı bilgiyi taşıyabilir. Adil modeller için veri setleri temsil açısından denetlenmeli, model performansı alt gruplar bazında ayrı ayrı raporlanmalı ve karar süreçlerinde insan denetimi korunmalıdır.

**Veri yönetişimi (data governance).** Erl ve arkadaşları büyük veri projelerinde şu konuların baştan planlanması gerektiğini vurgular:

* **Veri kökeni (provenance / lineage):** Verinin nereden geldiği, hangi dönüşümlerden geçtiği ve hangi analiz sonucunu ürettiği izlenebilmelidir. Bu hem tekrarlanabilirlik hem de denetim için şarttır.
* **Güvenlik:** Kimlik doğrulama, yetkilendirme, şifreleme. Hadoop ekosisteminde bu iş için Kerberos, Apache Ranger ve Apache Knox kullanılır.
* **Veri kalitesi ve meta veri yönetimi:** Veri gölünün "veri bataklığına" dönüşmemesi için (Bölüm 5.4).
* **Saklama ve imha politikaları:** Verinin ne kadar süre tutulacağı ve nasıl güvenle silineceği.

> Bir veri madenciliği projesine başlarken teknik soruların yanında şu soruları da sormak gerekir: *Bu veriyi kullanmaya hakkımız var mı? Sonuçlar kimin aleyhine kullanılabilir? Model bir hata yaptığında bedelini kim öder?*

---

[← 12. Klasik Veri Madenciliğinden Büyük Veriye](12-klasik-veri-madenciliginden-buyuk-veriye.md) · [İçindekiler](../ders_notu.md) · [Kısım I Kaynakları →](kisim-1-kaynaklari.md)
