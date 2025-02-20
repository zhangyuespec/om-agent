# om-agent
## 项目介绍

OM-Agent 是一个基于 Flask 的智能代理系统，集成了 ChromaDB 向量数据库和 BeautifulSoup 网页解析功能。该项目主要用于处理知识库的存储、检索和分析任务，通过 RESTful API 提供数据服务。

主要功能包括：
- 知识库数据存储与检索
- 网页内容解析与处理
- 向量化数据管理
- 基于配置的灵活部署

## 使用方法

1. 启动服务：
   ```bash
   ./run.sh
   ```

2. 访问 API：
   - 服务默认运行在 `http://localhost:8080`
   - 可通过配置文件 `config/config.yaml` 修改主机和端口

3. 配置管理：
   - 所有配置项均在 `config/config.yaml` 中管理
   - 包括数据库路径、API 密钥等敏感信息

## 安装步骤

1. 克隆项目：
   ```bash
   git clone https://github.com/your-repo/om-agent.git
   cd om-agent
   ```

2. 安装依赖：
   ```bash
   pip install -r requirements.txt
   ```

3. 配置环境：
   - 复制 `.env.example` 为 `.env` 并填写必要信息
   - 修改 `config/config.yaml` 中的配置项

4. 初始化数据库：
   ```bash
   python init_db.py
   ```

5. 启动服务：
   ```bash
   ./run.sh
   ```

## 注意事项
- 确保 Python 版本 >= 3.8
- 首次运行前需要初始化数据库
- 生产环境建议关闭调试模式
