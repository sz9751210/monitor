from utils.cert import get_ssl_cert_info


class DomainService:
    def __init__(self, repo, cloudflare_manager):
        self.repo = repo
        self.cloudflare_manager = cloudflare_manager

    def get_domain_info(self, domain):
        get_result = self.repo.get_domain_from_mongodb(domain)
        if get_result:
            simplified_result = {
                "domain": domain,
                "subdomains": get_result.get("subdomains", []),
            }
            return simplified_result
        else:
            raise Exception(f"Domain not found for  {domain}")

    def get_subdomain_info(self, subdomain):
        subdomain_data = self.repo.get_subdomain_data_from_mongodb(subdomain)
        if subdomain_data:
            return subdomain_data
        else:
            raise Exception(f"No subdomain information found for {subdomain}")

    def get_all_domains(self):
        all_domains = self.repo.get_all_domains_from_mongodb()
        if all_domains:
            return all_domains
        else:
            raise Exception(f"Domains not found")

    def add_subdomain(self, domain, subdomain):
        if get_ssl_cert_info(subdomain, check_only=True):
            return self.repo.add_subdomain_to_mongodb(domain, subdomain)
        else:
            raise ValueError("證書檢查失敗, 請檢查輸入的 subdomain 是否正確。")

    def bulk_add_subdomains(self, domain, subdomains):
        failed_subdomains = []
        for subdomain in subdomains:
            if not get_ssl_cert_info(domain, check_only=True):
                failed_subdomains.append(subdomain)
                continue
            self.repo.add_subdomain_to_mongodb(domain, subdomain)
        if failed_subdomains:
            raise ValueError(
                f"以下 subdomain 證書檢查失敗,請檢查輸入是否正確：{', '.join(failed_subdomains)}"
            )

    def update_subdomain(self, domain, origin_subdomain, new_subdomain):
        if get_ssl_cert_info(new_subdomain, check_only=True):
            result = self.repo.update_subdomain_in_mongodb(
                domain, origin_subdomain, new_subdomain
            )
            if not result:
                raise Exception("更新失敗，請檢查輸入的資料。")
            return result
        else:
            raise ValueError("證書檢查失敗, 請檢查輸入的 subdomain 是否正確。")

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

    def process_domains(self):
        domains = self.cloudflare_manager.fetch_all_domains_and_records()
        domain_dict = self.cloudflare_manager.convert_domains_to_dict(domains)
        failed_domains = []
        valid_domains = []

        for domain, subdomains in domain_dict.items():
            for subdomain in subdomains:
                if not get_ssl_cert_info(subdomain, check_only=True):
                    failed_domains.append(subdomain)
                    continue
                self.repo.save_domains_to_mongodb(domain, subdomain)
            valid_domains.append(domain)

        if failed_domains:
            raise ValueError(
                f"以下 Subdomain 證書檢查失敗,請檢查輸入是否正確：{', '.join(failed_domains)}"
            )

        return valid_domains

    def disable_subdomain(self, subdomain):
        return self.repo.disable_subdomain(subdomain)

    def enable_subdomain(self, subdomain):
        return self.repo.enable_subdomain(subdomain)
