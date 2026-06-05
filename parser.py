"""
parser.py — Analyseur syntaxique pour le lambda-calcul étendu.

Ce module fournit :
  • Un tokenizer qui transforme une chaîne en liste de tokens.
  • Des classes AST (Variable, Number, Lambda, Application, BinOp).
  • Un parseur récursif descendant respectant les priorités :
        lambda < addition/soustraction < multiplication/division < application/atome

Syntaxe acceptée :
  λx.corps   ou   \\x.corps   ou   lambda x.corps
  (λx.x+1)(5)
  (λx.λy.x+y)(3)(4)
  (λf.λx.f(f(x)))(λx.x+1)(0)
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import List, Union


# ═══════════════════════════════════════════════════════════════════════════════
#  NŒUDS DE L'ARBRE SYNTAXIQUE ABSTRAIT (AST)
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class Variable:
    """Représente une variable libre ou liée (ex: x, y, f)."""
    name: str

    def __str__(self) -> str:
        return self.name

    def __eq__(self, other) -> bool:
        return isinstance(other, Variable) and self.name == other.name

    def __hash__(self) -> int:
        return hash(("Variable", self.name))


@dataclass
class Number:
    """Représente un littéral numérique (ex: 5, 42)."""
    value: int

    def __str__(self) -> str:
        return str(self.value)

    def __eq__(self, other) -> bool:
        return isinstance(other, Number) and self.value == other.value

    def __hash__(self) -> int:
        return hash(("Number", self.value))


@dataclass
class Lambda:
    """
    Abstraction lambda : λparam.body
    Exemple : λx.x+1  →  Lambda("x", BinOp("+", Variable("x"), Number(1)))
    """
    param: str
    body: 'Expression'

    def __str__(self) -> str:
        return f"λ{self.param}.{self.body}"

    def __eq__(self, other) -> bool:
        return isinstance(other, Lambda) and self.param == other.param and self.body == other.body

    def __hash__(self) -> int:
        return hash(("Lambda", self.param, self.body))


@dataclass
class Application:
    """
    Application de fonction : func(arg)
    Exemple : (λx.x+1)(5)  →  Application(Lambda("x", ...), Number(5))
    """
    func: 'Expression'
    arg: 'Expression'

    def __str__(self) -> str:
        # Entourer la fonction de parenthèses si c'est un lambda ou une opération
        if isinstance(self.func, (Lambda, BinOp)):
            func_str = f"({self.func})"
        else:
            func_str = str(self.func)
        return f"{func_str}({self.arg})"

    def __eq__(self, other) -> bool:
        return isinstance(other, Application) and self.func == other.func and self.arg == other.arg

    def __hash__(self) -> int:
        return hash(("Application", self.func, self.arg))


@dataclass
class BinOp:
    """
    Opération binaire arithmétique : left op right
    Opérateurs supportés : +, -, *, /
    """
    op: str
    left: 'Expression'
    right: 'Expression'

    def __str__(self) -> str:
        left_str = str(self.left)
        right_str = str(self.right)

        # Parenthéser un lambda à gauche ou à droite
        if isinstance(self.left, Lambda):
            left_str = f"({left_str})"
        if isinstance(self.right, Lambda):
            right_str = f"({right_str})"

        # Gérer la priorité des opérateurs
        if self.op in ('*', '/'):
            if isinstance(self.left, BinOp) and self.left.op in ('+', '-'):
                left_str = f"({left_str})"
            if isinstance(self.right, BinOp) and self.right.op in ('+', '-'):
                right_str = f"({right_str})"

        # Gérer la soustraction/division à droite (associativité à gauche)
        if self.op == '-' and isinstance(self.right, BinOp) and self.right.op in ('+', '-'):
            right_str = f"({right_str})"
        if self.op == '/' and isinstance(self.right, BinOp) and self.right.op in ('*', '/'):
            right_str = f"({right_str})"

        return f"{left_str}{self.op}{right_str}"

    def __eq__(self, other) -> bool:
        return (isinstance(other, BinOp) and self.op == other.op
                and self.left == other.left and self.right == other.right)

    def __hash__(self) -> int:
        return hash(("BinOp", self.op, self.left, self.right))


# Type alias pour toutes les expressions possibles
Expression = Union[Variable, Number, Lambda, Application, BinOp]


# ═══════════════════════════════════════════════════════════════════════════════
#  TOKENIZER
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class Token:
    """Représente un token lexical."""
    type: str    # LPAREN, RPAREN, LAMBDA, DOT, PLUS, MINUS, STAR, SLASH, NUMBER, IDENT, EOF
    value: object
    position: int = 0


def tokenize(text: str) -> List[Token]:
    """
    Transforme une chaîne de caractères en liste de tokens.

    Caractères reconnus :
      ( ) λ \\ . + - * / chiffres identifiants
    Le mot-clé 'lambda' est reconnu comme le symbole λ.

    Raises:
        SyntaxError: Si un caractère non reconnu est rencontré.
    """
    tokens: List[Token] = []
    i = 0
    length = len(text)

    while i < length:
        ch = text[i]

        # ── Espaces ──
        if ch.isspace():
            i += 1
            continue

        # ── Parenthèses ──
        if ch == '(':
            tokens.append(Token('LPAREN', '(', i))
            i += 1
        elif ch == ')':
            tokens.append(Token('RPAREN', ')', i))
            i += 1

        # ── Symbole lambda ──
        elif ch == 'λ' or ch == '\\':
            tokens.append(Token('LAMBDA', 'λ', i))
            i += 1

        # ── Point (séparateur paramètre / corps) ──
        elif ch == '.':
            tokens.append(Token('DOT', '.', i))
            i += 1

        # ── Opérateurs arithmétiques ──
        elif ch == '+':
            tokens.append(Token('PLUS', '+', i))
            i += 1
        elif ch == '-':
            tokens.append(Token('MINUS', '-', i))
            i += 1
        elif ch == '*':
            tokens.append(Token('STAR', '*', i))
            i += 1
        elif ch == '/':
            tokens.append(Token('SLASH', '/', i))
            i += 1

        # ── Nombres entiers ──
        elif ch.isdigit():
            start = i
            while i < length and text[i].isdigit():
                i += 1
            tokens.append(Token('NUMBER', int(text[start:i]), start))

        # ── Identifiants et mot-clé 'lambda' ──
        elif ch.isalpha() or ch == '_':
            start = i
            while i < length and (text[i].isalnum() or text[i] == '_'):
                i += 1
            word = text[start:i]
            if word == 'lambda':
                tokens.append(Token('LAMBDA', 'λ', start))
            else:
                tokens.append(Token('IDENT', word, start))

        else:
            raise SyntaxError(
                f"Caractère inattendu '{ch}' à la position {i}"
            )

    tokens.append(Token('EOF', None, len(text)))
    return tokens


# ═══════════════════════════════════════════════════════════════════════════════
#  PARSEUR RÉCURSIF DESCENDANT
# ═══════════════════════════════════════════════════════════════════════════════

class Parser:
    """
    Parseur récursif descendant pour les expressions du lambda-calcul étendu.

    Grammaire (simplifiée) :
        expr         → lambda | add_expr
        lambda       → LAMBDA IDENT DOT expr
        add_expr     → mul_expr ((PLUS | MINUS) mul_expr)*
        mul_expr     → call_expr ((STAR | SLASH) call_expr)*
        call_expr    → atom (LPAREN expr RPAREN)*
        atom         → LPAREN expr RPAREN | NUMBER | IDENT
    """

    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.pos = 0

    # ── Utilitaires ──────────────────────────────────────────────────────────

    def peek(self) -> Token:
        """Retourne le token courant sans avancer."""
        return self.tokens[self.pos]

    def consume(self, expected_type: str = None) -> Token:
        """
        Avance d'un token et le retourne.
        Si expected_type est fourni, vérifie que le token correspond.
        """
        token = self.tokens[self.pos]
        if expected_type and token.type != expected_type:
            raise SyntaxError(
                f"Attendu '{expected_type}', obtenu '{token.type}' "
                f"(valeur: '{token.value}') à la position {token.position}"
            )
        self.pos += 1
        return token

    # ── Point d'entrée ───────────────────────────────────────────────────────

    def parse(self) -> Expression:
        """Parse l'entrée complète et retourne l'AST."""
        expr = self._parse_expr()
        if self.peek().type != 'EOF':
            tok = self.peek()
            raise SyntaxError(
                f"Entrée inattendue '{tok.value}' après la fin de l'expression "
                f"(position {tok.position})"
            )
        return expr

    # ── Règles de grammaire ──────────────────────────────────────────────────

    def _parse_expr(self) -> Expression:
        """expr → lambda | add_expr"""
        if self.peek().type == 'LAMBDA':
            return self._parse_lambda()
        return self._parse_add_expr()

    def _parse_lambda(self) -> Lambda:
        """lambda → LAMBDA IDENT DOT expr"""
        self.consume('LAMBDA')
        param_token = self.consume('IDENT')
        self.consume('DOT')
        body = self._parse_expr()
        return Lambda(param_token.value, body)

    def _parse_add_expr(self) -> Expression:
        """add_expr → mul_expr ((PLUS | MINUS) mul_expr)*"""
        left = self._parse_mul_expr()
        while self.peek().type in ('PLUS', 'MINUS'):
            op_token = self.consume()
            right = self._parse_mul_expr()
            left = BinOp(op_token.value, left, right)
        return left

    def _parse_mul_expr(self) -> Expression:
        """mul_expr → call_expr ((STAR | SLASH) call_expr)*"""
        left = self._parse_call_expr()
        while self.peek().type in ('STAR', 'SLASH'):
            op_token = self.consume()
            right = self._parse_call_expr()
            left = BinOp(op_token.value, left, right)
        return left

    def _parse_call_expr(self) -> Expression:
        """
        call_expr → atom (LPAREN expr RPAREN)*

        Gère l'application de fonction par juxtaposition de parenthèses :
        (λx.x+1)(5)  ou  f(x)  ou  (λx.λy.x+y)(3)(4)
        """
        expr = self._parse_atom()

        # Tant qu'on voit une parenthèse ouvrante, c'est une application
        while self.peek().type == 'LPAREN':
            # Sauvegarder la position pour pouvoir revenir en arrière
            # si ce n'est pas réellement une application
            saved_pos = self.pos
            self.consume('LPAREN')
            try:
                arg = self._parse_expr()
                self.consume('RPAREN')
                expr = Application(expr, arg)
            except SyntaxError:
                # Ce n'était pas une application, rétablir la position
                self.pos = saved_pos
                break

        return expr

    def _parse_atom(self) -> Expression:
        """atom → LPAREN expr RPAREN | NUMBER | IDENT"""
        token = self.peek()

        if token.type == 'LPAREN':
            self.consume('LPAREN')
            expr = self._parse_expr()
            self.consume('RPAREN')
            return expr

        if token.type == 'NUMBER':
            self.consume()
            return Number(token.value)

        if token.type == 'IDENT':
            self.consume()
            return Variable(token.value)

        raise SyntaxError(
            f"Expression inattendue : '{token.type}' "
            f"(valeur: '{token.value}') à la position {token.position}"
        )


# ═══════════════════════════════════════════════════════════════════════════════
#  FONCTION UTILITAIRE PUBLIQUE
# ═══════════════════════════════════════════════════════════════════════════════

def parse_expression(text: str) -> Expression:
    """
    Point d'entrée principal : parse une chaîne et retourne l'AST.

    Args:
        text: L'expression lambda sous forme de chaîne.

    Returns:
        L'arbre syntaxique abstrait de l'expression.

    Raises:
        SyntaxError: Si l'expression est mal formée.

    Exemples:
        >>> parse_expression("(λx.x+1)(5)")
        Application(Lambda('x', BinOp('+', Variable('x'), Number(1))), Number(5))
    """
    tokens = tokenize(text)
    parser = Parser(tokens)
    return parser.parse()
