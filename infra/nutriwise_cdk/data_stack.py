"""DynamoDB tables (+ future Aurora Serverless v2 wiring)."""
from __future__ import annotations

from dataclasses import dataclass

from aws_cdk import CfnOutput, RemovalPolicy, Stack
from aws_cdk import aws_dynamodb as ddb
from constructs import Construct


@dataclass
class Tables:
    users: ddb.Table
    nutritionists: ddb.Table
    food_logs: ddb.Table
    bookings: ddb.Table


class DataStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, *, env_name: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        destroy = env_name != "prod"

        users = ddb.Table(
            self,
            "Users",
            table_name=f"nutriwise-users-{env_name}",
            partition_key=ddb.Attribute(name="user_id", type=ddb.AttributeType.STRING),
            billing_mode=ddb.BillingMode.PAY_PER_REQUEST,
            encryption=ddb.TableEncryption.AWS_MANAGED,
            point_in_time_recovery=True,
            removal_policy=RemovalPolicy.DESTROY if destroy else RemovalPolicy.RETAIN,
        )

        nutritionists = ddb.Table(
            self,
            "Nutritionists",
            table_name=f"nutriwise-nutritionists-{env_name}",
            partition_key=ddb.Attribute(name="nutritionist_id", type=ddb.AttributeType.STRING),
            billing_mode=ddb.BillingMode.PAY_PER_REQUEST,
            encryption=ddb.TableEncryption.AWS_MANAGED,
            point_in_time_recovery=True,
            removal_policy=RemovalPolicy.DESTROY if destroy else RemovalPolicy.RETAIN,
        )
        # Country+city for regional discovery.
        nutritionists.add_global_secondary_index(
            index_name="by_country_city",
            partition_key=ddb.Attribute(name="country", type=ddb.AttributeType.STRING),
            sort_key=ddb.Attribute(name="city", type=ddb.AttributeType.STRING),
        )

        food_logs = ddb.Table(
            self,
            "FoodLogs",
            table_name=f"nutriwise-food-logs-{env_name}",
            # user_id (PK) + logged_at (SK) so a day's entries fetch as a single range query.
            partition_key=ddb.Attribute(name="user_id", type=ddb.AttributeType.STRING),
            sort_key=ddb.Attribute(name="logged_at", type=ddb.AttributeType.STRING),
            billing_mode=ddb.BillingMode.PAY_PER_REQUEST,
            encryption=ddb.TableEncryption.AWS_MANAGED,
            point_in_time_recovery=True,
            removal_policy=RemovalPolicy.DESTROY if destroy else RemovalPolicy.RETAIN,
        )

        bookings = ddb.Table(
            self,
            "Bookings",
            table_name=f"nutriwise-bookings-{env_name}",
            partition_key=ddb.Attribute(name="booking_id", type=ddb.AttributeType.STRING),
            billing_mode=ddb.BillingMode.PAY_PER_REQUEST,
            encryption=ddb.TableEncryption.AWS_MANAGED,
            point_in_time_recovery=True,
            removal_policy=RemovalPolicy.DESTROY if destroy else RemovalPolicy.RETAIN,
        )
        # Query by nutritionist (for conflict checks) and by user (for a user's history).
        bookings.add_global_secondary_index(
            index_name="by_nutritionist_start",
            partition_key=ddb.Attribute(name="nutritionist_id", type=ddb.AttributeType.STRING),
            sort_key=ddb.Attribute(name="starts_at", type=ddb.AttributeType.STRING),
        )
        bookings.add_global_secondary_index(
            index_name="by_user_start",
            partition_key=ddb.Attribute(name="user_id", type=ddb.AttributeType.STRING),
            sort_key=ddb.Attribute(name="starts_at", type=ddb.AttributeType.STRING),
        )

        self.tables = Tables(users=users, nutritionists=nutritionists, food_logs=food_logs, bookings=bookings)

        for t in (users, nutritionists, food_logs, bookings):
            CfnOutput(self, f"{t.node.id}TableName", value=t.table_name)
