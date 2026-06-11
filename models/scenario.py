"""Typed structures used by the mock PM Scenario Analyzer pipeline."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

FeatureType = Literal["Inquiry", "Transaction", "Hybrid"]
CoverageStatus = Literal["Covered", "Partially Covered", "Missing", "Assumed", "Needs Confirmation"]
Priority = Literal["Critical", "High", "Medium", "Low"]


@dataclass
class SubScenario:
    """A decomposed scenario inside a larger feature."""

    id: str
    name: str
    scenario_type: str
    description: str
    source: str = "Mock Analyzer"
    confidence: str = "Medium"


@dataclass
class GapItem:
    """A covered or missing requirement area."""

    area: str
    status: CoverageStatus
    detail: str
    impact: str = ""
    owner: str = "PM"
    priority: Priority = "Medium"


@dataclass
class MissingQuestion:
    """A concrete question that should be answered by the PM or stakeholder."""

    id: str
    category: str
    question: str
    why_it_matters: str
    owner: str
    blocks_mvp: bool


@dataclass
class BusinessRule:
    """Requirement-level business rule representation."""

    id: str
    rule_type: str
    description: str
    status: str
    missing_detail: str = ""


@dataclass
class DecisionTable:
    """A simple condition/action decision table."""

    name: str
    purpose: str
    conditions: list[str]
    actions: list[str]
    missing_coverage: list[str] = field(default_factory=list)


@dataclass
class StateDefinition:
    """A state in the scenario state model."""

    name: str
    state_type: str
    entry_condition: str
    stored_data: str
    allowed_events: str
    transition: str
    gaps: str = ""


@dataclass
class ToolMapping:
    """Tool/API mapping for CX Agent Studio planning."""

    name: str
    step: str
    purpose: str
    required_input: str
    expected_output: str
    success_behavior: str
    failure_behavior: str


@dataclass
class ScenarioSpec:
    """Common normalized requirement model for all PM input modes."""

    feature_name: str
    feature_type: FeatureType
    goal: str
    main_flow: list[str]
    sub_scenarios: list[SubScenario]
    business_rules: list[BusinessRule]
    decision_tables: list[DecisionTable]
    state_model: list[StateDefinition]
    exception_cases: list[str]
    journey_entry: str
    journey_exit: str
    tool_api_dependencies: list[str]
    assumptions: list[str]
    missing_information: list[str]
    input_modes: list[str]
    supplemental_notes: str = ""


@dataclass
class CXAgentStudioPackage:
    """Requirement-level CX Agent Studio design package."""

    feature_summary: dict[str, str]
    task_flow_steps: list[dict[str, str]]
    parameters: list[dict[str, str]]
    tool_mapping: list[ToolMapping]
    exception_handling: list[dict[str, str]]
    handoff_rules: list[dict[str, str]]
    example_conversations: list[dict[str, str]]
    test_cases: list[dict[str, str]]
    start_with_ai_description: str


@dataclass
class AnalysisResult:
    """Full analyzer result rendered in the Streamlit UI."""

    scenario_spec: ScenarioSpec
    covered_areas: list[GapItem]
    missing_areas: list[GapItem]
    missing_questions: list[MissingQuestion]
    missing_business_rules: list[GapItem]
    missing_decision_tables: list[GapItem]
    missing_state_definitions: list[GapItem]
    missing_journey_entry_exit: list[GapItem]
    recommended_next_actions: list[dict[str, str]]
    maturity_level: str
    maturity_label: str
    maturity_rationale: str
    cx_package: CXAgentStudioPackage
    mermaid_flow: str
