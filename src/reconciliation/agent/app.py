import os

import pandas as pd
import streamlit as st

from reconciliation.engine import reconcile_booking
from reconciliation.agent.tools import ReconciliationTools
from reconciliation.agent.investigator import ExceptionInvestigator
from reconciliation.agent.orchestrator import ExceptionOrchestrator
from reconciliation.agent.llm_reasoner import LLMReasoner
from reconciliation.agent.trace import AgentTrace


# ---------------------------------------------------------
# PAGE CONFIG
# ---------------------------------------------------------

st.set_page_config(
    page_title="Air Reconciliation Agent",
    page_icon="💳",
    layout="wide",
)


# ---------------------------------------------------------
# DATA LOADING
# ---------------------------------------------------------

DATA_DIR = "data"


@st.cache_data
def load_data():

    bookings = pd.read_csv(
        os.path.join(DATA_DIR, "air_bookings.csv")
    )

    tickets = pd.read_csv(
        os.path.join(DATA_DIR, "air_tickets.csv")
    )

    invoices = pd.read_csv(
        os.path.join(DATA_DIR, "air_invoices.csv")
    )

    settlements = pd.read_csv(
        os.path.join(DATA_DIR, "air_settlements.csv")
    )

    refunds = pd.read_csv(
        os.path.join(DATA_DIR, "air_refunds.csv")
    )

    exchanges = pd.read_csv(
        os.path.join(DATA_DIR, "air_exchanges.csv")
    )

    return (
        bookings,
        tickets,
        invoices,
        settlements,
        refunds,
        exchanges,
    )


(
    bookings,
    tickets,
    invoices,
    settlements,
    refunds,
    exchanges,
) = load_data()


# ---------------------------------------------------------
# HEADER
# ---------------------------------------------------------

st.title("Air Payment Reconciliation Agent")

st.caption(
    "Deterministic reconciliation with agentic exception investigation"
)


# ---------------------------------------------------------
# SIDEBAR
# ---------------------------------------------------------

st.sidebar.header("Investigation")

booking_ids = sorted(
    bookings["booking_id"].dropna().unique()
)

selected_booking = st.sidebar.selectbox(
    "Select booking",
    booking_ids,
)


run_investigation = st.sidebar.button(
    "Run Investigation",
    type="primary",
)


# ---------------------------------------------------------
# SESSION STATE
# ---------------------------------------------------------

if "case" not in st.session_state:
    st.session_state.case = None

if "trace" not in st.session_state:
    st.session_state.trace = None

if "result" not in st.session_state:
    st.session_state.result = None


# ---------------------------------------------------------
# RUN DETERMINISTIC + AGENT INVESTIGATION
# ---------------------------------------------------------

if run_investigation:

    # Create a fresh trace for every investigation.
    trace = AgentTrace()

    # Run deterministic reconciliation.
    result = reconcile_booking(
        booking_id=selected_booking,
        bookings=bookings,
        tickets=tickets,
        invoices=invoices,
        settlements=settlements,
        refunds=refunds,
        exchanges=exchanges,
    )

    st.session_state.result = result
    st.session_state.trace = trace
    st.session_state.case = None

    # -----------------------------------------------------
    # Only investigate exceptions.
    # -----------------------------------------------------

    if result.status == "EXCEPTION":

        tools = ReconciliationTools(
            bookings=bookings,
            tickets=tickets,
            invoices=invoices,
            settlements=settlements,
            refunds=refunds,
            exchanges=exchanges,
            trace=trace,
        )

        investigator = ExceptionInvestigator(
            tools=tools,
        )

        reasoner = LLMReasoner(
            tools=tools,
            trace=trace,
        )

        orchestrator = ExceptionOrchestrator(
            investigator=investigator,
            reasoner=reasoner,
            trace=trace,
        )

        case = orchestrator.process(result)

        st.session_state.case = case


# ---------------------------------------------------------
# RESULTS
# ---------------------------------------------------------

result = st.session_state.result
case = st.session_state.case
trace = st.session_state.trace


if result is None:

    st.info(
        "Select a booking and click **Run Investigation**."
    )

    st.stop()


# ---------------------------------------------------------
# DETERMINISTIC RESULT
# ---------------------------------------------------------

st.header("Deterministic Reconciliation")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        "Booking",
        result.booking_id,
    )

with col2:
    st.metric(
        "Status",
        result.status.value
        if hasattr(result.status, "value")
        else result.status,
    )

with col3:
    st.metric(
        "Exception",
        result.exception_type
        or "None",
    )

with col4:
    variance = result.variance

    if variance is not None:
        variance_display = f"${float(variance):,.2f}"
    else:
        variance_display = "—"

    st.metric(
        "Variance",
        variance_display,
    )


