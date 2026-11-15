import pytest

from anki.anki import Anki


@pytest.mark.parametrize(
    "word, case, expected",
    [
        (
            "hello",
            "корректных данных",
            "hello",
        ),
        (
            "hello world",
            "отсутствия пробельных символов в начале или конце строки",
            "hello world",
        ),
        (
            "python",
            "корректных данных",
            "python",
        ),
    ],
)
def test_normalize_word_method_returns_valid_input_unchanged(
    word,
    case,
    expected,
):
    """Метод `normalize_word` класса `Anki` должен вернуть переданную строку
    неизменённой, если:
     - строка записана в нижнем регистре,
     - в начале и в конце строки нет пробелов.
    """
    assert Anki.normalize_word(word) == expected, (
        "Метод `normalize_word` должен возвращать неизменённую строку," f" если {case}"
    )


@pytest.mark.parametrize(
    "word, expected",
    [
        ("pYtHoN", "python"),
        ("Hello World", "hello world"),
        ("   Python   ", "python"),
        ("\tHello World\n", "hello world"),
    ],
)
def test_normalize_word_method_normalizes_word(word, expected):
    """Метод `normalize_word` класса `Anki` должен выполнить нормализацию строки:
    - все символы приведены к нижнему регистру;
    - удалены пробелы в начале и в конце строки.
    """
    assert Anki.normalize_word(word) == expected, (
        "Метод `normalize_word` должен нормализовать"
        " некорректно отформатированные строки."
    )


@pytest.mark.parametrize(
    "invalid_input",
    [
        1,
        [],
        set(),
    ],
)
def test_normalize_word_raises_ValueError_on_invalid_input(invalid_input):
    """Метод `normalize_word` класса `Anki` должен выдавать исключение
    `ValueError`, если в качестве значения параметра `word`
    передана не строка.
    """
    with pytest.raises(ValueError, match="должно быть строкой"):
        Anki.normalize_word(invalid_input)
        pytest.fail(
            "Метод `normalize_word` должен выдавать ValueError"
            " для нестроковых параметров"
        )


@pytest.mark.parametrize(
    "words",
    [
        [],
        "hello",
        1,
        {"python", "питон"},
    ],
)
def test_anki_init_raises_ValueError_on_invalid_input(words):
    """Инициализатор `Anki` должен выдавать `ValueError`, если `words`
    не является словарём.
    """
    with pytest.raises(ValueError):
        Anki(words=words)
        pytest.fail(
            "Инициализатор `Anki` должен выдавать ValueError,"
            " если параметр `words` не является словарём"
        )


@pytest.fixture()
def anki():
    """Возвращает пустой экземпляр игры."""
    return Anki()


@pytest.mark.parametrize(
    "word, translation",
    [
        (1, "привет"),
        ("hello", 2),
        (None, "привет"),
        ("hello", None),
        ([], "привет"),
        ("hello", {}),
    ],
)
def test_anki_add_word_raises_ValueError_on_invalid_input(
    anki,
    word,
    translation,
):
    """Метод `add_word` должен выдавать `ValueError`, если `word`
    или `translation` не являются строками.
    """
    with pytest.raises(ValueError):
        anki.add_word(word, translation)
        pytest.fail(
            "Метод `add_word` должен выдавать ValueError,"
            " если `word` или `translation` не являются строками"
        )


def test_get_random_word_raises_when_deck_is_empty(anki):
    """Пустая колода не может выдать случайное слово."""
    with pytest.raises(ValueError):
        anki.get_random_word()
        pytest.fail(
            "Метод `get_random_word` должен выдавать ValueError,"
            " если в словаре нет слов"
        )


def test_get_random_word_returns_existing_word(anki):
    """Случайное слово берётся из ключей словаря."""
    anki.add_word("Hello", "Привет")
    assert anki.get_random_word() == "hello"


def test_check_translation_normalizes_and_compares(anki):
    """Проверка перевода не зависит от регистра и крайних пробелов."""
    anki.add_word("hello", "привет")
    assert anki.check_translation("  HELLO ", " Привет ") is True
    assert anki.check_translation("hello", "пока") is False


def test_check_translation_raises_for_unknown_word(anki):
    """Нельзя проверить перевод слова, которого нет в колоде."""
    with pytest.raises(ValueError):
        anki.check_translation("python", "питон")


def test_get_translation_returns_normalized_match(anki):
    """Перевод ищется по нормализованному слову."""
    anki.add_word("world", "мир")
    assert anki.get_translation("  WORLD ") == "мир"


def test_get_translation_raises_for_unknown_word(anki):
    """Для отсутствующего слова перевод не возвращается."""
    with pytest.raises(ValueError):
        anki.get_translation("python")
