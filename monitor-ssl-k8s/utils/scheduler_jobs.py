import schedule
from utils.cert import check_ssl_expiration


def perform_ssl_checks(bot, service, chat_id):
    try:
        domains_data = service.get_all_domains()
        for domain_data in domains_data:
            subdomains_list = domain_data["subdomains"]
            for subdomain_dict in subdomains_list:
                subdomain = subdomain_dict["name"]
                subdomain_status = subdomain_dict["enable"]
                if subdomain_status == True:
                    cert_info = service.get_cert_info(subdomain)
                    # 假設有函數 check_ssl_expiration 來檢查 SSL 證書的到期時間
                    check_ssl_expiration(subdomain, cert_info)
        # 通知用戶所有檢查都已完成
        bot.send_message(chat_id, "所有 domain 的 SSL 到期時間檢查完成。", parse_mode="Markdown")
    except Exception as e:
        bot.send_message(chat_id, str(e))  # 處理錯誤，並回報給用戶



def setup_scheduler(bot, service, chat_id):
    schedule.every().day.at("09:00").do(
        perform_ssl_checks,
        bot,
        service,
        chat_id,
    )
