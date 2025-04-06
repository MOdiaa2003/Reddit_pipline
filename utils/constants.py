import configparser
import os

parser = configparser.ConfigParser()
parser.read(os.path.join(os.path.dirname(__file__), '../config/config.conf'))

SECRET = parser.get('api_keys', 'reddit_secret_key').strip("[]")
CLIENT_ID = parser.get('api_keys', 'reddit_client_id').strip("[]")

DATABASE_HOST =  parser.get('database', 'database_host')
DATABASE_NAME =  parser.get('database', 'database_name')
DATABASE_PORT =  parser.get('database', 'database_port')
DATABASE_USER =  parser.get('database', 'database_username')
DATABASE_PASSWORD =  parser.get('database', 'database_password')

#AWS
AWS_ACCESS_KEY_ID = parser.get('aws', 'aws_access_key_id').strip("[]")
AWS_ACCESS_KEY = parser.get('aws', 'aws_secret_access_key').strip("[]")
AWS_REGION = parser.get('aws', 'aws_region')
AWS_BUCKET_NAME = parser.get('aws', 'aws_bucket_name').strip("[]")

INPUT_PATH = parser.get('file_paths', 'input_path')
OUTPUT_PATH = parser.get('file_paths', 'output_path')

POST_FIELDS = (
    'id',
    'author',
    'title',
    'subreddit',
    'ups',
    'upvote_ratio',
    'num_comments',
    'score',
    'created_utc',
    'subreddit_subscribers',
    'total_awards_received',
    'num_crossposts',
    'over_18',
    'edited'
)