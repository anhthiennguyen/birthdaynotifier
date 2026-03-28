import json
import os
import boto3
import urllib.request
import urllib.parse
from datetime import datetime
import pytz

def lambda_handler(event, context):
    # Get current date in Pacific Time
    pacific = pytz.timezone("America/Los_Angeles")
    now = datetime.now(pacific)
    today = now.strftime("%m-%d")

    # Load contacts from S3 (or bundled JSON if running locally)
    contacts = load_contacts()

    # Find today's birthdays
    birthdays_today = [c for c in contacts if c["birthday"] == today]

    if not birthdays_today:
        print(f"No birthdays today ({today} PT)")
        return {"statusCode": 200, "body": "No birthdays today"}

    api_key = os.environ["TEXTBELT_API_KEY"]

    results = []
    for contact in birthdays_today:
        name = contact["name"]
        phone = contact["phone"]
        message = f"Happy Birthday, {name}! Wishing you an amazing day filled with joy and celebration!"

        try:
            payload = urllib.parse.urlencode({
                "phone": phone,
                "message": message,
                "key": api_key,
            }).encode()
            req = urllib.request.Request(
                "https://textbelt.com/text",
                data=payload,
                method="POST"
            )
            with urllib.request.urlopen(req) as resp:
                result = json.loads(resp.read().decode())

            if result.get("success"):
                print(f"Sent birthday message to {name} ({phone}): textId={result.get('textId')}")
                results.append({"name": name, "status": "sent", "textId": result.get("textId")})
            else:
                print(f"TextBelt rejected message to {name}: {result.get('error')}")
                results.append({"name": name, "status": "failed", "error": result.get("error")})
        except Exception as e:
            print(f"Failed to send to {name} ({phone}): {e}")
            results.append({"name": name, "status": "failed", "error": str(e)})

    return {"statusCode": 200, "body": json.dumps(results)}


def load_contacts():
    # Try S3 first (for deployed Lambda), fall back to bundled contacts.json
    s3_bucket = os.environ.get("CONTACTS_S3_BUCKET")
    s3_key = os.environ.get("CONTACTS_S3_KEY", "contacts.json")

    if s3_bucket:
        s3 = boto3.client("s3")
        obj = s3.get_object(Bucket=s3_bucket, Key=s3_key)
        return json.loads(obj["Body"].read().decode("utf-8"))

    # Fall back to local contacts.json bundled with the Lambda package
    local_path = os.path.join(os.path.dirname(__file__), "contacts.json")
    with open(local_path, "r") as f:
        return json.load(f)
