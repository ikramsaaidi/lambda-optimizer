"""
beta_reduction.py — Moteur de réduction β pour le lambda-calcul.

Ce module implémente :
  • La collecte des variables libres.
  • La génération de noms frais (α-conversion).
  • La substitution  M[x := N]  avec gestion de la capture de variables.
  • La réduction β pas-à-pas (stratégie gauche-droite, outermost-first pour
    les redex, évaluation arithmétique quand les deux opérandes sont des nombres).
  • La réduction complète avec enregistrement de chaque étape.
"""

from __future__ import annotations
from typing import Optional, Tuple, List, Dict, Any, Set

from parser import (
    Expression, Variable, Number, Lambda, Application, BinOp
)


# ═══════════════════════════════════════════════════════════════════════════════
#  VARIABLES LIBRES
# ═══════════════════════════════════════════════════════════════════════════════

def get_free_variables(expr: Expression) -> Set[str]:
    """
    Retourne l'ensemble des variables libres d'une expression.

    Une variable est libre si elle n'est pas liée par un λ englobant.
    Exemples :
      • FV(x) = {x}
      • FV(λx.x+y) = {y}
      • FV(5) = ∅
    """
    if isinstance(expr, Variable):
        return {expr.name}
    if isinstance(expr, Number):
        return set()
    if isinstance(expr, Lambda):
        return get_free_variables(expr.body) - {expr.param}
    if isinstance(expr, Application):
        return get_free_variables(expr.func) | get_free_variables(expr.arg)
    if isinstance(expr, BinOp):
        return get_free_variables(expr.left) | get_free_variables(expr.right)
    return set()


# ═══════════════════════════════════════════════════════════════════════════════
#  GÉNÉRATION DE NOMS FRAIS  (α-conversion)
# ═══════════════════════════════════════════════════════════════════════════════

def fresh_variable(base_name: str, used: Set[str]) -> str:
    """
    Génère un nom de variable frais qui n'est pas dans `used`.

    Stratégie : base_name → base_name1 → base_name2 → …
    """
    candidate = base_name
    counter = 1
    while candidate in used:
        candidate = f"{base_name}{counter}"
        counter += 1
    return candidate


# ═══════════════════════════════════════════════════════════════════════════════
#  SUBSTITUTION :  expr[var_name := replacement]
# ═══════════════════════════════════════════════════════════════════════════════

def substitute(
    expr: Expression,
    var_name: str,
    replacement: Expression,
    alpha_events: Optional[List[str]] = None,
) -> Expression:
    """
    Effectue la substitution  expr[var_name := replacement].

    Si alpha_events est fourni, enregistre chaque α-conversion effectuée.
    """
    # ── Variable ──
    if isinstance(expr, Variable):
        return replacement if expr.name == var_name else expr

    # ── Nombre ──
    if isinstance(expr, Number):
        return expr

    # ── Lambda ──
    if isinstance(expr, Lambda):
        if expr.param == var_name:
            return expr

        free_in_replacement = get_free_variables(replacement)
        if expr.param in free_in_replacement:
            all_vars = (
                free_in_replacement
                | get_free_variables(expr.body)
                | {var_name}
            )
            new_param = fresh_variable(expr.param, all_vars)
            if alpha_events is not None:
                alpha_events.append(
                    f"α-conversion : λ{expr.param} renommé en λ{new_param} "
                    f"(éviter la capture de variable)"
                )
            new_body = substitute(expr.body, expr.param, Variable(new_param), alpha_events)
            return Lambda(new_param, substitute(new_body, var_name, replacement, alpha_events))

        return Lambda(expr.param, substitute(expr.body, var_name, replacement, alpha_events))

    # ── Application ──
    if isinstance(expr, Application):
        return Application(
            substitute(expr.func, var_name, replacement, alpha_events),
            substitute(expr.arg, var_name, replacement, alpha_events),
        )

    # ── Opération binaire ──
    if isinstance(expr, BinOp):
        return BinOp(
            expr.op,
            substitute(expr.left, var_name, replacement, alpha_events),
            substitute(expr.right, var_name, replacement, alpha_events),
        )

    return expr


# ═══════════════════════════════════════════════════════════════════════════════
#  ÉVALUATION ARITHMÉTIQUE
# ═══════════════════════════════════════════════════════════════════════════════

def eval_arithmetic(op: str, a: int, b: int) -> Optional[int]:
    """
    Évalue une opération arithmétique entre deux entiers.

    Retourne None si l'opération est impossible (ex: division par zéro).
    """
    if op == '+':
        return a + b
    if op == '-':
        return a - b
    if op == '*':
        return a * b
    if op == '/':
        if b == 0:
            return None  # Division par zéro
        return a // b    # Division entière
    return None


# ═══════════════════════════════════════════════════════════════════════════════
#  RÉDUCTION β  —  UN PAS
# ═══════════════════════════════════════════════════════════════════════════════

