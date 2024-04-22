from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
import yaml
import logging

mongodb_uri = "mongodb://rootuser:rootpass@localhost:27017/mydatabase?authSource=admin"


def init_mongo_client(mongodb_uri):
    try:
        # 嘗試連接 MongoDB
        client = MongoClient(mongodb_uri)

        # 嘗試獲取服務器信息，以確認連接
        info = client.server_info()  # 會在連接失敗時拋出 ConnectionFailure 異常
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
    for env, domains in domain_data.items():
        document = {"env": env, "domains": domains}
        # 更新條件，這裡假設 env 是唯一的
        query = {"env": env}
        # 使用 upsert=True，如果不存在則插入，存在則更新
        collection.update_one(query, {"$set": document}, upsert=True)
    print("數據已成功寫入 MongoDB。")


def add_domain_to_mongodb(collection, env, domain):
    # 嘗試添加或更新該 env 的域名
    result = collection.update_one(
        {"env": env}, {"$addToSet": {"domains": domain}}, upsert=True
    )
    if result.matched_count > 0 or result.upserted_id is not None:
        print("域名已成功添加或更新。")
        return True
    else:
        print("域名添加或更新失敗。")
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
    # 構造查詢條件
    query = {"env": env, "domains": domain}
    # 執行查詢操作
    result = collection.find_one(query)
    print("get result", result)
    if result:
        # 找到了相應的文檔，返回域名信息
        print(f"在環境 '{env}' 下找到域名 '{domain}' 的信息。")
        return result
    else:
        # 沒有找到相應的文檔
        print(f"在環境 '{env}' 下未找到域名 '{domain}' 的信息。")
        return None


def update_domain_in_mongodb(collection, env_value, old_domain, new_domain):
    # 構造查詢條件和更新動作
    query = {"env": env_value, "domains": old_domain}
    update_action = {"$set": {"domains.$": new_domain}}

    # 執行更新操作
    update_result = collection.update_many(query, update_action)

    if update_result.matched_count > 0:
        print(
            f"成功更新文檔。匹配數量: {update_result.matched_count}, 修改數量: {update_result.modified_count}."
        )
    else:
        print("未找到匹配的文檔或域名，更新未執行。")


def delete_domain_in_mongodb(collection, env_value, domain_to_delete):
    query = {"env": env_value}
    delete_action = {"$pull": {"domains": domain_to_delete}}
    collection.update_one(query, delete_action)


if __name__ == "__main__":
    client = init_mongo_client(mongodb_uri)
    collection_name = "domains"
    collection = get_collection(client, collection_name)
    yaml_file_path = "domains.yaml"
    domain_data = load_data_from_yaml(yaml_file_path, "domain_envs")
    write_domain_data_to_mongodb(collection, domain_data)
    mongo_domain_data = load_domain_envs_from_mongodb(collection)
    print("初始化 Mongo data : ", mongo_domain_data)
    add_env = "prod"
    add_domain = "alan.com"
    add_domain_to_mongodb(collection, add_env, add_domain)
    mongo_domain_data = load_domain_envs_from_mongodb(collection)
    print("新增後的 Mongo data : ", mongo_domain_data)
    print("查詢單一 domain")
    get_env = "prod"
    get_domain = "alan.com"
    get_domain_from_mongodb(collection, get_env, get_domain)
    update_env = "test"
    origin_domain = "abc.com"
    new_domain = "github.com"
    update_domain_in_mongodb(collection, update_env, origin_domain, new_domain)
    mongo_domain_data = load_domain_envs_from_mongodb(collection)
    print("更新後的 Mongo data : ", mongo_domain_data)
    delete_env = "test"
    delete_domain = "example.com"
    delete_domain_in_mongodb(collection, delete_env, delete_domain)
    mongo_domain_data = load_domain_envs_from_mongodb(collection)
    print("刪除後的 Mongo data : ", mongo_domain_data)
    client.close()
