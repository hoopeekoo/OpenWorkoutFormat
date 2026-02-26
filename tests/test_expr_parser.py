"""Tests for the expression parser."""

from owf.ast.expressions import BinOp, Literal, Percentage, VarRef
from owf.parser.expr_parser import parse_expression


def test_literal_with_unit():
    expr = parse_expression("200W")
    assert isinstance(expr, Literal)
    assert expr.value == 200
    assert expr.unit == "W"


def test_literal_kg():
    expr = parse_expression("80kg")
    assert isinstance(expr, Literal)
    assert expr.value == 80
    assert expr.unit == "kg"


def test_bare_number():
    expr = parse_expression("42")
    assert isinstance(expr, Literal)
    assert expr.value == 42
    assert expr.unit is None


def test_variable_reference():
    expr = parse_expression("FTP")
    assert isinstance(expr, VarRef)
    assert expr.name == "FTP"


def test_multi_word_variable():
    expr = parse_expression("1RM bench press")
    assert isinstance(expr, VarRef)
    assert expr.name == "1RM bench press"


def test_percentage_of():
    expr = parse_expression("80% of FTP")
    assert isinstance(expr, Percentage)
    assert expr.percent == 80
    assert isinstance(expr.of, VarRef)
    assert expr.of.name == "FTP"


def test_percentage_of_1rm():
    expr = parse_expression("70% of 1RM bench press")
    assert isinstance(expr, Percentage)
    assert expr.percent == 70
    assert isinstance(expr.of, VarRef)
    assert expr.of.name == "1RM bench press"


def test_binop_addition():
    expr = parse_expression("bodyweight + 20kg")
    assert isinstance(expr, BinOp)
    assert expr.op == "+"
    assert isinstance(expr.left, VarRef)
    assert expr.left.name == "bodyweight"
    assert isinstance(expr.right, Literal)
    assert expr.right.value == 20
    assert expr.right.unit == "kg"


def test_bare_percentage():
    expr = parse_expression("80%")
    assert isinstance(expr, Literal)
    assert expr.value == 80
    assert expr.unit == "%"
