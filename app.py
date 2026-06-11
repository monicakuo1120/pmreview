"""Streamlit MVP for PM Scenario Analyzer.

Run locally with:
    streamlit run app.py
"""

from __future__ import annotations

import streamlit as st

from models import AnalysisResult, DecisionTable, GapItem, MissingQuestion, StateDefinition, ToolMapping
from services import analyze_requirement

st.set_page_config(page_title="PM Scenario Analyzer", page_icon="🧭", layout="wide")

MATURITY_NOTE = "Requirement Maturity Level 僅供參考，不代表正式核准，也不取代 PM、UX、工程、法遵、風控、法務或營運審查。"
CX_NOTE = "This is a requirement-level design package. It is not a production agent instruction, final prompt, or approved implementation artifact."
AGENT_READY_LEVEL = "Level 5"



def main() -> None:
    st.title("🧭 PM Scenario Analyzer MVP")
    st.caption("Start with what you have：自由文字、Figma 截圖或結構化模板都會先轉成 ScenarioSpec，再進行分析。")

    left, right = st.columns([0.38, 0.62], gap="large")
    with left:
        free_text, structured_text, supplemental_notes, uploaded_files, analyze_clicked = render_input_panel()

    if analyze_clicked:
        if not free_text.strip() and not structured_text.strip() and not uploaded_files:
            st.error("請至少提供一種輸入：自由文字、Figma 截圖或結構化模板。")
            return
        image_names = [file.name for file in uploaded_files]
        result = analyze_requirement(
            free_text=free_text,
            structured_text=structured_text,
            supplemental_notes=supplemental_notes,
            image_filenames=image_names,
        )
        st.session_state["analysis_result"] = result
        st.session_state["cx_package_requested"] = False

    with right:
        result = st.session_state.get("analysis_result")
        if result is None:
            render_empty_state()
        else:
            render_output_panel(result)


def render_input_panel() -> tuple[str, str, str, list, bool]:
    st.subheader("Input")
    selected_modes = st.multiselect(
        "選擇輸入模式",
        ["Mode A：自由文字", "Mode B：Figma 截圖", "Mode C：結構化模板"],
        default=["Mode A：自由文字"],
        help="可選一種或多種。三種輸入最後都會進入 Scenario Normalization。",
    )

    free_text = ""
    structured_text = ""
    uploaded_files = []

    if "Mode A：自由文字" in selected_modes:
        st.markdown("#### Mode A：自由文字輸入")
        free_text = st.text_area(
            "貼上會議紀錄、零散想法、Figma 旁邊備註或業務口述內容",
            height=220,
            placeholder="例如：客戶可以掛失信用卡，先驗證身份，再選卡，停卡後問是否補發...",
        )

    if "Mode B：Figma 截圖" in selected_modes:
        st.markdown("#### Mode B：Figma 截圖輸入")
        st.info("第一版只支援圖片上傳，不支援 Figma API 或 Dev Mode Link。Mock Analyzer 會將圖片檔名納入輸入模式，暫不做真實 OCR。")
        uploaded_files = st.file_uploader(
            "上傳 Figma 流程圖截圖",
            type=["png", "jpg", "jpeg", "webp"],
            accept_multiple_files=True,
        )
        if uploaded_files:
            for file in uploaded_files:
                st.image(file, caption=file.name, use_container_width=True)

    if "Mode C：結構化模板" in selected_modes:
        st.markdown("#### Mode C：結構化模板輸入")
        structured_text = st.text_area(
            "填寫或貼上結構化需求",
            value=structured_template(),
            height=360,
        )

    supplemental_notes = st.text_area(
        "補充說明",
        height=120,
        placeholder="例如：哪些流程是 MVP、哪些規則待確認、哪些 API 尚未確定、哪些需法遵或風控確認。",
    )
    analyze_clicked = st.button("Analyze", type="primary", use_container_width=True)
    return free_text, structured_text, supplemental_notes, uploaded_files, analyze_clicked


