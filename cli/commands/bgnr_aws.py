'''Commands that use the AWS API via boto3'''

import json
import time
import boto3

from cli.bgnr_command import Command
from cli.bgnr_util import Config, Out, Proc


class RollbackCommand(Command):
    '''Rollback to previous deployment by repointing the DNS domain record

    **USAGE**
      bgnr [flags] rollback

    {flags}

    **EXAMPLES**
      $ bgnr rollback
      $ bgnr -v rollback
    '''

    @classmethod
    def key(cls):
        return 'rollback'

    def execute(self):
        ssm_client = boto3.client('ssm')

        with Out.Do(msg='Fetching deployment color parameters'):
            response = ssm_client.get_parameters(Names=['bgm-nerdrock-prod-deployment-colors',
                                                        'bgm-nerdrock-active-prod-color'])
            active_color = next(
                (x for x in response['Parameters'] if x['Name'] == 'bgm-nerdrock-active-prod-color')
            )['Value']
            color_list: list[str] = next(
                (x for x in response['Parameters'] if x['Name'] == 'bgm-nerdrock-prod-deployment-colors')
            )['Value'].split(',')
            prev_color = color_list[-1] if active_color == color_list[0] else color_list[color_list.index(active_color)-1]

        with Out.Do(msg='Finding HostedZone to update', error='Error finding HostedZone'):
            cf_client = boto3.client('cloudformation')
            global_resources = cf_client.list_stack_resources(StackName=Config.get().stack('global'))['StackResourceSummaries']
            hosted_zone = next(
                (x for x in global_resources if x['ResourceType'] == 'AWS::Route53::HostedZone')
            )['PhysicalResourceId']

        with Out.Do(msg='Finding the target distribution for prod DNS record update',
                    error='Error getting target distribution'):
            env_resources = cf_client.list_stack_resources(StackName=Config.get().stack(prev_color))['StackResourceSummaries']
            distribution_id = next(
                (x for x in env_resources if x['ResourceType'] == 'AWS::CloudFront::Distribution')
            )['PhysicalResourceId']
            cfront_client = boto3.client('cloudfront')
            distribution_domain = cfront_client.get_distribution(Id=distribution_id)['Distribution']['DomainName']

        with Out.Do(msg=f'Rolling back from {active_color} to {prev_color}',
                    error=f'Failed to roll back; prod is still pointed to {active_color}'):
            r53_client = boto3.client('route53')
            for record_type in ['A', 'AAAA']:
                r53_client.change_resource_record_sets(HostedZoneId=hosted_zone,
                                                       ChangeBatch={
                                                           'Changes': [{
                                                               'Action': 'UPSERT',
                                                               'ResourceRecordSet': {
                                                                   'Name': Config.get().domain,
                                                                   'Type': record_type,
                                                                   'AliasTarget': {
                                                                       'HostedZoneId': Config.get().cf_hosted_zone,
                                                                       'DNSName': distribution_domain,
                                                                       'EvaluateTargetHealth': False
                                                                   }
                                                               }
                                                           }]
                                                       })
            r53_client.change_resource_record_sets(HostedZoneId=hosted_zone,
                                                   ChangeBatch={
                                                        'Changes': [{
                                                            'Action': 'UPSERT',
                                                            'ResourceRecordSet': {
                                                                'Name': f'_.{Config.get().domain}.',
                                                                'Type': 'TXT',
                                                                'ResourceRecords': [{'Value': f'"{distribution_domain}."'}],
                                                                'TTL': 300
                                                            }
                                                        }]
                                                   })

            time.sleep(5)  # Takes a bit for the record to be seen, even if it shows back from an API call
            cfront_client.associate_alias(TargetDistributionId=distribution_id, Alias=Config.get().domain)

        with Out.Do(msg=f'Setting {prev_color} as the new active prod color',
                    error=f'Error updating the prod color to {prev_color}; DNS and SSM are mismatched!'):
            ssm_client.put_parameter(Name='bgm-nerdrock-active-prod-color', Value=prev_color, Overwrite=True)


class UpdateLocCommand(Command):
    '''Update the IP address that non-prod environments will allow to connect

    **USAGE**
      bgnr [flags] update-loc

    {flags}

    **EXAMPLES**
      $ bgnr update-loc
      $ bgnr -v update-loc

    **NOTES**
      Non-prod environments have an IP-based protection that only allows
      access from one allowed source. That will usually be my home, but in
      case I'm on the road, I can execute this and it will update the allowed
      IP with wherever I happen to be.
    '''

    @classmethod
    def key(cls):
        return 'update-loc'

    def execute(self):
        with Out.Do('Fetching public IP addresses'):
            ipv4 = Proc.exec(Config.get().ipv4_check, capture_stdout=True).stdout.strip()
            ipv6 = Proc.exec(Config.get().ipv6_check, capture_stdout=True).stdout.strip()
        with Out.Do(f'Updating key-value store with current location {ipv4}/{ipv6}'):
            cf_client = boto3.client('cloudformation')
            stack_name = f'{Config.get().org}-{Config.get().project}-global-stack'
            Out.trace('aws cloudformation describe-stacks --stack-name bgm-nerdrock-global-stack')
            stack = cf_client.describe_stacks(StackName=stack_name)['Stacks'][0]
            kvs_arn = next((x for x in stack['Outputs'] if x['OutputKey'] == 'KeyValueStoreArn'), None)['OutputValue']
            kvs_client = boto3.client('cloudfront-keyvaluestore')
            Out.trace(f'aws cloudfront-keyvaluestore describe-key-value-store --kvs-arn {kvs_arn}')
            etag = kvs_client.describe_key_value_store(KvsARN=kvs_arn)['ETag']
            Out.trace('aws cloudfront-keyvaluestore put-key '
                      f'--key {Config.get().allowed_ips_key} --value {ipv4} --kvs-arn {kvs_arn} --if-match {etag}')
            kvs_client.put_key(Key=Config.get().allowed_ips_key, Value=','.join([ipv4, ipv6]),
                               KvsARN=kvs_arn, IfMatch=etag)
