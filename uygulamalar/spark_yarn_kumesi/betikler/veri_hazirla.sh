#!/bin/bash
# Uygulamaların kullandığı verileri indirir/üretir ve HDFS'e koyar.
# Kullanım (uygulama klasöründen):  bash betikler/veri_hazirla.sh
set -e
. "$HOME/bigdata/ortam.sh"
cd "$(dirname "$0")/.."
GECICI=$(mktemp -d)
trap 'rm -rf "$GECICI"' EXIT

hdfs dfs -mkdir -p /veri /cikti

# --- 1) Kelime sayma için Project Gutenberg kitapları (Uygulama 3) ---------------------------
# 20 klasik eser (~20 MB) indirilir ve 25 kopya hâlinde HDFS'e konur (~500 MB). Kopyalar,
# "büyük" bir metin derlemi elde etmenin ucuz yoludur; kelime sıklıkları değişmez, yalnızca ölçeklenir.
if ! hdfs dfs -test -d /veri/kitaplar; then
    echo "== Kitaplar indiriliyor"
    for no in 1342 11 84 2701 1661 98 74 76 345 2600 1952 5200 174 1400 2554 64317 4300 205 1260 1080; do
        curl -sfL "https://www.gutenberg.org/cache/epub/$no/pg$no.txt" -o "$GECICI/pg$no.txt"
        sleep 1    # Gutenberg sunucusuna nazik davranalım
    done
    cat "$GECICI"/pg*.txt > "$GECICI/kitaplar.txt"
    hdfs dfs -mkdir -p /veri/kitaplar
    for i in $(seq -w 1 25); do
        hdfs dfs -put "$GECICI/kitaplar.txt" "/veri/kitaplar/kopya_$i.txt"
    done
fi

# --- 2) UCI Covertype veri seti (Uygulama 4) ------------------------------------------------
if ! hdfs dfs -test -e /veri/covtype/covtype.data; then
    echo "== Covertype indiriliyor"
    curl -sfL https://archive.ics.uci.edu/static/public/31/covertype.zip -o "$GECICI/covertype.zip"
    unzip -q -o "$GECICI/covertype.zip" -d "$GECICI"
    gunzip -f "$GECICI/covtype.data.gz"
    hdfs dfs -mkdir -p /veri/covtype
    hdfs dfs -put "$GECICI/covtype.data" /veri/covtype/
fi

# --- 3) 1BRC ölçüm verisi: küme üzerinde Spark ile üretilir (Uygulama 1) ----------------------
if ! hdfs dfs -test -d /veri/olcumler_csv; then
    echo "== 100 milyon satırlık ölçüm verisi üretiliyor"
    spark-submit python/01_olcum_verisi_uret.py 100000000
fi

echo "== HDFS'teki veriler"
hdfs dfs -du -h /veri
