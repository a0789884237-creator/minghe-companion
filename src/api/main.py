"""FastAPI application for Minghe Companion."""

import uuid
from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from src.agents.psychology_master import (
    PsychologyMasterAgent,
    get_psychology_master_agent,
)
from src.llm.client import get_llm_client
from src.core.config import settings


class ChatRequest(BaseModel):
    """聊天请求。"""

    user_id: str = Field(..., description="用户ID")
    message: str = Field(..., min_length=1, description="用户消息")
    session_id: str | None = Field(default=None, description="会话ID")


class ChatResponse(BaseModel):
    """聊天响应。"""

    response: str
    intent: str
    risk_level: str
    session_id: str
    tools_used: list[str]
    metadata: dict[str, str]


class HealthResponse(BaseModel):
    """健康检查响应。"""

    status: str
    timestamp: datetime
    version: str


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理。"""
    # 启动时
    print("Starting Minghe Companion API...")
    yield
    # 关闭时
    print("Shutting down Minghe Companion API...")


# 创建FastAPI应用
app = FastAPI(
    title="明禾陪伴 - 心理资讯大师 API",
    description="基于AI的心理健康服务平台核心API",
    version="0.1.0",
    lifespan=lifespan,
)

# 配置CORS - 允许所有来源
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 健康检查端点
@app.get("/health", response_model=HealthResponse)
async def health_check():
    """健康检查。"""
    return HealthResponse(status="healthy", timestamp=datetime.now(), version="0.1.0")


# 聊天端点
@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """与心理资讯大师对话。

    Args:
        request: 聊天请求

    Returns:
        ChatResponse: Agent响应
    """
    # 获取或生成session_id
    session_id = request.session_id or str(uuid.uuid4())

    try:
        # 获取LLM客户端
        llm_client = get_llm_client()
        print(f"DEBUG: llm_client = {llm_client}, api_key = {llm_client.api_key}")

        # 获取Agent实例
        agent = get_psychology_master_agent(llm_client=llm_client)
        print(f"DEBUG: agent.llm_client = {agent.llm_client}")

        # 处理消息
        response = agent.chat(
            user_id=request.user_id,
            message=request.message,
            session_id=session_id,
        )

        return ChatResponse(
            response=response.content,
            intent=response.intent.value,
            risk_level=response.risk_level.value,
            session_id=session_id,
            tools_used=response.tools_used,
            metadata=response.metadata,
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"处理消息时发生错误: {str(e)}")


# 评估端点
@app.post("/assessment")
async def assessment(user_id: str, assessment_type: str, answers: dict[str, int]):
    """心理评估。

    Args:
        user_id: 用户ID
        assessment_type: 评估类型 (anxiety/depression/stress)
        answers: 答案 {question_id: value}

    Returns:
        评估结果
    """
    from src.tools.assessment import get_assessment_tool

    try:
        assessment_tool = get_assessment_tool()
        result = assessment_tool.calculate_score(assessment_type, answers)

        # 保存评估结果
        assessment_tool.save_assessment_result(user_id, result)

        return result.to_dict()

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"评估计算错误: {str(e)}")


# 评估模板端点
@app.get("/assessment/template/{assessment_type}")
async def get_assessment_template(assessment_type: str):
    """获取评估问卷模板。

    Args:
        assessment_type: 评估类型

    Returns:
        评估模板
    """
    from src.tools.assessment import get_assessment_tool

    assessment_tool = get_assessment_tool()
    template = assessment_tool.get_assessment_template(assessment_type)

    if not template:
        raise HTTPException(
            status_code=404, detail=f"未找到评估类型: {assessment_type}"
        )

    return template


# 用户画像端点
@app.get("/user/{user_id}/profile")
async def get_user_profile(user_id: str):
    """获取用户画像。

    Args:
        user_id: 用户ID

    Returns:
        用户画像
    """
    from src.memory.system import get_memory_system

    memory_system = get_memory_system()
    profile = memory_system.get_user_profile(user_id)

    if not profile:
        raise HTTPException(status_code=404, detail=f"未找到用户: {user_id}")

    return {
        "user_id": profile.user_id,
        "age_group": profile.age_group,
        "name": profile.name,
        "preferences": profile.preferences,
        "characteristics": profile.characteristics,
    }


@app.patch("/user/{user_id}/profile")
async def update_user_profile(user_id: str, updates: dict[str, str]):
    """更新用户画像。

    Args:
        user_id: 用户ID
        updates: 更新的字段

    Returns:
        更新后的用户画像
    """
    from src.memory.system import get_memory_system

    memory_system = get_memory_system()
    profile = memory_system.update_user_profile(user_id, **updates)

    return {
        "user_id": profile.user_id,
        "age_group": profile.age_group,
        "name": profile.name,
        "preferences": profile.preferences,
        "updated_at": profile.updated_at.isoformat(),
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "src.api.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.api_debug,
    )