def beta_reduce_step(
    expr: Expression,
) -> Optional[Tuple[Expression, str, List[str]]]:
    """
    Effectue un seul pas de réduction β (ou d'évaluation arithmétique).

    Returns:
        (nouvelle_expression, description, liste_α_conversions) ou None si forme normale.
    """
    # ── Application d'un lambda (redex β) ──
    if isinstance(expr, Application):
        if isinstance(expr.func, Lambda):
            alpha_events: List[str] = []
            result = substitute(
                expr.func.body, expr.func.param, expr.arg, alpha_events
            )
            description = f"Substitution de {expr.func.param} par {expr.arg}"
            return result, description, alpha_events

        func_result = beta_reduce_step(expr.func)
        if func_result:
            new_func, desc, alphas = func_result
            return Application(new_func, expr.arg), desc, alphas

        arg_result = beta_reduce_step(expr.arg)
        if arg_result:
            new_arg, desc, alphas = arg_result
            return Application(expr.func, new_arg), desc, alphas

    # ── Opération binaire ──
    elif isinstance(expr, BinOp):
        if isinstance(expr.left, Number) and isinstance(expr.right, Number):
            result = eval_arithmetic(expr.op, expr.left.value, expr.right.value)
            if result is not None:
                desc = f"{expr.left.value} {expr.op} {expr.right.value} = {result}"
                return Number(result), desc, []

        left_result = beta_reduce_step(expr.left)
        if left_result:
            new_left, desc, alphas = left_result
            return BinOp(expr.op, new_left, expr.right), desc, alphas

        right_result = beta_reduce_step(expr.right)
        if right_result:
            new_right, desc, alphas = right_result
            return BinOp(expr.op, expr.left, new_right), desc, alphas

    # ── Lambda (réduire le corps) ──
    elif isinstance(expr, Lambda):
        body_result = beta_reduce_step(expr.body)
        if body_result:
            new_body, desc, alphas = body_result
            return Lambda(expr.param, new_body), desc, alphas

    return None


# ═══════════════════════════════════════════════════════════════════════════════
#  RÉDUCTION COMPLÈTE  —  TOUTES LES ÉTAPES
# ═══════════════════════════════════════════════════════════════════════════════

def full_reduction(expr: Expression, max_steps: int = 100) -> List[Dict[str, Any]]:
    """
    Effectue la réduction β complète et enregistre chaque étape.

    Numérotation à partir de 1 (Étape 1 = expression initiale).
    Les α-conversions apparaissent comme étapes distinctes avant la substitution β.
    """
    steps: List[Dict[str, Any]] = []
    step_num = 1

    steps.append({
        "step": step_num,
        "expression": expr,
        "expr_str": str(expr),
        "description": "Expression initiale",
        "kind": "initial",
    })

    current = expr
    for _ in range(max_steps):
        before = current
        result = beta_reduce_step(current)
        if result is None:
            break

        new_expr, description, alpha_events = result

        for alpha_desc in alpha_events:
            step_num += 1
            steps.append({
                "step": step_num,
                "expression": before,
                "expr_str": str(before),
                "description": alpha_desc,
                "kind": "alpha",
            })

        step_num += 1
        kind = "arithmetic" if " = " in description and isinstance(new_expr, Number) else "beta"
        steps.append({
            "step": step_num,
            "expression": new_expr,
            "expr_str": str(new_expr),
            "description": description,
            "kind": kind,
        })
        current = new_expr

    return steps


# ═══════════════════════════════════════════════════════════════════════════════
#  ANALYSE D'UNE EXPRESSION
# ═══════════════════════════════════════════════════════════════════════════════

def analyze_expression(expr: Expression) -> Dict[str, Any]:
    """
    Analyse une expression et retourne ses composants principaux.

    Pour une application (λx.M)(N) :
      • variable : x
      • corps : M
      • argument : N

    Pour d'autres formes, retourne les composants disponibles.
    """
    info: Dict[str, Any] = {
        "type": type(expr).__name__,
        "expression": str(expr),
        "detected": True,
        "message": "Expression détectée",
    }

    if isinstance(expr, Application):
        info["type_fr"] = "Application"
        info["fonction"] = str(expr.func)
        info["argument"] = str(expr.arg)

        if isinstance(expr.func, Lambda):
            info["variable"] = expr.func.param
            info["corps"] = str(expr.func.body)
            info["est_redex"] = True
        else:
            info["est_redex"] = False

    elif isinstance(expr, Lambda):
        info["type_fr"] = "Abstraction Lambda"
        info["variable"] = expr.param
        info["corps"] = str(expr.body)

    elif isinstance(expr, Variable):
        info["type_fr"] = "Variable"
        info["nom"] = expr.name

    elif isinstance(expr, Number):
        info["type_fr"] = "Nombre"
        info["valeur"] = expr.value

    elif isinstance(expr, BinOp):
        info["type_fr"] = "Opération Binaire"
        info["opérateur"] = expr.op
        info["gauche"] = str(expr.left)
        info["droite"] = str(expr.right)

    info["variables_libres"] = get_free_variables(expr)

    return info
