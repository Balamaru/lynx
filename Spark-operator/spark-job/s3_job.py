import os
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, when, upper, year, to_date

key = os.environ.get('access_key')
secret = os.environ.get('secret_key')

spark = SparkSession.builder \
    .appName("UK Price") \
    .getOrCreate()

s3_path = "s3://file/url/path.csv"

df = spark.read.csv(s3_path, header=True, inferSchema=True)

# Process transform and manipulation data (or data cleansing)
expected_columns = [
    'Transaction_unique_identifier', 'price', 'Date_of_Transfer', 'postcode', 'Property_Type', 'Old_New',
    'Duration', 'PAON', 'SAON', 'Street', 'Locality', 'Town_City', 'District', 'County', 'PPDCategory_Type',
    'Record_Status - monthly_file_only'
]

df = df.select([col(c).alias(expected_columns[i]) for i, c in enumerate(df.columns) if i < len(expected_columns)])

df = df.drop('PPDCategory_Type', 'Record_Status - monthly_file_only')

df = df.withColumn('Date_of_Transfer', to_date(col('Date_of_Transfer')))
df = df.withColumn('year', year(col('Date_of_Transfer')))

#df.show(5)

# Save data to postgresql
jdbc_url = "jdbc:postgresql://<host>:<port>/<databaseName>"
jdbc_properties = {
    "user": "<userName>",
    "password": "<password>",
    "driver": "org.postgresql.Driver"
}

df.write.jdbc(
    url=jdbc_url,
    table="<tableName>", # Nama tabel di PostgreSQL
    mode="Overwrite", # atau "append" jika ingin menambahkan data
    properties=jdbc_properties
)

spark.stop()