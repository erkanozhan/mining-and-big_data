# 17. Kurulum Ortamının Hazırlanması

Bu bölümden itibaren Hadoop'u ve Spark'ı kendi bilgisayarımıza kuracağız. Bütün kurulum, ek notta anlatılan laboratuvar kümesiyle aynı sürümleri ve aynı klasör düzenini kullanır:

| Bileşen | Sürüm | Not |
|---|---|---|
| İşletim sistemi | Ubuntu 22.04 LTS veya 24.04 LTS | Laboratuvar kümesinde Ubuntu tabanlı Linux Mint 22 kullanılmıştır |
| Java | OpenJDK 17 | Hadoop 3.5 ve Spark 4.x için gereklidir |
| Hadoop | 3.5.0 | |
| Spark | 4.1.3 (Hadoop 3 için derlenmiş paket) | |
| Kullanıcı ve klasör | `hduser`, `~/bigdata` | Bütün yazılımlar kullanıcının ev dizinine kurulur |

## 17.1 Sanal Makinenin Hazırlanması

Bir sistemi öğrenmenin en güvenli yolu, onu ana bilgisayardan yalıtılmış bir ortamda denemektir. Bu yüzden kurulumu bir **sanal makinede (virtual machine)** yapacağız. **Sanallaştırma (virtualization)**, bir bilgisayarın içinde, kendi işletim sistemi olan ikinci bir sanal bilgisayar çalıştırmaktır. Ana bilgisayarın işletim sistemi Windows, macOS veya Linux olabilir.

**Gerekli dosyalar:**

1. **Sanallaştırma yazılımı (hypervisor):** Ana bilgisayarın donanımını (işlemci, bellek, disk) sanal makineyle paylaştıran yazılımdır. Ücretsiz ve yaygın olduğu için **Oracle VirtualBox** kullanılacaktır.
2. **İşletim sistemi kalıbı (ISO dosyası):** Sanal makineye takılacak "sanal DVD"dir. Ubuntu'nun web sitesinden **LTS (Long Term Support, uzun süreli destek)** ibaresi taşıyan bir masaüstü sürümü (22.04 veya 24.04) indirilmelidir. Ara sürümler daha yeni özellikler içerse de kısa süre desteklenir; bu ders için kararlılık yenilikten daha önemlidir.

> **BIOS/UEFI ayarı:** VirtualBox sanal makineyi başlatırken hata veriyorsa, en sık sebep bilgisayarın BIOS/UEFI ayarlarında **donanım sanallaştırmasının (Intel VT-x veya AMD-V)** kapalı olmasıdır. Bilgisayar yeniden başlatılıp BIOS ekranında bu özellik etkinleştirilmelidir; aksi hâlde 64 bitlik bir sanal makine çalıştırılamaz.

**Sanal makinenin oluşturulması:**

* **Bellek ve işlemci:** Hadoop ve Spark bellek ister, ama ana bilgisayarı da kaynaksız bırakmamak gerekir. 16 GB belleği olan bir bilgisayarda sanal makineye 4–6 GB, 8 GB belleği olan bir bilgisayarda en fazla 4 GB verilmelidir. En az 2 işlemci çekirdeği ayrılması önerilir.
* **Sanal disk:** VDI biçiminde ve **dinamik olarak ayrılan (dynamically allocated)** bir disk seçilmelidir. Bu tür disk, ayrılan boyuta (ör. 50 GB) kadar ihtiyaç oldukça büyür; başlangıçta yalnızca kullanılan alan kadar yer kaplar. Disk boyutu en az 40–50 GB olmalıdır.

**Ubuntu kurulumu:** Sanal makinenin *Ayarlar > Depolama* bölümünden ISO dosyası sanal optik sürücüye takılır ve makine başlatılır. Kurulumda şu noktalara dikkat edilmelidir:

* **Dil:** Sistem dilinin İngilizce seçilmesi önerilir. Hata mesajları İngilizce olduğunda internette yapılan aramalar çok daha isabetli sonuç verir.
* **Disk yapılandırması:** "Erase disk and install Ubuntu" seçeneği yalnızca sanal makineye ayrılan sanal diski biçimlendirir; ana bilgisayardaki dosyalara dokunmaz.
* **Kullanıcı adı:** Kullanıcı adı olarak `hduser` girilmelidir. Bu notta ve ek notta bütün yollar `/home/hduser` üzerinden verilmiştir.

**Anlık görüntü (snapshot):** Kurulum bittikten ve sistem ilk kez güncellendikten sonra VirtualBox'ta makinenin bir anlık görüntüsü alınmalı ve örneğin "Temiz kurulum" diye adlandırılmalıdır. İleride bir yapılandırma hatası sistemi kullanılamaz hâle getirirse, makine tek adımda bu ana geri döndürülebilir.

