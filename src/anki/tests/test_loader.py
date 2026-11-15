import pytest

from anki.loader import TextFileLoader


@pytest.fixture()
def tmp_file(tmp_path):
    """Создаёт временный файл с одной парой «слово,перевод»."""
    path = tmp_path / "test_words.txt"
    path.write_text("hello,привет\n", encoding="utf-8")
    return str(path)


@pytest.fixture()
def empty_words_file(tmp_path):
    """Создаёт пустой временный файл для сохранения словаря."""
    path = tmp_path / "empty_words.txt"
    path.write_text("", encoding="utf-8")
    return path


def test_load_words_loads_words_from_comma_separated_values(tmp_file):
    """Метод `load_words` класса `TextFileLoader` должен выполнить
    загрузку слов из файла, путь до которого передан
    при инициализации экземпляра класса `TextFileLoader`.
    """
    loader = TextFileLoader(file_path=tmp_file)
    words = loader.load_words()
    assert words == {"hello": "привет"}


def test_save_words_saves_words_as_comma_separated_values(empty_words_file):
    """Метод `save_words` должен записать словарь в файл
    строками формата «слово,перевод».
    """
    loader = TextFileLoader(file_path=str(empty_words_file))
    loader.save_words({"hello": "привет", "world": "мир"})

    saved_lines = set(empty_words_file.read_text(encoding="utf-8").splitlines())
    assert saved_lines == {
        "hello,привет",
        "world,мир",
    }, "Метод `save_words` должен сохранять слова в формате «слово,перевод»"
