#
# please configure aws cli before using this program
#
import os, traceback, sys
from bottle import Bottle, request, post, response,run
from os import path
import json
import boto3
import datetime

listeningPort = "9098"
app = Bottle()
dynamodb = boto3.client('dynamodb','us-east-1')
counter_table = 'persondatacounter'
missing_person_table = 'personrecords'
@app.hook('after_request')
def enable_cors():
    """
    You need to add some headers to each request.
    Don't use the wildcard '*' for Access-Control-Allow-Origin in production.
    """
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'PUT, GET, POST, DELETE, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Origin, Accept, Content-Type, X-Requested-With, X-CSRF-Token'

@app.route('/upload', method=['POST'])
def uploadPersonData():
    printRequestHeaders(request)
    json_response_message_body = json.load(request.body)
    try:
        image = json_response_message_body['image']
        missing_person_data = json_response_message_body['missingpersondata']
        
        # implement auto increment here
        person_record_pk_id=incrementPersonRecordCounter(); 

        response = dynamodb.put_item(
                        TableName=missing_person_table,
                        Item = {
                                "person_record_id":{"N":person_record_pk_id},
                                "firstname": {"S":missing_person_data['firstname']},
                                "lastname": {"S":missing_person_data['lastname']},
                                "dateofbirth": {"S":missing_person_data['dateofbirth']},
                                "missingfromlocation": {"S":missing_person_data['missingfromlocation']},
                                "age": {"S":str(missing_person_data['age'])},
                                "familycontactphone": {"S":str(missing_person_data['familycontactphone'])},
                                "reportingcentrecontact": {"S":missing_person_data['reportingcentrecontact']}
                                }
                    )

        return {
            "statusCode": 200,
            "headers": {
                "Access-Control-Allow-Origin": "*",
                "Content-Type": "application/json"
            },
            "body": json.dumps({
                "message": "Success. Face recorded"
            }),
        }
    except Exception as e:
        print(e)
        return {
            "statusCode": 500,
            "headers": {
                "Access-Control-Allow-Origin": "*",
                "Content-Type": "application/json"
            },
            "body": json.dumps({
                "message": "Error: {}".format(e),
            }),
        }

# This method will increment the person record counter
def incrementPersonRecordCounter() :
    response= dynamodb.update_item (
                TableName=counter_table,
                Key={
                        "counterName":{"S":"personRecordCounter"}
                    },
                UpdateExpression="SET #v = #v + :a",
                ExpressionAttributeNames={ "#v": "currentValue" },
                ExpressionAttributeValues={
                     ":a": {"N":"1"}
                },
                ReturnValues='UPDATED_NEW'
            )
    return response['Attributes']['currentValue']['N']

@app.route('/search', method=['POST'])
def searchImage():
    json_response_message_body = json.load(request.body)
    try:
        image = json_response_message_body['image']
        db_response=findPersonDataByFaceId('61cb1187-0d70-4e4e-85c5-10266c6a7694')
        payload=db_response['Item']
        firstname = [*payload['firstname'].values()]
        lastname=[*payload['lastname'].values()]
        lastseendate=[*payload['dateofreport'].values()]
        lastseenlocation=[*payload['missingfromlocation'].values()]
        message = firstname[0]+","+lastname[0]+" , missing since="+lastseendate[0]+", from location="+lastseenlocation[0]
        return {
            "statusCode": 200,
            "headers": {
                "Access-Control-Allow-Origin": "*",
                "Content-Type": "application/json"
            },
            "body": json.dumps({
                "message": "Succeed to find"+message
            }),
        }

    except Exception as e:
        print(e)
        return {
            "statusCode": 500,
            "headers": {
                "Access-Control-Allow-Origin": "*",
                "Content-Type": "application/json"
            },
            "body": json.dumps({
                "message": "Error: {}".format(e),
            }),
        }

def findPersonDataByFaceId(faceId):
    response = dynamodb.get_item (
                TableName=missing_person_table,
                    Key={
                        "faceid" :{"S":faceId}
                    }
            )
    return response        

def printRequestHeaders(request):
    print(dict(request.headers)) 

if __name__ == '__main__':
    port = int(os.environ.get('PORT', listeningPort))
    run(app,host="0.0.0.0", port=port, debug=True)