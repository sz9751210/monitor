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
            subdomain_info = next(
                (item for item in result["subdomains"] if item["name"] == subdomain),
                None,
            )
            if subdomain_info:
                self.logger.info(f"Found subdomain information for '{subdomain}'.")
                # 返回子域名和它所屬的主域名
                return {
                    "subdomain": subdomain,
                    "domain": result["domain"],
                    "check": subdomain_info.get("check"),
                }
            else:
                self.logger.info(f"Subdomain '{subdomain}' not found in the results.")
                return None
        else:
            self.logger.info(
                f"No domain information found containing subdomain '{subdomain}'."
            )
            return None

    def get_all_domains_from_mongodb(self):
        try:
            domain_envs = []
            results = self.collection.find({})
            for item in results:
                domain = item.get("domain", {})
                subdomains = item.get("subdomains", [])
                if domain:
                    domain_envs.append({"domain": domain, "subdomains": subdomains})
            return domain_envs
        except Exception as e:
            self.logger.info(f"從 MongoDB 讀取資料失敗: {e}")
            return {}

    def add_subdomain_to_mongodb(self, domain, subdomain):
        subdomain_info = {"name": subdomain, "check": "enable"}
        try:
            # 檢查子域名是否已經存在於該域名下
            if (
                self.collection.count_documents(
                    {"domain": domain, "subdomains.name": subdomain}
                )
                > 0
            ):
                self.logger.info(
                    f"subdomain '{subdomain}' 已存在於 domain '{domain}' 下，不進行新增。"
                )
                return False

            # 如果子域名不存在，則進行添加
            filter = {"domain": domain}
            update = {
                "$addToSet": {"subdomains": subdomain_info}
            }  # 使用 $addToSet 以避免重複添加
            result = self.collection.update_one(filter, update, upsert=True)
            if not (result.matched_count > 0 or result.upserted_id is not None):
                raise Exception("無法添加 subdomain 到 MongoDB")

            self.logger.info(
                f"subdomain '{subdomain}' 已成功新增至 domain '{domain}'。"
            )
            return True
        except Exception as e:
            self.logger.error("添加 subdomain 失敗: %s", str(e))
            raise

    def write_domain_data_to_mongodb(self, domain_data):
        for platform, envs in domain_data.items():
            document = {"platform": platform, "envs": envs}
            self.collection.insert_one(document)
        self.logger.info("資料已成功寫入 MongoDB。")

    def update_subdomain_in_mongodb(self, domain, origin_subdomain, new_subdomain):
        try:
            query = {
                "domain": domain,
                "subdomains": {"$elemMatch": {"name": origin_subdomain}},
            }
            update = {"$set": {"subdomains.$.name": new_subdomain}}
            result = self.collection.update_one(query, update)
            if result.modified_count == 0:
                if self.collection.count_documents(query) == 0:
                    self.logger.info(
                        f"未找到 domain '{domain}' 的 subdomain '{origin_subdomain}'。"
                    )
                    return False
            return True
        except Exception as e:
            self.logger.error(
                f"更新 subdomain '{origin_subdomain}' 至 '{new_subdomain}' 失敗: {str(e)}"
            )
            return False

    def delete_subdomain(self, subdomain_to_delete):
        try:
            # 建構查詢來找到包含子 subdomain 的文檔
            query = {"subdomains.name": subdomain_to_delete}
            # 建構更新操作來移除 subdomain
            update = {
                "$pull": {"subdomains": {"name": subdomain_to_delete}}
            }
            # 執行更新操作
            result = self.collection.update_one(query, update)
            if result.modified_count == 0:
                # 如果沒有文檔被修改，可能是因為沒找到該 subdomain
                raise Exception("未找到匹配的 subdomain，刪除未執行。")
            self.logger.info(f"subdomain '{subdomain_to_delete}' 已成功從 MongoDB 中刪除。")
            return True  # 成功刪除
        except Exception as e:
            self.logger.error(f"刪除 subdomain 時發生錯誤: {str(e)}")
            raise

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
