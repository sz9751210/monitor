import requests


class CloudflareManager:
    def __init__(self, api_key, email):
        self.api_key = api_key
        self.email = email
        self.base_url = "https://api.cloudflare.com/client/v4/zones"

    def fetch_all_domains_and_records(self):
        headers = {
            "X-Auth-Email": self.email,
            "X-Auth-Key": self.api_key,
            "Content-Type": "application/json",
        }

        response = requests.get(self.base_url, headers=headers)
        zones = response.json().get("result", [])
        all_domains_info = []

        for zone in zones:
            domain_name = zone["name"]
            records_url = f"{self.base_url}/{zone['id']}/dns_records"
            records_response = requests.get(records_url, headers=headers)
            records = records_response.json().get("result", [])

            for record in records:
                if record["type"] in ["A", "CNAME"]:
                    subdomain = record["name"]
                    if subdomain.startswith("_"):
                        continue
                    all_domains_info.append((domain_name, subdomain))
        return all_domains_info

    def convert_domains_to_dict(self, domain_tuples):
        domain_dict = {}
        for main_domain, subdomain in domain_tuples:
            if main_domain in domain_dict:
                domain_dict[main_domain].append(subdomain)
            else:
                domain_dict[main_domain] = [subdomain]
        return domain_dict
