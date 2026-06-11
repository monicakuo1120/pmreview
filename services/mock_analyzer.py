"""Mock analyzer for the PM Scenario Analyzer MVP.

The first MVP intentionally avoids LLM/API calls. This module uses deterministic
keyword heuristics to demonstrate the complete product flow:
input -> ScenarioSpec -> decomposition -> gap analysis -> questions -> maturity
-> CX Agent Studio package.
"""

from __future__ import annotations

from models import (
    AnalysisResult,
    BusinessRule,
    CXAgentStudioPackage,
    DecisionTable,
    GapItem,
    MissingQuestion,
    ScenarioSpec,
    StateDefinition,
    SubScenario,
    ToolMapping,
)


def analyze_requirement(
    *,
    free_text: str = "",
    structured_text: str = "",
    supplemental_notes: str = "",
    image_filenames: list[str] | None = None,
) -> AnalysisResult:
    """Run the deterministic mock analysis pipeline."""

    image_filenames = image_filenames or []
    combined_text = "\n".join([free_text, structured_text, supplemental_notes]).strip()
    input_modes = _detect_input_modes(free_text, structured_text, image_filenames)
    scenario_family = _classify_scenario_family(combined_text, image_filenames)
    spec = _normalize_to_scenario_spec(scenario_family, combined_text, input_modes, supplemental_notes, image_filenames)
    return _build_analysis_result(spec, scenario_family)


def _detect_input_modes(free_text: str, structured_text: str, image_filenames: list[str]) -> list[str]:
    modes: list[str] = []
    if free_text.strip():
        modes.append("Mode A：自由文字輸入")
    if image_filenames:
        modes.append("Mode B：Figma 截圖輸入")
    if structured_text.strip():
        modes.append("Mode C：結構化模板輸入")
    return modes or ["未提供輸入"]


def _classify_scenario_family(text: str, image_filenames: list[str]) -> str:
    lowered = text.lower()
    if any(keyword in text for keyword in ["掛失", "補發", "停卡", "卡片不見", "遺失", "遭竊"]):
        return "card_loss_reissue"
    if any(keyword in text for keyword in ["爭議", "不認得", "未授權", "重複扣款", "商品未收到"]):
        return "dispute"
    if any(keyword in text for keyword in ["消費明細", "交易明細", "交易紀錄", "pending", "商店名稱"]):
        return "transaction_inquiry"
    if image_filenames:
        return "figma_generic"
    if "payment" in lowered or "bill" in lowered:
        return "payment_generic"
    return "generic"


def _normalize_to_scenario_spec(
    scenario_family: str,
    text: str,
    input_modes: list[str],
    supplemental_notes: str,
    image_filenames: list[str],
) -> ScenarioSpec:
    if scenario_family == "card_loss_reissue":
        return _card_loss_spec(input_modes, supplemental_notes)
    if scenario_family == "transaction_inquiry":
        return _transaction_inquiry_spec(input_modes, supplemental_notes)
    if scenario_family == "dispute":
        return _dispute_spec(input_modes, supplemental_notes)
    return _generic_spec(text, input_modes, supplemental_notes, image_filenames)


