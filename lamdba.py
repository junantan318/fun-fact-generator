import os
import json
import random
import boto3
from botocore.config import Config
from botocore.exceptions import ClientError

REGION = "eu-north-1"
TABLE_NAME = os.environ.get("TABLE_NAME", "CloudFacts")

# Optional: if you already know the right ID/ARN, set this env var to skip discovery.
# Example value: us.anthropic.claude-3-7-sonnet-20250219-v1:0  (short ID)
# or: arn:aws:bedrock:eu-north-1:aws:inference-profile/us.anthropic.claude-3-7-sonnet-20250219-v1:0
PREF_MODEL_ID = os.environ.get("MODEL_ID")

# ---- Clients ----
dynamodb = boto3.resource("dynamodb", region_name=REGION)
table = dynamodb.Table(TABLE_NAME)

# Control-plane for discovery
bedrock_cp = boto3.client("bedrock", region_name=REGION)
# Runtime for invocation
bedrock_rt = boto3.client(
    "bedrock-runtime",
    region_name=REGION,
    config=Config(read_timeout=3600, retries={"max_attempts": 3})
)

CLAUDE37_NAME_PART = "claude-3-7-sonnet"  # used to match profile by name


def _discover_claude37_profile_id():
    """
    Return the exact inference profile ID (or ARN) for Claude 3.7 Sonnet in eu-north-1.
    We try:
      1) Use PREF_MODEL_ID if it’s already valid (optional quick path).
      2) List inference profiles and find the one whose name contains 'claude-3-7-sonnet'.
    """
    # If user supplied an ID/ARN via env var, trust it.
    if PREF_MODEL_ID:
        return PREF_MODEL_ID

    # Otherwise, discover via control plane
    next_token = None
    matches = []
    try:
        while True:
            kwargs = {"maxResults": 100}
            if next_token:
                kwargs["nextToken"] = next_token
            resp = bedrock_cp.list_inference_profiles(**kwargs)
            for s in resp.get("inferenceProfileSummaries", []):
                name = s.get("name", "").lower()
                if CLAUDE37_NAME_PART in name:
                    # Prefer the short ID if present; otherwise use ARN
                    prof_id = s.get("inferenceProfileId") or s.get("inferenceProfileArn")
                    if prof_id:
                        matches.append(prof_id)
            next_token = resp.get("nextToken")
            if not next_token:
                break
    except ClientError as e:
        # If we cannot list, surface a clear error so you can fix IAM.
        raise RuntimeError(f"Failed to list inference profiles in {REGION}: {e}")

    if not matches:
        raise RuntimeError(
            "Claude 3.7 Sonnet inference profile not found in eu-north-1. "
            "Make sure model access is enabled in Bedrock console for Claude 3.7 Sonnet."
        )

    # If multiple (unlikely), take the first.
    return matches[0]


def lambda_handler(event, context):
    # --- Fetch facts from DynamoDB ---
    response = table.scan()
    items = response.get("Items", [])
    if not items:
        return _ok({"fact": "No facts available in DynamoDB."})

    fact = (random.choice(items) or {}).get("FactText", "")
    if not fact:
        return _ok({"fact": "No facts available in DynamoDB."})

    # --- Find the correct model/profile ID (cached if you set MODEL_ID) ---
    try:
        model_id = _discover_claude37_profile_id()
    except Exception as e:
        # Fail safe: return original fact with clear log
        print(f"Bedrock profile discovery error: {e}")
        return _ok({"fact": fact})

    # --- Prepare Bedrock request ---
    messages = [{
        "role": "user",
        "content": (
            "Take this cloud computing fact and make it fun and engaging in "
            f"1-2 sentences maximum. Keep it short and witty: {fact}"
        ),
    }]

    body = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 100,
        "messages": messages,
        "temperature": 0.7,
        # "thinking": {"type": "enabled", "budget_tokens": 512},  # optional
    }

    witty_fact = fact  # fallback if Bedrock fails
    try:
        resp = bedrock_rt.invoke_model(
            modelId=model_id,
            body=json.dumps(body),
            accept="application/json",
            contentType="application/json",
        )
        result = json.loads(resp["body"].read())

        for block in result.get("content", []):
            if block.get("type") == "text" and block.get("text"):
                witty_fact = block["text"].strip()
                break

        if not witty_fact or len(witty_fact) > 300:
            witty_fact = fact

    except Exception as e:
        print(f"Bedrock invoke error: {e}")

    return _ok({"fact": witty_fact})


def _ok(payload: dict):
    return {
        "statusCode": 200,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type"
        },
        "body": json.dumps(payload)
    }
