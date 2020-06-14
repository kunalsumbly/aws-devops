import boto3
from botocore.exceptions import ClientError
from boto3.dynamodb.conditions import Key, Attr
#import s3bucket_invoiceread

dynamodb = boto3.client('dynamodb','us-east-1')

def create_table():
    print ('\n*************************************************************************')
    print ('Creating table invoice')
    
    try:
        dynamodb.create_table(
                        TableName='invoice',
                        KeySchema=[
                            { 'AttributeName': 'cust_id', 'KeyType': 'HASH' }, # partition key
                            { 'AttributeName': 'inv_id', 'KeyType': 'RANGE' } # sort key
                        ],
                        AttributeDefinitions=[
                            { 'AttributeName': 'cust_id', 'AttributeType': 'S' },
                            { 'AttributeName': 'inv_id', 'AttributeType': 'S' }
                        ],
                        # Planning for capacity units
                        ProvisionedThroughput={ 'ReadCapacityUnits': 1, 'WriteCapacityUnits': 1 }
                ) 

        # Wait until the table exists.
        dynamodb.get_waiter('table_exists').wait(TableName='invoice')
        print (' Table Creation DONE')

        print ('Inserting data in the table')
        dynamodb.put_item(
                TableName='invoice',
                Item={
                        "cust_id": {"S": "21212"},
                        "inv_id": {"S":"121212"},
                        "details": {"S":"TSTSTST"},
                        "csvdtls": {"S":"CSVDETAILS"}
                    }
            )

    except Exception as e:
        print(e)



#s3bucket_invoiceread.readFileFromSrcS3Bucket(s3bucket_invoiceread.s3_src_bucket,s3bucket_invoiceread.s3_src_bucket_filename)
create_table()
 