def _card_loss_spec(input_modes: list[str], supplemental_notes: str) -> ScenarioSpec:
    sub_scenarios = [
        SubScenario("SS-001", "Intent Classification", "Decision", "判斷客戶是遺失、遭竊、損壞、疑似盜刷或單純補發。", "Input text / image", "High"),
        SubScenario("SS-002", "Identity Verification", "Authentication", "在停卡或補發前確認客戶身份。", "Input text / image", "High"),
        SubScenario("SS-003", "Card Selection", "Transaction prerequisite", "客戶選擇要掛失或補發的卡片。", "Input text / image", "High"),
        SubScenario("SS-004", "Loss Report", "Transaction", "客戶確認掛失並停用指定卡片。", "Input text / image", "High"),
        SubScenario("SS-005", "Fee Assessment", "Decision", "判斷補發是否收費與是否需要揭露。", "Inferred", "Medium"),
        SubScenario("SS-006", "Reissue Decision", "Transaction", "詢問客戶是否補發並建立補發申請。", "Input text / image", "High"),
        SubScenario("SS-007", "Fraud / Dispute Handoff", "Support / Hybrid", "若有可疑交易，轉爭議帳款或人工支援。", "Inferred", "Medium"),
    ]
    rules = [
        BusinessRule("BR-001", "Authentication", "停卡前需完成身份驗證。", "Partial", "驗證等級與失敗次數未定義。"),
        BusinessRule("BR-002", "Confirmation", "客戶需確認後才能停卡或補發。", "Partial", "停卡是否不可逆未定義。"),
        BusinessRule("BR-003", "Fee", "補發可能收費。", "Needs Review", "卡別、原因、寄送方式的費用規則未定義。"),
    ]
    return ScenarioSpec(
        feature_name="信用卡掛失補發",
        feature_type="Hybrid",
        goal="協助客戶回報信用卡遺失或遭竊，完成停卡，並視情況補發新卡。",
        main_flow=["辨識掛失意圖", "驗證身份", "選擇卡片", "確認停卡", "執行停卡", "詢問補發", "確認地址與費用", "送出補發申請"],
        sub_scenarios=sub_scenarios,
        business_rules=rules,
        decision_tables=[],
        state_model=[],
        exception_cases=["身份驗證失敗", "停卡 API 失敗", "補發 API 失敗", "客戶有可疑交易", "客戶中途離開"],
        journey_entry="客戶表示信用卡遺失、遭竊、損壞或需要補發。",
        journey_exit="停卡完成、補發完成、客戶取消、API 失敗轉人工或客戶中途離開。",
        tool_api_dependencies=["Customer Authentication Service", "Card List API", "Card Block API", "Card Reissue API", "Address Verification API", "Case Creation Tool"],
        assumptions=["補發前需要確認地址。", "遭竊或可疑交易需要轉人工或爭議流程。", "補發卡可能涉及費用揭露。"],
        missing_information=["補發費用規則", "停卡 finality rule", "API timeout / retry / failure 行為", "地址錯誤或海外地址處理", "可疑交易轉爭議條件"],
        input_modes=input_modes,
        supplemental_notes=supplemental_notes,
    )


def _transaction_inquiry_spec(input_modes: list[str], supplemental_notes: str) -> ScenarioSpec:
    sub_scenarios = [
        SubScenario("SS-001", "Intent Classification", "Inquiry / Routing", "判斷客戶查近期交易、單筆明細、商戶或不認得交易。", "Input text / image", "High"),
        SubScenario("SS-002", "Authentication / Authorization", "Authentication", "確認客戶是否可查看交易資料。", "Inferred", "Medium"),
        SubScenario("SS-003", "Transaction List Retrieval", "Inquiry / Tool", "取得近期交易列表。", "Input text / image", "High"),
        SubScenario("SS-004", "Transaction Selection", "Inquiry", "客戶選擇一筆交易。", "Input text / image", "High"),
        SubScenario("SS-005", "Transaction Detail Presentation", "Inquiry", "顯示商店名稱、金額、日期、交易狀態。", "Input text / image", "High"),
        SubScenario("SS-006", "Dispute Transition", "Hybrid", "客戶不認得交易時轉爭議帳款。", "Input text / image", "High"),
    ]
    return ScenarioSpec(
        feature_name="查詢消費明細",
        feature_type="Hybrid",
        goal="協助客戶查詢近期信用卡交易並查看單筆交易明細。",
        main_flow=["辨識交易查詢意圖", "驗證與授權", "查詢交易列表", "客戶選擇交易", "顯示交易明細", "提供爭議或離開等後續動作"],
        sub_scenarios=sub_scenarios,
        business_rules=[BusinessRule("BR-001", "Data Access", "客戶需通過身份驗證才能查看交易資料。", "Assumed", "授權範圍未定義。")],
        decision_tables=[],
        state_model=[],
        exception_cases=["無交易資料", "交易 API 失敗", "交易為 pending", "客戶不認得交易", "客戶選擇不明確"],
        journey_entry="客戶詢問近期交易、消費明細、商戶、金額或不認得交易。",
        journey_exit="交易明細顯示完成、轉入爭議、轉人工、客戶繼續查詢或離開。",
        tool_api_dependencies=["Customer Authentication Service", "Transaction History API", "Transaction Detail API", "Dispute Eligibility API"],
        assumptions=["交易資料屬敏感資料，需要驗證與授權。", "不認得交易可轉入爭議帳款流程。"],
        missing_information=["查詢範圍與筆數", "資料遮蔽規則", "主附卡授權規則", "API failure handling", "pending 交易說明規則"],
        input_modes=input_modes,
        supplemental_notes=supplemental_notes,
    )


