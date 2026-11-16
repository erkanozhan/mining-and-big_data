# 18. Hadoop Kurulumu: Tek Makinede Sözde Dağıtık Mod

Gerçek bir küme kurmadan önce bütün Hadoop servisleri tek bir makinede çalıştırılarak sistem öğrenilebilir. Bu kipe **sözde dağıtık mod (pseudo-distributed mode)** denir: Servisler aynı makinede çalışır, ama birbirleriyle gerçek bir kümedeki gibi ağ üzerinden haberleşir.

## 18.1 İndirme ve Yerleştirme

Hadoop, `.tar.gz` biçiminde sıkıştırılmış bir arşiv olarak dağıtılır. Apache'nin hızlı indirme sunucusu (`dlcdn.apache.org`) yalnızca en güncel sürümleri barındırır; eski sürümler kaldırıldığında bağlantılar çalışmaz hâle gelir. Belirli bir sürüm için kalıcı adres `archive.apache.org/dist` altındadır:

```bash
cd ~/bigdata/indirilen
wget https://archive.apache.org/dist/hadoop/common/hadoop-3.5.0/hadoop-3.5.0.tar.gz
wget https://archive.apache.org/dist/hadoop/common/hadoop-3.5.0/hadoop-3.5.0.tar.gz.sha512
sha512sum -c hadoop-3.5.0.tar.gz.sha512       # "OK" yazmalıdır: dosya bozulmadan inmiştir

cd ~/bigdata
tar xzf indirilen/hadoop-3.5.0.tar.gz         # x: aç, z: gzip, f: dosya adı
ln -s hadoop-3.5.0 hadoop                     # sürümden bağımsız kısa yol
hadoop version                                # Hadoop 3.5.0 yazmalıdır
```

## 18.2 Yapılandırma Dosyaları

Yapılandırma dosyaları `$HADOOP_HOME/etc/hadoop` klasöründedir. Bir XML dosyasında unutulan tek bir kapanış etiketi (`</property>`) veya yanlış yazılmış bir yol, servislerin başlamamasına yol açar. Aşağıdaki dosyalarda `<configuration>` öğesinin **tam içeriği** verilmiştir; dosyadaki boş `<configuration></configuration>` öğesi bununla değiştirilmelidir.

**`hadoop-env.sh`** dosyasının sonuna Java'nın yolu eklenir. Hadoop servisleri SSH ile başlatıldığında `.bashrc` okunmayabileceği için bu satır gereklidir:

```bash
export JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64
```

**`core-site.xml`:** Varsayılan dosya sistemini, yani NameNode'un adresini belirtir. NameNode bu makinede 9000 numaralı portu dinleyecektir.

```xml
<configuration>
    <property>
        <name>fs.defaultFS</name>
        <value>hdfs://localhost:9000</value>
    </property>
    <property>
        <name>hadoop.tmp.dir</name>
        <value>/home/hduser/bigdata/veri/tmp</value>
    </property>
</configuration>
```

**`hdfs-site.xml`:** Kopya sayısını ve NameNode ile DataNode verilerinin diskte nerede tutulacağını belirtir. Hadoop varsayılan olarak her bloğun 3 kopyasını tutar; tek makinede kopyaların yerleştirilebileceği başka düğüm olmadığı için bu değer 1'e indirilir. İndirilmezse bütün bloklar "eksik kopyalı" (under-replicated) olarak raporlanır.

```xml
<configuration>
    <property>
        <name>dfs.replication</name>
        <value>1</value>
    </property>
    <property>
        <name>dfs.namenode.name.dir</name>
        <value>file:///home/hduser/bigdata/veri/namenode</value>
    </property>
    <property>
        <name>dfs.datanode.data.dir</name>
        <value>file:///home/hduser/bigdata/veri/datanode</value>
    </property>
</configuration>
```

**`mapred-site.xml`:** MapReduce işlerinin YARN üzerinde çalışacağını ve MapReduce kütüphanelerinin nerede olduğunu belirtir. İkinci özellik eksik olursa ilk iş, `MRAppMaster` sınıfının bulunamadığını bildiren bir hatayla başarısız olur.

```xml
<configuration>
    <property>
        <name>mapreduce.framework.name</name>
        <value>yarn</value>
    </property>
    <property>
        <name>mapreduce.application.classpath</name>
        <value>$HADOOP_MAPRED_HOME/share/hadoop/mapreduce/*:$HADOOP_MAPRED_HOME/share/hadoop/mapreduce/lib/*</value>
    </property>
</configuration>
```

**`yarn-site.xml`:** Map ve reduce aşamaları arasındaki veri aktarımını (shuffle) sağlayan yardımcı servisi etkinleştirir ve konteynerlere aktarılacak ortam değişkenlerini listeler.

