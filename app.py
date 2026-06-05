"""
app.py — Interface Streamlit pour LAMBDA OPTIMIZER.

Application web interactive pour l'étude de la réduction β
dans le lambda-calcul, avec visualisation, métriques d'optimisation
et exemples intégrés.

Lancer avec :
    streamlit run app.py
"""

import html
import os
import re
import shutil
import streamlit as st
import pandas as pd

from parser import parse_expression
from beta_reduction import full_reduction, analyze_expression
import utils
from utils import (
    compute_optimization_metrics,
    expression_tree_root,
    EXAMPLES,
)

format_optimization_summary = getattr(
    utils,
    "format_optimization_summary",
    lambda m: (
        f"Nombre d'applications avant : {m['before_apps']}\n"
        f"Nombre d'applications après : {m['after_apps']}"
    ),
)
expression_tree_compact = getattr(
    utils,
    "expression_tree_compact",
    lambda e: str(e),
)


def ensure_graphviz_available() -> bool:
    """Vérifie la disponibilité de Graphviz (compatibilité toutes versions de utils.py)."""
    checker = getattr(utils, "ensure_graphviz_available", None)
    if checker is not None:
        return checker()

    if shutil.which("dot"):
        return True

    for directory in (
        r"C:\Program Files\Graphviz\bin",
        r"C:\Program Files (x86)\Graphviz\bin",
        "/opt/homebrew/bin",
        "/usr/local/bin",
    ):
        dot_name = "dot.exe" if os.name == "nt" else "dot"
        dot_path = os.path.join(directory, dot_name)
        if os.path.isfile(dot_path):
            os.environ["PATH"] = directory + os.pathsep + os.environ.get("PATH", "")
            return True
    return False


def render_ast_svg(expr) -> str:
    """Génère un SVG responsive de l'AST (utilise utils.py si disponible)."""
    renderer = getattr(utils, "render_ast_svg", None)
    if renderer is not None:
        return renderer(expr)

    from graphviz import Source

    to_dot = getattr(utils, "expression_to_dot", None)
    if to_dot is None:
        raise ImportError(
            "utils.py est incomplet : fonctions render_ast_svg / expression_to_dot manquantes."
        )

    ensure_graphviz_available()
    dot = to_dot(expr)
    svg = Source(dot, engine="dot").pipe(format="svg").decode("utf-8")
    svg = re.sub(r'\swidth="[^"]+"', "", svg, count=1)
    svg = re.sub(r'\sheight="[^"]+"', "", svg, count=1)
    return svg.replace(
        "<svg ",
        '<svg style="max-width:100%;height:auto;display:block;margin:0 auto;" ',
        1,
    )


def _display_ast_graph(expr, fallback_label: str) -> None:
    """Affiche l'arbre syntaxique avec un rendu SVG compact et centré."""
    try:
        svg = render_ast_svg(expr)
        st.markdown(
            f'<div class="ast-graph-container">{svg}</div>'
            '<p class="ast-legend">App = Application · fn = fonction · arg = argument · g/d = gauche/droite</p>',
            unsafe_allow_html=True,
        )
    except Exception as e:
        st.warning(f"Impossible de générer le graphe ({fallback_label}) : {e}")
        st.code(expression_tree_root(expr), language="text")


# ═══════════════════════════════════════════════════════════════════════════════
#  CONFIGURATION DE LA PAGE
# ═══════════════════════════════════════════════════════════════════════════════

