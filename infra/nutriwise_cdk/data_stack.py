"""DynamoDB tables.

Cost posture:
- On-demand billing (`PAY_PER_REQUEST`) — zero cost at rest, cheapest for
  unpredictable early-stage traffic. Reassess vs provisioned once we have
  a stable baseline above ~18% utilization.
- Point-in-time recovery costs ~$0.20/GB/month — enabled only in prod.
- GSIs project `KEYS_ONLY` where the caller just needs the PK to fetch the
  full item (halves storage and write amplification vs `ALL`).
"""
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
        is_prod = env_name == "prod"
        removal = RemovalPolicy.RETAIN if is_prod else RemovalPolicy.DESTROY
        pitr = is_prod  # ~$0.20/GB/month; not worth it in dev/staging.

        users = ddb.Table(
            self,
            "Users",
            table_name=f"nutriwise-users-{env_name}",
            partition_key=ddb.Attribute(name="user_id", type=ddb.AttributeType.STRING),
            billing_mode=ddb.BillingMode.PAY_PER_REQUEST,
            encryption=ddb.TableEncryption.AWS_MANAGED,
            point_in_time_recovery=pitr,
            removal_policy=removal,
        )

        nutritionists = ddb.Table(
            self,
            "Nutritionists",
            table_name=f"nutriwise-nutritionists-{env_name}",
            partition_key=ddb.Attribute(name="nutritionist_id", type=ddb.AttributeType.STRING),
            billing_mode=ddb.BillingMode.PAY_PER_REQUEST,
            encryption=ddb.TableEncryption.AWS_MANAGED,
            point_in_time_recovery=pitr,
            removal_policy=removal,
        )
        # GSI projects only keys — callers still need to fetch the full item,
        # but directory listings hit the GSI for country/city filtering only.
        nutritionists.add_global_secondary_index(
            index_name="by_country_city",
            partition_key=ddb.Attribute(name="country", type=ddb.AttributeType.STRING),
            sort_key=ddb.Attribute(name="city", type=ddb.AttributeType.STRING),
            projection_type=ddb.ProjectionType.KEYS_ONLY,
        )

        food_logs = ddb.Table(
            self,
            "FoodLogs",
            table_name=f"nutriwise-food-logs-{env_name}",
            partition_key=ddb.Attribute(name="user_id", type=ddb.AttributeType.STRING),
            sort_key=ddb.Attribute(name="logged_at", type=ddb.AttributeType.STRING),
            billing_mode=ddb.BillingMode.PAY_PER_REQUEST,
            encryption=ddb.TableEncryption.AWS_MANAGED,
            point_in_time_recovery=pitr,
            removal_policy=removal,
            # Auto-expire raw log rows older than 2 years — keeps storage bounded.
            # App sets `ttl` to `logged_at + 2y` when writing.
            time_to_live_attribute="ttl",
        )

        bookings = ddb.Table(
            self,
            "Bookings",
            table_name=f"nutriwise-bookings-{env_name}",
            partition_key=ddb.Attribute(name="booking_id", type=ddb.AttributeType.STRING),
            billing_mode=ddb.BillingMode.PAY_PER_REQUEST,
            encryption=ddb.TableEncryption.AWS_MANAGED,
            point_in_time_recovery=pitr,
            removal_policy=removal,
        )
        # Conflict check: query all bookings for a nutritionist by start time.
        # Needs enough data to compare overlaps without a second fetch, so INCLUDE
        # the minimal overlap-check attributes rather than KEYS_ONLY.
        bookings.add_global_secondary_index(
            index_name="by_nutritionist_start",
            partition_key=ddb.Attribute(name="nutritionist_id", type=ddb.AttributeType.STRING),
            sort_key=ddb.Attribute(name="starts_at", type=ddb.AttributeType.STRING),
            projection_type=ddb.ProjectionType.INCLUDE,
            non_key_attributes=["duration_minutes", "status"],
        )
        # User history — projection KEYS_ONLY since the mobile app fetches full
        # items only when the user taps a row.
        bookings.add_global_secondary_index(
            index_name="by_user_start",
            partition_key=ddb.Attribute(name="user_id", type=ddb.AttributeType.STRING),
            sort_key=ddb.Attribute(name="starts_at", type=ddb.AttributeType.STRING),
            projection_type=ddb.ProjectionType.KEYS_ONLY,
        )

        self.tables = Tables(users=users, nutritionists=nutritionists, food_logs=food_logs, bookings=bookings)

        for t in (users, nutritionists, food_logs, bookings):
            CfnOutput(self, f"{t.node.id}TableName", value=t.table_name)
