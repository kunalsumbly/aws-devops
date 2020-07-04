import boto3
from botocore.exceptions import ClientError
from boto3.dynamodb.conditions import Key, Attr

dynamodb = boto3.client('dynamodb','us-east-1')
count=0
def increment_page_visit_count():
    print ('\n*************************************************************************')
    for i in range (5):
        try:
            global count
            count=count+1
            print ('Inserting data in the table')
            dynamodb.put_item(
                    TableName='pagecount',
                    Item={
                            "id":{"N":"1"},
                            "counter": {"N":str(count)}
                        }
            ) 
            

        except Exception as e:
            print(e)

def get_current_page_count():
    try:
        print('Get the current page count')
        response = dynamodb.get_item(
            TableName='pagecount',
            Key={
                    "id": {'N':'1'} # Always need to mention the primary key
                }
        )
    except Exception as e:
        print(e)    
    else:
        return response['Item']

increment_page_visit_count()
print(get_current_page_count())
