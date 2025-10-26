import json
import logging
from typing import Any, Dict
from urllib.parse import quote_plus

import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)


def get_secret(region_name: str, secret_name: str) -> Dict[str, Any]:
    """
    Fetch secret from AWS Secrets Manager.
    
    Args:
        region_name: AWS region (e.g., 'us-east-1')
        secret_name: Full secret name/ARN
        
    Returns:
        Dict containing the secret values
        
    Raises:
        ClientError: If secret cannot be retrieved
        ValueError: If secret doesn't contain SecretString
    """
    session = boto3.session.Session()
    client = session.client(
        service_name='secretsmanager',
        region_name=region_name
    )

    try:
        response = client.get_secret_value(SecretId=secret_name)
    except ClientError:
        logger.error(f"Failed to retrieve secret: {secret_name}", exc_info=True)
        raise

    if 'SecretString' not in response:
        logger.error(f"Secret {secret_name} does not contain SecretString")
        raise ValueError(f"Secret does not contain SecretString: {secret_name}")

    return json.loads(response['SecretString'])


def build_database_url_from_secret(secret: Dict[str, Any]) -> str:
    """
    Construct PostgreSQL connection URL from secret dictionary.
    
    Expected secret format:
    {
        "username": "dbadmin",
        "password": "...",
        "host": "database.cluster-xxxxx.region.rds.amazonaws.com",
        "port": 5432,
        "dbname": "database_name"
    }
    
    Returns:
        PostgreSQL connection string
    """
    username = secret['username']
    password = secret['password']
    host = secret['host']
    port = secret['port']
    dbname = secret['dbname']
    
    # URL-encode password to handle special characters
    encoded_password = quote_plus(password)
    
    return f"postgresql://{username}:{encoded_password}@{host}:{port}/{dbname}"
