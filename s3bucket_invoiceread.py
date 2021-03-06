#
# please configure aws cli before using this program
#
import os, traceback, sys
from bottle import Bottle, request, post, response, static_file, run
from os import path
import json
import boto3
import datetime

listeningPort = "9098"
app = Bottle()
s3 = boto3.client('s3')
s3_target_bucket = 'great-learning-athena-target-bucket-kusu'
dynamodb = boto3.client('dynamodb','us-east-1')
s3_src_bucket = 'great-learning-invoices-upload-bucket-kusu'
s3_src_bucket_filename='invoices/docproc-invoice.txt'

# This method reads the data from S3 bucket
def readFileFromSrcS3Bucket(bucket,filename):
    with open('invoice.txt', 'wb') as f:
        # param 1 is the bucket name great-learning-invoices-customer-bucket-kusu
        # param2 is the file inside a folder : invoices folder and docproc-invoice.txt
        print('bucketName='+bucket)
        print('fileName='+filename)
        #s3.download_fileobj('great-learning-invoices-customer-bucket-kusu', 'invoices/docproc-invoice.txt', f)
        s3.download_fileobj(bucket, filename, f) # needs aws cli
        #Initialize to some default values which should be overwritten by the values from the invoice file
    cust_id = 'def'
    inv_id = 'def_001'
    line = ''
    file_content = ''
    #The below logic is needed because the content object returns 1 char at a time
    with open('invoice.txt', 'r', encoding='utf-8') as content: # wb means write binary data
        for currLine in content:
            for ch in currLine:
                file_content+=ch
                if ch == '\n':
                    print ('Line-> '+line)
                    if "Customer-ID:" in line:
                        cust_id = line.split(':')[1].strip()
                        print ('  Found Customer-ID '+ cust_id)
                    elif "Inv-ID:" in line:
                        inv_id = line.split(':')[1].strip()
                        print ('  Found Invoice-ID '+ inv_id)
                    line = ''
                else:
                    line += ch
                    

    #Insert to dynamo and push to kinesis stream
    try:
        parse_content =transform_content(cust_id, inv_id)
        print ('CSV ->'+ parse_content)
        insert_dynamodb(cust_id, inv_id, file_content, parse_content)
        write_to_target_bucket(cust_id, inv_id, parse_content)
    except:
        print(traceback.format_exc())

#TBD Need to conver the invoice to a CSV, care -> the data can have comma
def transform_content(cust_id, inv_id):
    line=''  
    dated=''  
    fromcust=''  
    tocust=''  
    amt='' 
    sgst='' 
    tot='' 
    words=''
    with open('invoice.txt', 'r', encoding='utf-8') as content: 
        for currLine in content:
            for one_char in currLine:
                if one_char == '\n':
                    if "Dated:" in line:
                        dated = line.split(":")[1]
                        print ('  Found dated '+ dated)
                    elif "From:" in line:
                        fromcust = line.split(":")[1]
                        print ('  Found fromcust '+ fromcust)
                    elif "To:" in line:
                        tocust = line.split(":")[1]
                        print ('  Found tocust '+tocust)
                    elif "Amount:" in line:
                        amt = line.split(":")[1]
                        print ('  Found amt '+ amt)
                    elif "SGST:" in line:
                        sgst = line.split(":")[1]
                        print ('  Found sgst '+ sgst)
                    elif "Total:" in line:
                        tot = line.split(":")[1]
                        print ('  Found tot '+ tot)
                    elif "InWords:" in line:
                        words = line.split(":")[1]
                        print ('  Found words '+ words)
                    line = ''
                else:
                    line += one_char

    return cust_id + "," + inv_id + "," + dated + "," + fromcust + "," + tocust + "," + amt + "," + sgst + "," + tot + "," + words

# this method is called when any request is posted to /sns endpoint
@app.route('/sns', method=['POST'])
def postJsonData():
    printRequestHeaders(request)
    #comments = request.json    # use this when content-type is application/json set by client
    json_response_message_body = json.load(request.body) # this is for content-type application
    if (json_response_message_body == None):
      return 'No data found in the POST body'
    
    sns_message_type_header = dict(request.headers)['X-Amz-Sns-Message-Type']
    
    if (sns_message_type_header == None):
        raise Exception('SNS message Type Header not found in the POST request')
    if (sns_message_type_header == 'SubscriptionConfirmation'):
        print('This is an SNS subscription message, we need to get the SubscribeURL  from the body')
        print('SubscribeURL:::::::::'+json_response_message_body['SubscribeURL'])
    elif (sns_message_type_header == 'Notification'):
        print('This is an SNS Notification message')
        bucket = json_response_message_body['Records'][0]['s3']['bucket']['name']
        filename = json_response_message_body['Records'][0]['s3']['object']['key']
        print ('Will read the file %s from the bucket %s',filename, bucket)
        readFileFromSrcS3Bucket(bucket,filename)

    elif (sns_message_type_header == 'UnsubscribeConfirmation'):
        print('This is an SNS unsubscription message')
    
    return 'API invoked; your http record is now saved.'
    
# this method prints all the headers in the request
def printRequestHeaders(request):
    print(dict(request.headers))    


def write_to_target_bucket(cust_id, inv_id,  xform_content):
    now = datetime.datetime.now()
    prefix_val = str(now.microsecond) + str(now.second)
    object_key = prefix_val + '_' + cust_id + '_' + inv_id + '.csv'
    print ("Written new s3 file"+object_key)
    print ("Uploading S3 object content"+xform_content)
    s3 = boto3.client('s3')
    s3.put_object(Bucket=s3_target_bucket, Key=object_key, Body=xform_content.encode())
    print ("Done")

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

    except Exception as e:
        print(e)

def insert_data(cust_id, inv_id, content, xform_content):
    print('**********Insert Started********')
    dynamodb.put_item(
        TableName='invoice',
        Item={
                "cust_id": {"S": cust_id},
                "inv_id": {"S":inv_id},
                "details": {"S":content},
                "csvdtls": {"S":xform_content}
            }
        )
    print('**********Insert Done************')


def insert_dynamodb(cust_id, inv_id, content, xform_content):
    create_table()
    insert_data(cust_id, inv_id, content, xform_content)



if __name__ == '__main__':
    port = int(os.environ.get('PORT', listeningPort))
    run(app,host="0.0.0.0", port=port, debug=True)
    



