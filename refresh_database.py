import boto3

lambda_client = boto3.client('lambda')
response = lambda_client.invoke(FunctionName='bgm-nerdrock-dev-databaseRefresh', InvocationType='RequestResponse')
print(response)
