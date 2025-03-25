import abc
from pathlib import Path
import re

import boto3
from botocore.exceptions import ClientError


class BgmContext():
    def __init__(self, config: dict):
        self.projectDirectory: Path = Path(__file__).parent.parent
        self.cdkDirectory: Path = Path(__file__).parent
        for key, value in config['context'].items():
            setattr(self, key, value)

    @abc.abstractmethod
    def logicalIdFor(self, id: str):
        pass

    @abc.abstractmethod
    def physicalIdFor(self, id: str):
        pass

    def getTags(self):
        return {'org': self.org, 'project': self.project}

    def capitalize(self, s: str):
        s = re.sub(r'[\W]', '', s)
        return re.sub('([a-zA-Z])', lambda x: x.groups()[0].upper(), s, 1)


class GlobalContext(BgmContext):
    def __init__(self, config: dict):
        super().__init__(config)

        self.logicalIdPrefix = ''.join([self.capitalize(x) for x in [self.org, self.project, 'global']])
        self.physicalIdPrefix = f'{self.org.lower()}-{self.project.lower()}-global'
        self.blockIpCfFuncPath = f'{self.cdkDirectory}/{self.blockIpFuncSourceFile}'
        self.restRoutingCfFuncPath = f'{self.cdkDirectory}/{self.restRoutingFuncSourceFile}'

    def logicalIdFor(self, id: str):
        return f'{self.logicalIdPrefix}{''.join([self.capitalize(x) for x in id.split('-')])}'

    def physicalIdFor(self, id: str):
        return f'{self.physicalIdPrefix}-{id}'

    def getTags(self):
        tags = super().getTags()
        tags['app'] = self.physicalIdPrefix
        return tags


class EnvContext(BgmContext):
    def __init__(self, env: str, config: dict):
        super().__init__(config)

        self.env = self.normalize_env_name(env)
        self.lambdaPackage = f'./{self.assetsDir}/{self.org.lower()}-{self.project.lower()}-{self.env}-lambdas.zip'
        self.webPackage = f'./{self.assetsDir}/{self.org.lower()}-{self.project.lower()}-{self.env}-web.zip'

        self.defaultProdColor = config['ssm-parameters']['active-prod-color']
        self.figureIfIsProd(config['ssm-parameters']['prod-deployment-colors'].copy())

        self.logicalIdPrefix = ''.join([self.capitalize(x) for x in [self.org, self.project, self.env]])
        self.physicalIdPrefix = f'{self.org.lower()}-{self.project.lower()}-{self.env}'
        self.hostName = f'{self.env.lower()}.{self.domain}'

    def normalize_env_name(self, env: str) -> str:
        env = re.sub('[^A-Za-z0-9-]+', '-', env)
        env = re.sub('^[-]', '', env)
        env = re.sub('[-]$', '', env)
        return env

    def figureIfIsProd(self, prodColors: list):
        ssm = boto3.client('ssm')
        if self.env == 'staging':
            self.isProd = True
        elif self.env == 'prod':
            self.isProd = True
            try:
                prodColorResult = ssm.get_parameter(Name='bgm-nerdrock-active-prod-color')
                self.env = self.getNextProdColor(prodColorResult['Parameter']['Value'], prodColors) \
                    or self.defaultProdColor
            except ClientError:
                self.env = self.defaultProdColor
        elif self.env.upper() in [x.upper() for x in prodColors]:
            self.isProd = True
        else:
            self.isProd = False

    def getNextProdColor(self, prodColor, prodColors):
        if prodColor == prodColors[-1]:
            return prodColors[0]
        else:
            return prodColors[prodColors.index(prodColor)+1]

    def logicalIdFor(self, id: str):
        return f'{self.logicalIdPrefix}{self.capitalize(id)}'

    def physicalIdFor(self, id: str):
        return f'{self.physicalIdPrefix}-{id}'

    def getTags(self):
        tags = super().getTags()
        tags['env'] = self.env
        tags['app'] = self.physicalIdPrefix
        return tags
