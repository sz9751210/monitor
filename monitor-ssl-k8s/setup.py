import yaml
import base64

def get_user_input():
    tg_token = input("請輸入您的 TELEGRAM_BOT_TOKEN: ")
    tg_group_id = input("請輸入您的 TELEGRAM_GROUP_ID: ")
    return tg_token, tg_group_id

def update_docker_compose(tg_token, tg_group_id, filename="dockerize/docker-compose.yaml"):
    with open(filename, 'r') as file:
        # 讀取 YAML 檔案內容
        data = yaml.safe_load(file)

    # 更新環境變量
    data['services']['telegram_bot']['environment']['TELEGRAM_BOT_TOKEN'] = tg_token
    data['services']['telegram_bot']['environment']['TELEGRAM_GROUP_ID'] = tg_group_id

    with open(filename, 'w') as file:
        # 將更新後的內容寫回檔案
        yaml.safe_dump(data, file)

def encode_base64(data):
    # 將輸入的字符串進行 base64 編碼並轉成合適的格式
    return base64.b64encode(data.encode('utf-8')).decode('utf-8')

def update_k8s_secret(tg_token, tg_group_id, filename="k8s/secret.yaml"):
    with open(filename, 'r') as file:
        # 讀取 YAML 檔案內容
        data = yaml.safe_load(file)

    # 更新環境變量並進行 base64 編碼
    data['data']['TELEGRAM_BOT_TOKEN'] = encode_base64(tg_token)
    data['data']['TELEGRAM_GROUP_ID'] = encode_base64(tg_group_id)

    with open(filename, 'w') as file:
        # 將更新後的內容寫回檔案
        yaml.safe_dump(data, file, default_flow_style=False)


def main():
    tg_token, tg_group_id = get_user_input()
    update_docker_compose(tg_token, tg_group_id)
    print("docker-compose.yaml 已經成功更新！")
    update_k8s_secret(tg_token, tg_group_id)
    print("secret.yaml 已經成功更新！")

if __name__ == "__main__":
    main()
