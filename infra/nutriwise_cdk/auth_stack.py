"""Cognito user pool + identity providers."""
from __future__ import annotations

from aws_cdk import CfnOutput, RemovalPolicy, Stack
from aws_cdk import aws_cognito as cognito
from constructs import Construct


class AuthStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, *, env_name: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        pool = cognito.UserPool(
            self,
            "Users",
            user_pool_name=f"nutriwise-{env_name}",
            self_sign_up_enabled=True,
            sign_in_aliases=cognito.SignInAliases(email=True),
            standard_attributes=cognito.StandardAttributes(
                email=cognito.StandardAttribute(required=True, mutable=True),
                given_name=cognito.StandardAttribute(required=False, mutable=True),
                family_name=cognito.StandardAttribute(required=False, mutable=True),
            ),
            custom_attributes={
                "role": cognito.StringAttribute(min_len=1, max_len=32, mutable=True),
                "country": cognito.StringAttribute(min_len=2, max_len=2, mutable=True),
            },
            password_policy=cognito.PasswordPolicy(
                min_length=10,
                require_digits=True,
                require_lowercase=True,
                require_uppercase=True,
                require_symbols=False,
            ),
            mfa=cognito.Mfa.OPTIONAL,
            mfa_second_factor=cognito.MfaSecondFactor(sms=False, otp=True),
            account_recovery=cognito.AccountRecovery.EMAIL_ONLY,
            removal_policy=RemovalPolicy.RETAIN if env_name == "prod" else RemovalPolicy.DESTROY,
        )

        # Groups drive the `custom:role` assignment for admins + nutritionists.
        for name in ("customers", "nutritionists", "admins"):
            cognito.CfnUserPoolGroup(
                self,
                f"Group{name.title()}",
                user_pool_id=pool.user_pool_id,
                group_name=name,
            )

        client = pool.add_client(
            "MobileClient",
            user_pool_client_name=f"nutriwise-mobile-{env_name}",
            auth_flows=cognito.AuthFlow(user_srp=True, user_password=False),
            o_auth=cognito.OAuthSettings(
                flows=cognito.OAuthFlows(authorization_code_grant=True),
                scopes=[cognito.OAuthScope.OPENID, cognito.OAuthScope.EMAIL, cognito.OAuthScope.PROFILE],
            ),
            prevent_user_existence_errors=True,
            access_token_validity=None,
            id_token_validity=None,
        )

        self.user_pool = pool
        self.user_pool_client = client

        CfnOutput(self, "UserPoolId", value=pool.user_pool_id)
        CfnOutput(self, "UserPoolClientId", value=client.user_pool_client_id)
