# TGuard - Telegram群组智能验证机器人

🤖 一个现代化的Telegram群组验证机器人，通过人机验证自动管理群组成员申请。

## ✨ 特性

- 🔐 **安全验证** - 集成hCaptcha人机验证，有效防止机器人
- ⚡ **自动处理** - 验证通过后自动批准用户加群
- 🌐 **Mini Web App** - 美观的Telegram Mini Web App界面
- 🏗️ **可扩展架构** - 支持多种验证码服务（hCaptcha、reCaptcha等）
- 📊 **管理功能** - 完整的统计和管理命令
- 🐳 **容器化部署** - Docker支持，一键部署
- 🔧 **高性能** - 基于Python 3.13 + aiogram + FastAPI

## 🚀 快速开始

### 1. 环境要求

- Python 3.13+
- Docker & Docker Compose
- PostgreSQL 16+
- Telegram Bot Token
- hCaptcha密钥

### 2. 安装部署

```bash
# 克隆项目
git clone https://github.com/yourrepo/tguard.git
cd tguard

# 复制配置文件
cp config.toml.example config.toml

# 编辑配置文件，填入你的密钥
nano config.toml

# 启动服务
docker-compose up -d
```

### 3. 配置说明

编辑 `config.toml` 文件：

```toml
[bot]
token = "YOUR_BOT_TOKEN_HERE"              # 你的Bot Token
verification_timeout = 300                 # 验证超时时间(秒)

[captcha.hcaptcha]
site_key = "YOUR_HCAPTCHA_SITE_KEY"       # hCaptcha站点密钥
secret_key = "YOUR_HCAPTCHA_SECRET_KEY"   # hCaptcha秘密密钥

[database]
host = "localhost"
name = "tguard"
user = "postgres"
password = "password"

[api]
base_url = "https://yourdomain.com"        # 你的域名
```

### 4. 设置Bot

1. 将机器人添加到群组
2. 给机器人管理员权限
3. 开启群组的"批准新成员"功能

## 📋 使用流程

1. **用户申请加群** → Bot接收到join request
2. **发送验证链接** → 用户收到Mini Web App链接
3. **完成人机验证** → 用户在Web App中通过hCaptcha
4. **自动批准入群** → 验证成功后自动加入群组

## 🎛️ 管理员命令

- `/start` - 查看Bot信息
- `/help` - 显示帮助信息
- `/status` - 查看验证统计
- `/pending` - 查看待处理申请

## 🔧 API接口

### 验证相关
- `POST /api/v1/verify` - 提交验证
- `GET /api/v1/verification-status/{token}` - 查询验证状态
- `GET /api/v1/captcha-config` - 获取验证码配置

### 健康检查
- `GET /health` - 基础健康检查
- `GET /health/detailed` - 详细健康检查

### 静态页面
- `GET /verify?token={token}` - 验证页面
- `GET /` - 主页

## 🏗️ 项目结构

```
TGuard/
├── src/
│   ├── bot/                 # Telegram Bot
│   │   ├── handlers/        # 消息处理器
│   │   └── main.py         # Bot入口
│   ├── api/                # FastAPI后端
│   │   ├── routes/         # API路由
│   │   ├── services/       # 业务服务
│   │   └── main.py         # API入口
│   ├── database/           # 数据库
│   │   ├── models.py       # 数据模型
│   │   ├── operations.py   # 数据库操作
│   │   └── connection.py   # 连接管理
│   ├── captcha/            # 验证码服务
│   │   ├── base.py         # 抽象接口
│   │   ├── hcaptcha.py     # hCaptcha实现
│   │   └── factory.py      # 工厂模式
│   ├── config/             # 配置管理
│   └── utils/              # 工具函数
├── templates/              # HTML模板
├── static/                 # 静态文件
├── database/               # 数据库脚本
├── config.toml            # 配置文件
├── requirements.txt       # Python依赖
├── docker-compose.yml     # Docker配置
└── Dockerfile            # Docker镜像
```

## 🔌 扩展验证码服务

TGuard采用抽象接口设计，轻松支持新的验证码服务：

```python
from src.captcha.base import CaptchaProvider

class YourCaptchaProvider(CaptchaProvider):
    async def verify(self, response: str, **kwargs):
        # 实现验证逻辑
        pass
    
    def get_frontend_config(self):
        # 返回前端配置
        pass
```

## 📊 数据库结构

### join_requests (加群申请)
- 用户信息、申请时间、验证状态
- 处理状态：pending/approved/rejected/expired

### verification_sessions (验证会话)
- 验证令牌、过期时间、验证结果
- IP地址、用户代理等安全信息

### bot_settings (机器人设置)
- 群组配置、超时设置、消息模板

## 🛡️ 安全特性

- ✅ 验证令牌唯一性和过期机制
- ✅ IP地址和用户代理记录
- ✅ 防重复提交和重放攻击
- ✅ 数据库连接池和事务安全
- ✅ 错误处理和日志记录

## 📈 性能特性

- ⚡ 异步处理，支持高并发
- ⚡ PostgreSQL连接池
- ⚡ 结构化日志和性能监控
- ⚡ Docker优化的多阶段构建
- ⚡ 静态文件CDN支持

### 测试

```bash
# 运行健康检查
curl http://localhost:8000/health

# 测试验证码配置
curl http://localhost:8000/api/v1/captcha-config
```

## 🤝 贡献

欢迎提交Issues和Pull Requests！

## 📄 许可证

MIT License - 详见 [LICENSE](LICENSE) 文件

---

⚡ **TGuard** - 让Telegram群组管理更简单、更安全！