# ---------------------------------------------------------
# NON-EXCEPTION CASES
# ---------------------------------------------------------

if result.status != "EXCEPTION":

    if str(result.status) == "RECONCILED":
        st.success(
            "No exception detected. No agent investigation required."
        )

    elif str(result.status) == "PENDING":
        st.warning(
            "The reconciliation is pending. "
            "No agent investigation was triggered."
        )

    st.stop()


# ---------------------------------------------------------
# AGENT INVESTIGATION
# ---------------------------------------------------------

if case is None:

    st.warning(
        "An exception was detected, but no investigation case was created."
    )

    st.stop()


st.header("Agent Investigation")


# ---------------------------------------------------------
# CONFIDENCE + CONTROL
# ---------------------------------------------------------

confidence_col1, confidence_col2, control_col1, control_col2 = (
    st.columns(4)
)

with confidence_col1:
    st.metric(
        "Finding Confidence",
        case.finding_confidence or "—",
    )

with confidence_col2:
    st.metric(
        "Root-Cause Confidence",
        case.root_cause_confidence or "—",
    )

with control_col1:
    st.metric(
        "Human Approval",
        "REQUIRED"
        if case.requires_human_approval
        else "NOT REQUIRED",
    )

with control_col2:
    st.metric(
        "Approval Status",
        case.approval_status,
    )


# ---------------------------------------------------------
# FINDINGS
# ---------------------------------------------------------

st.subheader("Findings")

if case.findings:

    for finding in case.findings:
        st.write(f"• {finding}")

else:

    st.info(
        "No findings were generated."
    )


# ---------------------------------------------------------
# HYPOTHESIS
# ---------------------------------------------------------

st.subheader("Hypothesis")

if case.hypothesis:

    st.info(case.hypothesis)

else:

    st.info(
        "No root-cause hypothesis was established."
    )


# ---------------------------------------------------------
# RECOMMENDATION
# ---------------------------------------------------------

st.subheader("Recommendation")

if case.recommendation:

    st.warning(case.recommendation)

else:

    st.info(
        "No recommendation was generated."
    )


# ---------------------------------------------------------
# HUMAN APPROVAL
# ---------------------------------------------------------

st.subheader("Human Approval")

approval_col1, approval_col2, approval_col3 = st.columns(3)


with approval_col1:

    if st.button(
        "Approve",
        key="approve_case",
    ):

        case.approve(
            approved_by="finance.reviewer",
            comment="Reviewed the investigation and supporting evidence.",
        )

        trace.add(
            "HUMAN",
            "Case approved by finance.reviewer",
        )

        st.success(
            "Case approved."
        )

        st.rerun()


with approval_col2:

    if st.button(
        "Reject",
        key="reject_case",
    ):

        case.reject(
            approved_by="finance.reviewer",
            comment="Investigation rejected by reviewer.",
        )

        trace.add(
            "HUMAN",
            "Case rejected by finance.reviewer",
        )

        st.error(
            "Case rejected."
        )

        st.rerun()


with approval_col3:

    if st.button(
        "Request More Evidence",
        key="more_evidence",
    ):

        case.request_more_evidence(
            requested_by="finance.reviewer",
            comment=(
                "Please provide additional authoritative "
                "records before approval."
            ),
        )

        trace.add(
            "HUMAN",
            "Additional evidence requested by finance.reviewer",
        )

        st.warning(
            "Additional evidence requested."
        )

        st.rerun()


# ---------------------------------------------------------
# AGENT OBSERVABILITY
# ---------------------------------------------------------

st.divider()

st.header("Agent Observability")


# ---------------------------------------------------------
# CALCULATE METRICS FROM TRACE
# ---------------------------------------------------------

events = trace.events if trace else []


llm_events = [
    event
    for event in events
    if event.event_type == "LLM"
]


tool_events = [
    event
    for event in events
    if event.event_type == "TOOL"
]


evidence_events = [
    event
    for event in events
    if event.event_type == "EVIDENCE"
]


metric_events = [
    event
    for event in events
    if event.event_type == "METRIC"
]


# Total investigation latency.
total_latency_ms = None

for event in reversed(metric_events):

    if event.message == "Investigation completed":
        total_latency_ms = event.duration_ms
        break


# Total LLM latency.
total_llm_latency_ms = sum(
    event.duration_ms or 0
    for event in llm_events
)


# Total tool latency.
total_tool_latency_ms = sum(
    event.duration_ms or 0
    for event in tool_events
)


# ---------------------------------------------------------
# TOP METRICS
# ---------------------------------------------------------