def structured_template() -> str:
    return """# Feature Name

# Feature Type
Inquiry / Transaction / Hybrid

# Goal

# Main Flow
1. 
2. 
3. 

# Sub-scenarios
- 

# Business Rules
- 

# Decision Tables
- 

# State Model
- 

# Exception Cases
- 

# Journey Entry / Exit
Entry:
Exit:

# Tool / API Dependencies
- 

# Assumptions
- 

# Missing Information
- 
"""


def render_empty_state() -> None:
    st.subheader("Output")
    st.info("請在左側提供至少一種輸入並點擊 Analyze。")
    st.markdown(
        """
        **MVP 產品流程**

        ```text
        Input
        ↓
        Analyze
        ↓
        PM Review Mode
        ↓
        Gap Fixing Iteration
        ↓
        Agent Ready
        ↓
        Generate CX Agent Studio Package
        ```
        """
    )


def render_output_panel(result: AnalysisResult) -> None:
    st.subheader("Output")
    st.caption("預設顯示 PM Review Mode。CX Agent Studio Package 只有在 Agent Ready 或 PM 主動選擇產生時才顯示。")
    output_mode = st.radio(
        "選擇輸出",
        ["PM Review Mode", "Mermaid Flow", "CX Agent Studio Package"],
        horizontal=True,
        index=0,
    )

    if output_mode == "PM Review Mode":
        render_pm_review(result)
    elif output_mode == "Mermaid Flow":
        render_mermaid_flow(result)
    else:
        render_cx_gate(result)


def render_mermaid_flow(result: AnalysisResult) -> None:
    st.markdown("### Mermaid Flow")
    st.code(result.mermaid_flow, language="mermaid")
    st.download_button("下載 Mermaid", result.mermaid_flow, file_name="pm_scenario_flow.mmd", mime="text/plain")


def render_cx_gate(result: AnalysisResult) -> None:
    st.markdown("### CX Agent Studio Package")
    agent_ready = result.maturity_level == AGENT_READY_LEVEL
    cx_requested = st.session_state.get("cx_package_requested", False)

    if agent_ready or cx_requested:
        if not agent_ready:
            st.warning("目前需求尚未達到 Agent Ready；以下 Package 是 PM 主動產生的草稿，仍需先完成缺口修正。")
        render_cx_package(result)
        return

    st.info(
        "目前預設流程停在 PM Review Mode，請先依缺口分析反覆修正需求。"
        "當 Requirement Maturity 達到 Level 5：Agent Ready，或 PM 主動選擇時，才產生 CX Agent Studio Package。"
    )
    st.markdown(
        """
        **目前建議下一步**

        1. 回到 PM Review Mode 檢查缺漏項目。
        2. 補齊 Missing Questions、Business Rules、Decision Tables、State Definitions。
        3. 重新 Analyze。
        4. 若仍需提前產生 CX 草稿，可手動點擊下方按鈕。
        """
    )
    if st.button("Generate CX Agent Studio Package Draft", type="secondary"):
        st.session_state["cx_package_requested"] = True
        st.rerun()


def render_pm_review(result: AnalysisResult) -> None:
    spec = result.scenario_spec
    st.markdown("### ScenarioSpec Summary")
    st.json(
        {
            "feature_name": spec.feature_name,
            "feature_type": spec.feature_type,
            "goal": spec.goal,
            "input_modes": spec.input_modes,
            "journey_entry": spec.journey_entry,
            "journey_exit": spec.journey_exit,
            "assumptions": spec.assumptions,
            "missing_information": spec.missing_information,
        }
    )

    st.markdown("### Scenario Decomposition")
    st.dataframe([scenario.__dict__ for scenario in spec.sub_scenarios], use_container_width=True, hide_index=True)

    st.markdown("### Requirement Maturity")
    st.table(
        [
            {"Field": "Level", "Value": result.maturity_level},
            {"Field": "Label", "Value": result.maturity_label},
            {"Field": "Rationale", "Value": result.maturity_rationale},
            {"Field": "CX Package Default", "Value": "Available by default only when Level 5: Agent Ready"},
        ]
    )
    st.warning(MATURITY_NOTE)

    st.markdown("### Gap Fixing Iteration")
    st.markdown(
        """
        1. Review missing areas and missing questions.
        2. Update PM inputs with clarified rules, decisions, states, journeys, and API behavior.
        3. Click **Analyze** again.
        4. Generate CX Agent Studio Package only after Agent Ready or by explicit PM request.
        """
    )

    st.markdown("### 已涵蓋項目")
    render_gap_table(result.covered_areas)
    st.markdown("### 缺漏項目")
    render_gap_table(result.missing_areas)
    st.markdown("### 待確認問題")
    render_question_table(result.missing_questions)
    st.markdown("### 缺漏 Business Rules")
    render_gap_table(result.missing_business_rules)
    st.markdown("### 缺漏 Decision Tables")
    render_gap_table(result.missing_decision_tables)
    st.markdown("### 缺漏 State Definitions")
    render_gap_table(result.missing_state_definitions)
    st.markdown("### 缺漏 Journey Entry / Exit")
    render_gap_table(result.missing_journey_entry_exit)
    st.markdown("### 建議下一步")
    st.dataframe(result.recommended_next_actions, use_container_width=True, hide_index=True)


