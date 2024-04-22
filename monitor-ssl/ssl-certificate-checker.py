import functions_framework
from datetime import datetime
import requests
import ssl
import socket
import os
import yaml
import logging


def get_ssl_cert_expiry_date(domain):
    ssl_context = ssl.create_default_context()
    conn = ssl_context.wrap_socket(
        socket.socket(socket.AF_INET), server_hostname=domain
    )
    conn.settimeout(3.0)
    try:
        conn.connect((domain, 443))
        ssl_info = conn.getpeercert()
        expire_date = datetime.strptime(ssl_info["notAfter"], "%b %d %H:%M:%S %Y %Z")
        return expire_date
    except Exception as e:
        print(f"無法獲取 {domain} 的 SSL 證書過期日期，錯誤：{e}")
        return None
    finally:
        conn.close()


def check_ssl_expiration(domain, env, platform, telegram_bot_token, telegram_group_id):
    expire_date = get_ssl_cert_expiry_date(domain)
    print(expire_date)
    if expire_date:
        remaining_days = (expire_date - datetime.utcnow()).days
        if remaining_days <= 30:
            message = "\n".join(
                [
                    "來源: Gitlab-Runner",
                    "標題: 憑證到期",
                    f"domain : {domain}",
                    f"到期日: {expire_date.strftime('%Y-%m-%d')}",
                    f"平台: {platform}",
                    f"環境: {env}",
                ]
            )

            print(f"{domain} 的 SSL 證書將在 {remaining_days} 天內過期。")
            send_notification(message, domain, telegram_bot_token, telegram_group_id)
        else:
            print(
                f"{domain} 的 SSL 證書過期日期是 {expire_date.strftime('%Y-%m-%d')}。"
            )


def send_notification(message, domain, telegram_bot_token, telegram_group_id):
    telegram_send_message_url = (
        f"https://api.telegram.org/bot{telegram_bot_token}/sendMessage"
    )
    response = requests.post(
        telegram_send_message_url, data={"chat_id": telegram_group_id, "text": message}
    )

    if response.status_code == 200:
        print(f"已為 {domain} 發送通知")
    else:
        print(f"為 {domain} 發送失敗")


def load_data_from_yaml(yaml_file_path, key):
    try:
        with open(yaml_file_path, "r", encoding="utf-8") as file:
            data = yaml.safe_load(file)
            return data.get(key, {})
    except FileNotFoundError as e:
        logging.error(f"YAML檔案未找到: {e}")
        return {}
    except Exception as e:
        logging.error(f"讀取YAML檔案時發生錯誤: {e}")
        return {}


def get_env_variable(name, default_value="未設定"):
    return os.environ.get(name, default_value)


@functions_framework.http
def check_ssl_cloud_function(request):
    """HTTP Cloud Function for checking SSL certificate expiration."""
    platform = get_env_variable("PLATFORM")
    telegram_bot_token = get_env_variable("TELEGRAM_BOT_TOKEN")
    telegram_group_id = get_env_variable("TELEGRAM_GROUP_ID")
    yaml_file_path = "domains.yaml"
    domain_envs = load_data_from_yaml(yaml_file_path, "domain_envs")
    for env, domains in domain_envs.items():
        for domain in domains:
            check_ssl_expiration(
                domain, env, platform, telegram_bot_token, telegram_group_id
            )
    return "SSL 檢查完成"
