# 明禾陪伴 - 心理资讯大师 Agent 开发指南

> **For Claude:** 本项目为"明禾陪伴"心理健康平台的AI Agent核心模块。
> 使用 `python-patterns`, `python-testing`, `software-architecture` skills。

## 1. 项目概述

- **项目名称**: 明禾陪伴 (Minghe Companion)
- **核心模块**: 心理资讯大师AI Agent
- **技术栈**: Python 3.10+ | LangGraph | LangChain | GLM-4.7 Flash
- **目标**: 构建全生命周期心理健康服务的AI对话Agent

## 2. 开发命令

### 2.1 环境管理

```bash
# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate    # Windows

# 安装依赖
pip install -e ".[dev]"
```

### 2.2 代码质量

```bash
# 格式化代码
black src/ tests/
isort src/ tests/

# 代码检查
ruff check src/ tests/
ruff check src/ tests/ --fix  # 自动修复

# 类型检查
mypy src/
mypy src/ --strict  # 严格模式

# 安全扫描
bandit -r src/
safety check
```

### 2.3 测试

```bash
# 运行所有测试
pytest

# 运行单个测试文件
pytest tests/test_agent.py -v

# 运行单个测试函数
pytest tests/test_agent.py::test_crisis_detection -v

# 带覆盖率
pytest --cov=src --cov-report=html --cov-report=term-missing

# 测试特定标记
pytest -m "unit" -v
pytest -m "integration" -v

# Watch模式（开发时自动重跑）
pytest --watch
```

### 2.4 运行

```bash
# 启动API服务
uvicorn src.api.main:app --reload --port 8000

# 运行Agent交互式测试
python -m src.scripts.interactive_chat
```

## 3. 代码规范

### 3.1 导入顺序

```python
# 标准库
import os
import sys
from typing import Optional, List, Dict, Any
from pathlib import Path

# 第三方库
import pytest
from fastapi import FastAPI
from langchain_core.messages import BaseMessage, HumanMessage
from langgraph.graph import StateGraph

# 本地模块
from src.agents.psychology_master import PsychologyMasterAgent
from src.memory.system import MemorySystem
from src.tools.crisis import CrisisDetector
```

### 3.2 命名约定

| 类型 | 规则 | 示例 |
|------|------|------|
| 类 | PascalCase | `PsychologyMasterAgent` |
| 函数/方法 | snake_case | `detect_crisis()` |
| 常量 | UPPER_SNAKE_CASE | `MAX_CONVERSATION_TURNS` |
| 私有方法 | `_leading_underscore` | `_validate_input()` |
| Pydantic模型 | PascalCase + Schema | `UserProfileSchema` |
| 配置文件 | snake_case | `config.yaml` |

### 3.3 类型提示（必需）

```python
# 必须为所有函数参数和返回值提供类型提示
from typing import Optional, List, Dict, Any, Union
from dataclasses import dataclass

def process_message(
    message: str,
    user_id: str,
    context: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """处理用户消息并返回响应。"""
    ...

@dataclass
class UserProfile:
    """用户画像数据结构。"""
    user_id: str
    age_group: str
    preferences: Dict[str, Any]
```

### 3.4 文档字符串

```python
def detect_crisis_keywords(message: str) -> Dict[str, Any]:
    """检测消息中的危机信号关键词。
    
    Args:
        message: 用户输入的消息内容
        
    Returns:
        包含检测结果的字典:
            - detected: bool - 是否检测到危机信号
            - keyword: str - 检测到的关键词
            - risk_level: str - 风险等级 (low/medium/high/critical)
            
    Raises:
        ValueError: 如果消息为空
        
    Example:
        >>> result = detect_crisis_keywords("我不想活了")
        >>> result['detected']
        True
    """
    if not message:
        raise ValueError("消息内容不能为空")
    ...
```

### 3.5 错误处理

```python
# ✅ 正确：具体异常 + 上下文记录
class AgentError(Exception):
    """Agent相关基础异常。"""
    pass

class CrisisDetectionError(AgentError):
    """危机检测失败时抛出。"""
    pass

def detect_crisis(message: str) -> Dict[str, Any]:
    try:
        return _detect_crisis_impl(message)
    except ValueError as e:
        logger.error(f"消息验证失败: {message[:50]}...")
        raise CrisisDetectionError(f"无法检测危机信号: {e}") from e

# ❌ 错误：空捕获 + 静默失败
def detect_crisis(message: str):
    try:
        return _detect_crisis_impl(message)
    except:
        return {"detected": False}
```