def _dispute_spec(input_modes: list[str], supplemental_notes: str) -> ScenarioSpec:
    sub_scenarios = [
        SubScenario("SS-001", "Dispute Intent Classification", "Decision", "判斷客戶是否要申請爭議帳款。", "Input text / image", "High"),
        SubScenario("SS-002", "Transaction Selection", "Transaction prerequisite", "客戶選擇要爭議的交易。", "Input text / image", "High"),
        SubScenario("SS-003", "Dispute Eligibility Check", "Decision", "判斷交易是否可申請爭議。", "Input text / image", "High"),
        SubScenario("SS-004", "Reason Collection", "Transaction", "收集爭議原因與必要資訊。", "Input text / image", "High"),
        SubScenario("SS-005", "Disclosure and Confirmation", "Compliance", "建案前揭露與客戶確認。", "Inferred", "Medium"),
        SubScenario("SS-006", "Case Creation", "Tool Execution", "建立爭議案件並提供案件編號。", "Input text / image", "High"),
        SubScenario("SS-007", "Human Handoff", "Support", "複雜、高風險或 API 失敗時轉人工。", "Input text / image", "Medium"),
    ]
    return ScenarioSpec(
        feature_name="申請爭議帳款",
        feature_type="Hybrid",
        goal="協助客戶針對不認得或有問題的信用卡交易提出爭議並建立案件。",
        main_flow=["辨識爭議意圖", "驗證身份", "選擇交易", "檢查資格", "收集原因", "揭露與確認", "建立案件", "提供案件編號"],
        sub_scenarios=sub_scenarios,
        business_rules=[BusinessRule("BR-001", "Eligibility", "pending 或超過期限的交易可能不能申請。", "Partial", "完整資格條件未定義。")],
        decision_tables=[],
        state_model=[],
        exception_cases=["pending 交易", "超過申請期限", "重複申請", "建案 API 失敗", "需要人工客服"],
        journey_entry="客戶表示不認得交易，或從交易明細查詢轉入爭議申請。",
        journey_exit="案件建立成功、不可申請、客戶取消、轉人工或建案失敗。",
        tool_api_dependencies=["Customer Authentication Service", "Transaction Detail API", "Dispute Eligibility API", "Dispute Case Creation API", "Case Management System"],
        assumptions=["爭議申請需身份驗證。", "建案前需揭露與確認。", "部分情境需人工客服協助。"],
        missing_information=["申請期限", "爭議原因 taxonomy", "各原因必填資料", "揭露內容", "重複案件處理", "建案失敗 fallback"],
        input_modes=input_modes,
        supplemental_notes=supplemental_notes,
    )


def _generic_spec(text: str, input_modes: list[str], supplemental_notes: str, image_filenames: list[str]) -> ScenarioSpec:
    feature_name = "未命名功能"
    if image_filenames:
        feature_name = "Figma 流程截圖分析"
    if text.strip():
        first_line = next((line.strip("# ：:") for line in text.splitlines() if line.strip()), "未命名功能")
        feature_name = first_line[:40]
    return ScenarioSpec(
        feature_name=feature_name,
        feature_type="Hybrid",
        goal="根據 PM 輸入推估的對話式金融服務需求。",
        main_flow=["接收客戶需求", "辨識意圖", "執行主要流程", "提供結果或後續動作"],
        sub_scenarios=[
            SubScenario("SS-001", "Intent Classification", "Decision", "判斷客戶主要意圖。", "Inferred", "Low"),
            SubScenario("SS-002", "Main Flow Execution", "Hybrid", "執行 PM 描述的主要流程。", "Inferred", "Low"),
        ],
        business_rules=[],
        decision_tables=[],
        state_model=[],
        exception_cases=["輸入不完整", "流程分支不明確", "API 或工具未定義"],
        journey_entry="客戶提出需求。",
        journey_exit="需求完成、轉人工或離開。",
        tool_api_dependencies=[],
        assumptions=["此輸入不足以完整判斷 feature type。", "需要 PM 補充業務規則與流程分支。"],
        missing_information=["Feature name", "Feature type", "Business rules", "Decision tables", "State model", "Tool / API dependencies"],
        input_modes=input_modes,
        supplemental_notes=supplemental_notes,
    )


