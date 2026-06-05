<div align="center">

# λ LAMBDA OPTIMIZER

**Moteur interactif de réduction β avec visualisation et optimisation**

*Mini-projet universitaire — Étude de la réduction β et optimisation des modèles IA*

![Python](https://img.shields.io/badge/Python-3.8+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-1.24+-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)
![Licence MIT](https://img.shields.io/badge/Licence-MIT-22C55E?style=for-the-badge)
![Status](https://img.shields.io/badge/Status-Terminé-6366F1?style=for-the-badge)

</div>

---

## 📌 Aperçu

**LAMBDA OPTIMIZER** est une application web interactive qui permet de :

- ✏️ **Saisir** des expressions du lambda-calcul (syntaxe `λ`, `\` ou `lambda`)
- 🔍 **Analyser** automatiquement les composants (variable, corps, argument)
- ⚡ **Effectuer la réduction β** pas-à-pas avec description de chaque étape
- 📊 **Mesurer les gains d'optimisation** avant/après réduction (taille AST, applications, profondeur)
- 🌳 **Visualiser l'arbre syntaxique** (AST) via Graphviz
- 📋 **Exporter** l'historique complet des réductions

> 💡 **Exemple rapide :** `(λx.λy.x+y)(3)(4)` est réduit en 4 étapes jusqu'à `7`, avec 2 applications éliminées.

---

## 📸 Captures d'écran

### Interface principale
> ![Interface principale](screenshots/main.png)

### Étapes de réduction β pas-à-pas
> *![Étapes de réduction](screenshots/steps.png)*

### Métriques d'optimisation avant / après
> ![Métriques](screenshots/metrics.png)
### Arbre syntaxique (AST) Graphviz
> *![Arbre syntaxique](screenshots/ast.png)*

---

## 🏗️ Architecture du projet

```
lambda-optimizer/
├── app.py                  ← Interface utilisateur Streamlit (point d'entrée)
├── parser.py               ← Tokenizer & parseur récursif descendant
├── beta_reduction.py       ← Moteur de réduction β (substitution + α-conversion)
├── utils.py                ← Métriques, visualisation Graphviz, exemples
├── test_core.py            ← Tests de validation (parseur + réduction)
├── requirements.txt        ← Dépendances Python
├── screenshots/            ← Captures d'écran de l'interface
├── .gitignore              ← Fichiers exclus de Git
├── LICENSE                 ← Licence MIT
└── README.md               ← Ce fichier
```

### Rôle de chaque module

| Module | Responsabilité |
|--------|---------------|
| `parser.py` | Analyse lexicale (tokenizer) et syntaxique (parseur récursif descendant). Produit un AST avec 5 types de nœuds : `Variable`, `Number`, `Lambda`, `Application`, `BinOp`. |
| `beta_reduction.py` | Implémente la substitution `M[x:=N]` avec gestion de l'α-conversion. Fournit la réduction pas-à-pas (`beta_reduce_step`) et complète (`full_reduction`). |
| `utils.py` | Calcul de métriques (taille AST, applications, profondeur), génération de graphes Graphviz (DOT), exemples prédéfinis. |
| `app.py` | Interface Streamlit avec sidebar, expanders, tableaux, visualisation graphique et métriques colorées. |

---

## ⚙️ Installation

### Prérequis

- **Python 3.8+**
- **pip**
- *(Optionnel)* **Graphviz** installé sur le système pour la visualisation graphique

### Étapes

```bash
# 1. Cloner le dépôt
git clone https://github.com/TON_USERNAME/lambda-optimizer.git
cd lambda-optimizer

# 2. (Recommandé) Créer un environnement virtuel
python -m venv venv

# Windows
venv\Scripts\activate

# Linux / macOS
source venv/bin/activate

# 3. Installer les dépendances Python
pip install -r requirements.txt

# 4. (Optionnel) Installer Graphviz système
# Windows  : winget install Graphviz.Graphviz
# Linux    : sudo apt install graphviz
# macOS    : brew install graphviz

# 5. Lancer l'application
streamlit run app.py
```

L'application s'ouvre automatiquement à **http://localhost:8501**

```bash
# 6. (Optionnel) Lancer les tests de validation
python test_core.py
```

---

## 🚀 Utilisation

### Saisie d'une expression

Entrez une expression lambda dans la zone de texte centrale :

```
(λx.x+1)(5)
```

**Syntaxes acceptées pour le symbole lambda :**

| Syntaxe | Exemple |
|---------|---------|
| Unicode λ | `λx.x+1` |
| Antislash `\` (style Haskell) | `\x.x+1` |
| Mot-clé `lambda` | `lambda x.x+1` |

### Résultats affichés

Après avoir cliqué sur **Réduire**, l'application affiche :

1. **Analyse** — type d'expression, variable, corps, argument, variables libres
2. **Étapes β** — chaque réduction avec description textuelle détaillée
3. **Historique** — tableau Pandas exportable de toutes les étapes
4. **Métriques** — comparaison avant/après (4 indicateurs avec pourcentage)
5. **Arbre syntaxique** — 4 vues : avant/après, simplifiée, détaillée

### Exemples intégrés

10 exemples de complexité croissante sont disponibles dans la **barre latérale** :

| Expression | Résultat | Description |
|------------|----------|-------------|
| `(λx.x)(5)` | `5` | Fonction identité |
| `(λx.x+1)(5)` | `6` | Successeur |
| `(λx.x)(λy.y)(5)` | `5` | Optimisation (2 applications → 0) |
| `(λx.λy.x+y)(3)(4)` | `7` | Addition curryfiée |
| `(λx.x*x)(4)` | `16` | Carré |
| `(λf.λx.f(f(x)))(λx.x+1)(0)` | `2` | Double application (style Church) |
| `(λx.λy.x*y)(6)(7)` | `42` | Multiplication curryfiée |
| `(λf.λg.λx.f(g(x)))(λx.x*2)(λx.x+3)(5)` | `16` | Composition de fonctions |
| `(λx.x*x+2*x+1)(3)` | `16` | Polynôme x²+2x+1 |

---

## 📘 Fondements théoriques

### La réduction β

La **réduction β** est la règle de calcul fondamentale du **lambda-calcul** (Alonzo Church, 1936) :

```
(λx. M) N  →β  M[x := N]
```

**Lecture :** appliquer la fonction `λx.M` à l'argument `N` revient à substituer toutes les occurrences libres de `x` dans `M` par `N`.

### Exemple détaillé

```
Expression : (λx.λy.x+y)(3)(4)

Étape 1 — Expression initiale
  (λx.λy.x+y)(3)(4)

Étape 2 — β-réduction : substitution x := 3
  (λy.3+y)(4)

Étape 3 — β-réduction : substitution y := 4
  3+4

Étape 4 — Évaluation arithmétique
  7

Résultat : 7  ✓  (2 applications éliminées)
```

### Résultats des tests

| Expression | Résultat | Étapes | Applications éliminées | Statut |
|------------|----------|--------|------------------------|--------|
| `(λx.x)(5)` | `5` | 2 | 1 → 0 | ✅ PASS |
| `(λx.x+1)(5)` | `6` | 3 | 1 → 0 | ✅ PASS |
| `(λx.x)(λy.y)(5)` | `5` | 3 | 2 → 0 | ✅ PASS |
| `(λx.λy.x+y)(3)(4)` | `7` | 4 | 2 → 0 | ✅ PASS |
| `(λx.x*x)(4)` | `16` | 3 | 1 → 0 | ✅ PASS |
| `(λf.λx.f(f(x)))(λx.x+1)(0)` | `2` | 7 | 3 → 0 | ✅ PASS |
| `(λx.λy.x*y)(6)(7)` | `42` | 4 | 2 → 0 | ✅ PASS |
| `(λx.x*x+2*x+1)(3)` | `16` | 5 | 1 → 0 | ✅ PASS |

---

## 🤖 Lien avec l'optimisation des modèles IA

La réduction β est directement liée aux techniques d'optimisation utilisées dans les compilateurs et les frameworks d'IA modernes :

| Technique | Lien avec la réduction β |
|-----------|--------------------------|
| **Inlining** (GCC, LLVM) | Remplacer un appel de fonction par son corps = réduction β |
| **Propagation de constantes** | Remplacer une variable par sa valeur connue = substitution `M[x:=N]` |
| **Fusion d'opérateurs** (PyTorch, TensorFlow) | Combiner des nœuds du graphe de calcul = réduire des applications imbriquées |
| **Évaluation partielle** | Spécialiser une fonction pour des arguments connus = β-réduction partielle |
| **Élimination de code mort** | Supprimer les sous-expressions inutiles = éliminer les variables libres non utilisées |

---

## 🛠️ Technologies utilisées

| Technologie | Version | Rôle |
|-------------|---------|------|
| Python | 3.8+ | Langage principal |
| Streamlit | ≥ 1.24 | Interface web interactive |
| Pandas | ≥ 1.5 | Affichage tabulaire et export |
| Graphviz | ≥ 0.20 | Visualisation des arbres syntaxiques |

---

## 📄 Licence

Ce projet est distribué sous licence **MIT**. Voir le fichier [LICENSE](LICENSE) pour plus de détails.

---

<div align="center">

**λ LAMBDA OPTIMIZER** — *Simplifier pour mieux calculer*

Réalisé avec ❤️ par **Ikram** — 2025-2026

</div>
