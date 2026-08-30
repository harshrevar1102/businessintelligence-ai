"""Reusable UI and visualization helpers for the BusinessIntelligence.ai dashboard.
Provides modern, high-contrast components, color palettes, and Plotly chart renderers.
"""

import textwrap
import plotly.graph_objects as go
import streamlit as st


def confidence_label(score):
    if score >= 0.75:
        return "High"
    if score >= 0.5:
        return "Medium"
    if score >= 0.25:
        return "Low"
    return "Insufficient"


def confidence_color(label):
    return {
        "High": "#15803d",        # Crisp Emerald Green
        "Medium": "#2563eb",      # Crisp Royal Blue (no orange)
        "Low": "#475569",         # High-contrast Slate (no orange)
        "Insufficient": "#94a3b8",# Crisp Muted Slate
    }.get(label, "#475569")


def render_kpi_card(col, kpi):
    arrow = "▲" if kpi.movement_pct >= 0 else "▼"
    
    # Invert delta coloring for wait time (higher wait time is negative)
    if kpi.name == "Wait Time":
        is_good = kpi.movement_pct <= 0
    else:
        is_good = kpi.movement_pct >= 0

    delta_color_cls = "up" if is_good else "down"
    
    if kpi.unit == "INR":
        if kpi.current_value < 1000:
            value_str = f"₹{kpi.current_value:,.1f}"
        else:
            value_str = f"₹{kpi.current_value / 1_000_000:,.1f}M"
    elif kpi.unit == "count":
        value_str = f"{kpi.current_value / 1000:,.0f}K"
    else:
        value_str = f"{kpi.current_value:,.1f} {kpi.unit}"

    card_html = textwrap.dedent(f"""
<div class="bi-card">
<div class="bi-label">{kpi.name}</div>
<div class="bi-value">{value_str}</div>
<div class="bi-delta {delta_color_cls}">{arrow} {abs(kpi.movement_pct):.1f}% vs baseline</div>
<div class="bi-meta">Materiality: <b>{kpi.materiality_label}</b> • p = {kpi.p_value:.3f}</div>
</div>
""").strip()
    col.markdown(card_html, unsafe_allow_html=True)


def render_trend_chart(daily_df):
    fig = go.Figure()
    
    # Revenue Actual Line
    fig.add_trace(go.Scatter(
        x=daily_df["date"],
        y=daily_df["revenue"],
        name="Actual Revenue",
        mode="lines+markers",
        line=dict(color="#2563eb", width=2.5),
        marker=dict(size=4, color="#1d4ed8"),
        hovertemplate="<b>Date:</b> %{x}<br><b>Revenue:</b> ₹%{y:,.0f}<extra></extra>"
    ))
    
    # Baseline Line (Slate dashed line - no orange)
    fig.add_trace(go.Scatter(
        x=daily_df["date"],
        y=daily_df["baseline"],
        name="Baseline",
        mode="lines",
        line=dict(color="#64748b", width=2, dash="dash"),
        hovertemplate="<b>Baseline:</b> ₹%{y:,.0f}<extra></extra>"
    ))
    
    # Highlight final observation anomaly
    if len(daily_df) > 0:
        last_row = daily_df.iloc[-1]
        fig.add_trace(go.Scatter(
            x=[last_row["date"]],
            y=[last_row["revenue"]],
            name="Current Observation",
            mode="markers+text",
            marker=dict(color="#dc2626", size=10, line=dict(color="#ffffff", width=2)),
            text=[f" ₹{last_row['revenue']/1_000_000:.1f}M"],
            textposition="bottom right",
            textfont=dict(color="#991b1b", size=11, family="Inter, -apple-system, sans-serif"),
            hovertemplate="<b>Current:</b> ₹%{y:,.0f}<extra></extra>"
        ))

    fig.update_layout(
        height=260,
        margin=dict(l=10, r=20, t=25, b=10),
        plot_bgcolor="#ffffff",
        paper_bgcolor="#ffffff",
        font=dict(family="Inter, -apple-system, sans-serif", size=12, color="#0f172a"),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            font=dict(color="#334155", size=12)
        ),
        xaxis=dict(
            showgrid=False,
            linecolor="#cbd5e1",
            tickfont=dict(color="#475569", size=11)
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor="#f1f5f9",
            linecolor="#cbd5e1",
            tickfont=dict(color="#475569", size=11),
            title=dict(text="Revenue (INR)", font=dict(color="#334155", size=12))
        ),
        hoverlabel=dict(
            bgcolor="#0f172a",
            font_size=12,
            font_family="Inter, -apple-system, sans-serif",
            font_color="#ffffff"
        )
    )
    return fig


