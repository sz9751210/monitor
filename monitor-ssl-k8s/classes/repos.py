import logging
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def init_mongo_client(mongodb_uri):
    try:
        client = MongoClient(mongodb_uri)
        info = client.server_info()
        logger.info(f"MongoDB 連接成功。Mongo 版本為 {info['version']}")
        return client
    except ConnectionFailure:
        logger.error("MongoDB 連接失敗。請檢查您的連接設置和 Server 狀態。")
        return None


def get_collection(mongo_client, collection_name):
    db = mongo_client.get_database()
    collection = db[collection_name]
    return collection


class DomainRepo:
    def __init__(self, collection):
        self.collection = collection
        self.logger = logging.getLogger(__name__)

    def get_domain_from_mongodb(self, domain):
        query = {"domain": domain}
        result = self.collection.find_one(query)

        if result:
            self.logger.info(f"找到 '{domain}' 的訊息。")
            return {"domain": domain, "subdomains": result.get("subdomains", [])}
        else:
            self.logger.info(f"未找到 '{domain}' 的訊息。")
            return None

    def get_subdomain_data_from_mongodb(self, subdomain):
        # 使用 MongoDB 的 $elemMatch 來匹配子陣列中的元素
        query = {"subdomains": {"$elemMatch": {"name": subdomain}}}
        result = self.collection.find_one(query)

        if result:
            # 從結果中提取子域名資訊
            subdomain_info = next((item for item in result["subdomains"] if item["name"] == subdomain), None)
            if subdomain_info:
                self.logger.info(f"Found subdomain information for '{subdomain}'.")
                # 返回子域名和它所屬的主域名
                return {"subdomain": subdomain, "domain": result["domain"], "check": subdomain_info.get("check")}
            else:
                self.logger.info(f"Subdomain '{subdomain}' not found in the results.")
                return None
        else:
            self.logger.info(f"No domain information found containing subdomain '{subdomain}'.")
            return None

    def get_all_domains_from_mongodb(self):
        try:
            domain_envs = []
            results = self.collection.find({})
            for item in results:
                platform = item.get("platform")
                envs = item.get("envs", {})
                if platform:
                    domain_envs.append({"platform": platform, "envs": envs})
            return domain_envs
        except Exception as e:
            self.logger.info(f"從 MongoDB 讀取資料失敗: {e}")
            return {}

    def add_domain_to_mongodb(self, platform, env, domain):
        try:
            result = self.collection.update_one(
                {"platform": platform},
                {"$addToSet": {f"envs.{env}": domain}},
                upsert=True,
            )
            if not (result.matched_count > 0 or result.upserted_id is not None):
                raise Exception("無法添加 domain 到 MongoDB")
        except Exception as e:
            self.logger.error("添加 domain 失敗: %s", str(e))
            raise

    def write_domain_data_to_mongodb(self, domain_data):
        for platform, envs in domain_data.items():
            document = {"platform": platform, "envs": envs}
            self.collection.insert_one(document)
        self.logger.info("資料已成功寫入 MongoDB。")

    def update_domain_in_mongodb(self, platform, env, origin_domain, new_domain):
        query = {"platform": platform, f"envs.{env}": origin_domain}
        update_action = {"$set": {f"envs.$[elem]": new_domain}}
        array_filters = [{"elem": origin_domain}]
        update_result = self.collection.update_one(
            query, update_action, arrayFilters=array_filters
        )

        return update_result.modified_count > 0

    def delete_domain(self, platform, env, domain_to_delete):
        query = {"platform": platform}
        delete_action = {"$pull": {f"envs.{env}": domain_to_delete}}
        result = self.collection.update_one(query, delete_action)

        return result.modified_count > 0

    def save_domains_to_mongodb(self, domain, subdomain):
        domain_info = {"name": subdomain, "check": "enable"}
        try:
            filter = {"domain": domain}
            update = {"$addToSet": {"subdomains": domain_info}}
            result = self.collection.update_one(filter, update, upsert=True)
            if not (result.matched_count > 0 or result.upserted_id is not None):
                raise Exception("無法添加 domain 到 MongoDB")
        except Exception as e:
            self.logger.error("添加 domain 失敗: %s", str(e))
            raise

    def disable_subdomain(self, subdomain):
        try:
            filter = {"subdomains.name": subdomain}
            update = {"$set": {"subdomains.$.check": "disable"}}
            result = self.collection.update_one(filter, update)
            if result.modified_count == 0:
                raise Exception("未找到指定的 subdomain 或已 disable")
            return True
        except Exception as e:
            self.logger.error("disable subdomain 失敗: %s", str(e))
            raise

    def enable_subdomain(self, subdomain):
        try:
            filter = {"subdomains.name": subdomain}
            update = {"$set": {"subdomains.$.check": "enable"}}
            result = self.collection.update_one(filter, update)
            if result.modified_count == 0:
                raise Exception("未找到指定的 subdomain 或已 enable")
            return True
        except Exception as e:
            self.logger.error("enable subdomain 失敗: %s", str(e))
            raise
