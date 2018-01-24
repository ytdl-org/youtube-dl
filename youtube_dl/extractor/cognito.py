from .common import InfoExtractor
from ..utils import ExtractorError


class CognitoBaseIE(InfoExtractor):

    def _cognito_login(self, auth_data):

        try:
            import boto3
            from warrant.aws_srp import AWSSRP
        except ImportError:
            raise ExtractorError('%s depends on boto3 and warrant.' % self.IE_NAME)

        region = auth_data['PoolId'].split('_')[0]
        client = boto3.client(
            'cognito-idp',
            region_name=region,
            aws_access_key_id='SomeNonsenseValue',
            aws_secret_access_key='YetAnotherNonsenseValue'
        )
        aws = AWSSRP(
            username=auth_data['Username'],
            password=auth_data['Password'],
            pool_id=auth_data['PoolId'],
            client_id=auth_data['ClientId'],
            client=client
        )
        return aws.authenticate_user()