```xml
<configuration>
    <property>
        <name>yarn.nodemanager.aux-services</name>
        <value>mapreduce_shuffle</value>
    </property>
    <property>
        <name>yarn.nodemanager.env-whitelist</name>
        <value>JAVA_HOME,HADOOP_COMMON_HOME,HADOOP_HDFS_HOME,HADOOP_CONF_DIR,CLASSPATH_PREPEND_DISTCACHE,HADOOP_YARN_HOME,HADOOP_HOME,PATH,LANG,TZ,HADOOP_MAPRED_HOME</value>
    </property>
</configuration>
```

## 18.3 Biçimlendirme ve Başlatma

HDFS ilk kullanımdan önce **bir kez** biçimlendirilir. Bu komut NameNode'un boş meta veri yapısını oluşturur. Veri içeren bir sistemde tekrarlanırsa mevcut bütün veriye erişim kaybedilir.

```bash
hdfs namenode -format
```

Çıktıda "Storage directory … has been successfully formatted" ifadesi görülmelidir. Ardından servisler başlatılır ve çalışan Java süreçleri `jps` (Java Process Status) komutuyla listelenir:

```bash
start-dfs.sh          # NameNode, DataNode, SecondaryNameNode
start-yarn.sh         # ResourceManager, NodeManager
jps
```

