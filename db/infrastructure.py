"""CDK Construct definitions for the NerdRock DynamoDB tables"""

import aws_cdk
from aws_cdk import aws_dynamodb
from constructs import Construct

from cdk import bgm_construct, bgm_context


class DbConstruct(bgm_construct.BgmConstruct):
    """CDK Construct definitions for the NerdRock DynamoDB tables"""

    db_table_spec = [
        {'name': 'albuminfo', 'pk': 'album_id', 'sk': None},
        {'name': 'trackinfo', 'pk': 'album_id', 'sk': 'number'}
    ]

    def __init__(self, scope: Construct, construct_id: str, context: bgm_context.BgmContext):
        super().__init__(scope, construct_id, context)

        # DynamoDB Tables
        for table in DbConstruct.db_table_spec:
            ddb = aws_dynamodb.Table(
                self, f'{self.capitalize(table['name'])}Table', table_name=self.physical_id_for(table['name']),
                partition_key=aws_dynamodb.Attribute(name=table['pk'],
                                                     type=aws_dynamodb.AttributeType.NUMBER) if table['pk'] else {},
                sort_key=aws_dynamodb.Attribute(name=table['sk'],
                                                type=aws_dynamodb.AttributeType.NUMBER) if table['sk'] else None,
                removal_policy=aws_cdk.RemovalPolicy.DESTROY, billing_mode=aws_dynamodb.BillingMode.PAY_PER_REQUEST,
                max_read_request_units=5)
            aws_cdk.CfnOutput(self, f'{self.capitalize(table['name'])}TableOutput', value=ddb.table_name)
