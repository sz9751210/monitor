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

    def get_domain_from_mongodb(self, platform, env):

        query = {"platform": platform}
        result = self.collection.find_one(query)

        if result and "envs" in result and env in result["envs"]:
            self.logger.info(
                f"在平台 '{platform}' 和環境 '{env}' 下找到 domain 的訊息。"
            )
            return {"env": env, "domains": result["envs"][env]}
        else:
            self.logger.info(
                f"在平台 '{platform}' 和環境 '{env}' 下未找到 domain 的訊息。"
            )
            return None

    def get_platform_data_from_mongodb(self, platform):
        query = {"platform": platform}
        result = self.collection.find_one(query)

        if result:
            self.logger.info(f"Found domain information for platform '{platform}'.")
            return {"platform": platform, "envs": result.get("envs", {})}
        else:
            self.logger.info(f"No domain information found for platform '{platform}'.")
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