def _build_analysis_result(spec: ScenarioSpec, scenario_family: str) -> AnalysisResult:
    covered = _covered_areas(spec)
    missing = _missing_areas(spec, scenario_family)
    questions = _missing_questions(spec, scenario_family)
    missing_rules = _missing_business_rules(scenario_family)
    missing_tables = _missing_decision_tables(scenario_family)
    missing_states = _missing_states(scenario_family)
    missing_journeys = _missing_journeys(scenario_family)
    maturity = _maturity(scenario_family)
    cx_package = _cx_package(spec, scenario_family)
    mermaid = _mermaid(spec, scenario_family)
    next_actions = _next_actions(scenario_family)
    return AnalysisResult(
        scenario_spec=spec,
        covered_areas=covered,
        missing_areas=missing,
        missing_questions=questions,
        missing_business_rules=missing_rules,
        missing_decision_tables=missing_tables,
        missing_state_definitions=missing_states,
        missing_journey_entry_exit=missing_journeys,
        recommended_next_actions=next_actions,
        maturity_level=maturity[0],
        maturity_label=maturity[1],
        maturity_rationale=maturity[2],
        cx_package=cx_package,
        mermaid_flow=mermaid,
    )


def _covered_areas(spec: ScenarioSpec) -> list[GapItem]:
    return [
        GapItem("Feature Name", "Covered", spec.feature_name),
        GapItem("Feature Type", "Covered", spec.feature_type),
        GapItem("Goal", "Covered", spec.goal),
        GapItem("Main Flow", "Partially Covered", " → ".join(spec.main_flow), "需要補齊例外與狀態細節。"),
        GapItem("Sub-scenarios", "Partially Covered", f"已辨識 {len(spec.sub_scenarios)} 個子場景。", "需 PM 確認分解是否正確。"),
        GapItem("Tool / API Dependencies", "Partially Covered", ", ".join(spec.tool_api_dependencies) or "未提供", "需要補齊輸入、輸出、成功/失敗行為。"),
        GapItem("Assumptions", "Needs Confirmation", "; ".join(spec.assumptions), "推論項目需 PM 確認。"),
    ]


def _missing_areas(spec: ScenarioSpec, scenario_family: str) -> list[GapItem]:
    base = [
        GapItem("Decision Table Coverage", "Missing", "主要決策點尚未表格化。", "工程、測試與法遵難以一致審查。", "PM / Engineering", "High"),
        GapItem("State Model Coverage", "Missing", "狀態模型尚未完整定義。", "上下文保存、例外恢復與清理規則不明。", "PM / Engineering", "High"),
        GapItem("Tool/API Failure Behavior", "Missing", "API timeout、retry、partial response、failure fallback 未定義。", "客戶可能卡住，工程無法實作可靠流程。", "Engineering / PM", "High"),
        GapItem("Journey Entry / Exit", "Partially Covered", "進入與離開條件仍需補齊。", "可能造成流程開始或結束不一致。", "PM / UX", "Medium"),
    ]
    if scenario_family == "card_loss_reissue":
        base.insert(0, GapItem("Fee and Address Rules", "Missing", "補發費用、地址驗證與地址更新規則未定義。", "補發流程可能無法完成或產生合規風險。", "PM / Compliance", "High"))
    elif scenario_family == "transaction_inquiry":
        base.insert(0, GapItem("Data Access and Masking", "Missing", "交易資料授權、查詢範圍與遮蔽規則未定義。", "可能造成敏感資料外洩。", "Risk / Compliance", "Critical"))
    elif scenario_family == "dispute":
        base.insert(0, GapItem("Dispute Eligibility and Disclosure", "Missing", "爭議資格、期限、揭露與原因分流未定義。", "可能錯誤受理或違反作業/合規要求。", "PM / Compliance", "Critical"))
    else:
        base.insert(0, GapItem("Scenario Specific Rules", "Missing", "尚未提供足夠業務規則。", "需求不可直接交付。", "PM", "High"))
    return base


