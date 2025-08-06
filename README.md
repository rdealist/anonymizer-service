# DICOM 脱敏服务

一个基于 FastAPI 的 DICOM 文件脱敏微服务，可以对医学影像文件进行隐私保护处理并上传到阿里云 OSS。

## 功能特性

- 🏥 **DICOM 文件脱敏**: 支持多种脱敏策略（替换、移除、哈希、清空等）
- 📋 **多配置文件**: 支持不同场景的脱敏规则（默认、科研等）
- ☁️ **云存储集成**: 自动上传脱敏后的文件到阿里云 OSS
- 🚀 **高性能**: 基于 FastAPI，支持异步处理
- 🐳 **容器化**: 提供 Docker 支持，便于部署
- 🔒 **内存处理**: 文件在内存中处理，不写入本地磁盘，提高安全性

## 技术栈

- **Web 框架**: FastAPI
- **DICOM 处理**: pydicom
- **云存储**: 阿里云 OSS (oss2)
- **配置管理**: PyYAML, python-dotenv
- **运行环境**: Python 3.9+

## 项目结构

```
anonymizer-service/
├── app/
│   ├── __init__.py
│   ├── main.py             # API 路由和主逻辑
│   ├── anonymizer.py       # 核心脱敏类
│   ├── config.py           # 配置加载
│   ├── profiles.yaml       # 脱敏规则配置文件
│   └── utils.py            # 工具函数
├── Dockerfile              # Docker 构建文件
├── requirements.txt        # Python 依赖
├── design.md              # 设计文档
└── README.md              # 项目说明
```

## 快速开始

### 环境要求

- Python 3.9+
- Docker (可选)

### 1. 克隆项目

```bash
git clone <repository-url>
cd anonymizer-service
```

### 2. 环境配置

创建 `.env` 文件并配置相关参数：

```env
# 开发模式 - 设置为 true 可在没有真实 OSS 配置时运行
DEV_MODE=true

# 阿里云 OSS 配置（生产环境需要）
OSS_ACCESS_KEY_ID=your_access_key_id
OSS_ACCESS_KEY_SECRET=your_access_key_secret
OSS_BUCKET_NAME=your_bucket_name
OSS_ENDPOINT=https://oss-cn-hangzhou.aliyuncs.com
```

**开发模式说明**：
- `DEV_MODE=true`: 跳过 OSS 初始化，模拟文件上传，适合开发和测试
- `DEV_MODE=false`: 使用真实的 OSS 配置，适合生产环境

### 3. 安装依赖

```bash
pip install -r requirements.txt
```

### 4. 测试应用

在启动服务之前，建议先运行测试脚本验证配置：

```bash
python test_app.py
```

### 5. 启动服务

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

服务将在 `http://localhost:8000` 启动。

**注意**: 项目默认运行在开发模式 (`DEV_MODE=true`)，此时不需要真实的 OSS 配置即可启动和测试 API。

### 6. 使用启动脚本（可选）

项目提供了几个辅助脚本：

```bash
# 测试应用配置和依赖
python test_app.py

# 使用简单启动脚本
python start_server.py
```

### 7. Docker 部署（推荐）

```bash
# 构建镜像
docker build -t dicom-anonymizer .

# 运行容器
docker run -d \
  --name dicom-anonymizer \
  -p 8000:8000 \
  --env-file .env \
  dicom-anonymizer
```

## API 使用

### 脱敏接口

**端点**: `POST /api/v1/anonymize`

**请求格式**: `multipart/form-data`

**参数**:
- `file` (必需): DICOM 文件 (.dcm)
- `profile` (可选): 脱敏配置名称，默认为 "default"

**示例请求**:

```bash
curl -X POST "http://localhost:8000/api/v1/anonymize" \
  -F "file=@example.dcm" \
  -F "profile=default"
```

**成功响应** (200 OK):

```json
{
  "success": true,
  "message": "File anonymized and uploaded successfully.",
  "data": {
    "originalFilename": "example.dcm",
    "ossUrl": "https://your-bucket.oss-cn-hangzhou.aliyuncs.com/anonymized/uuid.dcm",
    "ossKey": "anonymized/uuid.dcm"
  }
}
```

### 健康检查

**端点**: `GET /`

```bash
curl http://localhost:8000/
```

## 脱敏配置

脱敏规则在 `app/profiles.yaml` 中定义，支持以下操作：

- `replace`: 替换为指定值
- `remove`: 删除标签
- `empty`: 清空标签值
- `hash`: 哈希处理
- `keep`: 保留原值

### 预定义配置

- **default**: 默认配置，较为保守的脱敏策略
- **research**: 科研用配置，保留部分信息用于研究

### 自定义配置

可以在 `profiles.yaml` 中添加新的配置文件：

```yaml
profiles:
  custom:
    - tag: [0x0010, 0x0010]  # PatientName
      action: "replace"
      value: "CUSTOM_PATIENT"
    # 更多规则...
```

## API 文档

启动服务后，可以访问以下地址查看完整的 API 文档：

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## 开发

### 本地开发

```bash
# 安装开发依赖
pip install -r requirements.txt

# 启动开发服务器
uvicorn app.main:app --reload
```

### 测试

```bash
# 运行测试
python -m pytest

# 测试 API
curl -X POST "http://localhost:8000/api/v1/anonymize" \
  -F "file=@test.dcm" \
  -F "profile=default"
```

## 部署

### Docker 部署

1. 构建镜像：
```bash
docker build -t dicom-anonymizer .
```

2. 运行容器：
```bash
docker run -d \
  --name dicom-anonymizer \
  -p 8000:8000 \
  --env-file .env \
  dicom-anonymizer
```

### 生产环境建议

- 使用反向代理 (Nginx)
- 配置 HTTPS
- 设置适当的资源限制
- 配置日志记录
- 设置监控和健康检查

## 安全注意事项

- 确保 OSS 凭证安全存储
- 定期更新依赖包
- 在生产环境中禁用调试模式
- 配置适当的网络安全策略
- 定期审查脱敏规则的有效性

## 贡献

欢迎提交 Issue 和 Pull Request！

## 许可证

[MIT License](LICENSE)

## 联系方式

如有问题或建议，请联系项目维护者。
