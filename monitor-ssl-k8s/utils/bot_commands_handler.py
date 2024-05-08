from utils.cert import parse_ssl_cert_info, check_ssl_expiration
from utils.utils import convert_to_yaml


def setup_handlers(bot, service):
    @bot.message_handler(commands=["get"])
    def handle_get_command(message):
        try:
            _, platform, env = message.text.split(maxsplit=2)
            domain_info = service.get_domain_info(platform, env)
            domain_info_yaml = convert_to_yaml(domain_info)
            bot.reply_to(message, domain_info_yaml)
        except ValueError:
            bot.reply_to(
                message,
                "使用方式不正確。請按照以下格式輸入：\n/get <platform> <env>",
            )
        except Exception as e:
            bot.reply_to(message, str(e))

    @bot.message_handler(commands=["get_platform"])
    def handle_get_platform_command(message):
        try:
            _, platform = message.text.split(maxsplit=1)
            platform_info = service.get_platform_info(platform)
            platform_info_yaml = convert_to_yaml(platform_info)
            bot.reply_to(message, platform_info_yaml)
        except ValueError:
            bot.reply_to(
                message,
                "使用方式不正確。請按照以下格式輸入：\n/get_platform <platform>",
            )
        except Exception as e:
            bot.reply_to(message, str(e))

    @bot.message_handler(commands=["get_all"])
    def handle_get_all_command(message):
        try:
            domains_data = service.get_all_domains()
            for domain_data in domains_data:
                yaml_domain_data = convert_to_yaml(domain_data)
                bot.send_message(
                    message.chat.id, f"{yaml_domain_data}", parse_mode="Markdown"
                )
        except Exception as e:
            bot.reply_to(message, str(e))

    @bot.message_handler(commands=["add"])
    def handle_add_command(message):
        try:
            _, platform, env, domain = message.text.split(maxsplit=3)
            service.add_domain(platform, env, domain)
            bot.reply_to(
                message, f"Platform {platform}, 環境為 {env}, domain {domain} 新增成功"
            )
        except ValueError:
            bot.reply_to(
                message,
                "使用方式不正確。請按照以下格式輸入：\n/add <platform> <env> <domain>",
            )
        except Exception as e:
            bot.reply_to(
                message, f"domain 新增失敗，請檢查輸入的資料。錯誤訊息：{str(e)}"
            )

    @bot.message_handler(commands=["bulk_add"])
    def handle_bulk_add_command(message):
        try:
            parts = message.text.split()
            if len(parts) < 4:
                return bot.reply_to(
                    message,
                    "使用方式不正確。請按照以下格式輸入：\n/bulk_add <platform> <env> <domain1> <domain2> ...",
                )
            platform = parts[1]
            env = parts[2]
            domains = parts[3:]
            service.bulk_add_domains(platform, env, domains)
            bot.reply_to(
                message, f"Platform {platform}, 環境 {env} 下的 domain 批量新增成功。"
            )
        except ValueError as e:
            bot.reply_to(message, str(e))
        except Exception as e:
            bot.reply_to(
                message, f"domain 批量新增失敗，請檢查輸入的資料。錯誤訊息：{str(e)}"
            )

    @bot.message_handler(commands=["update"])
    def handle_update_command(message):
        try:
            _, platform, env, origin_domain, new_domain = message.text.split(maxsplit=4)
            service.upate_domain(platform, env, origin_domain, new_domain)
            bot.reply_to(message, f"Platform {platform}, env {env}, domain 更新成功。")
        except ValueError:
            bot.reply_to(
                message,
                "使用方式不正確。請按照以下格式輸入：\n/update <platform> <env> <old_domain> <new_domain>",
            )
        except Exception as e:
            bot.reply_to(
                message, f"Domain 更新失敗，請檢查輸入的資料。錯誤訊息：{str(e)}"
            )

    @bot.message_handler(commands=["del"])
    def handle_delete_command(message):
        try:
            _, platform, env, domain = message.text.split(maxsplit=3)
            service.delete_domain(platform, env, domain)
            bot.reply_to(message, f"Platform {platform}, env {env}, domain 刪除成功。")
        except ValueError:
            bot.reply_to(
                message,
                "使用方式不正確。請按照以下格式輸入：\n/del <platform> <env> <domain>",
            )
        except Exception as e:
            bot.reply_to(
                message, f"Domain 刪除失敗，請檢查輸入的資料。錯誤訊息：{str(e)}"
            )

    @bot.message_handler(commands=["cert_info"])
    def send_cert_info(message):
        try:
            _, get_domain = message.text.split(maxsplit=1)
            cert_info = service.get_cert_info(get_domain)
            parse_cert_info = parse_ssl_cert_info(get_domain, cert_info)
            bot.send_message(message.chat.id, parse_cert_info)
        except ValueError as e:
            bot.send_message(
                message.chat.id, "請提供一個 domain。例如：/cert_info example.com"
            )
        except Exception as e:
            bot.reply_to(
                message,
                f"domain 錯誤: 無法取得 {get_domain} 的 SSL 證書資訊。錯誤訊息：{str(e)}",
            )

    @bot.message_handler(commands=["check"])
    def handle_check_command(message):
        try:
            domain_data = service.get_domain_envs()
            for platform_data in domain_data:
                platform = platform_data["platform"]
                envs = platform_data["envs"]
                for env, domains in envs.items():
                    for domain in domains:
                        cert_info = service.get_cert_info(domain)
                        check_ssl_expiration(domain, cert_info, env, platform)
            bot.reply_to(
                message, "所有 domain 的 SSL 到期時間檢查完成。", parse_mode="Markdown"
            )
        except Exception as e:
            bot.reply_to(message, str(e))

    @bot.message_handler(commands=["add_cloudflare"])
    def handle_add_command(message):
        try:
            valid_domain = service.process_domains()
            bot.reply_to(message, f"{convert_to_yaml(valid_domain)} 新增成功")
        except Exception as e:
            bot.reply_to(
                message, f"domain 新增失敗，請檢查輸入的資料。錯誤訊息：{str(e)}"
            )

    @bot.message_handler(commands=["disable"])
    def handle_disable_command(message):
        try:
            _, subdomain = message.text.split(maxsplit=1)
            service.disable_subdomain(subdomain)
            bot.reply_to(message, f"subdomain {subdomain} 停用成功")
        except ValueError:
            bot.reply_to(
                message,
                "使用方式不正確。請按照以下格式輸入：\n/disable <subdomain>",
            )
        except Exception as e:
            bot.reply_to(
                message, f"domain 停用失敗，請檢查輸入的資料。錯誤訊息：{str(e)}"
            )

    @bot.message_handler(commands=["enable"])
    def handle_enable_command(message):
        try:
            _, subdomain = message.text.split(maxsplit=1)
            service.enable_subdomain(subdomain)
            bot.reply_to(message, f"subdomain {subdomain} 啟用成功")
        except ValueError:
            bot.reply_to(
                message,
                "使用方式不正確。請按照以下格式輸入：\n/enable <subdomain>",
            )
        except Exception as e:
            bot.reply_to(
                message, f"domain 啟用失敗，請檢查輸入的資料。錯誤訊息：{str(e)}"
            )

    @bot.message_handler(commands=["help"])
    def send_help_message(message):
        help_text = """
以下是可用的命令列表及其用途：

/cert_info <domain> - 取得指定 domain 的 SSL 證書資訊。
/get_all - 從 MongoDB 取得所有 platform 及其下的所有 env 和 domain 的資訊。
/get_platform <platform> - 取得指定 platform 下所有 env 的 domain 資訊。
/get <platform> <env> - 取得指定 platform 和 env 下的所有 domain 的資訊。
/add <platform> <env> <domain> - 向 MongoDB 新增一個新的 domain 及其環境和平台。
/bulk_add <platform> <env> <domain1> <domain2> ... - 向 MongoDB 批量新增多個 domain 及其環境和平台。
/update <platform> <env> <old_domain> <new_domain> - 更新指定平台和環境下的 domain 資訊。
/del <platform> <env> <domain> - 從 MongoDB 刪除指定平台和環境下的 domain。
/check - 檢查所有 domain 的 SSL 到期時間並通知。

請根據需要使用上述命令。
"""
        bot.send_message(message.chat.id, help_text)