def _missing_questions(spec: ScenarioSpec, scenario_family: str) -> list[MissingQuestion]:
    if scenario_family == "card_loss_reissue":
        return [
            MissingQuestion("MQ-001", "Authentication", "停卡前與補發前分別需要哪種驗證等級？", "高風險操作需明確安全規則。", "Risk / PM", True),
            MissingQuestion("MQ-002", "Fee", "補發卡在不同卡別、掛失原因與寄送方式下是否收費？", "影響費用揭露與確認。", "PM / Compliance", True),
            MissingQuestion("MQ-003", "API Failure", "停卡 API 失敗時是否必須立即轉人工或建立案件？", "客戶卡片風險不可懸而未決。", "Engineering / Operations", True),
            MissingQuestion("MQ-004", "Journey", "客戶表示有可疑交易時，是先停卡、轉爭議，還是轉人工？", "影響風險流程銜接。", "PM / Risk", True),
        ]
    if scenario_family == "transaction_inquiry":
        return [
            MissingQuestion("MQ-001", "Authorization", "主卡、附卡、共同帳戶交易可見範圍為何？", "避免資料外洩。", "Risk / PM", True),
            MissingQuestion("MQ-002", "Data Range", "預設顯示幾筆交易？可查詢多久以前？", "影響 API 與 UX。", "PM / Engineering", True),
            MissingQuestion("MQ-003", "Masking", "交易明細哪些欄位需要遮蔽？", "涉及敏感資料合規。", "Compliance / Risk", True),
            MissingQuestion("MQ-004", "Hybrid Transition", "客戶不認得交易時是否直接進入爭議帳款流程？", "影響跨場景銜接。", "PM / Operations", True),
        ]
    if scenario_family == "dispute":
        return [
            MissingQuestion("MQ-001", "Eligibility", "posted、pending、reversed、refunded 交易是否都可申請爭議？", "決定是否可受理。", "PM / Operations", True),
            MissingQuestion("MQ-002", "Time Limit", "爭議申請期限是多少天？不同原因是否不同？", "影響資格判斷與合規。", "Compliance / PM", True),
            MissingQuestion("MQ-003", "Required Info", "每種爭議原因需收集哪些資料與附件？", "影響案件完整性。", "Operations / PM", True),
            MissingQuestion("MQ-004", "Disclosure", "建案前需要揭露哪些事項並取得確認？", "合規要求。", "Compliance / Legal", True),
        ]
    return [
        MissingQuestion("MQ-001", "Scenario", "此功能的主要客戶目標與完成條件是什麼？", "需要確認分析邊界。", "PM", True),
        MissingQuestion("MQ-002", "Tool/API", "此流程需要哪些 API 或後端系統？", "工程需要評估可行性。", "PM / Engineering", True),
    ]


def _missing_business_rules(scenario_family: str) -> list[GapItem]:
    common = [
        GapItem("Authentication Rule", "Missing", "驗證等級與 step-up 條件未完整定義。", "影響安全與合規。", "Risk / PM", "High"),
        GapItem("Handoff Rule", "Missing", "轉人工條件與上下文傳遞未定義。", "營運不可執行。", "Operations / PM", "High"),
    ]
    if scenario_family == "card_loss_reissue":
        return [GapItem("Replacement Fee Rule", "Missing", "補發費用與豁免條件未定義。", "影響揭露與客訴。", "PM / Compliance", "High"), *common]
    if scenario_family == "transaction_inquiry":
        return [GapItem("Data Masking Rule", "Missing", "交易欄位遮蔽規則未定義。", "敏感資料風險。", "Compliance / Risk", "Critical"), *common]
    if scenario_family == "dispute":
        return [GapItem("Eligibility Rule", "Missing", "爭議資格與申請期限未定義。", "核心受理條件不明。", "PM / Compliance", "Critical"), *common]
    return common