> **Linux kullanan bilgisayarlar için not:** Bilgisayarında zaten Linux kurulu olanlar da kurulumu bir sanal makinede yapmayı tercih etmelidir. Kurulum sırasında `/etc/hosts` ve `.bashrc` gibi sistem dosyalarında değişiklik yapılır; yalıtılmış bir ortamda (sandbox, "kum havuzu") çalışmak ana sistemi koruma altına alır. Mevcut bir Linux sisteminde çalışılacaksa önce `sudo adduser hduser` komutuyla ayrı bir kullanıcı oluşturulmalı ve sonraki bütün adımlar `su - hduser` ile bu kullanıcıya geçildikten sonra yapılmalıdır.

## 17.2 Java ve SSH

Hadoop ve Spark Java ile yazılmıştır ve Java Sanal Makinesi (JVM) üzerinde çalışır. Hadoop'un başlatma betikleri ise servisleri, tek makinede bile, **SSH (Secure Shell)** ile bağlanarak başlatır. Bu yüzden önce bu iki bileşen kurulmalıdır:

```bash
sudo apt update && sudo apt upgrade -y         # paket listesini ve sistemi güncelle
sudo apt install -y openjdk-17-jdk openssh-server
java -version                                   # çıktıda 'openjdk version "17...' görülmelidir
readlink -f "$(which java)"                     # Java'nın kurulduğu gerçek yol
```

Sistemde birden fazla Java sürümü kuruluysa etkin sürüm `sudo update-alternatives --config java` komutuyla seçilir.

**Parolasız SSH.** Başlatma betiklerinin her seferinde parola sormadan bağlanabilmesi için bir anahtar çifti oluşturulur ve açık anahtar, "güvenilen anahtarlar" listesine eklenir:

```bash
ssh-keygen -t ed25519 -N "" -f ~/.ssh/id_ed25519    # parolasız anahtar çifti
cat ~/.ssh/id_ed25519.pub >> ~/.ssh/authorized_keys  # açık anahtarı güvenilenlere ekle
chmod 600 ~/.ssh/authorized_keys                     # SSH, başkalarının yazabildiği dosyayı reddeder
ssh localhost                                        # parola sorulmamalıdır; çıkmak için: exit
```

İlk bağlantıda sunucunun tanınmadığına dair bir soru gelir; `yes` yazılarak devam edilir. Parola hâlâ soruluyorsa `authorized_keys` adımı ve dosya izinleri kontrol edilmelidir. Bu adım çalışmazsa Hadoop servisleri de başlatılamaz.

## 17.3 Klasör Düzeni ve Ortam Değişkenleri

Bütün yazılımlar `~/bigdata` klasörüne kurulur. Sürüm numaralı klasörlere sürümden bağımsız kısa yollar (sembolik bağlantı) verilir; ileride yeni bir sürüme geçmek yalnızca bağlantıyı değiştirmekten ibaret olur. Ortam değişkenleri tek bir `~/bigdata/ortam.sh` dosyasında toplanır:

```bash
mkdir -p ~/bigdata/indirilen ~/bigdata/veri
nano ~/bigdata/ortam.sh
```

```bash
export JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64
export HADOOP_HOME=$HOME/bigdata/hadoop
export HADOOP_CONF_DIR=$HADOOP_HOME/etc/hadoop
export SPARK_HOME=$HOME/bigdata/spark
export PYSPARK_PYTHON=python3
export PATH=$HADOOP_HOME/bin:$HADOOP_HOME/sbin:$SPARK_HOME/bin:$PATH
```

Dosya kaydedilir (nano'da `Ctrl+O`, `Enter`, çıkmak için `Ctrl+X`) ve her yeni terminalde okunması için `~/.bashrc` dosyasına bağlanır:

```bash
echo '. "$HOME/bigdata/ortam.sh"' >> ~/.bashrc
source ~/.bashrc
echo $HADOOP_HOME                      # /home/hduser/bigdata/hadoop yazmalıdır
```

`JAVA_HOME` yolu, bir önceki adımda `readlink` komutunun gösterdiği yoldan sondaki `/bin/java` kısmı çıkarılarak doğrulanabilir.

---

[← 16. Hadoop Ekosistemi](16-hadoop-ekosistemi.md) · [İçindekiler](../ders_notu.md) · [18. Hadoop Kurulumu: Tek Makinede Sözde Dağıtık Mod →](18-hadoop-kurulumu.md)
