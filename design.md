**DICOM脱敏模块实现方案**

流程：**API接收DICOM文件 -> 模块化脱敏 -> 上传阿里云OSS -> 返回OSS路径**。

### 核心理念

我们将把这个脱敏模块设计成一个独立的、可部署的**微服务**。这种设计具有高度内聚性、易于维护、可独立扩展等优点，非常适合处理这类原子化任务。

### 1. 总体工作流

下面是当一个请求到达时，系统内部发生的详细步骤：

1.  **API接收请求**：客户端通过 `POST` 请求，以 `multipart/form-data` 格式，将DICOM文件和指定的脱敏配置（`profile`）发送到脱敏服务的API端点。
2.  **请求校验**：服务首先验证请求的合法性，例如文件是否存在、是否为有效的DICOM格式、指定的`profile`是否有效。
3.  **内存中处理**：为了效率和安全，服务将上传的文件内容读入内存中，不写入本地磁盘。
4.  **加载脱敏规则**：根据请求中指定的`profile`，从配置文件中加载对应的脱敏规则集。
5.  **执行脱敏**：
    *   使用`pydicom`库解析内存中的DICOM数据。
    *   遍历加载的规则，对DICOM数据集（dataset）中的每个Tag执行相应的操作（替换、移除、哈希等）。
    *   强制更新`PatientIdentityRemoved (0012,0062)`标签为`YES`。
6.  **生成新文件**：将修改后的DICOM数据集在内存中保存为一个新的字节流（bytes stream）。
7.  **上传至OSS**：
    *   生成一个唯一的对象键（Object Key），例如使用`UUID`，以避免文件名冲突 (`anonymized/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx.dcm`)。
    *   使用阿里云OSS SDK，将内存中的新文件字节流直接上传到指定的Bucket中。
8.  **构建返回路径**：上传成功后，根据Bucket名称、Endpoint和Object Key，拼接成可访问的完整OSS URL。
9.  **响应客户端**：向客户端返回一个包含成功标识和OSS URL的JSON响应。

---

### 2. API接口设计

这是模块对外暴露的契约，设计需清晰明了。

*   **Endpoint**: `POST /api/v1/anonymize`
*   **Request**:
    *   **Method**: `POST`
    *   **Content-Type**: `multipart/form-data`
    *   **Body Parts**:
        *   `file`: (必需) 待脱敏的DICOM文件。
        *   `profile`: (可选, string) 指定使用的脱敏规则配置。例如: `"default"`, `"research"`, `"full_anonymous"`。如果未提供，则使用默认的`profile`。
*   **Success Response (Status `200 OK`)**:
    ```json
    {
      "success": true,
      "message": "File anonymized and uploaded successfully.",
      "data": {
        "originalFilename": "CT_Chest_123.dcm",
        "ossUrl": "https://your-bucket.oss-cn-hangzhou.aliyuncs.com/anonymized/a1b2c3d4-e5f6-7890-1234-567890abcdef.dcm",
        "ossKey": "anonymized/a1b2c3d4-e5f6-7890-1234-567890abcdef.dcm"
      }
    }
    ```
*   **Error Responses**:
    *   **Status `400 Bad Request`**: 请求无效，如未上传文件、文件非DICOM格式、`profile`不存在。
    *   **Status `500 Internal Server Error`**: 服务器内部错误，如脱敏逻辑失败、OSS上传失败。

---

### 3. 核心模块实现方案 (Python + FastAPI/Flask)

选择Python是因为其拥有强大的`pydicom`库和成熟的云SDK。FastAPI是现代、高性能的Web框架，非常适合构建API服务。

#### 3.1. 技术栈

*   **Web框架**: **FastAPI** (或 Flask)
*   **DICOM处理**: **pydicom**
*   **云存储SDK**: **oss2** (阿里云官方Python SDK)
*   **运行环境**: **Docker**

#### 3.2. 项目结构

```
anonymizer-service/
├── app/
│   ├── __init__.py
│   ├── main.py             # API路由和主逻辑
│   ├── anonymizer.py       # 核心脱敏类
│   ├── config.py           # 配置加载 (OSS, profiles)
│   ├── profiles.yaml       # 脱敏规则配置文件
│   └── utils.py            # 工具函数 (如哈希)
├── Dockerfile
├── requirements.txt
└── .env                    # 环境变量 (OSS凭证等)
```

#### 3.3. 关键代码实现

**1. 脱敏规则配置 (`profiles.yaml`)**

采用YAML格式，清晰易读，方便非开发人员维护。

```yaml
# profiles.yaml
profiles:
  default:  # 默认配置，较为保守
    - tag: [0x0010, 0x0010]  # PatientName
      action: "replace"
      value: "ANONYMOUS"
    - tag: [0x0010, 0x0020]  # PatientID
      action: "hash"
    - tag: [0x0010, 0x0030]  # PatientBirthDate
      action: "remove"
    - tag: [0x0008, 0x0090]  # ReferringPhysicianName
      action: "empty"
    # ... 其他基础规则

  research: # 科研用，保留部分信息
    - tag: [0x0010, 0x0010]
      action: "replace"
      value: "RESEARCH-PATIENT"
    - tag: [0x0010, 0x0020]
      action: "hash_persistent" # 可复现的哈希，以便关联同一患者数据
      # secret_key: some_secret # 可以为项目配置一个密钥
    - tag: [0x0010, 0x1010]  # PatientAge
      action: "keep"
    - tag: [0x0010, 0x0040]  # PatientSex
      action: "keep"
    # ... 其他科研规则
```

**2. 核心脱敏逻辑 (`anonymizer.py`)**

```python
# app/anonymizer.py
import pydicom
from pydicom.errors import InvalidDicomError
from io import BytesIO
import yaml
from .utils import hash_value # 假设utils里有哈希函数

class DicomAnonymizer:
    def __init__(self, profile_name: str = 'default'):
        self.rules = self._load_rules(profile_name)

    def _load_rules(self, profile_name):
        with open("app/profiles.yaml", "r") as f:
            all_profiles = yaml.safe_load(f)
        return all_profiles['profiles'].get(profile_name, [])

    def anonymize(self, file_bytes: bytes) -> pydicom.Dataset:
        try:
            # 从字节流读取，不在磁盘上创建临时文件
            dataset = pydicom.dcmread(BytesIO(file_bytes))
        except InvalidDicomError:
            raise ValueError("Invalid DICOM file.")

        for rule in self.rules:
            tag = tuple(rule['tag'])
            action = rule['action']
          
            if tag in dataset:
                if action == "remove":
                    del dataset[tag]
                elif action == "empty":
                    dataset[tag].value = ""
                elif action == "replace":
                    dataset[tag].value = rule['value']
                elif action == "hash":
                    dataset[tag].value = hash_value(str(dataset[tag].value))
                # 可以扩展更多action, 如 "keep", "date_shift"等

        # 关键步骤：标记文件已被脱敏
        dataset.add_new