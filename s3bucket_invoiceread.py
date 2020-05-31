#
# please configure aws cli before using this program
#

import boto3, sys, traceback

s3 = boto3.client('s3')
with open('invoice.txt', 'wb') as f:
    # param 1 is the bucket name great-learning-invoices-customer-bucket-kusu
    # param2 is the file inside a folder : invoices folder and docproc-invoice.txt
    s3.download_fileobj('great-learning-invoices-customer-bucket-kusu', 'invoices/docproc-invoice.txt', f)

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

#obj = s3.Object('great-learning-invoices-customer-bucket-kusu', 'invoices/docproc-invoice.txt')

#Initialize to some default values which should be overwritten by the values from the invoice file
cust_id = 'def'
inv_id = 'def_001'
line = ''
#The below logic is needed because the content object returns 1 char at a time
with open('invoice.txt', 'r', encoding='utf-8') as content: # wb means write binary data
    for currLine in content:
        for ch in currLine:
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
except:
     print(traceback.format_exc())
    



