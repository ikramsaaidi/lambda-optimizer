"""
utils.py — Fonctions utilitaires pour LAMBDA OPTIMIZER.

Ce module fournit :
  • Métriques d'expression (taille, nombre d'applications, profondeur).
  • Comparaison avant/après réduction (gains d'optimisation).
  • Génération de graphe Graphviz pour la visualisation de l'AST.
  • Exemples prédéfinis.
"""

from __future__ import annotations
import os
import shutil
from typing import Dict, Any, List, Tuple

from parser import (
    Expression, Variable, Number, Lambda, Application, BinOp
)


# ═══════════════════════════════════════════════════════════════════════════════
#  GRAPHVIZ — DISPONIBILITÉ
# ═══════════════════════════════════════════════════════════════════════════════

def ensure_graphviz_available() -> bool:
    """
    Vérifie si l'exécutable Graphviz `dot` est disponible.
    Tente d'ajouter des chemins d'installation courants au PATH si nécessaire.
    """
    if shutil.which("dot"):
        return True

    candidates = [
        r"C:\Program Files\Graphviz\bin",
        r"C:\Program Files (x86)\Graphviz\bin",
        "/opt/homebrew/bin",
        "/usr/local/bin",
    ]
    for directory in candidates:
        dot_name = "dot.exe" if os.name == "nt" else "dot"
        dot_path = os.path.join(directory, dot_name)
        if os.path.isfile(dot_path):
            os.environ["PATH"] = directory + os.pathsep + os.environ.get("PATH", "")
            return True
    return False


# ═══════════════════════════════════════════════════════════════════════════════
#  MÉTRIQUES D'EXPRESSION
# ═══════════════════════════════════════════════════════════════════════════════

def expression_size(expr: Expression) -> int:
    """
    Calcule la taille d'une expression (nombre total de nœuds dans l'AST).

    Chaque nœud (Variable, Number, Lambda, Application, BinOp) compte pour 1.
    """
    if isinstance(expr, (Variable, Number)):
        return 1
    if isinstance(expr, Lambda):
        return 1 + expression_size(expr.body)
    if isinstance(expr, Application):
        return 1 + expression_size(expr.func) + expression_size(expr.arg)
    if isinstance(expr, BinOp):
        return 1 + expression_size(expr.left) + expression_size(expr.right)
    return 1


def count_applications(expr: Expression) -> int:
    """Compte le nombre de nœuds Application dans l'expression."""
    if isinstance(expr, (Variable, Number)):
        return 0
    if isinstance(expr, Lambda):
        return count_applications(expr.body)
    if isinstance(expr, Application):
        return 1 + count_applications(expr.func) + count_applications(expr.arg)
    if isinstance(expr, BinOp):
        return count_applications(expr.left) + count_applications(expr.right)
    return 0


def count_lambdas(expr: Expression) -> int:
    """Compte le nombre d'abstractions λ dans l'expression."""
    if isinstance(expr, (Variable, Number)):
        return 0
    if isinstance(expr, Lambda):
        return 1 + count_lambdas(expr.body)
    if isinstance(expr, Application):
        return count_lambdas(expr.func) + count_lambdas(expr.arg)
    if isinstance(expr, BinOp):
        return count_lambdas(expr.left) + count_lambdas(expr.right)
    return 0


def expression_depth(expr: Expression) -> int:
    """Calcule la profondeur maximale de l'AST."""
    if isinstance(expr, (Variable, Number)):
        return 1
    if isinstance(expr, Lambda):
        return 1 + expression_depth(expr.body)
    if isinstance(expr, Application):
        return 1 + max(expression_depth(expr.func), expression_depth(expr.arg))
    if isinstance(expr, BinOp):
        return 1 + max(expression_depth(expr.left), expression_depth(expr.right))
    return 1


# ═══════════════════════════════════════════════════════════════════════════════
#  COMPARAISON AVANT / APRÈS RÉDUCTION
# ═══════════════════════════════════════════════════════════════════════════════

