#!/usr/bin/env bash
# FX lab kumesi: Spark, YARN uzerinde calisir (master = yarn)
export JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64
export HADOOP_CONF_DIR=$HOME/bigdata/hadoop/etc/hadoop
# Makinede VPN gibi baska ag arabirimleri de olabilir; Spark yerel ag IP'sini kullansin
export SPARK_LOCAL_IP=$(ip -4 -o addr show | grep -oE '192\.168\.1\.[0-9]+' | head -1)
export PYSPARK_PYTHON=$HOME/bigdata/venv/bin/python
export PYSPARK_DRIVER_PYTHON=${PYSPARK_DRIVER_PYTHON:-$HOME/bigdata/venv/bin/python}
