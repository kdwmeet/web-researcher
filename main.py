import streamlit as st
from app.graph import app_graph

st.set_page_config(page_title="자율 웹 리서치 에이전트", layout="wide")

st.title("자율 심층 웹 리서치 에이전트")
st.markdown("질문을 입력하면 AI가 스스로 판단하여 필요한 만큼 웹 검색을 수행하고 최종 리포트를 작성합니다.")
st.divider()

col1, col2 = st.columns([1, 2])

with col1:
    st.subheader("리서치 주제 입력")
    with st.form(key="research_form"):
        topic_input = st.text_area("궁금한 점을 구체적으로 입력하십시오.", height=150, placeholder="예: 양자 컴퓨팅의 최신 발전 동향과 상용화 예상 시기에 대해 조사해 줘.")
        submit_btn = st.form_submit_button("리서치 시작", use_container_width=True)

with col2:
    st.subheader("리서치 진행 현황 및 결과")
    status_container = st.empty()
    result_container = st.container()
    
    if submit_btn and topic_input.strip():
        initial_state = {
            "topic": topic_input,
            "search_history": [],
            "context": [],
            "loop_count": 0,
            "current_query": "",
            "final_answer": ""
        }
        
        with status_container.container():
            st.info("리서치를 시작합니다...")
            
        final_state = None
        
        # 노드 단위 스트리밍으로 진행 상황 실시간 출력
        for output in app_graph.stream(initial_state):
            for node_name, state_update in output.items():
                final_state = state_update
                
                with status_container.container():
                    if node_name == "agent_node":
                        if state_update.get("needs_search") and state_update.get("current_query"):
                            st.warning(f"에이전트 판단: 정보가 부족합니다. 다음 검색어를 생성했습니다.\n\n**검색어:** {state_update['current_query']}")
                        else:
                            st.success("에이전트 판단: 충분한 정보가 수집되었습니다. 최종 답변을 작성합니다.")
                            
                    elif node_name == "search_node":
                        st.info(f"웹 검색 수행 중... (수행 횟수: {state_update.get('loop_count')}/3)")
                        
        # 최종 답변 출력
        if final_state and final_state.get("final_answer"):
            with result_container:
                st.markdown("### 최종 리서치 리포트")
                st.markdown(final_state["final_answer"])
                
                with st.expander("에이전트 검색 기록 및 수집된 원문 데이터 보기"):
                    st.write("**검색어 기록:**", ", ".join(final_state.get("search_history", [])))
                    st.divider()
                    for idx, ctx in enumerate(final_state.get("context", [])):
                        st.text_area(f"수집된 정보 {idx+1}", value=ctx, height=200, disabled=True)