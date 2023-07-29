import json
import pandas as pd
import boto3
import logging
import io
from botocore.exceptions import ClientError

def lambda_handler(event, context):
    
    ssm_client = boto3.client('ssm')
    try:
        source_s3_bucket = ssm_client.get_parameter(
            Name="cicd-poc-source-data-bucket"
        )
        processed_s3_bucket = ssm_client.get_parameter(
            Name="cicd-poc-processed-data-bucket"
        )
    except ClientError as e:
        logging.error(e)
        return None
        
        
    source_s3_file_key="taxi_sample_data.csv"
    processed_s3_file_key="taxi_processed_data.csv"
    
    source_file_key="s3://"+source_s3_bucket['Parameter']['Value']+"/"+source_s3_file_key
    processed_file_key="s3://"+processed_s3_bucket['Parameter']['Value']+"/"+processed_s3_file_key
    
    s3_client = boto3.client('s3')
    try:
        print("Reading data from the source bucket - ", source_file_key)
        resp = s3_client.get_object(Bucket=source_s3_bucket['Parameter']['Value'], Key=source_s3_file_key)
  
    except ClientError as e:
        logging.error(e)
        return None    

    source_data_df = pd.read_csv(resp['Body'], sep=',')
    print(source_data_df.head())

    print("Selecting data of VendorId = 1")
    output_df_vendor1 = source_data_df.loc[source_data_df['VendorID'] == 1]
    print(output_df_vendor1.head())
    
    with io.StringIO() as csv_buffer:
        output_df_vendor1.to_csv(csv_buffer, index=False)
        response = s3_client.put_object(Bucket=processed_s3_bucket['Parameter']['Value'], Key=processed_s3_file_key, Body=csv_buffer.getvalue())
        status = response.get("ResponseMetadata", {}).get("HTTPStatusCode")
    
    if status == 200:
        print(f"Data processed Successfully, avaiable on  S3 - ", processed_file_key)
    else:
        print(f"Error in writting the output into the S3 bucket. Status - {status}")
    
    return {
        'statusCode': status,
        'body': json.dumps('Taxi Analyzer Exiting')

    }
