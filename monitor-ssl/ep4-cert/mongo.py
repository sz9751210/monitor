import yaml
import logging
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure

mongodb_uri = "mongodb://rootuser:rootpass@localhost:27017/mydatabase?authSource=admin"


def init_mongo_client(mongodb_uri):
    try:
        client = MongoClient(mongodb_uri)

        info = client.server_info()
        mongodb_version = info["version"]
        print("MongoDB 連接成功。Mongo 版本為", mongodb_version)
        return client
    except ConnectionFailure:
        print("MongoDB 連接失敗。請檢查您的連接設置和Server狀態。")


def get_collection(mongo_client, collection_name):
    db = mongo_client.get_default_database()
    collection = db[collection_name]
    return collection


def load_data_from_yaml(yaml_file_path, key):
    try:
        with open(yaml_file_path, "r", encoding="utf-8") as file:
            data = yaml.safe_load(file)
            return data.get(key, {})
    except FileNotFoundError as e:
        logging.error(f"YAML檔案未找到: {e}")
        return {}
    except Exception as e:
        logging.error(f"讀取YAML檔案時發生錯誤: {e}")
        return {}


def write_domain_data_to_mongodb(collection, domain_data):
    print("domain_data", domain_data)
    for env, domains in domain_data.items():
        document = {"env": env, "domains": domains}
        query = {"env": env}
        collection.update_one(query, {"$set": document}, upsert=True)
    print("數據已成功寫入 MongoDB。")


def add_domain_to_mongodb(collection, env, domain):
    result = collection.update_one(
        {"env": env}, {"$addToSet": {"domains": domain}}, upsert=True
    )
    if result.matched_count > 0 or result.upserted_id is not None:
        print("domain 已成功添加或更新。")
        return True
    else:
        print("domain 添加或更新失敗。")
        return False


def load_domain_envs_from_mongodb(collection):
    try:
        domain_envs = {}
        data = collection.find({})
        for item in data:
            env = item.get("env")
            domains = item.get("domains", [])
            if env and domains:
                domain_envs[env] = domains
        return domain_envs
    except Exception as e:
        print(f"從 MongoDB 讀取數據失敗: {e}")
        return {}


def get_domain_from_mongodb(collection, env, domain):
    query = {"env": env, "domains": {"$elemMatch": {"$eq": domain}}}
    result = collection.find_one(query)

    if result:
        if domain in result.get("domains", []):
            print(f"在環境 '{env}' 下找到 domain  '{domain}' 的訊息。")
            return {"env": env, "domain": domain}
        else:
            print(f"在環境 '{env}' 下未找到 domain  '{domain}' 的具體訊息。")
            return None
    else:
        print(f"在環境 '{env}' 下未找到 domain  '{domain}' 的訊息。")
        return None


def update_domain_in_mongodb(collection, env_value, old_domain, new_domain):
    query = {"env": env_value, "domains": old_domain}
    update_action = {"$set": {"domains.$": new_domain}}

    update_result = collection.update_many(query, update_action)

    if update_result.matched_count > 0:
        print(
            f"成功更新文檔。匹配數量: {update_result.matched_count}, 修改數量: {update_result.modified_count}."
        )
        return True
    else:
        print("未找到匹配的文檔或 domain ，更新未執行。")
        return False


def delete_domain_in_mongodb(collection, env_value, domain_to_delete):
    query = {"env": env_value}
    delete_action = {"$pull": {"domains": domain_to_delete}}
    result = collection.update_one(query, delete_action)
    if result.modified_count > 0:
        print("domain 已成功刪除。")
        return True
    else:
        print("未找到匹配的 domain 或環境，刪除未執行。")
        return False


def bulk_add_domains_to_mongodb(collection, env, domains):
    result = collection.update_one(
        {"env": env}, {"$addToSet": {"domains": {"$each": domains}}}, upsert=True
    )
    if result.matched_count > 0 or result.upserted_id is not None:
        print("domain 已成功批量添加或更新。")
        return True
    else:
        print("domain 批量添加或更新失敗。")
        return False


if __name__ == "__main__":
    client = init_mongo_client(mongodb_uri)
    collection_name = "domains"
    collection = get_collection(client, collection_name)
    yaml_file_path = "domains.yaml"
    domain_data = load_data_from_yaml(yaml_file_path, "domain_envs")
    print("yaml_data", domain_data)
    write_domain_data_to_mongodb(collection, domain_data)
    mongo_domain_data = load_domain_envs_from_mongodb(collection)
    add_env = "dev"
    add_domain = "test.com"
    add_domain_to_mongodb(collection, add_env, add_domain)
    get_domain_from_mongodb(collection, add_env, add_domain)
    print("mongo data : ", mongo_domain_data)
    update_env = "test"
    origin_domain = "abc.com"
    new_domain = "github.com"
    update_domain_in_mongodb(collection, update_env, origin_domain, new_domain)
    mongo_domain_data = load_domain_envs_from_mongodb(collection)
    print("updated result : ", mongo_domain_data)
    delete_env = "test"
    delete_domain = "example.com"
    delete_domain_in_mongodb(collection, delete_env, delete_domain)
    mongo_domain_data = load_domain_envs_from_mongodb(collection)
    print("delete result : ", mongo_domain_data)