def render_driver_bars(drivers):
    names = [d.name for d in drivers]
    values = [d.contribution_pct for d in drivers]
    
    # Modern rich palette (Blue, Purple, Emerald, Sky, Slate) - NO orange
    palette = ["#2563eb", "#7c3aed", "#10b981", "#0284c7", "#64748b", "#475569"]
    bar_colors = [palette[i % len(palette)] for i in range(len(drivers))]

    fig = go.Figure(go.Bar(
        x=values,
        y=names,
        orientation="h",
        marker=dict(
            color=bar_colors,
            line=dict(width=0),
            cornerradius=4
        ),
        text=[f"<b>{v:.1f}%</b>" for v in values],
        textposition="outside",
        textfont=dict(color="#0f172a", size=12, family="Inter, -apple-system, sans-serif"),
        hovertemplate="<b>%{y}:</b> %{x:.1f}% contribution<extra></extra>"
    ))
    
    fig.update_layout(
        height=260,
        margin=dict(l=10, r=45, t=15, b=10),
        plot_bgcolor="#ffffff",
        paper_bgcolor="#ffffff",
        font=dict(family="Inter, -apple-system, sans-serif", size=12, color="#0f172a"),
        xaxis=dict(
            title=dict(text="Approximate contribution (%)", font=dict(color="#334155", size=11)),
            showgrid=True,
            gridcolor="#f1f5f9",
            linecolor="#cbd5e1",
            tickfont=dict(color="#475569", size=11)
        ),
        yaxis=dict(
            autorange="reversed",
            tickfont=dict(color="#0f172a", size=12, family="Inter, -apple-system, sans-serif"),
            linecolor="#cbd5e1"
        ),
        hoverlabel=dict(
            bgcolor="#0f172a",
            font_size=12,
            font_color="#ffffff"
        )
    )
    return fig


def section_header(title, subtitle=None, badge_text=None, badge_type="critical"):
    badge_html = f'<span class="bi-badge bi-badge-{badge_type}">{badge_text}</span>' if badge_text else ""
    sub_html = f'<div class="bi-section-sub">{subtitle}</div>' if subtitle else ""
    
    header_html = textwrap.dedent(f"""
<div class="bi-section-header">
<div class="bi-section-title-wrap">
<h2 class="bi-section-title">{title}</h2>
{badge_html}
</div>
{sub_html}
</div>
""").strip()
    st.markdown(header_html, unsafe_allow_html=True)


def render_alert_banner(title, message, meta=None, alert_type="critical"):
    meta_html = f'<div class="bi-alert-meta">{meta}</div>' if meta else ""
    alert_html = textwrap.dedent(f"""
<div class="bi-alert bi-alert-{alert_type}">
<div class="bi-alert-icon">⚠️</div>
<div class="bi-alert-content">
<div class="bi-alert-title">{title}</div>
<div class="bi-alert-body">{message}</div>
{meta_html}
</div>
</div>
""").strip()
    st.markdown(alert_html, unsafe_allow_html=True)


def render_insight_card(number, title, body):
    return textwrap.dedent(f"""
<div class="bi-insight-card">
<div class="bi-insight-header">
<span class="bi-insight-num">{number}</span>
<span class="bi-insight-title">{title}</span>
</div>
<div class="bi-insight-body">{body}</div>
</div>
""").strip()


def render_action_box(driver, lever, action, owner, monitoring_kpis, monitoring_days, impact=None):
    impact_html = f'<div class="bi-action-impact">Expected impact: <b>₹{impact:+,.0f}</b></div>' if impact is not None else ""
    return textwrap.dedent(f"""
<div class="bi-action-box">
<div class="bi-action-flow">
<div class="bi-action-step"><span class="step-label">Driver</span><span class="step-val">{driver}</span></div>
<div class="bi-action-arrow">→</div>
<div class="bi-action-step"><span class="step-label">Lever</span><span class="step-val">{lever}</span></div>
<div class="bi-action-arrow">→</div>
<div class="bi-action-step"><span class="step-label">Action</span><span class="step-val">{action}</span></div>
<div class="bi-action-arrow">→</div>
<div class="bi-action-step"><span class="step-label">Owner</span><span class="step-val">{owner}</span></div>
</div>
<div class="bi-action-footer">
<div>Monitoring: <b>{', '.join(monitoring_kpis)}</b> for <b>{monitoring_days} days</b></div>
{impact_html}
</div>
</div>
""").strip()
