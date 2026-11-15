from anki.anki import Anki
from anki.loader import TextFileLoader


def test_integration(tmp_path):
    """Проверяет путь от файла словаря через загрузчик и игру обратно в файл."""
    file_path = tmp_path / "words.txt"
    file_path.write_text("hello,привет\nworld,мир\n", encoding="utf-8")

    loader = TextFileLoader(file_path=str(file_path))
    words = loader.load_words()
    anki = Anki(words=words)

    assert anki.words == {
        "hello": "привет",
        "world": "мир",
    }, "После загрузки свойство `words` должно вернуть слова из файла"

    anki.add_word("  Python  ", "Питон")
    loader.save_words(anki.words)

    saved_lines = set(file_path.read_text(encoding="utf-8").splitlines())
    assert saved_lines == {
        "hello,привет",
        "world,мир",
        "python,питон",
    }, "Файл должен содержать исходные слова и слово, добавленное через `add_word()`"