def compute_optimization_metrics(
    before: Expression, after: Expression
) -> Dict[str, Any]:
    """
    Compare les métriques d'une expression avant et après réduction.

    Returns:
        Dictionnaire contenant :
          - before_size, after_size, size_reduction, size_pct
          - before_apps, after_apps, apps_reduction, apps_pct
          - before_lambdas, after_lambdas, lambda_reduction, lambda_pct
          - before_depth, after_depth, depth_reduction, depth_pct
    """
    b_size = expression_size(before)
    a_size = expression_size(after)
    b_apps = count_applications(before)
    a_apps = count_applications(after)
    b_lambdas = count_lambdas(before)
    a_lambdas = count_lambdas(after)
    b_depth = expression_depth(before)
    a_depth = expression_depth(after)

    def pct(before_val: int, after_val: int) -> float:
        if before_val == 0:
            return 0.0
        return round((1 - after_val / before_val) * 100, 1)

    return {
        "before_size": b_size,
        "after_size": a_size,
        "size_reduction": b_size - a_size,
        "size_pct": pct(b_size, a_size),

        "before_apps": b_apps,
        "after_apps": a_apps,
        "apps_reduction": b_apps - a_apps,
        "apps_pct": pct(b_apps, a_apps),

        "before_lambdas": b_lambdas,
        "after_lambdas": a_lambdas,
        "lambda_reduction": b_lambdas - a_lambdas,
        "lambda_pct": pct(b_lambdas, a_lambdas),

        "before_depth": b_depth,
        "after_depth": a_depth,
        "depth_reduction": b_depth - a_depth,
        "depth_pct": pct(b_depth, a_depth),
    }


# ═══════════════════════════════════════════════════════════════════════════════
#  VISUALISATION — GRAPHVIZ DOT
# ═══════════════════════════════════════════════════════════════════════════════

def _dot_layout_for(expr: Expression) -> Dict[str, Any]:
    """Paramètres de mise en page adaptés à la taille de l'arbre."""
    n = expression_size(expr)
    if n <= 6:
        return {
            "node_fs": 10, "edge_fs": 7, "ranksep": 0.45, "nodesep": 0.35,
            "node_w": 0.72, "node_h": 0.30, "leaf_w": 0.42, "leaf_h": 0.26,
        }
    if n <= 14:
        return {
            "node_fs": 9, "edge_fs": 6, "ranksep": 0.38, "nodesep": 0.28,
            "node_w": 0.66, "node_h": 0.28, "leaf_w": 0.38, "leaf_h": 0.24,
        }
    return {
        "node_fs": 8, "edge_fs": 5, "ranksep": 0.32, "nodesep": 0.22,
        "node_w": 0.60, "node_h": 0.26, "leaf_w": 0.34, "leaf_h": 0.22,
    }


def _build_dot_nodes(
    expr: Expression,
    counter: List[int],
    lines: List[str],
    layout: Dict[str, Any],
    parent_id: str = None,
    edge_label: str = None,
) -> str:
    """Construction récursive des nœuds et arêtes du graphe DOT."""
    node_id = f"n{counter[0]}"
    counter[0] += 1

    if isinstance(expr, Variable):
        label = expr.name
        color = "#6C63FF"
        shape = "ellipse"
        width, height = layout["leaf_w"], layout["leaf_h"]
    elif isinstance(expr, Number):
        label = str(expr.value)
        color = "#00C896"
        shape = "ellipse"
        width, height = layout["leaf_w"], layout["leaf_h"]
    elif isinstance(expr, Lambda):
        label = f"λ{expr.param}"
        color = "#FF6B6B"
        shape = "box"
        width, height = layout["node_w"], layout["node_h"]
    elif isinstance(expr, Application):
        label = "App"
        color = "#4ECDC4"
        shape = "box"
        width, height = layout["node_w"], layout["node_h"]
    elif isinstance(expr, BinOp):
        label = expr.op
        color = "#FFD93D"
        shape = "diamond"
        width, height = layout["leaf_w"], layout["leaf_h"]
    else:
        label = "?"
        color = "#CCCCCC"
        shape = "box"
        width, height = layout["node_w"], layout["node_h"]

    fontcolor = "#333333" if isinstance(expr, BinOp) else "white"

    lines.append(
        f'  {node_id} [label="{label}", shape="{shape}", style="filled,rounded", '
        f'fillcolor="{color}", fontcolor="{fontcolor}", fontname="Arial", '
        f'fontsize="{layout["node_fs"]}", width="{width}", height="{height}", '
        f'fixedsize=true, margin="0.04,0.02"];'
    )

    if parent_id:
        edge_attrs = (
            f'color="#777777", penwidth="0.7", arrowsize="0.45", '
            f'fontsize="{layout["edge_fs"]}", fontcolor="#999999", '
            f'labeldistance="1.0", labelangle="0"'
        )
        if edge_label:
            edge_attrs += f', label="{edge_label}"'
        lines.append(f"  {parent_id} -> {node_id} [{edge_attrs}];")

    if isinstance(expr, Lambda):
        _build_dot_nodes(expr.body, counter, lines, layout, node_id, "corps")
    elif isinstance(expr, Application):
        _build_dot_nodes(expr.func, counter, lines, layout, node_id, "fn")
        _build_dot_nodes(expr.arg, counter, lines, layout, node_id, "arg")
    elif isinstance(expr, BinOp):
        _build_dot_nodes(expr.left, counter, lines, layout, node_id, "g")
        _build_dot_nodes(expr.right, counter, lines, layout, node_id, "d")

    return node_id


