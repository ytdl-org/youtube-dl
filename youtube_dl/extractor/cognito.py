from .common import InfoExtractor

import boto3
from warrant import Cognito
from warrant.aws_srp import AWSSRP

class CognitoBaseIE(InfoExtractor):

    def _cognito_login(self, auth_data):
        region = auth_data['PoolId'].split('_')[0]
        client = boto3.client(
            'cognito-idp',
            region_name = region,
            aws_access_key_id = 'SomeNonsenseValue',
            aws_secret_access_key = 'YetAnotherNonsenseValue'
        )
        aws = AWSSRP(
            username = auth_data['Username'],
            password = auth_data['Password'],
            pool_id = auth_data['PoolId'],
            client_id = auth_data['ClientId'],
            client=client
        )
        return aws.authenticate_user()
