# Hadoop + Spark ortam degiskenleri (~/.bashrc icinden okunur)
export JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64
export HADOOP_HOME=$HOME/bigdata/hadoop
export HADOOP_CONF_DIR=$HADOOP_HOME/etc/hadoop
export SPARK_HOME=$HOME/bigdata/spark
export PYSPARK_PYTHON=$HOME/bigdata/venv/bin/python
export PATH=$HOME/bigdata:$HADOOP_HOME/bin:$HADOOP_HOME/sbin:$SPARK_HOME/bin:$PATH
