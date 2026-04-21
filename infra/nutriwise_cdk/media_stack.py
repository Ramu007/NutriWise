"""S3 bucket for food photos + CloudFront distribution.

Cost posture:
- Raw uploads expire at 30 days — photos only exist for analysis retry.
- Thumbnails/processed images move to Intelligent-Tiering after 30 days and
  Glacier Instant Retrieval after 180. Intelligent-Tiering handles access-
  pattern changes automatically without charging for retrievals.
- CloudFront price class defaults to North America + EU in non-prod
  (~40% cheaper than the global distribution).
- Transfer acceleration is off — we don't need it for meal photos.
"""
from __future__ import annotations

from aws_cdk import CfnOutput, Duration, RemovalPolicy, Stack
from aws_cdk import aws_cloudfront as cf
from aws_cdk import aws_cloudfront_origins as origins
from aws_cdk import aws_s3 as s3
from constructs import Construct


class MediaStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, *, env_name: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        is_prod = env_name == "prod"
        destroy = not is_prod

        self.photo_bucket = s3.Bucket(
            self,
            "FoodPhotos",
            bucket_name=None,
            encryption=s3.BucketEncryption.S3_MANAGED,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            enforce_ssl=True,
            versioned=False,
            lifecycle_rules=[
                # Raw uploads: auto-delete after analysis window.
                s3.LifecycleRule(
                    id="expire-raw-uploads",
                    prefix="uploads/",
                    expiration=Duration.days(30),
                    abort_incomplete_multipart_upload_after=Duration.days(1),
                ),
                # Processed / thumbnail objects: move to cheaper tiers over time.
                s3.LifecycleRule(
                    id="tier-processed",
                    prefix="processed/",
                    transitions=[
                        s3.Transition(
                            storage_class=s3.StorageClass.INTELLIGENT_TIERING,
                            transition_after=Duration.days(30),
                        ),
                        s3.Transition(
                            storage_class=s3.StorageClass.GLACIER_INSTANT_RETRIEVAL,
                            transition_after=Duration.days(180),
                        ),
                    ],
                    abort_incomplete_multipart_upload_after=Duration.days(1),
                ),
            ],
            removal_policy=RemovalPolicy.DESTROY if destroy else RemovalPolicy.RETAIN,
            auto_delete_objects=destroy,
        )

        # North America + Europe only in non-prod saves ~40% vs PRICE_CLASS_ALL.
        # Prod uses the global distribution for latency in APAC.
        price_class = (
            cf.PriceClass.PRICE_CLASS_ALL if is_prod else cf.PriceClass.PRICE_CLASS_100
        )

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
            price_class=price_class,
            http_version=cf.HttpVersion.HTTP2_AND_3,  # HTTP/3 is free and trims RTTs.
            comment=f"NutriWise food photos ({env_name})",
        )

        CfnOutput(self, "PhotoBucketName", value=self.photo_bucket.bucket_name)
        CfnOutput(self, "PhotoCdnDomain", value=dist.distribution_domain_name)
