import logging
import yaml


def convert_to_yaml(python_obj):
    return yaml.dump(python_obj, allow_unicode=True)


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
