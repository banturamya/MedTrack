# AWS Services Integration Module
# Healthcare Management System (MedTrack)

import logging
import os
import uuid
from datetime import date, datetime
from typing import Any, Dict, List, Tuple

from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

DATABASE_TYPE = os.getenv("DATABASE_TYPE", "memory").strip().lower()
AWS_REGION = os.getenv("AWS_REGION", "us-east-1").strip()
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID", "").strip()
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY", "").strip()
USERS_TABLE = os.getenv("USERS_TABLE", "MedTrack_Users").strip()
APPOINTMENTS_TABLE = os.getenv("APPOINTMENTS_TABLE", "MedTrack_Appointments").strip()
NOTIFICATIONS_TABLE = os.getenv("NOTIFICATIONS_TABLE", "MedTrack_Notifications").strip()
SNS_TOPIC_ARN = os.getenv("SNS_TOPIC_ARN", "").strip()
ENABLE_SNS_NOTIFICATIONS = os.getenv("ENABLE_SNS_NOTIFICATIONS", "false").strip().lower() == "true"


def _aws_kwargs() -> Dict[str, str]:
    kwargs: Dict[str, str] = {"region_name": AWS_REGION}

    # Keep IAM role auth as default; only inject keys when explicitly provided.
    if AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY:
        kwargs["aws_access_key_id"] = AWS_ACCESS_KEY_ID
        kwargs["aws_secret_access_key"] = AWS_SECRET_ACCESS_KEY

    return kwargs


def _get_boto3():
    try:
        import boto3

        return boto3
    except Exception as exc:
        logger.error("boto3 is unavailable: %s", str(exc))
        return None


def _get_dynamodb_tables():
    if DATABASE_TYPE != "dynamodb":
        return None, None, None

    boto3 = _get_boto3()
    if boto3 is None:
        return None, None, None

    try:
        dynamodb = boto3.resource("dynamodb", **_aws_kwargs())
        return (
            dynamodb.Table(USERS_TABLE),
            dynamodb.Table(APPOINTMENTS_TABLE),
            dynamodb.Table(NOTIFICATIONS_TABLE),
        )
    except Exception as exc:
        logger.error("Failed to initialize DynamoDB tables: %s", str(exc))
        return None, None, None


def _scan_all(table) -> List[Dict[str, Any]]:
    items: List[Dict[str, Any]] = []
    response = table.scan()
    items.extend(response.get("Items", []))

    while "LastEvaluatedKey" in response:
        response = table.scan(ExclusiveStartKey=response["LastEvaluatedKey"])
        items.extend(response.get("Items", []))

    return items


def _serialize(item: Dict[str, Any]) -> Dict[str, Any]:
    serialized: Dict[str, Any] = {}
    for key, value in item.items():
        if isinstance(value, (datetime, date)):
            serialized[key] = value.isoformat()
        else:
            serialized[key] = value
    return serialized


def load_runtime_data(
    default_users: Dict[str, Dict[str, Any]],
    default_appointments: Dict[str, Dict[str, Any]],
) -> Tuple[Dict[str, Dict[str, Any]], Dict[str, Dict[str, Any]], List[Dict[str, Any]]]:
    if DATABASE_TYPE != "dynamodb":
        logger.info("Using in-memory data store")
        return dict(default_users), dict(default_appointments), []

    users_table, appointments_table, notifications_table = _get_dynamodb_tables()
    if not all([users_table, appointments_table, notifications_table]):
        logger.warning("Falling back to in-memory data due to DynamoDB initialization issue")
        return dict(default_users), dict(default_appointments), []

    try:
        users_items = _scan_all(users_table)
        appointment_items = _scan_all(appointments_table)
        notification_items = _scan_all(notifications_table)

        users = {item["user_id"]: item for item in users_items if "user_id" in item}
        appointments = {
            item["appointment_id"]: item
            for item in appointment_items
            if "appointment_id" in item
        }

        # Seed tables when they are empty.
        if not users:
            for user in default_users.values():
                users_table.put_item(Item=_serialize(user))
            users = dict(default_users)

        if not appointments:
            for appointment in default_appointments.values():
                appointments_table.put_item(Item=_serialize(appointment))
            appointments = dict(default_appointments)

        logger.info(
            "Loaded runtime data from DynamoDB: %s users, %s appointments, %s notifications",
            len(users),
            len(appointments),
            len(notification_items),
        )
        return users, appointments, notification_items
    except Exception as exc:
        logger.error("Failed to load data from DynamoDB: %s", str(exc))
        return dict(default_users), dict(default_appointments), []


def persist_user(user: Dict[str, Any]) -> bool:
    users_table, _, _ = _get_dynamodb_tables()
    if not users_table:
        return False

    try:
        users_table.put_item(Item=_serialize(user))
        return True
    except Exception as exc:
        logger.error("Failed to persist user: %s", str(exc))
        return False


def persist_appointment(appointment: Dict[str, Any]) -> bool:
    _, appointments_table, _ = _get_dynamodb_tables()
    if not appointments_table:
        return False

    try:
        appointments_table.put_item(Item=_serialize(appointment))
        return True
    except Exception as exc:
        logger.error("Failed to persist appointment: %s", str(exc))
        return False


def persist_notification(notification: Dict[str, Any]) -> bool:
    _, _, notifications_table = _get_dynamodb_tables()
    if not notifications_table:
        return False

    try:
        payload = dict(notification)
        payload.setdefault("notification_id", str(uuid.uuid4()))
        payload.setdefault("created_at", datetime.utcnow().isoformat())
        notifications_table.put_item(Item=_serialize(payload))
        return True
    except Exception as exc:
        logger.error("Failed to persist notification: %s", str(exc))
        return False


def publish_sns_notification(subject: str, message: str) -> bool:
    if not ENABLE_SNS_NOTIFICATIONS:
        return False

    if not SNS_TOPIC_ARN:
        logger.warning("SNS_TOPIC_ARN is not configured, skipping SNS publish")
        return False

    boto3 = _get_boto3()
    if boto3 is None:
        return False

    try:
        sns_client = boto3.client("sns", **_aws_kwargs())
        sns_client.publish(TopicArn=SNS_TOPIC_ARN, Subject=subject[:100], Message=message)
        return True
    except Exception as exc:
        logger.error("Failed to publish SNS notification: %s", str(exc))
        return False
