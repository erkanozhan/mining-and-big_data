"""Uygulama betiklerinin ortak yardımcıları (yalnızca sürücü/driver tarafında çalışır)."""

import json
import time
from pathlib import Path

CIKTILAR = Path(__file__).resolve().parent.parent / "ciktilar"
SONUC_DOSYASI = CIKTILAR / "sonuclar.json"

# HDFS'teki veri yolları (betikler/veri_hazirla.sh bu yollara yazar)
OLCUM_CSV = "hdfs:///veri/olcumler_csv"
OLCUM_PARQUET = "hdfs:///veri/olcumler_parquet"
KITAPLAR = "hdfs:///veri/kitaplar"
COVTYPE = "hdfs:///veri/covtype/covtype.data"


def hdfs_boyut(spark, yol):
    """Bir HDFS dosyasının/klasörünün bayt cinsinden boyutu (tek kopya için)."""
    jvm = spark._jvm
    p = jvm.org.apache.hadoop.fs.Path(yol)
    fs = p.getFileSystem(spark._jsc.hadoopConfiguration())
    return fs.getContentSummary(p).getLength()


def hdfs_var_mi(spark, yol):
    jvm = spark._jvm
    p = jvm.org.apache.hadoop.fs.Path(yol)
    return p.getFileSystem(spark._jsc.hadoopConfiguration()).exists(p)


def sonuc_kaydet(anahtar, veri):
    """Ölçüm sonuçlarını ciktilar/sonuclar.json içinde `anahtar` altına yazar."""
    CIKTILAR.mkdir(exist_ok=True)
    tum = json.loads(SONUC_DOSYASI.read_text(encoding="utf-8")) if SONUC_DOSYASI.exists() else {}
    tum[anahtar] = veri
    SONUC_DOSYASI.write_text(json.dumps(tum, indent=2, ensure_ascii=False), encoding="utf-8")


class Kronometre:
    """`with Kronometre("iş adı") as k:` bloğunun süresini ölçer; süre k.sn içindedir."""

    def __init__(self, ad):
        self.ad = ad

    def __enter__(self):
        self.t0 = time.perf_counter()
        return self

    def __exit__(self, *_):
        self.sn = time.perf_counter() - self.t0
        print(f"[süre] {self.ad}: {self.sn:.1f} sn")