def _missing_decision_tables(scenario_family: str) -> list[GapItem]:
    names = {
        "card_loss_reissue": ["Intent Classification", "Card Blocking Eligibility", "Replacement Fee", "API Failure Handling"],
        "transaction_inquiry": ["Transaction Data Display", "No-Data Handling", "API Failure Handling", "Inquiry-to-Dispute"],
        "dispute": ["Dispute Eligibility", "Dispute Reason Routing", "Time Limit Handling", "Case Creation Failure"],
    }.get(scenario_family, ["Intent Routing", "API Failure Handling"])
    return [GapItem(name, "Missing", f"需要建立 {name} 決策表。", "決策邏輯需要可審查、可實作、可測試。", "PM / Engineering", "High") for name in names]


def _missing_states(scenario_family: str) -> list[GapItem]:
    states = {
        "card_loss_reissue": ["AUTH_REQUIRED", "CARD_SELECTED", "CARD_BLOCK_API_IN_PROGRESS", "CARD_BLOCKED", "REISSUE_REQUESTED", "HANDOFF_REQUIRED"],
        "transaction_inquiry": ["AUTH_REQUIRED", "TRANSACTION_LIST_RETRIEVING", "TRANSACTION_DETAIL_PRESENTED", "DISPUTE_TRANSITION_PENDING", "API_ERROR"],
        "dispute": ["TRANSACTION_SELECTED", "ELIGIBILITY_CHECK_IN_PROGRESS", "REASON_COLLECTION_REQUIRED", "DISCLOSURE_PENDING", "CASE_CREATION_IN_PROGRESS", "CASE_CREATED"],
    }.get(scenario_family, ["INTENT_CAPTURED", "API_ERROR", "JOURNEY_COMPLETED"])
    return [GapItem(state, "Missing", f"狀態 {state} 的 entry、stored data、events、transition 未完整定義。", "工程需要狀態模型支援上下文與例外恢復。", "PM / Engineering", "High") for state in states]


def _missing_journeys(scenario_family: str) -> list[GapItem]:
    return [
        GapItem("Journey Entry", "Partially Covered", "入口意圖、前置條件與 channel 未完整定義。", "可能導致流程觸發不一致。", "PM / UX", "Medium"),
        GapItem("Journey Exit", "Partially Covered", "成功、失敗、取消、中途離開、轉人工的 exit behavior 未完整定義。", "流程可能無法乾淨結束。", "PM / Engineering", "Medium"),
    ]


def _maturity(scenario_family: str) -> tuple[str, str, str]:
    if scenario_family == "dispute":
        return ("Level 2", "Scenario Coverage", "已有主流程概念與部分資格限制，但重要例外、揭露、決策表與狀態模型缺漏較多。")
    if scenario_family in {"card_loss_reissue", "transaction_inquiry"}:
        return ("Level 3", "Exception Coverage", "已有主流程、部分例外與工具/API，但 journey coverage、決策表與狀態定義仍需補齊。")
    return ("Level 1", "Happy Path Only", "目前輸入只能支持基本 happy path，仍需補充場景分支、例外、規則與狀態。")


def _next_actions(scenario_family: str) -> list[dict[str, str]]:
    return [
        {"priority": "1", "action": "確認缺漏 Business Rules", "purpose": "補齊可審查的業務邏輯", "owner": "PM / Compliance", "expected_output": "Business rule list"},
        {"priority": "2", "action": "建立缺漏 Decision Tables", "purpose": "讓複雜決策可實作與可測試", "owner": "PM / Engineering", "expected_output": "Decision tables"},
        {"priority": "3", "action": "補齊 State Model", "purpose": "支援上下文、錯誤恢復與狀態清理", "owner": "PM / Engineering", "expected_output": "State model"},
        {"priority": "4", "action": "確認 Tool / API success and failure behavior", "purpose": "降低流程中斷風險", "owner": "Engineering / Operations", "expected_output": "Tool/API mapping"},
    ]


