from aws_cdk import RemovalPolicy, CfnOutput
from aws_cdk.aws_dynamodb import Table, Attribute, AttributeType
from constructs import Construct

from cdk.bgm_construct import BgmConstruct
from cdk.bgm_context import BgmContext


class DbConstruct(BgmConstruct):

    db_table_spec = [
        {'name': 'albuminfo', 'pk': 'album_id', 'sk': None},
        {'name': 'trackinfo', 'pk': 'album_id', 'sk': 'number'}
    ]

    def __init__(self, scope: Construct, id: str, context: BgmContext):
        super().__init__(scope, id, context)

        # DynamoDB Tables
        for table in DbConstruct.db_table_spec:
            ddb = Table(
                self, f'{self.capitalize(table["name"])}Table', table_name=self.physicalIdFor(table['name']),
                partition_key=Attribute(name=table['pk'], type=AttributeType.NUMBER) if table['pk'] else None,
                sort_key=Attribute(name=table['sk'], type=AttributeType.NUMBER) if table['sk'] else None,
                removal_policy=RemovalPolicy.DESTROY)
            CfnOutput(self, f'{self.capitalize(table["name"])}TableOutput', value=ddb.table_name)
