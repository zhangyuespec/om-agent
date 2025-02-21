# OM-Agent 运维知识库助手

## 🚀 技术栈

- **核心框架**: 
  [Flask](https://flask.palletsprojects.com/) - 轻量级Web框架
- **向量数据库**: 
  [ChromaDB](https://www.trychroma.com/) - 开源向量数据库
- **网页解析**: 
  [BeautifulSoup](https://www.crummy.com/software/BeautifulSoup/) - HTML/XML解析库
- **AI服务**: 
  [SiliconFlow API](https://www.siliconflow.cn/) - 大模型API服务
- **配置管理**: 
  [PyYAML](https://pyyaml.org/) - YAML配置文件处理

## 📦 安装指南

### Conda 环境安装

```bash
# 创建conda环境
conda create -n om-agent python=3.9
conda activate om-agent

# 安装依赖
pip install -r requirements.txt

# 配置环境
cp config/config.example.yaml config/config.yaml
nano config/config.yaml  # 按需修改配置
```

### 常规安装

```bash
git clone https://github.com/your-repo/om-agent.git
cd om-agent
python -m venv venv
source venv/bin/activate  # Windows使用 venv\Scripts\activate
pip install -r requirements.txt
```

## ⚙️ 配置说明

1. **配置文件**:
   - 使用 `config/config.example.yaml` 作为模板
   - 复制并重命名为 `config/config.yaml`
   ```bash
   cp config/config.example.yaml config/config.yaml
   ```
   - 需要配置的关键参数：
     - `wiki`: 企业Wiki认证信息
     - `siliconflow.api_key`: AI服务API密钥
     - `vector_db.persist_directory`: 向量数据库存储路径

2. **敏感信息**:
   - 请勿将 `config.yaml` 提交到版本控制
   - 已通过 `.gitignore` 自动排除

## 🏃 快速启动

```bash
# 启动服务
./run.sh

# 或手动启动
flask run --host 0.0.0.0 --port 8080
```

### API 使用示例

```bash
# 初始化知识库 (POST)
curl -X POST http://localhost:8080/init \
  -H "Content-Type: application/json" \
  -d '{"page_id": "74780551"}'

# 提问示例 (GET)
curl "http://localhost:8080/query?question=如何重启生产服务器？"
```

## 🌟 功能特性

- 支持增量式知识库更新
- 流式问答接口
- 自动重试机制（网络请求）
- 内容安全过滤
- 多格式文档支持（HTML/Text）

## 🔧 测试验证

```bash
# 运行单元测试
pytest tests/

# 检查服务状态
curl http://localhost:8080
```

## 📌 注意事项

- 推荐 Python 3.9+ 环境
- 首次使用需先执行知识库初始化
- 生产环境设置 `app.debug: false`
- Wiki页面需开启API访问权限

## 📄 许可证
MIT License