def expression_to_dot(expr: Expression) -> str:
    """Convertit une expression en code DOT compact pour la visualisation."""
    layout = _dot_layout_for(expr)
    lines: List[str] = [
        "digraph AST {",
        "  graph [",
        '    rankdir="TB"',
        '    bgcolor="transparent"',
        f'    nodesep="{layout["nodesep"]}"',
        f'    ranksep="{layout["ranksep"]}"',
        '    splines="true"',
        '    overlap="false"',
        '    ordering="out"',
        "  ];",
        "  node [penwidth=0];",
        '  edge [penwidth=0.7, arrowsize=0.45];',
    ]
    _build_dot_nodes(expr, [0], lines, layout)
    lines.append("}")
    return "\n".join(lines)


def render_ast_svg(expr: Expression) -> str:
    """
    Génère un SVG responsive de l'arbre syntaxique via Graphviz.

    Returns:
        Chaîne SVG prête à être intégrée dans Streamlit (HTML).
    """
    import re
    from graphviz import Source

    ensure_graphviz_available()
    dot = expression_to_dot(expr)
    svg_bytes = Source(dot, engine="dot").pipe(format="svg")
    svg = svg_bytes.decode("utf-8")

    # Retirer width/height fixes pour permettre le redimensionnement CSS
    svg = re.sub(r'\swidth="[^"]+"', "", svg, count=1)
    svg = re.sub(r'\sheight="[^"]+"', "", svg, count=1)
    svg = svg.replace(
        "<svg ",
        '<svg style="max-width:100%;height:auto;display:block;margin:0 auto;" ',
        1,
    )
    return svg


# ═══════════════════════════════════════════════════════════════════════════════
#  REPRÉSENTATION TEXTUELLE DE L'ARBRE
# ═══════════════════════════════════════════════════════════════════════════════

def expression_tree_text(expr: Expression, prefix: str = "", is_last: bool = True) -> str:
    """
    Génère une représentation textuelle de l'arbre (style 'tree' Unix).

    Utile pour l'affichage en mode texte brut.

    Exemple de sortie :
        Application
        ├── λx
        │   └── +
        │       ├── x
        │       └── 1
        └── 5
    """
    connector = "└── " if is_last else "├── "
    child_prefix = prefix + ("    " if is_last else "│   ")

    if isinstance(expr, Variable):
        return f"{prefix}{connector}{expr.name}\n"
    if isinstance(expr, Number):
        return f"{prefix}{connector}{expr.value}\n"

    result = ""

    if isinstance(expr, Lambda):
        result += f"{prefix}{connector}λ{expr.param}\n"
        result += expression_tree_text(expr.body, child_prefix, True)

    elif isinstance(expr, Application):
        result += f"{prefix}{connector}Application\n"
        result += expression_tree_text(expr.func, child_prefix, False)
        result += expression_tree_text(expr.arg, child_prefix, True)

    elif isinstance(expr, BinOp):
        result += f"{prefix}{connector}{expr.op}\n"
        result += expression_tree_text(expr.left, child_prefix, False)
        result += expression_tree_text(expr.right, child_prefix, True)

    return result


