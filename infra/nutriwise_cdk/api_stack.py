"""FastAPI on Lambda via Mangum, fronted by API Gateway HTTP API.

Phase 0: Docker-based Lambda so we don't have to vendor wheels for asyncpg /
cryptography manually. `cdk synth` still works without Docker installed —
the asset bundling is evaluated lazily.
"""
from __future__ import annotations

from aws_cdk import CfnOutput, Duration, Stack
from aws_cdk import aws_apigatewayv2 as apigw
from aws_cdk import aws_apigatewayv2_integrations as apigw_int
from aws_cdk import aws_cognito as cognito
from aws_cdk import aws_iam as iam
from aws_cdk import aws_lambda as _lambda
from aws_cdk import aws_s3 as s3
from constructs import Construct

from nutriwise_cdk.data_stack import Tables


class ApiStack(Stack):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        *,
        env_name: str,
        user_pool: cognito.UserPool,
        tables: Tables,
        photo_bucket: s3.Bucket,
        **kwargs,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        fn = _lambda.DockerImageFunction(
            self,
            "ApiFn",
            function_name=f"nutriwise-api-{env_name}",
            code=_lambda.DockerImageCode.from_image_asset("../api"),
            memory_size=1024,
            timeout=Duration.seconds(30),
            architecture=_lambda.Architecture.ARM_64,
            environment={
                "ENV": env_name,
                "COGNITO_USER_POOL_ID": user_pool.user_pool_id,
                "USERS_TABLE": tables.users.table_name,
                "NUTRITIONISTS_TABLE": tables.nutritionists.table_name,
                "FOOD_LOGS_TABLE": tables.food_logs.table_name,
                "BOOKINGS_TABLE": tables.bookings.table_name,
                "FOOD_PHOTOS_BUCKET": photo_bucket.bucket_name,
            },
        )

        tables.users.grant_read_write_data(fn)
        tables.nutritionists.grant_read_write_data(fn)
        tables.food_logs.grant_read_write_data(fn)
        tables.bookings.grant_read_write_data(fn)
        photo_bucket.grant_read_write(fn)

        # Bedrock InvokeModel for Claude vision.
        fn.add_to_role_policy(
            iam.PolicyStatement(
                actions=["bedrock:InvokeModel", "bedrock:InvokeModelWithResponseStream"],
                resources=["*"],  # Bedrock model ARNs vary by region; tighten once model is pinned.
            )
        )

        http_api = apigw.HttpApi(
            self,
            "HttpApi",
            api_name=f"nutriwise-api-{env_name}",
            cors_preflight=apigw.CorsPreflightOptions(
                allow_origins=["*"],
                allow_methods=[apigw.CorsHttpMethod.ANY],
                allow_headers=["*"],
            ),
        )
        http_api.add_routes(
            path="/{proxy+}",
            methods=[apigw.HttpMethod.ANY],
            integration=apigw_int.HttpLambdaIntegration("LambdaIntegration", fn),
        )

        self.api_fn = fn
        self.http_api = http_api

        CfnOutput(self, "ApiEndpoint", value=http_api.api_endpoint)
        CfnOutput(self, "ApiLambdaName", value=fn.function_name)