st.set_page_config(
    page_title="Lambda Optimizer — Réduction β",
    page_icon="λ",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ═══════════════════════════════════════════════════════════════════════════════
#  STYLES CSS PERSONNALISÉS
# ═══════════════════════════════════════════════════════════════════════════════

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap');

    :root {
        --primary: #4F46E5;
        --primary-light: #6366F1;
        --primary-soft: #EEF2FF;
        --secondary: #059669;
        --secondary-soft: #ECFDF5;
        --accent: #DC2626;
        --accent-soft: #FEF2F2;
        --alpha: #D97706;
        --alpha-soft: #FFFBEB;
        --bg-page: #F8FAFC;
        --bg-card: #FFFFFF;
        --text-primary: #1E293B;
        --text-secondary: #64748B;
        --border-color: #E2E8F0;
        --shadow-sm: 0 1px 3px rgba(15, 23, 42, 0.08);
        --gradient-1: linear-gradient(135deg, #4F46E5 0%, #059669 100%);
    }

    .stApp { background-color: var(--bg-page); }

    html, body, .stApp, .stMarkdown, .stTextInput label, .stButton button {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        color: var(--text-primary);
    }
    code, pre, .stCodeBlock, .step-expr, .analysis-item .a-value {
        font-family: 'JetBrains Mono', monospace !important;
    }

    [data-testid="stIconMaterial"],
    [data-testid="stIconMaterial"] span,
    .material-icons,
    .material-symbols-rounded {
        font-family: 'Material Symbols Rounded', 'Material Icons' !important;
        font-feature-settings: 'liga' !important;
        -webkit-font-feature-settings: 'liga' !important;
        letter-spacing: normal !important;
        text-transform: none !important;
    }

    [data-testid="stExpander"] summary { gap: 0.5rem; align-items: center; }
    [data-testid="stExpander"] summary p {
        font-family: 'Inter', sans-serif !important;
        margin: 0;
        color: var(--text-primary);
    }

    .main-title { text-align: center; padding: 0.25rem 0 0.75rem; }
    .main-title h1 {
        font-size: 2.2rem;
        font-weight: 800;
        background: var(--gradient-1);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        margin: 0;
        line-height: 1.2;
    }
    .main-title .subtitle {
        font-size: 0.95rem;
        color: var(--text-secondary);
        margin: 0.25rem 0 0;
    }

    .detected-banner {
        display: flex;
        align-items: center;
        gap: 0.6rem;
        padding: 0.75rem 1rem;
        margin: 0.75rem 0;
        background: var(--secondary-soft);
        border: 1px solid #A7F3D0;
        border-radius: 10px;
        color: #065F46;
        font-weight: 600;
        font-size: 0.9rem;
        box-shadow: var(--shadow-sm);
    }
    .detected-banner .icon {
        background: var(--secondary);
        color: white;
        width: 1.5rem;
        height: 1.5rem;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 0.85rem;
        flex-shrink: 0;
    }

    .badge {
        display: inline-block;
        padding: 0.15rem 0.6rem;
        border-radius: 999px;
        font-size: 0.72rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.4px;
    }
    .badge-purple { background: var(--primary-soft); color: var(--primary); }
    .badge-green  { background: var(--secondary-soft); color: var(--secondary); }
    .badge-red    { background: var(--accent-soft); color: var(--accent); }
    .badge-amber  { background: var(--alpha-soft); color: var(--alpha); }

    .step-container {
        position: relative;
        padding: 0.75rem 1rem 0.75rem 2.5rem;
        margin-bottom: 0.5rem;
        background: var(--bg-card);
        border: 1px solid var(--border-color);
        border-radius: 10px;
        box-shadow: var(--shadow-sm);
    }
    .step-container.step-alpha {
        border-left: 4px solid var(--alpha);
        background: var(--alpha-soft);
    }
    .step-container.step-initial { border-left: 4px solid var(--primary); }
    .step-container.step-final { border-left: 4px solid var(--secondary); }

    .step-dot {
        position: absolute;
        left: 0.85rem;
        top: 1rem;
        width: 0.65rem;
        height: 0.65rem;
        border-radius: 50%;
        background: var(--primary);
    }
    .step-alpha .step-dot { background: var(--alpha); }

    .step-number {
        font-size: 0.68rem;
        font-weight: 700;
        color: var(--primary);
        text-transform: uppercase;
        letter-spacing: 0.8px;
        margin-bottom: 0.15rem;
    }
    .step-alpha .step-number { color: var(--alpha); }

    .step-description {
        font-size: 0.82rem;
        color: var(--text-secondary);
        margin-bottom: 0.35rem;
    }
    .step-expr {
        font-size: 0.95rem;
        color: var(--text-primary);
        background: var(--primary-soft);
        border: 1px solid #C7D2FE;
        border-radius: 8px;
        padding: 0.4rem 0.65rem;
        display: inline-block;
    }

    .result-box {
        text-align: center;
        padding: 1.1rem;
        border-radius: 12px;
        background: var(--secondary-soft);
        border: 1px solid #A7F3D0;
        margin-top: 0.75rem;
        box-shadow: var(--shadow-sm);
    }
    .result-box .label {
        font-size: 0.75rem;
        font-weight: 600;
        color: var(--secondary);
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    .result-box .value {
        font-family: 'JetBrains Mono', monospace;
        font-size: 1.6rem;
        font-weight: 700;
        color: var(--text-primary);
        margin-top: 0.25rem;
    }

    .benefit-box {
        background: var(--bg-card);
        border: 1px solid var(--border-color);
        border-radius: 12px;
        padding: 1rem 1.25rem;
        margin-top: 0.75rem;
        box-shadow: var(--shadow-sm);
    }
    .benefit-box h4 {
        margin: 0 0 0.5rem;
        font-size: 0.85rem;
        color: var(--primary);
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    .benefit-box pre {
        margin: 0;
        font-family: 'JetBrains Mono', monospace !important;
        font-size: 0.85rem;
        color: var(--text-primary);
        white-space: pre-wrap;
        background: var(--bg-page);
        padding: 0.75rem;
        border-radius: 8px;
        border: 1px solid var(--border-color);
    }

    .metric-card {
        text-align: center;
        padding: 1rem;
        border-radius: 12px;
        background: var(--bg-card);
        border: 1px solid var(--border-color);
        box-shadow: var(--shadow-sm);
    }
    .metric-card .metric-label {
        font-size: 0.68rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        color: var(--text-secondary);
    }
    .metric-card .metric-value {
        font-family: 'JetBrains Mono', monospace;
        font-size: 1.5rem;
        font-weight: 700;
        margin-top: 0.2rem;
    }
    .metric-card .metric-delta { font-size: 0.78rem; font-weight: 600; margin-top: 0.15rem; }
    .delta-positive { color: var(--secondary); }
    .delta-neutral  { color: var(--text-secondary); }

    .sidebar-logo { text-align: center; padding: 0.25rem 0 0.75rem; }
    .sidebar-logo h2 {
        font-size: 1.1rem;
        font-weight: 800;
        color: var(--primary);
        margin: 0;
    }
    .sidebar-logo p {
        font-size: 0.75rem;
        color: var(--text-secondary);
        margin: 0.15rem 0 0;
    }

    section[data-testid="stSidebar"] {
        background-color: #FFFFFF;
        border-right: 1px solid var(--border-color);
    }
    section[data-testid="stSidebar"] div.stButton > button {
        font-family: 'JetBrains Mono', monospace !important;
        font-size: 0.74rem !important;
        padding: 0.3rem 0.45rem !important;
        min-height: 2rem !important;
        border: 1px solid var(--border-color) !important;
        background: var(--bg-page) !important;
        color: var(--text-primary) !important;
    }
    section[data-testid="stSidebar"] div.stButton > button:hover {
        border-color: var(--primary) !important;
        color: var(--primary) !important;
    }

    .analysis-item {
        display: flex;
        align-items: center;
        gap: 0.65rem;
        padding: 0.55rem 0.75rem;
        border-radius: 8px;
        background: var(--primary-soft);
        border-left: 3px solid var(--primary);
        margin-bottom: 0.35rem;
    }
    .analysis-item .a-label {
        font-size: 0.72rem;
        font-weight: 600;
        text-transform: uppercase;
        color: var(--text-secondary);
        min-width: 72px;
    }
    .analysis-item .a-value {
        font-size: 0.88rem;
        color: var(--text-primary);
    }

    .section-divider {
        border: none;
        height: 1px;
        background: var(--border-color);
        margin: 1.25rem 0;
    }

    .block-container { padding-top: 1.25rem !important; padding-bottom: 2rem !important; }
    footer { visibility: hidden; }

    .ast-graph-container {
        max-width: 780px;
        margin: 0.5rem auto;
        padding: 0.75rem;
        background: var(--bg-card);
        border: 1px solid var(--border-color);
        border-radius: 12px;
        overflow: auto;
        max-height: 420px;
        text-align: center;
        box-shadow: var(--shadow-sm);
    }
    .ast-graph-container svg { max-width: 100% !important; height: auto !important; }
    .ast-legend {
        text-align: center;
        font-size: 0.72rem;
        color: var(--text-secondary);
        margin-top: 0.35rem;
    }

    div[data-testid="stVerticalBlockBorderWrapper"] {
        border-color: var(--border-color) !important;
        background: var(--bg-card);
        border-radius: 12px;
        box-shadow: var(--shadow-sm);
    }
</style>
""", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
#  SIDEBAR
# ═══════════════════════════════════════════════════════════════════════════════

with st.sidebar:
    st.markdown("""
    <div class="sidebar-logo">
        <h2>λ LAMBDA OPTIMIZER</h2>
        <p>Réduction β interactive</p>
    </div>
    """, unsafe_allow_html=True)

    st.caption("📌 Exemples intégrés")

    for ex in EXAMPLES:
        if st.button(
            ex["expr"],
            key=f"ex_{ex['name']}",
            use_container_width=True,
            help=ex["description"],
        ):
            st.session_state["expr_input_field"] = ex["expr"]
            st.session_state["auto_reduce"] = True
            st.rerun()

    st.divider()

    with st.expander("À propos", expanded=False):
        st.markdown("""
        **LAMBDA OPTIMIZER** est un outil pédagogique pour
        l'étude de la **réduction β** dans le lambda-calcul.

        - Analyser des expressions lambda
        - Effectuer la réduction β pas-à-pas
        - Mesurer les gains d'optimisation
        - Visualiser l'arbre syntaxique
        """)

    with st.expander("La réduction β", expanded=False):
        st.markdown(r"""
        La **réduction β** est la règle fondamentale du lambda-calcul :

        $$(\lambda x.\, M)\, N \;\longrightarrow_\beta\; M[x := N]$$

        **Exemple :**
        $$(\lambda x.\, x + 1)(5) \;\longrightarrow\; 5 + 1 \;\longrightarrow\; 6$$
        """)

    with st.expander("Architecture du projet", expanded=False):
        st.code("""
Projet_ikram/
├── app.py
├── parser.py
├── beta_reduction.py
├── utils.py
├── requirements.txt
└── README.md
        """, language="text")

    with st.expander("Lien avec l'optimisation IA", expanded=False):
        st.markdown("""
        - **Compilation** : inlining ≈ réduction β
        - **Réseaux de neurones** : simplification de graphes
        - **Propagation de constantes** : évaluation partielle
        - **Élimination de code mort**
        """)


# ═══════════════════════════════════════════════════════════════════════════════
#  CONTENU PRINCIPAL
# ═══════════════════════════════════════════════════════════════════════════════

# ── Titre ──
st.markdown("""
<div class="main-title">
    <h1>λ LAMBDA OPTIMIZER</h1>
    <p class="subtitle">Étude de la réduction β et optimisation des modèles IA</p>
</div>
""", unsafe_allow_html=True)

# ── Zone de saisie ──
if "expr_input_field" not in st.session_state:
    st.session_state["expr_input_field"] = "(λx.x+1)(5)"

with st.container(border=True):
    col_input, col_btn = st.columns([6, 1], vertical_alignment="bottom")
    with col_input:
        user_input = st.text_input(
            "Expression lambda",
            placeholder="Ex : (λx.x+1)(5)",
            label_visibility="visible",
            key="expr_input_field",
        )
    with col_btn:
        reduce_clicked = st.button("Réduire", type="primary", use_container_width=True)

# Déterminer si on doit lancer la réduction
should_reduce = reduce_clicked or st.session_state.get("auto_reduce", False)
if "auto_reduce" in st.session_state:
    st.session_state["auto_reduce"] = False

# ═══════════════════════════════════════════════════════════════════════════════
#  RÉSULTATS
# ═══════════════════════════════════════════════════════════════════════════════

if should_reduce and user_input.strip():
    try:
        # ── 1. Parsing ──
        expr = parse_expression(user_input.strip())

        # ── 2. Analyse ──
        analysis = analyze_expression(expr)

        # ── 3. Réduction β complète ──
        steps = full_reduction(expr)
        final_expr = steps[-1]["expression"]
        num_reduction_steps = len(steps) - 1

        st.markdown(
            f'<div class="detected-banner">'
            f'<span class="icon">✓</span>'
            f'{html.escape(analysis.get("message", "Expression détectée"))} '
            f'— {html.escape(str(analysis.get("type_fr", analysis["type"])))}'
            f'</div>',
            unsafe_allow_html=True,
        )

        st.markdown('<hr class="section-divider">', unsafe_allow_html=True)

        # ════════════════════════════════════════════════════════════════════
        #  SECTION : ANALYSE DE L'EXPRESSION
        # ════════════════════════════════════════════════════════════════════
        with st.expander("Analyse de l'expression", expanded=True):
            st.markdown(f"""
            <div class="analysis-item">
                <span class="a-label">Type</span>
                <span class="badge badge-purple">{analysis.get('type_fr', analysis['type'])}</span>
            </div>
            """, unsafe_allow_html=True)

            if "variable" in analysis:
                st.markdown(f"""
                <div class="analysis-item">
                    <span class="a-label">Variable</span>
                    <span class="a-value">{html.escape(str(analysis['variable']))}</span>
                </div>
                """, unsafe_allow_html=True)

            if "corps" in analysis:
                st.markdown(f"""
                <div class="analysis-item">
                    <span class="a-label">Corps</span>
                    <span class="a-value">{html.escape(str(analysis['corps']))}</span>
                </div>
                """, unsafe_allow_html=True)

            if "argument" in analysis:
                st.markdown(f"""
                <div class="analysis-item">
                    <span class="a-label">Argument</span>
                    <span class="a-value">{html.escape(str(analysis['argument']))}</span>
                </div>
                """, unsafe_allow_html=True)

            if "fonction" in analysis and "variable" not in analysis:
                st.markdown(f"""
                <div class="analysis-item">
                    <span class="a-label">Fonction</span>
                    <span class="a-value">{html.escape(str(analysis['fonction']))}</span>
                </div>
                """, unsafe_allow_html=True)

            free_vars = analysis.get("variables_libres", set())
            if free_vars:
                st.markdown(f"""
                <div class="analysis-item">
                    <span class="a-label">Var. libres</span>
                    <span class="a-value">{', '.join(sorted(free_vars))}</span>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown("""
                <div class="analysis-item">
                    <span class="a-label">Var. libres</span>
                    <span class="a-value" style="color: var(--secondary);">Aucune (expression close)</span>
                </div>
                """, unsafe_allow_html=True)

        # ════════════════════════════════════════════════════════════════════
        #  SECTION : ÉTAPES DE RÉDUCTION β
        # ════════════════════════════════════════════════════════════════════
        st.markdown("### Réduction β — Étapes de calcul")

        if num_reduction_steps == 0:
            st.info("L'expression est déjà en forme normale. Aucune réduction nécessaire.")
        else:
            for s in steps:
                step_num = s["step"]
                kind = s.get("kind", "")
                extra_class = ""
                if kind == "alpha":
                    extra_class = " step-alpha"
                elif kind == "initial":
                    extra_class = " step-initial"

                label = f"ÉTAPE {step_num}"
                desc = html.escape(s["description"])
                expr_str = html.escape(s["expr_str"])

                st.markdown(f"""
                <div class="step-container{extra_class}">
                    <div class="step-dot"></div>
                    <div class="step-number">{label}</div>
                    <div class="step-description">{desc}</div>
                    <div class="step-expr">{expr_str}</div>
                </div>
                """, unsafe_allow_html=True)

            final_str = html.escape(steps[-1]["expr_str"])
            st.markdown(f"""
            <div class="result-box">
                <div class="label">Résultat final (forme normale)</div>
                <div class="value">{final_str}</div>
            </div>
            """, unsafe_allow_html=True)

        # ════════════════════════════════════════════════════════════════════
        #  SECTION : HISTORIQUE (TABLEAU)
        # ════════════════════════════════════════════════════════════════════
        st.markdown("")
        with st.expander("Historique des réductions", expanded=False):
            df = pd.DataFrame([
                {
                    "Étape": s["step"],
                    "Type": s.get("kind", ""),
                    "Description": s["description"],
                    "Expression": s["expr_str"],
                }
                for s in steps
            ])
            st.dataframe(
                df,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Étape": st.column_config.NumberColumn("Étape", width="small"),
                    "Description": st.column_config.TextColumn("Description", width="medium"),
                    "Expression": st.column_config.TextColumn("Expression", width="large"),
                },
            )

        # ════════════════════════════════════════════════════════════════════
        #  SECTION : OPTIMISATION (MÉTRIQUES)
        # ════════════════════════════════════════════════════════════════════
        st.markdown('<hr class="section-divider">', unsafe_allow_html=True)
        st.markdown("### Métriques d'optimisation")

        metrics = compute_optimization_metrics(expr, final_expr)
        benefit_text = html.escape(format_optimization_summary(metrics))

        st.markdown(f"""
        <div class="benefit-box">
            <h4>Bénéfice de l'optimisation</h4>
            <pre>{benefit_text}</pre>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("")
        col_before, col_arrow, col_after = st.columns([5, 1, 5])

        with col_before:
            st.markdown(
                '<span class="badge badge-red">AVANT RÉDUCTION</span>',
                unsafe_allow_html=True,
            )
            bc1, bc2, bc3, bc4 = st.columns(4)
            with bc1:
                st.metric("Taille AST", metrics["before_size"])
            with bc2:
                st.metric("Applications", metrics["before_apps"])
            with bc3:
                st.metric("Lambdas", metrics["before_lambdas"])
            with bc4:
                st.metric("Profondeur", metrics["before_depth"])

        with col_arrow:
            st.markdown(
                "<div style='text-align:center; font-size:2rem; padding-top:2rem; color: var(--text-secondary);'>→</div>",
                unsafe_allow_html=True,
            )

        with col_after:
            st.markdown(
                '<span class="badge badge-green">APRÈS RÉDUCTION</span>',
                unsafe_allow_html=True,
            )
            ac1, ac2, ac3, ac4 = st.columns(4)
            with ac1:
                st.metric("Taille AST", metrics["after_size"],
                          delta=f"-{metrics['size_reduction']}" if metrics["size_reduction"] > 0 else "0",
                          delta_color="normal" if metrics["size_reduction"] > 0 else "off")
            with ac2:
                st.metric("Applications", metrics["after_apps"],
                          delta=f"-{metrics['apps_reduction']}" if metrics["apps_reduction"] > 0 else "0",
                          delta_color="normal" if metrics["apps_reduction"] > 0 else "off")
            with ac3:
                st.metric("Lambdas", metrics["after_lambdas"],
                          delta=f"-{metrics['lambda_reduction']}" if metrics["lambda_reduction"] > 0 else "0",
                          delta_color="normal" if metrics["lambda_reduction"] > 0 else "off")
            with ac4:
                st.metric("Profondeur", metrics["after_depth"],
                          delta=f"-{metrics['depth_reduction']}" if metrics["depth_reduction"] > 0 else "0",
                          delta_color="normal" if metrics["depth_reduction"] > 0 else "off")

        # Gains en pourcentage
        st.markdown("")
        g1, g2, g3, g4 = st.columns(4)
        with g1:
            pct = metrics["size_pct"]
            color = "delta-positive" if pct > 0 else "delta-neutral"
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">Réduction taille</div>
                <div class="metric-value" style="color: var(--secondary);">{pct}%</div>
                <div class="metric-delta {color}">{"↓ " + str(metrics['size_reduction']) + " nœuds" if pct > 0 else "—"}</div>
            </div>
            """, unsafe_allow_html=True)
        with g2:
            pct = metrics["apps_pct"]
            color = "delta-positive" if pct > 0 else "delta-neutral"
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">Réduction applications</div>
                <div class="metric-value" style="color: var(--primary);">{pct}%</div>
                <div class="metric-delta {color}">{"↓ " + str(metrics['apps_reduction']) + " apps" if pct > 0 else "—"}</div>
            </div>
            """, unsafe_allow_html=True)
        with g3:
            pct = metrics["lambda_pct"]
            color = "delta-positive" if pct > 0 else "delta-neutral"
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">Réduction lambdas</div>
                <div class="metric-value" style="color: var(--accent);">{pct}%</div>
                <div class="metric-delta {color}">{"↓ " + str(metrics['lambda_reduction']) + " λ" if pct > 0 else "—"}</div>
            </div>
            """, unsafe_allow_html=True)
        with g4:
            pct = metrics["depth_pct"]
            color = "delta-positive" if pct > 0 else "delta-neutral"
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">Réduction profondeur</div>
                <div class="metric-value" style="color: #4ECDC4;">{pct}%</div>
                <div class="metric-delta {color}">{"↓ " + str(metrics['depth_reduction']) + " niveaux" if pct > 0 else "—"}</div>
            </div>
            """, unsafe_allow_html=True)

        # ════════════════════════════════════════════════════════════════════
        #  SECTION : VISUALISATION (ARBRE)
        # ════════════════════════════════════════════════════════════════════
        st.markdown('<hr class="section-divider">', unsafe_allow_html=True)
        st.markdown("### Visualisation de l'arbre syntaxique")

        graphviz_ok = ensure_graphviz_available()
        if not graphviz_ok:
            st.info(
                "Graphviz n'est pas installé. Les vues textuelles restent disponibles."
            )

        tab_before, tab_after, tab_compact, tab_text = st.tabs([
            "Avant réduction",
            "Après réduction",
            "Vue simplifiée",
            "Vue détaillée",
        ])

        with tab_before:
            if graphviz_ok:
                _display_ast_graph(expr, "avant réduction")
            st.markdown("**Arbre compact :**")
            st.code(expression_tree_compact(expr), language="text")

        with tab_after:
            if graphviz_ok:
                _display_ast_graph(final_expr, "après réduction")
            st.markdown("**Arbre compact :**")
            st.code(expression_tree_compact(final_expr), language="text")

        with tab_compact:
            c1, c2 = st.columns(2)
            with c1:
                st.markdown("**Avant :**")
                st.code(expression_tree_compact(expr), language="text")
            with c2:
                st.markdown("**Après :**")
                st.code(expression_tree_compact(final_expr), language="text")

        with tab_text:
            c1, c2 = st.columns(2)
            with c1:
                st.markdown("**Avant (AST complet) :**")
                st.code(expression_tree_root(expr), language="text")
            with c2:
                st.markdown("**Après (AST complet) :**")
                st.code(expression_tree_root(final_expr), language="text")

    except SyntaxError as e:
        st.error(f"❌ **Erreur de syntaxe** : {e}")
        st.info(
            "💡 **Syntaxe acceptée** :\n"
            "- `λx.corps` ou `\\x.corps` pour une abstraction\n"
            "- `(λx.corps)(argument)` pour une application\n"
            "- `+`, `-`, `*`, `/` pour l'arithmétique\n"
            "- Exemples : `(λx.x+1)(5)`, `(λx.λy.x+y)(3)(4)`"
        )
    except Exception as e:
        st.error(f"❌ **Erreur inattendue** : {e}")

elif should_reduce:
    st.warning("⚠️ Veuillez saisir une expression lambda.")


# ═══════════════════════════════════════════════════════════════════════════════
#  PIED DE PAGE
# ═══════════════════════════════════════════════════════════════════════════════

if not should_reduce or not user_input.strip():
    st.markdown("""
    <div style="text-align: center; padding: 2rem 0 1rem; color: var(--text-secondary); font-size: 0.8rem;">
        <strong>LAMBDA OPTIMIZER</strong> — Mini-projet universitaire<br>
        Étude de la réduction β et optimisation des modèles IA<br>
        <span style="opacity: 0.6;">Réalisé avec Python 3 & Streamlit</span>
    </div>
    """, unsafe_allow_html=True)
