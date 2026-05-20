import requests
import json
import os
import sys
import argparse

if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

CONFIG_FILE = os.path.join(BASE_DIR, "config.json")


def load_config():
    if not os.path.exists(CONFIG_FILE):
        raise FileNotFoundError(f"配置文件不存在: {CONFIG_FILE}")
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


class FishStoreAPI:
    def __init__(self, token, config):
        self.BASE_URL = config.get("api", {}).get("base_url", "https://ed.weeeg.com/adminapi")
        self.TOKEN = token
        self.headers = {
            "authori-zation": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/json, text/plain, */*",
            "Referer": config.get("api", {}).get("referer", "https://ed.weeeg.com/ekadmin/product/add_product")
        }

    def upload_image(self, file_path):
        url = f"{self.BASE_URL}/file/upload"
        upload_headers = {
            "authori-zation": f"Bearer {self.TOKEN}",
            "Referer": self.headers["Referer"]
        }
        with open(file_path, 'rb') as f:
            files = {'file': f}
            data = {'pid': ''}
            r = requests.post(url, headers=upload_headers, files=files, data=data)
        result = r.json()
        
        if result.get("status") == 200:
            return self._get_latest_image_url()
        return None

    def _get_latest_image_url(self):
        url = f"{self.BASE_URL}/file/file?limit=1"
        r = requests.get(url, headers=self.headers)
        data = r.json()
        if data.get("status") == 200:
            images = data.get("data", {}).get("list", [])
            if images:
                return images[0].get("att_dir", "")
        return ""

    def get_images(self, limit=10):
        url = f"{self.BASE_URL}/file/file?limit={limit}"
        r = requests.get(url, headers=self.headers)
        data = r.json()
        if data.get("status") == 200:
            images = data.get("data", {}).get("list", [])
            print("=== 图片列表 ===")
            for img in images:
                print(f"  ID: {img['att_id']}, 名称: {img.get('real_name', '')}, URL: {img['att_dir'][:60]}...")
        return data

    def add_product(self, product_data):
        url = f"{self.BASE_URL}/product/product_goods/0"
        r = requests.post(url, headers=self.headers, json=product_data)
        return r.json()

    def get_orders(self, status=0):
        url = f"{self.BASE_URL}/order/list"
        r = requests.get(url, headers=self.headers)
        data = r.json()
        if data.get("status") == 200:
            print("=== 订单列表 ===")
            for order in data.get("data", {}).get("data", []):
                if status is None or order.get("status") == status:
                    print(f"  ID: {order['order_id']}, 状态: {order.get('status_name', {}).get('status_name', 'N/A')}")
        return data


def list_templates():
    templates_dir = os.path.join(BASE_DIR, "templates")
    if not os.path.exists(templates_dir):
        print("templates 文件夹不存在")
        return
    
    templates = [d for d in os.listdir(templates_dir) if os.path.isdir(os.path.join(templates_dir, d))]
    if templates:
        print("=== 可用模板 ===")
        for t in templates:
            print(f"  - {t}")
    else:
        print("暂无模板")


def load_template(template_name):
    template_dir = os.path.join(BASE_DIR, "templates", template_name)
    config_path = os.path.join(template_dir, "config.json")
    
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"模板不存在: templates/{template_name}/config.json")
    
    with open(config_path, "r", encoding="utf-8") as f:
        config = json.load(f)
    
    return template_dir, config


def create_product_from_config(template_dir, config, default_config):
    product = default_config.copy()
    product.update(config)
    
    image_file = config.get("image", "")
    if image_file:
        image_path = os.path.join(template_dir, image_file)
        return product, image_path
    return product, None


def main():
    parser = argparse.ArgumentParser(description="易店自动发货工具")
    parser.add_argument("-test", "--test", action="store_true", help="使用default模板测试")
    parser.add_argument("-t", "--template", type=str, help="指定模板名称")
    parser.add_argument("-list", "--list", action="store_true", help="列出可用模板")
    args = parser.parse_args()
    
    config = load_config()
    token = config.get("token", "")
    
    if not token or token == "请在此处填入你的Bearer Token":
        print("错误: 请先在 config.json 中配置 Token")
        return
    
    client = FishStoreAPI(token, config)
    default_config = config.get("default", {})
    
    if args.list:
        list_templates()
        return
    
    if args.test:
        print("=== 使用 default 模板测试 ===")
        template_name = "default"
    elif args.template:
        template_name = args.template
    else:
        print("用法:")
        print("  python auto_delivery.py -list          # 列出可用模板")
        print("  python auto_delivery.py -test         # 使用default模板测试")
        print("  python auto_delivery.py -t <模板名>    # 使用指定模板")
        print()
        list_templates()
        return
    
    try:
        print(f"\n=== 加载模板: {template_name} ===")
        template_dir, template_config = load_template(template_name)
        print(f"商品名称: {template_config.get('store_name')}")
        print(f"商品价格: {template_config.get('price')}")
        
        print("\n=== 上传图片 ===")
        product_config, image_path = create_product_from_config(template_dir, template_config, default_config)
        
        if image_path and os.path.exists(image_path):
            image_url = client.upload_image(image_path)
            print(f"图片URL: {image_url}")
            product_config["image"] = image_url
            product_config["slider_image"] = [image_url]
        else:
            print("未找到图片文件")
        
        print("\n=== 添加商品 ===")
        result = client.add_product(product_config)
        print(json.dumps(result, indent=2, ensure_ascii=False))
        
        if result.get("status") == 200:
            print("\n✅ 发布成功!")
        else:
            print(f"\n❌ 发布失败: {result.get('msg')}")
            
    except FileNotFoundError as e:
        print(f"错误: {e}")
        list_templates()


if __name__ == "__main__":
    main()