metric1, metric2, metric3, metric4 = st.columns(4)


with metric1:

    if total_latency_ms is not None:
        value = f"{total_latency_ms / 1000:.2f} sec"
    else:
        value = "—"

    st.metric(
        "Total Latency",
        value,
    )


with metric2:

    st.metric(
        "LLM Calls",
        len(llm_events),
    )


with metric3:

    st.metric(
        "Tool Calls",
        len(tool_events),
    )


with metric4:

    st.metric(
        "Evidence Items",
        len(evidence_events),
    )


# ---------------------------------------------------------
# LLM PERFORMANCE
# ---------------------------------------------------------

st.subheader("LLM Performance")

llm_col1, llm_col2 = st.columns(2)


with llm_col1:

    st.metric(
        "Total LLM Time",
        f"{total_llm_latency_ms / 1000:.2f} sec",
    )


with llm_col2:

    if len(llm_events) > 0:

        avg_llm_latency = (
            total_llm_latency_ms
            / len(llm_events)
        )

        st.metric(
            "Average LLM Call",
            f"{avg_llm_latency / 1000:.2f} sec",
        )

    else:

        st.metric(
            "Average LLM Call",
            "—",
        )


if llm_events:

    llm_rows = []

    for index, event in enumerate(
        llm_events,
        start=1,
    ):

        llm_rows.append(
            {
                "Call": index,
                "Description": event.message,
                "Latency (ms)": round(
                    event.duration_ms or 0,
                    1,
                ),
            }
        )

    st.dataframe(
        pd.DataFrame(llm_rows),
        use_container_width=True,
        hide_index=True,
    )


# ---------------------------------------------------------
# TOOL PERFORMANCE
# ---------------------------------------------------------

st.subheader("Tool Performance")

tool_col1, tool_col2 = st.columns(2)


with tool_col1:

    st.metric(
        "Total Tool Time",
        f"{total_tool_latency_ms:.2f} ms",
    )


with tool_col2:

    if tool_events:

        avg_tool_latency = (
            total_tool_latency_ms
            / len(tool_events)
        )

        st.metric(
            "Average Tool Call",
            f"{avg_tool_latency:.2f} ms",
        )

    else:

        st.metric(
            "Average Tool Call",
            "—",
        )


if tool_events:

    tool_rows = []

    for event in tool_events:

        tool_rows.append(
            {
                "Tool": event.message,
                "Latency (ms)": round(
                    event.duration_ms or 0,
                    2,
                ),
            }
        )

    st.dataframe(
        pd.DataFrame(tool_rows),
        use_container_width=True,
        hide_index=True,
    )


# ---------------------------------------------------------
# CONFIDENCE / CONTROL SUMMARY
# ---------------------------------------------------------

st.subheader("Agent Decision Controls")

control_data = {
    "Finding Confidence": (
        case.finding_confidence or "—"
    ),
    "Root-Cause Confidence": (
        case.root_cause_confidence or "—"
    ),
    "Human Approval Required": (
        "YES"
        if case.requires_human_approval
        else "NO"
    ),
    "Approval Status": case.approval_status,
}

control_df = pd.DataFrame(
    [
        {
            "Metric": key,
            "Value": value,
        }
        for key, value in control_data.items()
    ]
)

st.dataframe(
    control_df,
    use_container_width=True,
    hide_index=True,
)


# ---------------------------------------------------------
# FULL TRACE
# ---------------------------------------------------------

st.subheader("Agent Trace")

if events:

    trace_rows = []

    for event in events:

        trace_rows.append(
            {
                "Step": event.step,
                "Type": event.event_type,
                "Message": event.message,
                "Timestamp": event.timestamp,
                "Duration (ms)": (
                    round(event.duration_ms, 2)
                    if event.duration_ms is not None
                    else None
                ),
            }
        )

    trace_df = pd.DataFrame(trace_rows)

    st.dataframe(
        trace_df,
        use_container_width=True,
        hide_index=True,
    )

else:

    st.info(
        "No trace events available."
    )


# ---------------------------------------------------------
# INVESTIGATION STEPS
# ---------------------------------------------------------

with st.expander(
    "Investigation Steps",
    expanded=False,
):

    if case.investigation_steps:

        for step in case.investigation_steps:
            st.write(f"• {step}")

    else:

        st.info(
            "No investigation steps recorded."
        )


# ---------------------------------------------------------
# EVIDENCE
# ---------------------------------------------------------

with st.expander(
    "Evidence",
    expanded=False,
):

    if case.evidence:

        for item in case.evidence:
            st.write(f"• {item}")

    else:

        st.info(
            "No evidence recorded."
        )