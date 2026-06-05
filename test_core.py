"""
test_core.py — Tests de validation (parseur + réduction β).
"""

import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from parser import parse_expression
from beta_reduction import full_reduction, analyze_expression
from utils import count_applications, compute_optimization_metrics

def test_case(name, expr_str, expected_result):
    """Teste un cas et affiche le résultat."""
    print(f"\n{'='*60}")
    print(f"Test : {name}")
    print(f"Expression : {expr_str}")

    try:
        expr = parse_expression(expr_str)
        analysis = analyze_expression(expr)
        print(f"Détection : {analysis.get('message', 'OK')}")

        steps = full_reduction(expr)
        for s in steps:
            kind = s.get("kind", "")
            tag = f" [{kind}]" if kind and kind != "initial" else ""
            print(f"  Étape {s['step']} : {s['expr_str']}  ({s['description']}){tag}")

        result = steps[-1]['expr_str']
        status = "✅ OK" if result == expected_result else f"❌ ERREUR (attendu: {expected_result})"
        print(f"Résultat : {result}  {status}")
        return result == expected_result
    except Exception as e:
        print(f"❌ EXCEPTION : {e}")
        return False


def test_optimization(name, expr_str, before_apps, after_apps):
    """Teste les métriques d'optimisation."""
    print(f"\n{'='*60}")
    print(f"Test optimisation : {name}")
    expr = parse_expression(expr_str)
    steps = full_reduction(expr)
    metrics = compute_optimization_metrics(expr, steps[-1]["expression"])
    ok = metrics["before_apps"] == before_apps and metrics["after_apps"] == after_apps
    print(f"  Applications avant : {metrics['before_apps']} (attendu {before_apps})")
    print(f"  Applications après : {metrics['after_apps']} (attendu {after_apps})")
    print(f"  {'✅ OK' if ok else '❌ ERREUR'}")
    return ok


if __name__ == "__main__":
    results = []

    # Phase 7 — tests obligatoires
    results.append(test_case("Test 1 — Identité", "(λx.x)(5)", "5"))
    results.append(test_case("Test 2 — Successeur", "(λx.x+1)(4)", "5"))
    results.append(test_case("Test 3 — Addition curryfiée", "(λx.λy.x+y)(3)(4)", "7"))

    # Tests supplémentaires
    results.append(test_case("Successeur (5)", "(λx.x+1)(5)", "6"))
    results.append(test_case("Carré", "(λx.x*x)(4)", "16"))
    results.append(test_case("Double application", "(λf.λx.f(f(x)))(λx.x+1)(0)", "2"))
    results.append(test_case("Multiplication curryfiée", "(λx.λy.x*y)(6)(7)", "42"))
    results.append(test_case("Composition", "(λf.λg.λx.f(g(x)))(λx.x*2)(λx.x+3)(5)", "16"))
    results.append(test_case("Polynôme", "(λx.x*x+2*x+1)(3)", "16"))

    # Phase 4 — optimisation
    results.append(test_optimization("Double app éliminée", "(λx.x)(λy.y)(5)", 2, 0))

    print(f"\n{'='*60}")
    passed = sum(results)
    total = len(results)
    print(f"\nRésultat : {passed}/{total} tests réussis")
    if passed == total:
        print("🎉 Tous les tests passent !")
    else:
        print("⚠️ Certains tests ont échoué.")
