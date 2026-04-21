"""FastAPI on Lambda via Mangum, fronted by API Gateway HTTP API.

Cost posture:
- HTTP API is ~70% cheaper than REST API ($1.00 vs $3.50 per million) and
  covers everything we need (JWT authorizer, Lambda integration, CORS).
- Lambda on ARM64 (Graviton): ~20% cheaper per GB-second than x86 and
  usually faster on Python workloads.
- Memory right-sized at 512 MiB (FastAPI + Bedrock SDK fits comfortably).
  CPU scales linearly with memory on Lambda, so over-provisioning memory
  also overpays for CPU you rarely use.
- Log retention capped at 14 days in non-prod (default is indefinite =
  CloudWatch Logs storage charges grow forever).
- No VPC — no NAT gateway ($32/mo minimum per AZ). Lambda reaches DynamoDB,
  S3, and Bedrock over the AWS network without one. We only need a VPC
  when Aurora joins (Phase 2).
- IAM scoped to just the four NutriWise tables + the Bedrock model we use.
"""
from __future__ import annotations

from aws_cdk import CfnOutput, Duration, RemovalPolicy, Stack
from aws_cdk import aws_apigatewayv2 as apigw
from aws_cdk import aws_apigatewayv2_integrations as apigw_int
from aws_cdk import aws_cognito as cognito
from aws_cdk import aws_iam as iam
from aws_cdk import aws_lambda as _lambda
from aws_cdk import aws_logs as logs
from aws_cdk import aws_s3 as s3
from constructs import Construct

from nutriwise_cdk.data_stack import Tables


# Cross-region inference profile pattern (e.g. us.anthropic.claude-*). Bedrock
# checks the `bedrock:InvokeModel` action against the model ARN; we scope IAM
# to the model family rather than all Bedrock.
_BEDROCK_MODEL_ARN_PATTERN = "arn:aws:bedrock:*::foundation-model/*claude*"
_BEDROCK_INFERENCE_PROFILE_PATTERN = "arn:aws:bedrock:*:*:inference-profile/*claude*"


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
        is_prod = env_name == "prod"

        # Explicit log group lets us set retention without the CDK's log-retention
        # helper (which spawns an extra custom-resource Lambda).
        log_group = logs.LogGroup(
            self,
            "ApiFnLogs",
            log_group_name=f"/aws/lambda/nutriwise-api-{env_name}",
            retention=logs.RetentionDays.ONE_MONTH if is_prod else logs.RetentionDays.TWO_WEEKS,
            removal_policy=RemovalPolicy.RETAIN if is_prod else RemovalPolicy.DESTROY,
        )

        fn = _lambda.DockerImageFunction(
            self,
            "ApiFn",
            function_name=f"nutriwise-api-{env_name}",
            code=_lambda.DockerImageCode.from_image_asset("../api"),
            memory_size=512,  # Right-sized; bump via Power Tuning once we have real traffic.
            timeout=Duration.seconds(15),  # HTTP API has a 29s hard cap anyway.
            architecture=_lambda.Architecture.ARM_64,
            log_group=log_group,
            environment={
                "ENV": env_name,
                "COGNITO_USER_POOL_ID": user_pool.user_pool_id,
                "USERS_TABLE": tables.users.table_name,
                "NUTRITIONISTS_TABLE": tables.nutritionists.table_name,
                "FOOD_LOGS_TABLE": tables.food_logs.table_name,
                "BOOKINGS_TABLE": tables.bookings.table_name,
                "FOOD_PHOTOS_BUCKET": photo_bucket.bucket_name,
                # Connection reuse for boto3 — saves handshake latency & cost.
                "AWS_LAMBDA_EXEC_WRAPPER": "",
            },
        )

        tables.users.grant_read_write_data(fn)
        tables.nutritionists.grant_read_write_data(fn)
        tables.food_logs.grant_read_write_data(fn)
        tables.bookings.grant_read_write_data(fn)
        photo_bucket.grant_read_write(fn)

        # Bedrock — scoped to Claude models only, not bedrock:* on *.
        fn.add_to_role_policy(
            iam.PolicyStatement(
                actions=["bedrock:InvokeModel", "bedrock:InvokeModelWithResponseStream"],
                resources=[_BEDROCK_MODEL_ARN_PATTERN, _BEDROCK_INFERENCE_PROFILE_PATTERN],
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
                max_age=Duration.hours(1),  # Reduces preflight round trips.
            ),
            # HTTP API has no per-stage fees and no $1/mo data-trace overhead.
            disable_execute_api_endpoint=False,
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