### 3.6 日志规范

```python
import logging
import json
from datetime import datetime

# 使用结构化日志
def log_interaction(
    user_id: str,
    message: str,
    response: str,
    metadata: Optional[Dict] = None
):
    """记录用户交互日志。"""
    log_entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "user_id": user_id,
        "message_preview": message[:100],
        "response_preview": response[:100],
        "metadata": metadata or {}
    }
    logger.info(json.dumps(log_entry))
```

## 4. 项目结构

```
minghe-companion/
├── src/
│   ├── __init__.py
│   ├── api/
│   │   ├── __init__.py
│   │   ├── main.py              # FastAPI应用入口
│   │   └── routes.py           # API路由
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── base.py             # Agent基类
│   │   ├── psychology_master.py # 心理资讯大师Agent
│   │   └── state.py            # 状态定义
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── base.py             # 工具基类
│   │   ├── crisis.py           # 危机检测工具
│   │   ├── rag.py              # RAG检索工具
│   │   └── assessment.py       # 心理评估工具
│   ├── memory/
│   │   ├── __init__.py
│   │   ├── base.py             # 记忆基类
│   │   ├── short_term.py       # 短期记忆
│   │   └── long_term.py        # 长期记忆
│   ├── knowledge/
│   │   ├── __init__.py
│   │   ├── base.py             # 知识库基类
│   │   └── manager.py          # 知识库管理器
│   └── core/
│       ├── __init__.py
│       ├── config.py           # 配置管理
│       ├── prompt.py          # 提示词模板
│       └── constants.py        # 常量定义
├── tests/
│   ├── __init__.py
│   ├── test_agents/
│   ├── test_tools/
│   └── test_memory/
├── knowledge_base/             # 知识库文件
│   ├── psychology_basics/
│   ├── therapy_techniques/
│   ├── chinese_wisdom/
│   └── crisis_resources/
├── docs/
│   └── plans/
├── pyproject.toml
├── .env.example
└── README.md
```

## 5. 核心开发原则

### 5.1 KISS & YAGNI

- 保持代码简单直接
- 不添加未来可能需要的功能
- 每个文件不超过350行

### 5.2 SOLID原则

- 单一职责：每个类/模块有明确目的
- 开闭原则：对扩展开放，对修改封闭
- 依赖倒置：依赖抽象而非具体实现

### 5.3 安全优先

```python
# ✅ 正确：环境变量存储密钥
import os
API_KEY = os.getenv("ZHIPU_API_KEY")

# ❌ 错误：硬编码密钥
API_KEY = "sk-xxx..."  # 禁止！
```

## 6. 测试规范

### 6.1 单元测试

```python
import pytest
from src.tools.crisis import CrisisDetector

class TestCrisisDetector:
    """危机检测器测试。"""
    
    def test_detect_suicide_keyword(self):
        """测试自杀关键词检测。"""
        detector = CrisisDetector()
        result = detector.detect("我不想活了")
        
        assert result["detected"] is True
        assert result["risk_level"] == "critical"
    
    def test_no_crisis_returns_normal(self):
        """测试正常消息返回。"""
        detector = CrisisDetector()
        result = detector.detect("今天天气真好")
        
        assert result["detected"] is False
        assert result["risk_level"] == "low"
```

### 6.2 集成测试

```python
import pytest
from src.agents.psychology_master import PsychologyMasterAgent

@pytest.mark.integration
class TestPsychologyMasterAgent:
    """心理资讯大师Agent集成测试。"""
    
    @pytest.fixture
    def agent(self):
        return PsychologyMasterAgent()
    
    def test_basic_conversation(self, agent):
        """测试基础对话功能。"""
        response = agent.chat(
            user_id="test_user",
            message="我最近压力很大"
        )
        
        assert response is not None
        assert len(response.content) > 0
```

## 7. 提交规范

```bash
# 提交前检查
ruff check src/ tests/
mypy src/
pytest -v

# 提交信息格式
git commit -m "feat(agent): 添加危机检测功能

- 实现自杀/自伤关键词检测
- 添加4级风险评估系统
- 集成危机干预协议

Closes #123"
```

## 8. 关键提醒

> ⚠️ **心理健康Agent特殊要求**:
> 1. 危机检测是最高优先级，必须有测试覆盖
> 2. 不输出任何可能导致用户伤害的内容
> 3. 所有响应需符合伦理和法律要求
> 4. 严格保护用户隐私，不记录敏感对话
