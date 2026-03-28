from dataclasses import dataclass

from adqa.profiling.utils.rounding import round_value


@dataclass
class SubData:
    val: float


@dataclass
class SampleData:
    a: float
    b: int
    c: str
    d: SubData


def test_round_value_basic():
    assert round_value(1.23456, 2) == 1.23
    assert round_value(1, 2) == 1
    assert round_value("text", 2) == "text"


def test_round_value_dict():
    data = {"a": 1.23456, "b": {"c": 2.34567}}
    expected = {"a": 1.23, "b": {"c": 2.35}}
    assert round_value(data, 2) == expected


def test_round_value_list_tuple():
    data = [1.23456, (2.34567, 3.45678)]
    expected = [1.23, (2.35, 3.46)]
    assert round_value(data, 2) == expected


def test_round_value_dataclass():
    data = SampleData(a=1.23456, b=10, c="hello", d=SubData(val=3.45678))
    expected = SampleData(a=1.23, b=10, c="hello", d=SubData(val=3.46))
    result = round_value(data, 2)
    assert result == expected
    assert isinstance(result, SampleData)
    assert isinstance(result.d, SubData)


def test_round_value_with_type():
    # Ensure it doesn't crash or try to "round" a class itself
    assert round_value(SampleData, 2) == SampleData
