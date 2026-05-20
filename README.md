# 易店快速发布商品工具

使用模板快速发布商品到易店商城后台。

## 下载安装

1. 前往 [Release 页面](https://github.com/Holosukiyaa/RMAR_YDROBOT/releases) 下载最新版本
2. 下载 `auto_delivery.exe`
3. 在电脑上创建一个新文件夹，将 `auto_delivery.exe` 放进去
4. 首次运行会自动生成 `config.json` 和 `templates` 文件夹

## 图形界面使用

1. 双击运行 `auto_delivery.exe`
2. 在界面中输入你的 Bearer Token，点击"保存Token"
3. 选择模板
4. 点击"开始发布"

## 命令行使用

```cmd
# 列出模板
auto_delivery.exe -list

# 测试发布
auto_delivery.exe -test

# 指定模板发布
auto_delivery.exe -t my_template
```

## 配置 Token

### 图形界面：
- 打开程序后输入Token，点击保存

### 命令行：
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

## 模板制作

在 `templates/` 目录下创建新文件夹，放入：

1. `config.json` - 商品配置
2. 商品图片文件

## 常见问题

**Q: 运行显示"请先在 config.json 中配置 Token"**
A: 用记事本打开 config.json，将 token 值替换为你的 Bearer Token

**Q: Token 过期了怎么办**
A: 重新获取 Token 并更新

## 开发者

```bash
pip install requests PyQt5
python auto_delivery_gui.py
```
