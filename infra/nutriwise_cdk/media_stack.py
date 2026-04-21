"""S3 bucket for food photos + CloudFront distribution."""
from __future__ import annotations

from aws_cdk import CfnOutput, Duration, RemovalPolicy, Stack
from aws_cdk import aws_cloudfront as cf
from aws_cdk import aws_cloudfront_origins as origins
from aws_cdk import aws_s3 as s3
from constructs import Construct


class MediaStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, *, env_name: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        destroy = env_name != "prod"

        self.photo_bucket = s3.Bucket(
            self,
            "FoodPhotos",
            bucket_name=None,  # CFN auto-name — env has its own stack name already.
            encryption=s3.BucketEncryption.S3_MANAGED,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            enforce_ssl=True,
            versioned=False,
            lifecycle_rules=[
                s3.LifecycleRule(
                    id="expire-raw-uploads",
                    prefix="uploads/",
                    expiration=Duration.days(30),  # Photos only needed for short-term analysis retry.
                )
            ],
            removal_policy=RemovalPolicy.DESTROY if destroy else RemovalPolicy.RETAIN,
            auto_delete_objects=destroy,
        )

        # Public CDN for delivering thumbnails back to the mobile app.
        origin = origins.S3BucketOrigin.with_origin_access_control(self.photo_bucket)
        dist = cf.Distribution(
            self,
            "FoodPhotosCdn",
            default_behavior=cf.BehaviorOptions(
                origin=origin,
                viewer_protocol_policy=cf.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
                allowed_methods=cf.AllowedMethods.ALLOW_GET_HEAD,
                cache_policy=cf.CachePolicy.CACHING_OPTIMIZED,
            ),
            comment=f"NutriWise food photos ({env_name})",
        )

        CfnOutput(self, "PhotoBucketName", value=self.photo_bucket.bucket_name)
        CfnOutput(self, "PhotoCdnDomain", value=dist.distribution_domain_name)
