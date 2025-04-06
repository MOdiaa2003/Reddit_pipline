import sys
from awsglue.transforms import *
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from awsglue.context import GlueContext
from awsglue.job import Job
from awsgluedq.transforms import EvaluateDataQuality
from pyspark.sql.functions import col, when, lower, trim
from awsglue.dynamicframe import DynamicFrame
from pyspark.sql.types import IntegerType, DoubleType

# Initialize Glue job
args = getResolvedOptions(sys.argv, ['JOB_NAME'])
sc = SparkContext()
glueContext = GlueContext(sc)
spark = glueContext.spark_session
job = Job(glueContext)
job.init(args['JOB_NAME'], args)

# Default data quality ruleset
DEFAULT_DATA_QUALITY_RULESET = """
    Rules = [
        ColumnCount > 0
    ]
"""

# Step 1: Read data from S3
input_frame = glueContext.create_dynamic_frame.from_options(
    format_options={"quoteChar": "\"", "withHeader": True, "separator": ","},
    connection_type="s3",
    format="csv",
    connection_options={"paths": ["s3://reddit-de-project1972/raw/reddit_20250313_10:32:50AM.csv"], "recurse": True},
    transformation_ctx="input_frame"
)

# Step 2: Convert to Spark DataFrame for cleaning
df = input_frame.toDF()

# Fill missing numerical values with median
numerical_cols = ['ups', 'upvote_ratio', 'num_comments', 'score', 'subreddit_subscribers', 'total_awards_received', 'num_crossposts']


# Convert 'created_utc' to timestamp
df = df.withColumn('created_utc', col('created_utc').cast('timestamp'))

# Remove duplicates based on 'id'
df = df.dropDuplicates(['id'])

# Standardize 'subreddit' to lowercase
df = df.withColumn('subreddit', lower(col('subreddit')))

# Strip whitespaces from 'title'
df = df.withColumn('title', trim(col('title')))

# Ensure numerical columns have non-negative values
for col_name in numerical_cols:
    df = df.withColumn(col_name, when(col(col_name) < 0, 0).otherwise(col(col_name)))

# Clip 'upvote_ratio' to [0,1]
df = df.withColumn('upvote_ratio', when(col('upvote_ratio') < 0, 0).when(col('upvote_ratio') > 1, 1).otherwise(col('upvote_ratio')))
df = df.withColumn('ups_bin',when(col('ups') < 20000, 'low')
.when((col('ups') >= 20000) & (col('ups') < 50000), 'medium').otherwise('high'))
# Step 5: Repartition to a single partition for one output file
df = df.coalesce(1)

# Step 6: Convert back to dynamic frame
cleaned_frame = DynamicFrame.fromDF(df, glueContext, "cleaned_frame")

# Step 7: Apply data quality check
EvaluateDataQuality().process_rows(
    frame=cleaned_frame,
    ruleset=DEFAULT_DATA_QUALITY_RULESET,
    publishing_options={"dataQualityEvaluationContext": "data_quality_check", "enableDataQualityResultsPublishing": True},
    additional_options={"dataQualityResultsPublishing.strategy": "BEST_EFFORT", "observations.scope": "ALL"}
)

# Step 8: Write cleaned data to S3 as a single file
glueContext.write_dynamic_frame.from_options(
    frame=cleaned_frame,
    connection_type="s3",
    format="csv",
    connection_options={
        "path": "s3://reddit-de-project1972/Transformed/",
        "partitionKeys": []
    },
    transformation_ctx="output_frame"
)

# Commit the job
job.commit()