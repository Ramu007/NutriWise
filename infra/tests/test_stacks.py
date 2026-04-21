"""Smoke tests — confirm stacks synthesize and emit the resources we care about.

These tests protect against refactors that silently drop a resource: a missing
DynamoDB table or Cognito pool is the kind of thing nobody notices until
deploy time.
"""
from __future__ import annotations

import aws_cdk as cdk
import pytest
from aws_cdk.assertions import Match, Template

from nutriwise_cdk.api_stack import ApiStack
from nutriwise_cdk.auth_stack import AuthStack
from nutriwise_cdk.data_stack import DataStack
from nutriwise_cdk.media_stack import MediaStack


@pytest.fixture
def app() -> cdk.App:
    return cdk.App()


def test_auth_stack_creates_user_pool(app: cdk.App):
    stack = AuthStack(app, "Auth", env_name="dev")
    tpl = Template.from_stack(stack)
    tpl.resource_count_is("AWS::Cognito::UserPool", 1)
    tpl.resource_count_is("AWS::Cognito::UserPoolClient", 1)
    # Three groups: customers, nutritionists, admins.
    tpl.resource_count_is("AWS::Cognito::UserPoolGroup", 3)


def test_data_stack_creates_all_tables(app: cdk.App):
    stack = DataStack(app, "Data", env_name="dev")
    tpl = Template.from_stack(stack)
    tpl.resource_count_is("AWS::DynamoDB::Table", 4)
    # Bookings has two GSIs; nutritionists has one; users + food_logs have none.
    tpl.has_resource_properties(
        "AWS::DynamoDB::Table",
        {"TableName": "nutriwise-bookings-dev"},
    )


def test_media_stack_creates_bucket_and_cdn(app: cdk.App):
    stack = MediaStack(app, "Media", env_name="dev")
    tpl = Template.from_stack(stack)
    tpl.resource_count_is("AWS::S3::Bucket", 1)
    tpl.resource_count_is("AWS::CloudFront::Distribution", 1)


def test_api_stack_wires_lambda_and_apigw(app: cdk.App):
    auth = AuthStack(app, "Auth2", env_name="dev")
    data = DataStack(app, "Data2", env_name="dev")
    media = MediaStack(app, "Media2", env_name="dev")
    api = ApiStack(
        app,
        "Api",
        env_name="dev",
        user_pool=auth.user_pool,
        tables=data.tables,
        photo_bucket=media.photo_bucket,
    )
    tpl = Template.from_stack(api)
    tpl.resource_count_is("AWS::Lambda::Function", 1)
    tpl.resource_count_is("AWS::ApiGatewayV2::Api", 1)
    tpl.resource_count_is("AWS::ApiGatewayV2::Route", 1)


def test_prod_uses_retain_removal_policy():
    app = cdk.App()
    stack = DataStack(app, "DataProd", env_name="prod")
    tpl = Template.from_stack(stack)
    # In prod we retain tables on stack deletion.
    tpl.has_resource("AWS::DynamoDB::Table", {"DeletionPolicy": "Retain"})


# --- Cost-optimization guardrails ------------------------------------------------
# These tests protect against regressions: if someone drops the ARM architecture,
# loses the KEYS_ONLY projection, or forgets the price-class override for dev,
# the bill climbs silently. Tests make the intent explicit.


def test_api_lambda_uses_arm64_for_cost(app: cdk.App):
    auth = AuthStack(app, "A", env_name="dev")
    data = DataStack(app, "D", env_name="dev")
    media = MediaStack(app, "M", env_name="dev")
    api = ApiStack(
        app, "Api-arm", env_name="dev",
        user_pool=auth.user_pool, tables=data.tables, photo_bucket=media.photo_bucket,
    )
    tpl = Template.from_stack(api)
    tpl.has_resource_properties(
        "AWS::Lambda::Function",
        Match.object_like({"Architectures": ["arm64"]}),
    )


def test_api_lambda_right_sized_memory(app: cdk.App):
    auth = AuthStack(app, "A2", env_name="dev")
    data = DataStack(app, "D2", env_name="dev")
    media = MediaStack(app, "M2", env_name="dev")
    api = ApiStack(
        app, "Api-mem", env_name="dev",
        user_pool=auth.user_pool, tables=data.tables, photo_bucket=media.photo_bucket,
    )
    tpl = Template.from_stack(api)
    tpl.has_resource_properties(
        "AWS::Lambda::Function",
        Match.object_like({"MemorySize": 512}),
    )


def test_dev_cloudfront_is_regional_price_class(app: cdk.App):
    stack = MediaStack(app, "Media-dev-pc", env_name="dev")
    tpl = Template.from_stack(stack)
    tpl.has_resource_properties(
        "AWS::CloudFront::Distribution",
        Match.object_like({
            "DistributionConfig": Match.object_like({"PriceClass": "PriceClass_100"}),
        }),
    )


def test_prod_cloudfront_is_global_for_latency():
    app = cdk.App()
    stack = MediaStack(app, "Media-prod-pc", env_name="prod")
    tpl = Template.from_stack(stack)
    tpl.has_resource_properties(
        "AWS::CloudFront::Distribution",
        Match.object_like({
            "DistributionConfig": Match.object_like({"PriceClass": "PriceClass_All"}),
        }),
    )


def test_gsis_use_cheap_projections(app: cdk.App):
    stack = DataStack(app, "Data-gsi", env_name="dev")
    tpl = Template.from_stack(stack)
    # At least one GSI must be KEYS_ONLY (the cheapest projection type).
    tpl.has_resource_properties(
        "AWS::DynamoDB::Table",
        Match.object_like({
            "GlobalSecondaryIndexes": Match.array_with([
                Match.object_like({
                    "Projection": Match.object_like({"ProjectionType": "KEYS_ONLY"}),
                }),
            ]),
        }),
    )


def test_food_logs_has_ttl_for_storage_cap(app: cdk.App):
    stack = DataStack(app, "Data-ttl", env_name="dev")
    tpl = Template.from_stack(stack)
    tpl.has_resource_properties(
        "AWS::DynamoDB::Table",
        Match.object_like({
            "TableName": "nutriwise-food-logs-dev",
            "TimeToLiveSpecification": Match.object_like({"AttributeName": "ttl", "Enabled": True}),
        }),
    )


def test_dev_skips_pitr_to_save_cost(app: cdk.App):
    stack = DataStack(app, "Data-no-pitr", env_name="dev")
    tpl = Template.from_stack(stack)
    tables = tpl.find_resources("AWS::DynamoDB::Table")
    # None of the dev tables should enable PITR.
    for _, props in tables.items():
        pitr = props.get("Properties", {}).get("PointInTimeRecoverySpecification")
        if pitr:
            assert pitr.get("PointInTimeRecoveryEnabled") is False


def test_no_vpc_anywhere(app: cdk.App):
    # A stray VPC drags in a NAT gateway ($32/mo/AZ) the moment someone wires
    # a subnet. Guard against it until we have a reason (e.g. Aurora).
    auth = AuthStack(app, "A3", env_name="dev")
    data = DataStack(app, "D3", env_name="dev")
    media = MediaStack(app, "M3", env_name="dev")
    api = ApiStack(
        app, "Api-novpc", env_name="dev",
        user_pool=auth.user_pool, tables=data.tables, photo_bucket=media.photo_bucket,
    )
    for stack in (auth, data, media, api):
        tpl = Template.from_stack(stack)
        tpl.resource_count_is("AWS::EC2::VPC", 0)
        tpl.resource_count_is("AWS::EC2::NatGateway", 0)
