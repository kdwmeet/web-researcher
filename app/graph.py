from typing import TypedDict, List
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langgraph.graph import StateGraph, START, END
from langchain_community.tools import DuckDuckGoSearchRun

load_dotenv()

# Pydantic 스키마 정의 (에이전트의 의사결정 강제)
class AgentDecision(BaseModel):
    """에이전트의 다음 행동 결정"""
    needs_search: bool = Field(description="사용자의 질문을 완벽히 답변하기 위해 웹 검색이 추가로 필요한지 여부")
    search_query: str = Field(description="검색이 필요할 경우 사용할 구체적이고 최적화된 검색어 (필요 없을 경우 빈 문자열)")
    final_answer: str = Field(description="검색이 완료되었거나 필요 없을 경우 사용자에게 제공할 최종 상세 답변 (마크다운 포맷)")

# 상태 정의
class ResearchState(TypedDict):
    topic: str
    search_history: List[str]       # 수행한 검색어 목록
    context: List[str]              # 수집된 검색 결과 원문
    loop_count: int                 # 무한 루프 방지용 카운터
    current_query: str              # 현재 실행할 검색어
    final_answer: str               # 최종 도출된 답변
    
# 도구 초기화
search_tool = DuckDuckGoSearchRun()

# 노드 구현
def agent_node(state: ResearchState):
    """현재까지 수집된 정보를 바탕으로 검색을 계속 할지, 답변을 작성할지 결정합니다."""
    llm = ChatOpenAI(model="gpt-5-mini", reasoning_effort="low")
    structured_llm = llm.with_structured_output(AgentDecision)

    # 컨텐스트 병합
    context_str = "\n\n".join(state.get("context", []))

    prompt = ChatPromptTemplate.from_messages([
        ("system", """당신은 심층 웹 리서치 전문가입니다.
주어진 주제에 대해 완벽하고 정확한 답변을 제공해야 합니다.
현재까지 수집된 정보를 분석하여, 답변을 구성하기에 정보가 부족하다면 새로운 검색어를 제안하십시오.
충분한 정보가 모였거나 최대 검색 횟수에 도달했다면, 상세하고 구조화된 최종 답변을 작성하십시오.

[수집된 정보]
{context}

[이전 검색어 기록]
{search_history}"""),
        ("user", "리서치 주제: {topic}")
    ])

    decision: AgentDecision = (prompt | structured_llm).invoke({
        "context": context_str,
        "search_history": ", ".join(state.get("search_history", [])),
        "topic": state.get("topic")
    }) 

    return {
        "current_query": decision.search_query,
        "final_answer": decision.final_answer,
        "needs_search": decision.needs_search
    }

def search_node(state: ResearchState):
    """결정된 검색어를 바탕으로 웹 검색을 수행하고 결과를 컨텍스트에 추가합니다."""
    query = state.get("current_query")

    try:
        # DuckDuckGo 검색 실행
        result = search_tool.invoke(query)
    except Exception as e:
        result = f"검색 중 오류 발생: {str(e)}"

    new_context = state.get("context", []).copy()
    new_context.append(f"검색어 [{query}] 결과:\n{result}")

    new_history = state.get("search_history", []).copy()
    new_history.append(query)

    return {
        "context": new_context,
        "search_history": new_history,
        "loop_count": state.get("loop_count", 0) + 1
    }

# 라우팅 로직
def route_research(state: dict):
    """에이전트의 결정과 루프 카운트를 확인하여 분기합니다."""
    # 최대 3번까지만 검색 허용
    if state.get("needs_search") and state.get("loop_count", 0) < 3:
        return "search_node"
    return END

# 그래프 조립
workflow = StateGraph(ResearchState)

workflow.add_node("agent_node", agent_node)
workflow.add_node("search_node", search_node)

workflow.add_edge(START, "agent_node")
workflow.add_conditional_edges("agent_node", route_research, ["search_node", END])
workflow.add_edge("search_node", "agent_node")

app_graph = workflow.compile()