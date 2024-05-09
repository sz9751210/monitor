import ssl
import socket
import requests
from datetime import datetime
from utils.config_loader import YamlConfigLoader

yaml_loader = YamlConfigLoader("config.yaml")
telegram_config = yaml_loader.get_telegram_config()
telegram_bot_token = telegram_config["telegram_bot_token"]
telegram_group_id = telegram_config["telegram_group_id"]


def get_ssl_cert_info(domain, check_only=False):
    ssl_context = ssl.create_default_context()
    with ssl_context.wrap_socket(
        socket.socket(socket.AF_INET), server_hostname=domain
    ) as conn:
        conn.settimeout(3.0)
        try:
            conn.connect((domain, 443))
            if check_only:
                return True
            else:
                return conn.getpeercert()
        except Exception as e:
            return False if check_only else None


def parse_ssl_cert_info(domain, cert):
    if cert is None:
        return f"domain錯誤: 無法取得 {domain} 的 SSL 證書資訊。"

    issuer = dict(x[0] for x in cert["issuer"])
    subject = dict(x[0] for x in cert["subject"])
    issued_to = subject.get("commonName", subject.get("organizationName", ""))
    issued_by = issuer.get("commonName", issuer.get("organizationName", ""))
    valid_from = datetime.strptime(cert["notBefore"], "%b %d %H:%M:%S %Y %Z").strftime(
        "%Y-%m-%d"
    )
    valid_until = datetime.strptime(cert["notAfter"], "%b %d %H:%M:%S %Y %Z").strftime(
        "%Y-%m-%d"
    )

    cert_info = (
        f"Domain: {domain}\n"
        f"Issued To: {issued_to}\n"
        f"Issued By: {issued_by}\n"
        f"Valid From: {valid_from}\n"
        f"Valid Until: {valid_until}"
    )
    return cert_info


def check_ssl_cert_valid(domain):
    ssl_context = ssl.create_default_context()
    conn = ssl_context.wrap_socket(
        socket.socket(socket.AF_INET), server_hostname=domain
    )
    conn.settimeout(3.0)
    try:
        conn.connect((domain, 443))
        return True
    except Exception as e:
        print(f"無法取得 {domain} 的 SSL，錯誤：{e}")
        return False
    finally:
        conn.close()


def get_ssl_cert_expiry_date(cert):
    if cert is None:
        return None
    try:
        expire_date = datetime.strptime(cert["notAfter"], "%b %d %H:%M:%S %Y %Z")
        return expire_date
    except Exception as e:
        print(f"Error parsing SSL certificate's expiry date: {e}")
        return None


def check_ssl_expiration(subdomain, cert_info):
    expire_date = get_ssl_cert_expiry_date(cert_info)
    if expire_date:
        remaining_days = (expire_date - datetime.utcnow()).days
        if remaining_days <= 30:
            message = "\n".join(
                [
                    "來源: Cloudflare",
                    "標題: 憑證將到期",
                    f"domain : {subdomain}",
                    f"到期日: {expire_date.strftime('%Y-%m-%d')}",
                    f"剩餘天數: {remaining_days}",
                ]
            )

            print(f"{subdomain} 的 SSL 證書將在 {remaining_days} 天內過期。")
            send_notification(message, subdomain)
        else:
            print(
                f"{subdomain} 的 SSL 證書過期日期是 {expire_date.strftime('%Y-%m-%d')}。"
            )


def send_notification(message, subdomain):
    telegram_send_message_url = (
        f"https://api.telegram.org/bot{telegram_bot_token}/sendMessage"
    )
    response = requests.post(
        telegram_send_message_url, data={"chat_id": telegram_group_id, "text": message}
    )

    if response.status_code == 200:
        print(f"已為 {subdomain} 發送通知")
    else:
        print(f"為 {subdomain} 發送失敗")
