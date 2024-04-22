import schedule
from cert import get_ssl_cert_info, check_ssl_expiration
from mongo import load_domain_envs_from_mongodb


def perform_ssl_checks(
    bot, collection, chat_id, platform, telegram_bot_token, telegram_group_id
):
    domain_data = load_domain_envs_from_mongodb(collection)
    for env, domains in domain_data.items():
        for domain in domains:
            cert = get_ssl_cert_info(domain, check_only=False)
            check_ssl_expiration(
                domain, cert, env, platform, telegram_bot_token, telegram_group_id
            )
    bot.send_message(
        chat_id, "所有 domain 的 SSL 到期時間檢查完成。", parse_mode="Markdown"
    )


def setup_scheduler(
    bot, collection, chat_id, platform, telegram_bot_token, telegram_group_id
):
    schedule.every(10).seconds.do(
        perform_ssl_checks,
        bot,
        collection,
        chat_id,
        platform,
        telegram_bot_token,
        telegram_group_id,
    )
