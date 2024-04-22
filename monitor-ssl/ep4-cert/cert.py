import ssl
import socket
import requests
from datetime import datetime


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


def get_ssl_cert_expiry_date(cert):
    if cert is None:
        return None
    try:
        expire_date = datetime.strptime(cert["notAfter"], "%b %d %H:%M:%S %Y %Z")
        return expire_date
    except Exception as e:
        print(f"Error parsing SSL certificate's expiry date: {e}")
        return None


def check_ssl_expiration(
    domain, cert, env, platform, telegram_bot_token, telegram_group_id
):
    expire_date = get_ssl_cert_expiry_date(cert)
    if expire_date:
        remaining_days = (expire_date - datetime.utcnow()).days
        if remaining_days <= 30:
            message = "\n".join(
                [
                    "來源: Python",
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
