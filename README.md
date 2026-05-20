# 易店自动发货工具

自动化发布商品到易店商城后台。

## 下载安装

1. 前往 [Release 页面](https://github.com/Holosukiyaa/RMAR_YDROBOT/releases) 下载最新版本
2. 下载 `auto_delivery.exe`
3. 在电脑上创建一个新文件夹，将 `auto_delivery.exe` 放进去

## 配置

### 1. 首次运行生成配置

双击运行 `auto_delivery.exe -list`，会在同级目录下生成 `config.json` 和 `templates` 文件夹

### 2. 配置 Token

用记事本打开 `config.json`，将 `token` 替换为你的 Bearer Token：

```json
{
  "token": "你的Bearer Token"
}
```

**如何获取 Token：**
- 登录易店后台 (https://ed.weeeg.com/ekadmin)
- 打开浏览器开发者工具 (F12)
- 切换到 Network/网络标签
- 刷新页面，找到任意请求
- 复制请求头中的 `authorization` 值（Bearer xxx）

## 使用方法

### 命令行运行

```cmd
cd "你创建的文件夹路径"

# 列出可用模板
auto_delivery.exe -list

# 使用 default 模板测试发布
auto_delivery.exe -test

# 使用指定模板发布
auto_delivery.exe -t my_template
```

### 文件结构

下载后的文件夹应该包含：
```
文件夹/
├── auto_delivery.exe    # 主程序
├── config.json          # 配置文件（首次运行后生成）
└── templates/           # 模板文件夹（首次运行后生成）
    ├── default/
    │   └── config.json
    └── customTest/
        └── config.json
```

## 模板制作

在 `templates/` 目录下创建新文件夹，放入：

1. `config.json` - 商品配置
2. 商品图片文件

示例：
```
templates/
└── my_product/
    ├── config.json
    └── product.png
```

### config.json 配置说明

| 配置项 | 说明 | 必填 |
|--------|------|------|
| store_name | 商品名称 | 是 |
| store_info | 商品描述 | 否 |
| price | 价格 | 是 |
| cate_id | 分类ID | 是 |
| unit_name | 单位 | 是 |
| is_show | 是否上架 (1=上架, 0=下架) | 是 |
| address | 地区ID | 是 |
| image | 图片文件名 | 是 |

## 常见问题

**Q: 运行显示"请先在 config.json 中配置 Token"**
A: 用记事本打开 config.json，将 token 值替换为你的 Bearer Token

**Q: Token 过期了怎么办**
A: 重新获取 Token 并更新 config.json 中的 token 值

**Q: 发布失败怎么办**
A: 检查 config.json 中的 token 是否正确，分类 ID、地区 ID 等是否有效

## 开发者

如需修改代码，请安装 Python 环境：
```bash
pip install requests
python auto_delivery.py -test
```