def expression_tree_root(expr: Expression) -> str:
    """Version qui affiche aussi la racine sans connecteur."""
    if isinstance(expr, Variable):
        return f"{expr.name}\n"
    if isinstance(expr, Number):
        return f"{expr.value}\n"

    result = ""
    if isinstance(expr, Lambda):
        result = f"λ{expr.param}\n"
        result += expression_tree_text(expr.body, "", True)
    elif isinstance(expr, Application):
        result = "Application\n"
        result += expression_tree_text(expr.func, "", False)
        result += expression_tree_text(expr.arg, "", True)
    elif isinstance(expr, BinOp):
        result = f"{expr.op}\n"
        result += expression_tree_text(expr.left, "", False)
        result += expression_tree_text(expr.right, "", True)

    return result


def expression_tree_compact(expr: Expression) -> str:
    """
    Arbre syntaxique simplifié (vue pédagogique).

    Exemple :
        Application
        ├── λx.x+1
        └── 5
    """
    if isinstance(expr, Application):
        return f"Application\n├── {expr.func}\n└── {expr.arg}"
    if isinstance(expr, Lambda):
        return str(expr)
    if isinstance(expr, BinOp):
        return f"{expr.op}\n├── {expr.left}\n└── {expr.right}"
    return str(expr)


def format_optimization_summary(metrics: Dict[str, Any]) -> str:
    """Résumé textuel du bénéfice d'optimisation (format rapport)."""
    lines = [
        f"Nombre d'applications avant : {metrics['before_apps']}",
        f"Nombre d'applications après : {metrics['after_apps']}",
        f"Taille AST avant : {metrics['before_size']} nœuds",
        f"Taille AST après : {metrics['after_size']} nœuds",
    ]
    if metrics["apps_reduction"] > 0:
        lines.append(
            f"Bénéfice : {metrics['apps_reduction']} application(s) éliminée(s) "
            f"({metrics['apps_pct']}% de réduction)"
        )
    else:
        lines.append("Bénéfice : expression déjà optimale (aucune application restante).")
    return "\n".join(lines)


# ═══════════════════════════════════════════════════════════════════════════════
#  EXEMPLES PRÉDÉFINIS
# ═══════════════════════════════════════════════════════════════════════════════

EXAMPLES: List[Dict[str, str]] = [
    {
        "name": "Identité",
        "expr": "(λx.x)(5)",
        "description": "Fonction identité appliquée à 5 → retourne 5.",
    },
    {
        "name": "Successeur",
        "expr": "(λx.x+1)(5)",
        "description": "Fonction successeur appliquée à 5 → retourne 6.",
    },
    {
        "name": "Successeur (4)",
        "expr": "(λx.x+1)(4)",
        "description": "Successeur appliqué à 4 → retourne 5.",
    },
    {
        "name": "Optimisation",
        "expr": "(λx.x)(λy.y)(5)",
        "description": "Double application éliminée → 5 (2 apps → 0).",
    },
    {
        "name": "Addition curryfiée",
        "expr": "(λx.λy.x+y)(3)(4)",
        "description": "Addition de deux arguments par application successive → 7.",
    },
    {
        "name": "Carré",
        "expr": "(λx.x*x)(4)",
        "description": "Fonction carré appliquée à 4 → retourne 16.",
    },
    {
        "name": "Double application",
        "expr": "(λf.λx.f(f(x)))(λx.x+1)(0)",
        "description": "Applique deux fois le successeur à 0 → retourne 2.",
    },
    {
        "name": "Multiplication curryfiée",
        "expr": "(λx.λy.x*y)(6)(7)",
        "description": "Multiplication curryfiée de 6 et 7 → retourne 42.",
    },
    {
        "name": "Composition",
        "expr": "(λf.λg.λx.f(g(x)))(λx.x*2)(λx.x+3)(5)",
        "description": "Composition : d'abord +3, puis ×2 → (5+3)×2 = 16.",
    },
    {
        "name": "Expression arithmétique",
        "expr": "(λx.x*x+2*x+1)(3)",
        "description": "Polynôme x²+2x+1 évalué en 3 → retourne 16.",
    },
]

__all__ = [
    "ensure_graphviz_available",
    "expression_size",
    "count_applications",
    "count_lambdas",
    "expression_depth",
    "compute_optimization_metrics",
    "expression_to_dot",
    "render_ast_svg",
    "expression_tree_root",
    "expression_tree_compact",
    "expression_tree_text",
    "format_optimization_summary",
    "EXAMPLES",
]
