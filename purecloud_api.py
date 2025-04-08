import os
import base64
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import requests
import certifi
from dotenv import load_dotenv

load_dotenv()

class PureCloudAPI:
    def __init__(self) -> None:
        self.environment: Optional[str] = os.getenv("ENVIRONMENT")
        self.client_id: Optional[str] = os.getenv("CLIENT_ID")
        self.client_secret: Optional[str] = os.getenv("CLIENT_SECRET")
        if not all([self.environment, self.client_id, self.client_secret]):
            raise ValueError("Credenciais não configuradas corretamente no arquivo .env")
        ssl_verify_env = os.getenv("SSL_VERIFY", "true").lower()
        if ssl_verify_env in ["false", "0"]:
            self.ssl_verify = False
            logging.warning("Verificação de certificado SSL desabilitada!")
        else:
            self.ssl_verify = certifi.where()

    def get_oauth_token(self) -> Optional[str]:
        url = f"https://login.{self.environment}/oauth/token"
        payload = {"grant_type": "client_credentials"}
        auth_str = f"{self.client_id}:{self.client_secret}"
        auth_bytes = auth_str.encode("utf-8")
        authorization = base64.b64encode(auth_bytes).decode("utf-8")
        headers = {
            "Authorization": f"Basic {authorization}",
            "Content-Type": "application/x-www-form-urlencoded"
        }
        try:
            response = requests.post(url, data=payload, headers=headers, verify=self.ssl_verify)
            response.raise_for_status()
            return response.json().get("access_token")
        except requests.HTTPError as e:
            logging.exception(f"HTTP error em get_oauth_token: {e.response.text}")
        except requests.RequestException as e:
            logging.exception(f"Erro de requisição em get_oauth_token: {str(e)}")
        return None

    def get_users(self, access_token: str) -> List[Dict[str, Any]]:
        users: List[Dict[str, Any]] = []
        params = {
            "pageSize": 500,
            "pageNumber": 1,
            "sortOrder": "ASC",
            "state": "any"
        }
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": f"Bearer {access_token}"
        }
        while True:
            url = f"https://api.{self.environment}/api/v2/users"
            try:
                response = requests.get(url, headers=headers, params=params, verify=self.ssl_verify)
                response.raise_for_status()
                data = response.json()
            except requests.HTTPError as e:
                logging.exception(f"HTTP error em get_users: {e.response.text}")
                break
            except requests.RequestException as e:
                logging.exception(f"Erro de requisição em get_users: {str(e)}")
                break

            entities = data.get("entities", [])
            if not entities:
                break

            for i in entities:
                user = {
                    "id": i.get("id"),
                    "email": i.get("email"),
                    "title": i.get("title", "").upper(),
                    "manager": i.get("manager", {}).get("id", "")
                }
                users.append(user)
            params["pageNumber"] += 1
        return users

    def get_user_time(
        self,
        access_token: str,
        user: Dict[str, Any],
        start_date: datetime,
        end_date: datetime
    ) -> List[Dict[str, Any]]:
        rows: List[Dict[str, Any]] = []
        current_date = start_date
        while current_date <= end_date:
            next_date = current_date + timedelta(days=1)
            interval = f"{current_date.strftime('%Y-%m-%dT03:00:00.000Z')}/{next_date.strftime('%Y-%m-%dT03:00:00.000Z')}"
            payload = {
                "interval": interval,
                "groupBy": ["userId"],
                "filter": {
                    "type": "or",
                    "predicates": [
                        {
                            "type": "dimension",
                            "dimension": "userId",
                            "operator": "matches",
                            "value": user["id"]
                        }
                    ]
                },
                "metrics": [
                    "tAgentRoutingStatus",
                    "tOrganizationPresence",
                    "tSystemPresence"
                ]
            }
            url = f"https://api.{self.environment}/api/v2/analytics/users/aggregates/query"
            headers = {
                "Content-Type": "application/json",
                "Accept": "application/json",
                "Authorization": f"Bearer {access_token}"
            }
            try:
                response = requests.post(url, headers=headers, json=payload, verify=self.ssl_verify)
                response.raise_for_status()
                data = response.json()
            except requests.HTTPError as e:
                logging.exception(f"HTTP error para {user['email']} em {current_date.strftime('%d/%m/%Y')}: {e.response.text}")
                current_date = next_date
                continue
            except requests.RequestException as e:
                logging.exception(f"Erro de requisição para {user['email']} em {current_date.strftime('%d/%m/%Y')}: {str(e)}")
                current_date = next_date
                continue

            metrics_data: Dict[str, Any] = {}
            for group in data.get("results", []):
                for item in group.get("data", []):
                    for metric in item.get("metrics", []):
                        key = f"{metric['metric']}_{metric['qualifier']}"
                        metrics_data[key] = metric["stats"].get("sum", 0)

            user_time = {
                "DATE": current_date.strftime("%d/%m/%Y"),
                "USER_ID": user["id"],
                "USER_EMAIL": user["email"],
                "LOGGED_IN": 0,
                "ON_QUEUE": metrics_data.get("tSystemPresence_ON_QUEUE", 0),
                "OFF_QUEUE": 0,
                "INTERACTING": metrics_data.get("tAgentRoutingStatus_INTERACTING", 0),
                "IDLE": metrics_data.get("tAgentRoutingStatus_IDLE", 0),
                "NOT_RESPONDING": metrics_data.get("tAgentRoutingStatus_NOT_RESPONDING", 0),
                "AVAILABLE": metrics_data.get("tSystemPresence_AVAILABLE", 0),
                "AWAY": metrics_data.get("tSystemPresence_AWAY", 0),
                "BREAK": metrics_data.get("tSystemPresence_BREAK", 0),
                "BUSY": metrics_data.get("tSystemPresence_BUSY", 0),
                "SYSTEM_AWAY": metrics_data.get("tSystemPresence_IDLE", 0),
                "MEAL": metrics_data.get("tSystemPresence_MEAL", 0),
                "MEETING": metrics_data.get("tSystemPresence_MEETING", 0),
                "TRAINING": metrics_data.get("tSystemPresence_TRAINING", 0)
            }
            user_time["OFF_QUEUE"] = (
                user_time["AVAILABLE"] +
                user_time["AWAY"] +
                user_time["BREAK"] +
                user_time["BUSY"] +
                user_time["MEAL"] +
                user_time["MEETING"] +
                user_time["TRAINING"]
            )
            user_time["LOGGED_IN"] = user_time["ON_QUEUE"] + user_time["OFF_QUEUE"]

            rows.append(user_time)
            current_date = next_date
        return rows

def find_user_by_login(login: str, users: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    for user in users:
        email = user.get("email", "")
        if email.split("@")[0].lower() == login.lower():
            return user
    return None