def render_cx_package(result: AnalysisResult) -> None:
    package = result.cx_package
    spec = result.scenario_spec
    st.warning(CX_NOTE)

    st.markdown("### Feature Summary")
    st.table([{"Field": key, "Value": value} for key, value in package.feature_summary.items()])

    st.markdown("### Scenario Breakdown")
    st.dataframe([scenario.__dict__ for scenario in spec.sub_scenarios], use_container_width=True, hide_index=True)

    st.markdown("### Task / Flow Steps")
    st.dataframe(package.task_flow_steps, use_container_width=True, hide_index=True)

    st.markdown("### Parameters")
    st.dataframe(package.parameters, use_container_width=True, hide_index=True)

    st.markdown("### State Model")
    if spec.state_model:
        render_state_table(spec.state_model)
    else:
        st.info("Mock Analyzer 已在 PM Review Mode 標示缺漏 State Definitions；補齊後可在此產生完整狀態模型。")

    st.markdown("### Decision Tables")
    if spec.decision_tables:
        for table in spec.decision_tables:
            render_decision_table(table)
    else:
        st.info("Mock Analyzer 已在 PM Review Mode 標示缺漏 Decision Tables；補齊後可在此產生正式決策表。")

    st.markdown("### Tool / API Mapping")
    render_tool_table(package.tool_mapping)

    st.markdown("### Exception Handling")
    st.dataframe(package.exception_handling, use_container_width=True, hide_index=True)

    st.markdown("### Handoff Rules")
    st.dataframe(package.handoff_rules, use_container_width=True, hide_index=True)

    st.markdown("### Example Conversations")
    for item in package.example_conversations:
        st.markdown(f"**{item['title']}**")
        st.markdown(f"- Customer: {item['customer']}")
        st.markdown(f"- Assistant: {item['assistant']}")

    st.markdown("### Test Cases")
    st.dataframe(package.test_cases, use_container_width=True, hide_index=True)

    st.markdown("### CX Agent Studio Start with AI 可用的流程描述")
    st.text_area("Start with AI Flow Description", value=package.start_with_ai_description, height=180)


def render_gap_table(items: list[GapItem]) -> None:
    st.dataframe([item.__dict__ for item in items], use_container_width=True, hide_index=True)


def render_question_table(items: list[MissingQuestion]) -> None:
    st.dataframe([item.__dict__ for item in items], use_container_width=True, hide_index=True)


def render_state_table(items: list[StateDefinition]) -> None:
    st.dataframe([item.__dict__ for item in items], use_container_width=True, hide_index=True)


def render_tool_table(items: list[ToolMapping]) -> None:
    st.dataframe([item.__dict__ for item in items], use_container_width=True, hide_index=True)


def render_decision_table(table: DecisionTable) -> None:
    st.markdown(f"#### {table.name}")
    st.caption(table.purpose)
    st.dataframe({"conditions": table.conditions, "actions": table.actions}, use_container_width=True)


if __name__ == "__main__":
    main()
