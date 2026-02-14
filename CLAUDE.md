# 明禾陪伴 - 心理资讯大师 Agent 项目

## 1. 项目概览

- **愿景**: 构建全生命周期心理健康服务平台——"明禾陪伴"
- **当前阶段**: 核心AI Agent模块开发
- **核心架构**: LangGraph状态图 + 多工具协作 + 分层记忆系统
- **开发策略**: TDD优先，安全第一，逐步迭代

## 2. 项目结构

```
minghe-companion/
├── src/
│   ├── agents/          # Agent核心逻辑
│   ├── tools/           # 工具系统
│   ├── memory/          # 记忆系统
│   ├── knowledge/       # 知识库管理
│   ├── api/             # FastAPI服务
│   └── core/            # 核心配置
├── tests/               # 测试文件
├── knowledge_base/      # 知识库文档
└── docs/               # 文档
```

## 3. 编码规范

### 3.1 核心原则

- **KISS & YAGNI**: 保持简单，不提前设计
- **类型提示**: 所有函数必须有类型注解
- **文档**: 公共API必须写docstring
- **测试**: 核心功能必须有测试覆盖

### 3.2 心理健康特殊要求

1. **危机检测优先级最高**: 任何可能涉及自伤/自杀的内容必须立即响应
2. **不替代专业诊断**: Agent不提供诊断，只提供支持性信息
3. **数据保护**: 严格保护用户隐私，不记录敏感对话内容

## 4. 开发流程

### 4.1 任务执行

1. 先写测试 (TDD)
2. 运行测试确认失败
3. 编写最小实现
4. 测试通过后重构
5. 提交代码

### 4.2 代码质量门禁

```bash
# 必须在提交前运行
ruff check src/ tests/
mypy src/
pytest -v
```

## 5. 关键模块说明

### 5.1 Agent模块 (src/agents/)

- `psychology_master.py`: 心理资讯大师核心Agent
- `state.py`: LangGraph状态定义
- `base.py`: Agent基类

### 5.2 工具模块 (src/tools/)

- `crisis.py`: 危机检测工具（最高优先级）
- `rag.py`: RAG知识库检索
- `assessment.py`: 心理评估问卷

### 5.3 记忆模块 (src/memory/)

- `short_term.py`: 短期记忆（会话上下文）
- `long_term.py`: 长期记忆（用户画像）

## 6. 注意事项

- 遵循 `AGENTS.md` 中的所有规范
- 使用 `python-patterns` skill指导编码
- 使用 `software-architecture` skill指导架构决策
- 心理健康Agent必须遵守伦理边界
