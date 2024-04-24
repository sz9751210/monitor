from utils.cert import get_ssl_cert_info


class DomainService:
    def __init__(self, repo):
        self.repo = repo

    def get_domain_info(self, platform, env):
        get_result = self.repo.get_domain_from_mongodb(platform, env)
        if get_result:
            simplified_result = {
                "platform": platform,
                "env": env,
                "domains": get_result.get("domains", []),
            }
            return simplified_result
        else:
            raise Exception(f"Domain not found for platform {platform} and env {env}")

    def get_platform_info(self, platform):
        platform_data = self.repo.get_platform_data_from_mongodb(platform)
        if platform_data:
            return platform_data
        else:
            raise Exception(f"No domain information found for platform {platform}")

    def get_all_domains(self):
        all_domains = self.repo.get_all_domains_from_mongodb()
        if all_domains:
            return all_domains
        else:
            raise Exception(f"Domains not found")


    def add_domain(self, platform, env, domain):
        if get_ssl_cert_info(domain, check_only=True):
            return self.repo.add_domain_to_mongodb(platform, env, domain)
        else:
            raise ValueError("證書檢查失敗, 請檢查輸入的 domain 是否正確。")

    def bulk_add_domains(self, platform, env, domains):
        failed_domains = []
        for domain in domains:
            if not get_ssl_cert_info(domain, check_only=True):
                failed_domains.append(domain)
                continue
            self.repo.add_domain_to_mongodb(platform, env, domain)
        if failed_domains:
            raise ValueError(
                f"以下 Domain 證書檢查失敗,請檢查輸入是否正確：{', '.join(failed_domains)}"
            )

    def update_domain(self, platform, env, origin_domain, new_domain):
        if get_ssl_cert_info(new_domain, check_only=True):
            result = self.repo.update_domain_in_mongodb(
                platform, env, origin_domain, new_domain
            )
            if not result:
                raise Exception("更新失敗，請檢查輸入的資料。")
            return result
        else:
            raise ValueError("證書檢查失敗, 請檢查輸入的 domain 是否正確。")

    def delete_domain(self, platform, env, domain_to_delete):
        result = self.repo.delete_domain(platform, env, domain_to_delete)
        if not result:
            raise Exception("未找到匹配的 domain 或環境，刪除未執行。")
        return result

    def get_cert_info(self, domain):
        cert = get_ssl_cert_info(domain, check_only=False)
        if cert is None or cert is False:
            raise ValueError(f"Domain {domain} 證書檢查失敗,請檢查輸入是否正確。")
        return cert
