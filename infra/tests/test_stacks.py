"""Smoke tests — confirm stacks synthesize and emit the resources we care about.

These tests protect against refactors that silently drop a resource: a missing
DynamoDB table or Cognito pool is the kind of thing nobody notices until
deploy time.
"""
from __future__ import annotations

import aws_cdk as cdk
import pytest
from aws_cdk.assertions import Template

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
