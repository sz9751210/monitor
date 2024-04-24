import schedule
from utils.cert import check_ssl_expiration


def perform_ssl_checks(bot, service, chat_id):
    domain_data = service.get_domain_envs()
    for platform_data in domain_data:
        platform = platform_data["platform"]
        envs = platform_data["envs"]
        for env, domains in envs.items():
            for domain in domains:
                cert_info = service.get_cert_info(domain)
                check_ssl_expiration(domain, cert_info, env, platform)
    bot.send_message(
        chat_id, "所有 domain 的 SSL 到期時間檢查完成。", parse_mode="Markdown"
    )


def setup_scheduler(bot, service, chat_id):
    schedule.every().day.at("09:00").do(
        perform_ssl_checks,
        bot,
        service,
        chat_id,
    )
