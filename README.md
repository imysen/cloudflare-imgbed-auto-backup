# 自动备份程序

[CloudFlare-ImgBed项目](https://github.com/MarSeventh/CloudFlare-ImgBed)用基于GitHub Actions定期自动备份数据脚本

> [!IMPORTANT]
> ## 🚨 重要安全提醒 🚨
> **⚠️ 在备份文件中包含重要的敏感信息数据！**  
> - 为了保护您的数据安全，程序内置了仓库隐私检查功能：  
> - 每次运行前自动检查仓库是否为 **私有** ；  
> - 因此，在使用本项目前请确保您已将仓库**解除复刻网络**并更改为**私有**  
> - 如果仓库为公开状态，程序将拒绝执行并显示安全警告  
> **步骤：你的仓库➡Settings➡General➡（划到最下面）Danger➡Leave fork network➡Change repository visibility**  
> (其实公开仓库不会执行actions)





## 功能特性

- 🕒 **定时备份**: 每天UTC+8的2：00自动执行备份任务
- 🔐 **安全认证**: 通过仓库机密统一管理
- 🛡️ **隐私保护**: 强制检查仓库隐私状态，防止敏感数据泄露
- 📁 **自动管理**: 自动保存和管理备份文件
- 🚀 **GitHub Actions**: 完全基于GitHub Actions运行
- 🧹 **自动清理**: 自动清理旧备份文件（默认保留最近100个，可自定义）
- 🔍 **智能检测**: 通过MD5自动检测数据变化，只在有变更时保存备份

## 快速开始

请确保你的cloudflare-imgbed版本大于V2.0.3

### 1. 🔒 确保仓库为私有

**重要：请务必确保您的仓库设置为私有（Private）状态！**

1. 前往您的GitHub仓库主页
2. 点击 `Settings` 选项卡
3. 滚动到页面底部的 `Danger Zone` 区域
4. 点击 `Leave fork network` 将你的仓库脱离复刻网络
![alt text](https://imgbed.112601.xyz/file/cloudflare-imgbed-auto-backup/1755364661684.png)
5. 点击 `Change repository visibility` 选择 `Make private` 将仓库设为私有
![alt text](https://imgbed.112601.xyz/file/cloudflare-imgbed-auto-backup/1755365226055.png)

### 2. 配置GitHub仓库机密

在你的GitHub仓库中，进入 `Settings` -> `Secrets and variables` -> `Actions`，添加以下机密：
![alt text](https://imgbed.112601.xyz/file/cloudflare-imgbed-auto-backup/1755366168729.png)
**必需配置**:
| 机密名称 | 说明 | 示例值 |
|---------|------|--------|
| `BACKUP_URL` | 网站完整URL（包含协议和端口） | `cfbed.1314883.xyz` |
| `BACKUP_USERNAME` | 登录用户名（BASIC_USER） | `your_username` |
| `BACKUP_PASSWORD` | 登录密码（BASIC_PASS） | `your_password` |

**可选配置** (不设置将使用默认值):
| 机密名称 | 说明 | 示例值 | 默认值 |
|---------|------|--------|--------|
| `MAX_BACKUPS` | 最大保留备份文件数量 | `1145` | `100` |
| `ENABLE_CHANGE_DETECTION` | 启用智能变更检测 | `true/false` | `true` |


### 2. 启用GitHub Actions

确保你的仓库已启用GitHub Actions功能。

**注意**: 程序会自动将你提供的URL拼接成完整的API路径：
- 输入: `cfbed.1314883.xyz`
- 自动拼接为: `https://cfbed.1314883.xyz/api/manage/sysConfig/backup?action=backup`
- 支持 HTTP 和 HTTPS 协议，会保持你指定的协议类型
> [!IMPORTANT]  
> 如果你是http/非标准端口，请在变量中填完整的URL，如：`  http://cfbed.1314883.xyz:11451`  
> 默认拼接为https

### 3. 执行备份

备份程序会：
- **自动执行**: 每天北京时间02:00自动运行
- **手动触发**: 你也可以在Actions页面手动触发备份
如果您是第一次部署本项目，请在Action中手动执行一次确保执行正常
![alt text](https://imgbed.112601.xyz/file/cloudflare-imgbed-auto-backup/1755367335196.png)
正确输出：  
![正确输出](https://imgbed.112601.xyz/file/cloudflare-imgbed-auto-backup/1755368429729.png)
## 文件结构

```
cloudflare-imgbed-auto-backup/
├── .github/
│   └── workflows/
│       └── backup.yml          # GitHub Actions工作流配置
├── backups/                    # 备份文件存储目录
│   ├──.privacy_verified        # 安全性证明文件
│   ├── backup_20240816_100000.json
│   ├── backup_20240817_100000.json
│   └── latest_backup.json      # 最新备份文件
├── backup_script.py            # 主备份脚本
├── requirements.txt            # Python依赖
└── README.md                   # 说明文档
```

## 备份文件说明

- **带时间标志的备份文件**: `backup_YYYYMMDD_HHMMSS.json`
- **最新备份文件**: `latest_backup.json` (始终指向最新的备份)
- **自动清理**: 程序会自动保留最近的指定数量个备份文件（默认100个）

## 🔍 智能变更检测

程序默认启用智能变更检测功能，只有在数据发生变化时才会保存新的备份文件：

### 检测原理
- 使用MD5哈希算法计算JSON数据的指纹
- 将新下载的数据与最新备份文件进行对比
- 只有当哈希值不同时才保存新的备份文件

### 优势
- **节省存储空间**: 避免保存重复的备份文件
- **减少提交噪音**: GitHub仓库不会产生无意义的提交
- **提高效率**: 跳过无变化的备份操作

### 控制选项
- **启用**: `ENABLE_CHANGE_DETECTION=true` （默认）
- **禁用**: `ENABLE_CHANGE_DETECTION=false` （强制每次都备份）

### 特殊情况处理
- **首次备份**: 没有历史数据时，总是保存备份
- **计算错误**: 无法计算哈希时，为安全起见会强制保存备份
- **文件缺失**: 找不到最新备份文件时，会保存新的备份

## 🛡️ 仓库隐私保护功能

为了防止敏感数据泄露，程序内置了强制的仓库隐私检查功能。
[详见](https://github.com/yunsen2025/cloudflare-imgbed-auto-backup/blob/main/SECURITY_FEATURES.md)

- **强制执行，无配置选项可以禁用此功能**

### 常见问题

**Q: 为什么需要这个功能？**  
A: 在导出的JSON文件中，包含TG变量与S3端点信息等，属于十分敏感的信息，为安全起见，本项目仅允许私有仓库使用。公开仓库会让任何人都能访问这些数据，造成严重的安全风险。

**Q: 可以禁用这个检查吗？**  
A: 不可以。为了确保数据安全，此功能强制执行，无法禁用。

**Q: 检查失败了怎么办？**  
A: 按照错误提示将仓库设置为私有，然后重新运行备份任务。程序会自动重新检查。如还有错误请提起[ISSUE](https://github.com/yunsen2025/cloudflare-imgbed-auto-backup/issues)，请不要提交有关隐私的信息

## 🌐 HTTP/HTTPS 协议支持

程序支持 HTTP 和 HTTPS 两种协议，并能智能处理不同的网络环境：

### HTTP 协议特殊情况

#### 1. **混合内容问题**
- 在 GitHub Actions 环境中，HTTP 连接可能会受到安全策略限制
- 如果遇到连接问题，建议优先使用 HTTPS

#### 2. **端口配置**
- HTTP 默认端口：80
- HTTPS 默认端口：443
- 自定义端口：如 `http://example.com:8080/`
- 程序会保持你指定的端口号

#### 3. **SSL/TLS 证书问题**
- HTTP 连接不涉及证书验证
- 如果你的 HTTPS 使用自签名证书，可能需要特殊处理，懒得写这块了~~也没人给图床用自签吧~~

#### 4. **连接超时设置**
- 程序默认超时时间：30秒
- 对于较慢的服务器，可能需要调整超时时间

### 常见问题解决

1. **"Connection refused" 错误**
   ```bash
   # 检查服务是否运行
   netstat -tulpn | grep 40968
   
   # 检查防火墙状态
   sudo ufw status
   ```

2. **"Certificate verify failed" 错误**
   - 这通常发生在 HTTPS 连接中
   - 确保证书有效或使用 HTTP 协议

3. **"Timeout" 错误**
   - 检查网络连接
   - 确认服务器响应时间
   - 考虑增加超时时间

## 本地运行

如果你想在本地运行备份脚本：

1. 安装依赖：
```bash
pip install -r requirements.txt
```

2. 设置环境变量：
```bash
export BACKUP_URL="http://"
export BACKUP_USERNAME="your_username"
export BACKUP_PASSWORD="your_password"
export MAX_BACKUPS="100"  # 可选，默认100
export ENABLE_CHANGE_DETECTION="true"  # 可选，默认true

# 本地运行时需要设置以下变量进行隐私检查：
export GITHUB_TOKEN="your_github_token"  # GitHub Personal Access Token
export GITHUB_REPOSITORY="username/repo-name"  # 仓库名称
```

**本地运行说明**：
- 本地运行时也会执行隐私检查，需要设置有效的 `GITHUB_TOKEN` 和 `GITHUB_REPOSITORY`
- 如果您需要在测试环境中跳过检查，请修改源代码 `self.force_private_repo` 值

3. 运行脚本：
```bash
python backup_script.py
```

## 故障排除

### 常见问题

1. **🔒 仓库隐私检查失败**
   - **问题**: 显示"仓库当前为公开状态"错误
   - **解决**: 将仓库设置为私有
     1. 前往 GitHub 仓库设置: `https://github.com/用户名/仓库名/settings`
     2. 滚动到底部 `Danger Zone` 区域
     3. 点击 `Change repository visibility` → `Make private`
   - **注意**: 程序会拒绝在公开仓库中备份敏感数据

2. **GitHub API 访问失败**
   - **问题**: "无法验证仓库隐私状态"
   - **原因**: GitHub Token 权限不足或网络问题
   - **解决**: 确认 Actions 有足够权限访问仓库信息（通常 `GITHUB_TOKEN` 自动提供）

3. **认证失败**
   - 检查用户名和密码是否正确
   - 确认GitHub机密设置正确

4. **网络连接问题**
   - 检查完整URL是否正确（http与非标准端口需要填写完整URL）
   - 确认服务器端口是否开放
   - 确认网站的完整API路径可访问
   - 确保使用版本支持导出
   - 确认网站没有IP限制
   - 如果使用HTTP，确保服务器支持HTTP连接
   - **HTTP特有问题**：某些网络环境可能阻止HTTP连接，建议先测试HTTPS

5. **协议相关问题**
   - **HTTP**: 检查是否被防火墙或代理阻止
   - **HTTPS**: 检查SSL证书是否有效
   - **端口**: 确认自定义端口已正确开放
   - **超时**: 如果服务器响应慢，可能需要增加超时时间

6. **JSON解析错误**
   - 确认版本大于2.0.3
   - 检查API是否正常工作

7. **变更检测问题**
   - 如果怀疑变更检测有误，可以设置 `ENABLE_CHANGE_DETECTION=false` 强制备份
   - 检查 `latest_backup.json` 文件是否存在且格式正确

8. **配置错误**
   - 如果看到 `invalid literal for int()` 错误，检查 `MAX_BACKUPS` 是否设置了有效数字
   - 可选配置项如果不需要可以不设置，程序会使用默认值

### 本地测试方法

在配置GitHub Actions之前，建议先在本地测试连接：

```bash
# 测试HTTP连接
curl -v -u "username:password" "http:///api/manage/sysConfig/backup?action=backup"

# 测试HTTPS连接（如果支持）
curl -v -u "username:password" "https:///api/manage/sysConfig/backup?action=backup"

# 检查端口是否开放
telnet 11
```

### 查看日志

在GitHub Actions页面可以查看详细的执行日志，包括：
- 认证过程
- 下载进度
- 变更检测结果
- 文件保存状态
- 错误信息

## 自定义配置

你可以修改以下设置：

### 修改备份时间

编辑 `.github/workflows/backup.yml` 中的cron表达式：
```yaml
schedule:
  - cron: '0 18 * * *'  # 每天UTC时间18:00（北京时间02:00）
```

### 修改保留备份数量

编辑 `backup_script.py` 中的清理逻辑，或者在GitHub仓库机密中设置 `MAX_BACKUPS`：
```python
# 默认保留最近的100个备份文件
self.max_backups = int(os.getenv('MAX_BACKUPS', '100'))
```

### 禁用变更检测

如果你希望每次都强制保存（不管数据是否变化），可以设置：
```yaml
# 在GitHub仓库机密中设置
ENABLE_CHANGE_DETECTION: false
```

## 贡献

欢迎提交[Issues](https://github.com/yunsen2025/cloudflare-imgbed-auto-backup/issues)和[Pull Requests](https://github.com/yunsen2025/cloudflare-imgbed-auto-backup/pulls)来改进这个项目！

## 许可证

MIT License