`jps` çıktısında **NameNode, DataNode, SecondaryNameNode, ResourceManager, NodeManager** (ve `Jps`'in kendisi) görülmelidir. Bunlardan biri eksikse, o servisin `$HADOOP_HOME/logs` klasöründeki günlük dosyası incelenmelidir.

Hadoop, kümenin durumunu izlemek için web arayüzleri sunar:

| Arayüz | Adres | Ne gösterir? |
|---|---|---|
| HDFS NameNode | http://localhost:9870 | Canlı DataNode'lar, disk doluluğu, dosyalar ve bloklar |
| YARN ResourceManager | http://localhost:8088 | Çalışan ve biten uygulamalar, düğümlerin kaynak kullanımı |

NameNode arayüzündeki "Live Nodes" değeri 1 ise kurulum başarılıdır. Çalışma bitince servisler ters sırayla kapatılır:

```bash
stop-yarn.sh
stop-dfs.sh
```

## 18.4 Sorun Giderme

Bir servis başlamıyorsa ilk bakılacak yer, `$HADOOP_HOME/logs` klasöründeki ilgili günlük dosyasıdır. Hata mesajlarını dikkatle okumak, dağıtık sistemlerde sorun çözmenin en önemli alışkanlığıdır. Sık karşılaşılan sorunlar şunlardır:

| Belirti | Sebep | Çözüm |
|---|---|---|
| `start-dfs.sh` parola soruyor veya bağlanamıyor | Parolasız SSH eksik | Bölüm 17.2'deki adımlar ve `chmod 600 ~/.ssh/authorized_keys` |
| `rcmd: socket: Permission denied` | Sistemde `pdsh` kurulu; Hadoop betikleri SSH yerine pdsh kullanır, pdsh'ın varsayılan bağlantı türü ise `rsh`'tır | `ortam.sh` dosyasına `export PDSH_RCMD_TYPE=ssh` eklemek veya `pdsh`'ı kaldırmak |
| `JAVA_HOME is not set` | `hadoop-env.sh` içinde Java yolu yok | Bölüm 18.2'deki `export JAVA_HOME=...` satırı |
| DataNode başlamıyor; günlükte `Incompatible clusterIDs` | NameNode yeniden biçimlendirilmiş, DataNode klasöründe eski kümenin kimliği kalmış | Servisleri durdurup `~/bigdata/veri/datanode` klasörünü boşaltmak, sonra yeniden başlatmak (içindeki veri silinir) |
| İşçi makinedeki DataNode yöneticiye bağlanamıyor | Güvenlik duvarı portları engelliyor | Aşağıdaki güvenlik duvarı kuralları |

**Güvenlik duvarı.** Tek makinede servisler birbirine `localhost` üzerinden bağlandığı için güvenlik duvarı sorun çıkarmaz. Çok makineli kümede ise Hadoop servisleri birbirleriyle çok sayıda porttan konuşur: NameNode 9000 (RPC) ve 9870 (web), DataNode 9866 (veri aktarımı), 9867 (IPC) ve 9864 (web), SecondaryNameNode 9868, ResourceManager 8030–8033 ve 8088 (web), NodeManager 8040 ve 8042 (web), MapReduce shuffle 13562, JobHistory 10020 ve 19888. Ayrıca NodeManager'ların ve ApplicationMaster'ların kullandığı bazı portlar her çalıştırmada rastgele seçilir. Bu yüzden portları tek tek açmak yerine, `ufw` etkinse her makinede **yalnızca küme üyelerinden** gelen bağlantılara izin verilir:

```bash
sudo ufw status                                         # etkin mi, hangi kurallar var?
sudo ufw allow from 192.168.1.10 comment "hadoop kume"  # her makinede, diğer her küme üyesi için tekrarlanır
sudo ufw allow from 192.168.1.11 comment "hadoop kume"
```

Güvenlik duvarını kapatmak veya bütün portları herkese açmak, ağdaki herkesin HDFS'e erişebilmesi demektir; bu yüzden önerilmez.

## 18.5 Çok Düğümlü Kümeye Geçiş

Tek makinede çalışan kurulum, birkaç ek adımla iki veya daha fazla makineli bir kümeye dönüştürülebilir. Aşağıda bir yönetici (`master-node`, 192.168.1.10) ve bir işçi (`worker-node`, 192.168.1.11) makine örnek alınmıştır. Üç makineli gerçek laboratuvar kümesinin bütün dosyaları ve karşılaşılan sorunlar ek notta ayrıntılı olarak anlatılmıştır: [Kurulum: Adım Adım](../spark_ders_notu.md#5-kurulum-adım-adım).

1. **İşçi makinenin hazırlanması:** İşçi makinede de Bölüm 17.1 ve 17.2'deki adımlar uygulanır: aynı kullanıcı adı (`hduser`), aynı Java sürümü ve `openssh-server`. Hadoop'un başlatma betikleri diğer makinelerde aynı yolları aradığı için klasör düzeni de aynı olmalıdır.
2. **Ad çözümleme:** Her makinenin `/etc/hosts` dosyasına bütün küme üyeleri eklenir. Ubuntu, makinenin kendi adını `127.0.1.1` adresine bağlayan bir satır ekler; bu satır kaldırılmalı veya makine adı gerçek IP adresine bağlanmalıdır. Aksi hâlde servis kendini geri döngü adresiyle tanıtır ve diğer makineler ona ulaşamaz.

   ```text
   192.168.1.10   master-node
   192.168.1.11   worker-node
   ```

3. **Yöneticiden işçiye parolasız SSH:** Yöneticinin açık anahtarı işçinin `authorized_keys` dosyasına eklenir ve bağlantı denenir:

   ```bash
   ssh-copy-id -i ~/.ssh/id_ed25519.pub hduser@worker-node
   ssh worker-node hostname            # parola sormadan "worker-node" yazmalıdır
   ```

4. **Yapılandırma değişiklikleri (yöneticide):**
   * `core-site.xml`: `fs.defaultFS` değeri `hdfs://master-node:9000` olur.
   * `yarn-site.xml`: ResourceManager'ın adresi eklenir: `<property><name>yarn.resourcemanager.hostname</name><value>master-node</value></property>`.
   * `hdfs-site.xml`: Artık iki DataNode olduğu için `dfs.replication` değeri 2 yapılabilir.
   * `workers` dosyası: DataNode ve NodeManager çalışacak makinelerin listesidir. `localhost` satırı silinir; yönetici de işçi olarak çalışacaksa her iki ad yazılır:

     ```text
     master-node
     worker-node
     ```

5. **Dağıtma:** Yönetici makinedeki `~/bigdata` klasörü, veri ve indirme klasörleri hariç işçiye kopyalanır; `ortam.sh` da işçinin `.bashrc` dosyasına bağlanır:

   ```bash
   rsync -a --exclude veri --exclude indirilen ~/bigdata/ worker-node:bigdata/
   ssh worker-node 'mkdir -p ~/bigdata/veri && echo ". \$HOME/bigdata/ortam.sh" >> ~/.bashrc'
   ```

6. **Başlatma ve doğrulama:** Tek makineli kurulumda biçimlendirilmiş bir NameNode varsa, servisler durdurulup yöneticinin `~/bigdata/veri` klasörü boşaltılır ve NameNode yönetici makinede bir kez yeniden biçimlendirilir. Ardından servisler **yalnızca yönetici makineden** başlatılır; betikler `workers` dosyasındaki makinelere SSH ile bağlanarak ilgili servisleri orada başlatır:

   ```bash
   hdfs namenode -format              # yalnızca ilk kurulumda, yalnızca yöneticide
   start-dfs.sh
   start-yarn.sh
   hdfs dfsadmin -report | grep "Live datanodes"     # Live datanodes (2) görülmelidir
   yarn node -list                                    # iki NodeManager RUNNING olmalıdır
   ```

---

[← 17. Kurulum Ortamının Hazırlanması](17-kurulum-ortaminin-hazirlanmasi.md) · [İçindekiler](../ders_notu.md) · [19. Uygulama: İlk MapReduce İşi (WordCount) →](19-ilk-mapreduce-isi-wordcount.md)
