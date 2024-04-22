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
    print("domain_data", domain_data)
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
    # 構造查詢條件，这里使用 $elemMatch 来匹配数组中的元素
    query = {"env": env, "domains": {"$elemMatch": {"$eq": domain}}}
    # 執行查詢操作
    result = collection.find_one(query)
    
    if result:
        # 检查是否真的包含了指定的域名，防止空数组等异常情况
        if domain in result.get("domains", []):
            print(f"在环境 '{env}' 下找到域名 '{domain}' 的信息。")
            # 可以根据需要调整返回的信息结构
            return {"env": env, "domain": domain}
        else:
            print(f"在环境 '{env}' 下未找到域名 '{domain}' 的具体信息，尽管匹配到了文档。")
            return None
    else:
        # 没有找到相应的文档
        print(f"在环境 '{env}' 下未找到域名 '{domain}' 的信息。")
        return None


def update_domain_in_mongodb(collection, env_value, old_domain, new_domain):
    # 構造查詢條件和更新動作
    query = {"env": env_value, "domains": old_domain}
    update_action = {"$set": {"domains.$": new_domain}}

    # 執行更新操作
    update_result = collection.update_many(query, update_action)

    # 判斷是否有文檔被成功更新
    if update_result.matched_count > 0:
        print(
            f"成功更新文檔。匹配數量: {update_result.matched_count}, 修改數量: {update_result.modified_count}."
        )
        return True  # 返回 True 表示至少有一個文檔被成功更新
    else:
        print("未找到匹配的文檔或域名，更新未執行。")
        return False  # 返回 False 表示沒有文檔被更新


def delete_domain_in_mongodb(collection, env_value, domain_to_delete):
    query = {"env": env_value}
    delete_action = {"$pull": {"domains": domain_to_delete}}
    result = collection.update_one(query, delete_action)
    if result.modified_count > 0:
        print("域名已成功刪除。")
        return True
    else:
        print("未找到匹配的域名或環境，刪除未執行。")
        return False


def bulk_add_domains_to_mongodb(collection, env, domains):
    # 使用 $addToSet 和 $each 來同時添加多個唯一的域名到相同的 env 中
    result = collection.update_one(
        {"env": env}, {"$addToSet": {"domains": {"$each": domains}}}, upsert=True
    )
    if result.matched_count > 0 or result.upserted_id is not None:
        print("域名已成功批量添加或更新。")
        return True
    else:
        print("域名批量添加或更新失敗。")
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
