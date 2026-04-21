FROM public.ecr.aws/lambda/python:3.13

COPY pyproject.toml ${LAMBDA_TASK_ROOT}/
COPY app ${LAMBDA_TASK_ROOT}/app

RUN pip install --no-cache-dir "fastapi>=0.115" "pydantic[email]>=2.9" "pydantic-settings>=2.6" \
      "python-multipart>=0.0.12" "boto3>=1.35" "anthropic[bedrock]>=0.40" \
      "sqlalchemy>=2.0" "asyncpg>=0.30" "httpx>=0.28" "python-jose[cryptography]>=3.3" \
      "mangum>=0.17"

CMD ["app.lambda_handler.handler"]
