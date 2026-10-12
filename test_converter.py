import pytest

from converter import ConversionError, convert_text, parse_number


@pytest.mark.parametrize("text, expected", [
    ("convert 5 kilometers to miles", 3.10686),
    ("convert one hundred degrees celsius to fahrenheit", 212),
    ("how many feet in a mile", 5280),
    ("what is 100 fahrenheit in celsius", 37.7778),
    ("10 kg to pounds", 22.0462),
    ("two point five liters to milliliters", 2500),
    ("one thousand two hundred meters in km", 1.2),
    ("5km to miles", 3.10686),
    ("convert 3 tablespoons to teaspoons", 9),
    ("1 gigabyte to megabytes", 1000),
    ("60 mph to km/h", 96.5606),
    ("minus forty celsius to fahrenheit", -40),
    ("twenty-five kilometers to meters", 25000),
    ("how many meters are in 2 kilometers", 2000),
    ("please convert 2 hours to minutes thanks", 120),
    ("1,500 grams to kilograms", 1.5),
])
def test_conversions(text, expected):
    assert convert_text(text).result == pytest.approx(expected, rel=1e-4)


@pytest.mark.parametrize("text", [
    "", "hello", "convert foo to bar", "convert 5 kg to meters",
    "convert -300 celsius to kelvin", "convert kilometers to miles x y",
])
def test_errors(text):
    with pytest.raises(ConversionError):
        convert_text(text)


@pytest.mark.parametrize("tokens, expected", [
    (["twenty", "five"], (25, 2)),
    (["one", "hundred", "and", "five"], (105, 4)),
    (["two", "thousand", "five", "hundred"], (2500, 4)),
    (["3.5", "km"], (3.5, 1)),
    (["a", "hundred", "meters"], (100, 2)),
])
def test_parse_number(tokens, expected):
    assert parse_number(tokens) == expected


def test_spoken_text_pluralises():
    d = convert_text("1 kilometer to meters").to_dict()
    assert d["spoken"] == "1 kilometer is 1000 meters"