def _cx_package(spec: ScenarioSpec, scenario_family: str) -> CXAgentStudioPackage:
    task_steps = [
        {
            "step_id": f"FS-{idx:03d}",
            "step_name": step,
            "purpose": "完成需求流程中的一步。",
            "actor": "Assistant / System",
            "input": "Customer context / prior state",
            "system_action": step,
            "customer_outcome": "Customer progresses to next step",
            "next_step": spec.main_flow[idx] if idx < len(spec.main_flow) else "Exit or follow-up",
            "requirement_gaps": "See PM Review Mode gaps",
        }
        for idx, step in enumerate(spec.main_flow, start=1)
    ]
    parameters = [
        {"parameter": "customer_id", "type": "String", "required": "Yes", "source": "Authentication", "used_in": "Tool calls", "notes": "Required for personalized financial service."},
        {"parameter": "selected_item_id", "type": "String", "required": "Conditional", "source": "Customer selection", "used_in": "Transaction/detail/case tools", "notes": "Represents selected card, transaction, or case target."},
    ]
    tool_mapping = [
        ToolMapping(tool, "Related scenario step", "Support the scenario with backend capability", "customer_id and context", "status / data / reference", "Continue next step", "Retry, fallback, or handoff")
        for tool in spec.tool_api_dependencies
    ]
    exception_handling = [{"exception": case, "trigger": case, "customer_impact": "Flow cannot continue normally", "recovery_path": "Retry, clarify, fallback, or handoff", "handoff_required": "Depends on severity"} for case in spec.exception_cases]
    handoff_rules = [
        {"trigger": "Authentication failure", "reason": "Customer cannot safely continue self-service", "context_to_pass": "Customer intent, current state, failure reason", "destination": "Human support"},
        {"trigger": "Tool/API hard failure", "reason": "System cannot complete action", "context_to_pass": "Tool name, request context, error", "destination": "Operations / support"},
    ]
    examples = [
        {"title": "Happy Path", "customer": "我想處理這個服務。", "assistant": "確認需求、檢查必要條件、執行流程並提供結果。"},
        {"title": "Exception Path", "customer": "系統好像找不到資料。", "assistant": "說明目前狀況，提供重試、替代路徑或轉人工。"},
    ]
    tests = [
        {"id": "TC-001", "scenario": "Happy path", "given": "Customer has required access", "when": "Customer completes all required steps", "then": "Flow completes successfully", "expected": "Confirmation or result is shown"},
        {"id": "TC-002", "scenario": "API failure", "given": "Backend API fails", "when": "System calls tool", "then": "Fallback or handoff is triggered", "expected": "Customer is not stranded"},
    ]
    description = (
        f"Build a requirement-level conversational flow for {spec.feature_name}. "
        f"The flow should support: {', '.join(step for step in spec.main_flow)}. "
        "Use the state model, decision tables, tool mappings, exception handling, and handoff rules in this package as design inputs. "
        "This description must be reviewed before implementation and is not a production prompt."
    )
    return CXAgentStudioPackage(
        feature_summary={
            "Feature Name": spec.feature_name,
            "Feature Type": spec.feature_type,
            "Goal": spec.goal,
            "Journey Entry": spec.journey_entry,
            "Journey Exit": spec.journey_exit,
        },
        task_flow_steps=task_steps,
        parameters=parameters,
        tool_mapping=tool_mapping,
        exception_handling=exception_handling,
        handoff_rules=handoff_rules,
        example_conversations=examples,
        test_cases=tests,
        start_with_ai_description=description,
    )


def _mermaid(spec: ScenarioSpec, scenario_family: str) -> str:
    labels = spec.main_flow[:8]
    if not labels:
        labels = ["Identify intent", "Execute flow", "Complete"]
    lines = ["flowchart TD"]
    lines.append(f"    A[Start: {spec.journey_entry}] --> B[{labels[0]}]")
    previous = "B"
    for idx, label in enumerate(labels[1:], start=1):
        node = chr(ord("B") + idx)
        lines.append(f"    {previous} --> {node}[{label}]")
        previous = node
    lines.append(f"    {previous} --> X{{Exception or missing info?}}")
    lines.append("    X -- Yes --> H[Retry, clarify, fallback, or handoff]")
    lines.append("    X -- No --> Z[Complete journey]")
    return "\n".join(lines)
