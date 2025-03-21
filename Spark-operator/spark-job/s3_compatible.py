from pyspark.sql import SparkSession
from pyspark.sql.functions import col, when, upper, year

access_key = "acces_key"
secret_key = "secret_key"
bucket_name = "bucket_name"
endpoint_url = "https://s3-penyedia-layanan.com"

# Buat SparkSession
spark = SparkSession.builder \
    .appName("Book Review Analysis") \
    .getOrCreate()

try:
    file1_key=f"s3://{bucket_name}/books_data.csv"
    file2_key=f"s3://{bucket_name}/Books_rating.csv"

    try:
        df1 = spark.read.csv(file1_key, header=True, inferSchema=True)
        print(f"file 'books_data.csv' berhasil diubah menjadi df1")
        df1.printSchema()

    except Exception as e:
        print(f"Error membaca file 'books_data.csv': {e}")

    try:
        df2 = spark.read.csv(file2_key, header=True, inferSchema=True)
        print(f"file 'Books_rating.csv' berhasil diubah menjadi df2")
        df2.printSchema()

    except Exception as e:
        print(f"Error membaca file 'Books_rating.csv': {e}")
except Exception as e:
    print(f"Terjadi kesalahan : {e}")

# Merge dataframe and drop duplicates data
# books=pd.merge(df1,df2,on="title")
# books.drop_duplicates(inplace = True)

books = df1_final.join(df2_final,['Tittle'],how='inner').distinct()

# Consume important columns (Drop unused columns)
# book = books[['title','review/score','review/text','authors','categories','ratingsCount']]

columns_to_drop = [
    "description", "image", "previewLink", "publisher", "publishedDate", "infoLink", "ratingsCount", "Id", "Price", "User_id", "profileName", "review/helpfulness", "review/time", "review/summary"
]

book = books.drop(*columns_to_drop)

# Redefine column (Renamae column)
df = book.withColumnRenamed("Title", "title") \
            .withColumnRenamed("review/score", "review_per_score") \
            .withColumnRenamed("review/text", "review_per_text") \
            .withColumnRenamed("ratingsCount", "ratings_count")

# Drop null data
df.dropna()

# Show data
df.show(5)

# Store data to Posstgresql
# Define jdbc connection
jdbc_url = "jdbc:postgresql://<host>:<port>/<databaseName>"
jdbc_properties = {
    "user": "<userName>",
    "password": "<password>",
    "driver": "org.postgresql.Driver"
}

# Write to existing table
df.write.jdbc(
    url=jdbc_url,
    table="books",
    mode="overwrite", # atau "append" jika ingin menambahkan data
    properties=jdbc_properties
)

spark.stop()