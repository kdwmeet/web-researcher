# Autonomous Web Research Agent (자율 심층 웹 리서치 에이전트)

## 1. 프로젝트 개요

Autonomous Web Research Agent는 LangGraph의 순환형 라우팅(Cyclic Routing)과 외부 도구 연동(Tool Calling) 기능을 활용하여, 스스로 판단하고 웹을 검색하는 AI 에이전트 시스템입니다.

단순히 사전에 학습된 지식에 의존하는 것을 넘어, 사용자의 복잡한 질문을 분석하고 DuckDuckGo 검색 엔진을 통해 실시간 데이터를 수집합니다. 수집된 정보가 부족하다고 판단할 경우 에이전트가 스스로 검색어를 수정하여 추가 검색을 진행하며, 충분한 정보가 모이거나 최대 검색 횟수에 도달하면 최종 심층 리포트를 작성합니다. Pydantic을 통해 에이전트의 의사결정(검색 여부, 검색어 도출, 최종 답변 작성)을 엄격하게 통제합니다.

## 2. 시스템 아키텍처



본 시스템은 외부 도구와 상호작용하며 상태를 갱신하는 루프(Loop) 형태의 워크플로우를 가집니다.

1. **Agent Node (의사결정):** 현재까지 수집된 웹 검색 결과(Context)와 과거 검색어 기록을 바탕으로 추가 검색이 필요한지 판별합니다. Pydantic 스키마(`AgentDecision`)를 통해 다음 행동 지침을 구조화된 JSON 형태로 반환합니다.
2. **Search Node (정보 수집):** Agent Node에서 도출한 최적화된 검색어를 사용하여 `DuckDuckGoSearchRun` 도구를 호출합니다. 검색된 원문 데이터를 상태 객체의 Context에 누적하고 루프 카운트를 증가시킵니다.
3. **Conditional Routing:** Agent Node의 `needs_search` 결과값과 무한 루프 방지를 위한 `loop_count`(최대 3회)를 평가하여, Search Node로 재진입할지 반복을 종료(`END`)할지 결정합니다.
4. **Node-level Streaming:** 에이전트의 판단 과정과 검색 도구의 실행 현황을 Streamlit 화면에 실시간으로 중계하여 에이전트의 사고 흐름을 시각화합니다.

## 3. 기술 스택

* **Language:** Python 3.10+
* **Package Manager:** uv
* **LLM:** OpenAI gpt-5-mini (검색어 추론 및 정보 요약)
* **Data Validation:** Pydantic (v2)
* **Orchestration:** LangGraph, LangChain (langchain_core, langchain_community)
* **Search Tool:** DuckDuckGo Search API (`duckduckgo-search`, `ddgs`)
* **Web Framework:** Streamlit

## 4. 프로젝트 구조

```text
web-researcher/
├── .env                  # OpenAI API 키 설정
├── requirements.txt      # 의존성 패키지 목록 (ddgs 포함)
├── main.py               # Streamlit 기반 리서치 진행 현황 및 실시간 중계 대시보드
└── app/
    ├── __init__.py
    └── graph.py          # 웹 검색 도구 연동, 에이전트 의사결정 노드 및 라우팅 로직 구현
```

## 5. 설치 및 실행 가이드
### 5.1. 환경 변수 설정
프로젝트 루트 경로에 .env 파일을 생성하고 API 키를 입력하십시오.

```Ini, TOML
OPENAI_API_KEY=sk-your-api-key-here
```
### 5.2. 의존성 설치 및 앱 실행
독립된 가상환경을 구성하고 애플리케이션을 구동합니다.

```Bash
uv venv
uv pip install -r requirements.txt
uv run streamlit run main.py
```
## 6. 테스트 시나리오 및 검증 방법
애플리케이션 구동 후 다음 과정을 거쳐 에이전트의 자율 검색 로직을 검증합니다.

* **복합 추론 질문 테스트**: 단일 검색으로 답을 찾기 어려운 복합적인 질문(예: "최근 발표된 특정 기술의 장단점과 주요 경쟁사 현황")을 입력합니다.

* **자율 순환(Loop) 시스템 검증**: 우측 '리서치 진행 현황' 패널에서 에이전트가 첫 번째 검색 결과를 확인한 뒤 정보가 부족하다고 판단하여 새로운 검색어를 도출하고, 웹 검색(Search Node)을 반복 수행하는지 확인합니다.

* **무한 루프 방지 및 결과 병합**: 에이전트가 스스로 충분한 정보를 모았다고 판단하거나, 설정된 최대 검색 횟수(3회)에 도달했을 때 탐색을 중단하고 최종 마크다운 리포트를 정상적으로 출력하는지 점검합니다. 하단 익스팬더를 통해 에이전트가 참조한 실제 검색 원문을 확인할 수 있습니다.

## 7. 실행 화면