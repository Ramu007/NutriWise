"""CDK entrypoint — synthesize all stacks for the selected environment.

Environment is selected via the `ENV` env var (default: `dev`). Stacks per env
are cheap to synthesize individually, so we keep them in one app.

Cost-allocation tags (`project`, `env`, `component`) flow to every resource
and surface in AWS Cost Explorer once activated in Billing preferences.
"""
from __future__ import annotations

import os

import aws_cdk as cdk

from nutriwise_cdk.api_stack import ApiStack
from nutriwise_cdk.auth_stack import AuthStack
from nutriwise_cdk.data_stack import DataStack
from nutriwise_cdk.media_stack import MediaStack

env_name = os.getenv("ENV", "dev")
aws_account = os.getenv("CDK_DEFAULT_ACCOUNT")
aws_region = os.getenv("CDK_DEFAULT_REGION", "us-east-1")

env = cdk.Environment(account=aws_account, region=aws_region)

app = cdk.App()

cdk.Tags.of(app).add("project", "nutriwise")
cdk.Tags.of(app).add("env", env_name)
cdk.Tags.of(app).add("managed_by", "cdk")

auth = AuthStack(app, f"NutriWise-Auth-{env_name}", env=env, env_name=env_name)
data = DataStack(app, f"NutriWise-Data-{env_name}", env=env, env_name=env_name)
media = MediaStack(app, f"NutriWise-Media-{env_name}", env=env, env_name=env_name)
api = ApiStack(
    app,
    f"NutriWise-Api-{env_name}",
    env=env,
    env_name=env_name,
    user_pool=auth.user_pool,
    tables=data.tables,
    photo_bucket=media.photo_bucket,
)

cdk.Tags.of(auth).add("component", "auth")
cdk.Tags.of(data).add("component", "data")
cdk.Tags.of(media).add("component", "media")
cdk.Tags.of(api).add("component", "api")

app.synth()
