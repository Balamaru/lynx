from pyspark.sql import SparkSession

spark = SparkSession.builder.appName("ExampleSparkJob").getOrCreate()

data = [("Alice", 25), ("Bob", 30), ("Charlie", 35)]
columns = ["Name", "Age"]
df = spark.createDataFrame(data, columns)

df.show()
df.write.mode("overwrite").csv("/tmp/spark_output")

spark.stop()