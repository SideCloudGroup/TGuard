# TGuard - Telegram智能验证机器人

🤖 一个现代化的 Telegram 智能验证机器人，既可以用作群组加群验证，通过人机验证自动管理群组成员申请，也提供了完整的 RESTful API 接口，可供第三方 Telegram 程序调用，实现多用途的人机验证功能，为各种需要人机验证的场景提供安全、可靠的验证服务。

## 📑 目录

- [✨ 特性](#-特性)
- [🛡️ 支持的验证码驱动](#️-支持的验证码驱动)
- [🚀 使用教程](#-使用教程)
- [📋 使用流程](#-使用流程)
- [🔧 API接口](#-api接口)
- [🏗️ 项目结构](#️-项目结构)
- [🔌 扩展验证码服务](#-扩展验证码服务)
- [📊 数据库结构](#-数据库结构)
- [🤝 贡献](#-贡献)
- [📄 许可证](#-许可证)

## ✨ 特性

- 🔐 **安全验证** - 集成多种人机验证服务，有效防止机器人
- ⚡ **自动处理** - 验证通过后自动批准用户加群
- 🌐 **Mini Web App** - 美观的Telegram Mini Web App界面
- 🏗️ **可扩展架构** - 支持多种验证码服务，易于扩展
- 📊 **管理功能** - 完整的统计和管理命令
- 🐳 **容器化部署** - Docker支持，一键部署
- 🔧 **高性能** - 基于Python 3.13 + aiogram + FastAPI
- 🔌 **外部API** - 提供RESTful API接口，支持第三方Bot集成和多用途验证

## 🛡️ 支持的验证码驱动

| 驱动            | 描述                      | 配置要求                                   |
|---------------|-------------------------|----------------------------------------|
| **hCaptcha**  | 隐私友好的人机验证服务             | `site_key`, `secret_key`               |
| **Cap.js**    | 基于Proof-Of-Work的验证码解决方案 | `server_url`, `site_key`, `secret_key` |
| **Turnstile** | Cloudflare的免费人机验证服务     | `site_key`, `secret_key`               |

### 验证码驱动特性

- 🔄 **自动切换** - 根据配置自动选择验证码服务
- 🎨 **统一界面** - 所有驱动使用相同的用户界面
- ⚙️ **灵活配置** - 支持独立配置每个验证码服务
- 🔧 **易于扩展** - 基于抽象接口，轻松添加新驱动

## 🚀 使用教程

### 🛠️ 自建部署

#### 1. 环境要求

- Docker & Docker Compose

#### 2. 安装部署

```bash
# 下载配置文件
mkdir tguard && cd tguard
wget https://github.com/SideCloudGroup/TGuard/raw/refs/heads/main/config.example.toml -O config.toml
wget https://github.com/SideCloudGroup/TGuard/raw/refs/heads/main/docker-compose.yml

# 编辑配置文件，填入你的密钥
nano config.toml

# 启动服务
docker compose up -d
```

#### 3. 配置说明

编辑 `config.toml` 文件，参考 `config.example.toml` 中的详细注释进行配置：

- **Bot Token**: 从 [@BotFather](https://t.me/botfather) 获取
- **验证码服务**: 选择 hCaptcha 或 Cap.js，并填入相应密钥
- **数据库**: 默认使用 PostgreSQL，可根据需要调整
- **API域名**: 更新为你的实际域名

#### 4. 设置Bot

1. 将机器人添加到群组
2. 给机器人管理员权限
3. 开启群组的"批准新成员"功能

## 📋 使用流程

1. **用户申请加群** → Bot接收到join request
2. **发送验证链接** → 用户收到Mini Web App链接
3. **完成人机验证** → 用户在Web App中通过验证码
4. **自动批准入群** → 验证成功后自动加入群组

## 🔧 API接口

### 验证相关

- `POST /api/v1/verify` - 提交验证
- `GET /api/v1/verification-status/{token}` - 查询验证状态
- `GET /api/v1/captcha-config` - 获取验证码配置

### 外部API（External API）

TGuard 提供了外部 API 接口，允许其他 Telegram Bot 通过 API 创建验证请求，实现多用途的验证功能。

#### 启用外部API

在 `config.toml` 中配置：

```toml
[api]
enable = true  # 启用外部API
api_key = "your-secret-api-key"  # 设置API密钥
```

#### API接口

- `POST /api/verification/create` - 创建验证请求
  - **认证**: 需要在请求头中提供 `X-API-Key: your-secret-api-key`
  - **请求体**:
    ```json
    {
      "user_id": 123456789
    }
    ```
  - **响应**:
    ```json
    {
      "token": "verification-token",
      "verification_url": "https://example.com/verify?token=...",
      "expires_at": "2025-01-01T12:00:00"
    }
    ```
  - **说明**: 
    - 验证链接和Token有效期为10分钟
    - 验证完成后，如果请求类型为API且chat_id有效，将自动执行approve操作
    - 验证链接通过Telegram Mini Web App打开，用户完成验证后，可通过token查询验证状态

#### 使用场景

外部API适用于以下场景：

- **第三方Bot集成**: 其他Telegram Bot可以通过API创建验证请求
- **多用途验证**: 不仅限于群组加群验证，可用于任何需要人机验证的场景
- **统一验证服务**: 作为独立的验证服务，为多个应用提供验证能力

### 健康检查

- `GET /health` - 基础健康检查
- `GET /health/detailed` - 详细健康检查

### 静态页面

- `GET /verify?token={token}` - 验证页面
- `GET /` - 主页

## 🏗️ 项目结构

```text
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
│   │   ├── cap.py          # Cap.js实现
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
from src.captcha.base import CaptchaProvider, CaptchaVerificationResult


class YourCaptchaProvider(CaptchaProvider):
    @property
    def provider_name(self) -> str:
        return "your_captcha"

    async def verify(self, response: str, **kwargs) -> CaptchaVerificationResult:
        # 实现验证逻辑
        # 返回 CaptchaVerificationResult 对象
        pass

    def get_frontend_config(self) -> Dict[str, Any]:
        # 返回前端配置
        # 包含验证码服务所需的所有配置
        pass
```

### 添加新驱动的步骤

1. 在 `src/captcha/` 目录下创建新的驱动文件
2. 继承 `CaptchaProvider` 基类并实现必要方法
3. 在 `src/captcha/factory.py` 中注册新驱动
4. 在 `src/config/settings.py` 中添加配置支持
5. 更新前端模板以支持新的验证码服务

## 📊 数据库结构

### join_requests (加群申请)

- 用户信息、申请时间、验证状态
- 处理状态：pending/approved/rejected/expired

### verification_sessions (验证会话)

- 验证令牌、过期时间、验证结果
- IP地址、用户代理等安全信息

### bot_settings (机器人设置)

- 群组配置、超时设置、消息模板

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