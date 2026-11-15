from __future__ import annotations

import json
from pathlib import Path
from typing import Callable, Protocol, TextIO

import requests


class LoaderProtocol(Protocol):
    """Структура загрузчика словаря, без общего базового класса.

    Файловые загрузчики и загрузчик по HTTP подходят под этот протокол,
    если умеют читать и сохранять пары «слово — перевод».
    """

    @classmethod
    def from_source(cls, source: str) -> LoaderProtocol:
        """Создаёт экземпляр загрузчика из строки источника."""

    def load_words(self) -> dict[str, str]:
        """Возвращает словарь слов и переводов."""

    def save_words(self, words: dict[str, str]) -> None:
        """Сохраняет словарь слов и переводов."""


class LoaderRegistry:
    """Хранит классы загрузчиков и стратегию применимости каждого."""

    _registry: dict[type[LoaderProtocol], Callable[[str], bool]]

    def __init__(self) -> None:
        self._registry = {}

    def register(
        self,
        predicate: Callable[[str], bool],
    ) -> Callable[[type[LoaderProtocol]], type[LoaderProtocol]]:
        """Регистрирует класс загрузчика вместе с функцией применимости.

        Args:
            predicate: Функция, которая по строке источника решает,
                подходит ли этот загрузчик.

        Returns:
            Декоратор, который сохраняет класс и возвращает его без изменений.
        """

        def decorator(cls: type[LoaderProtocol]) -> type[LoaderProtocol]:
            self._registry[cls] = predicate
            return cls

        return decorator

    def get_loader(self, source: str) -> type[LoaderProtocol]:
        """Находит подходящий загрузчик для source.

        Args:
            source: Путь к файлу или ссылка.

        Returns:
            Класс загрузчика, чья стратегия вернула True.

        Raises:
            ValueError: Если ни одна стратегия не подошла.
        """
        for loader_cls, predicate in self._registry.items():
            if predicate(source):
                return loader_cls
        raise ValueError(f"Неизвестный источник: {source}")


loader_registry = LoaderRegistry()


class BaseFileLoader:
    """Читает и записывает словарь слов в файл.

    Наследники определяют только формат данных.
    """

    DEFAULT_FILE_PATH: str = "./words.txt"
    _file_path: Path

    def __init__(self, *, file_path: str | None = None) -> None:
        if file_path is None:
            file_path = self.DEFAULT_FILE_PATH
        self._file_path = Path(file_path)
        if self._file_path.exists() and self._file_path.is_dir():
            raise ValueError(
                f"Путь {file_path} является директорией, а должен быть файлом"
            )

    def load_words(self) -> dict[str, str]:
        """Загружает словарь слов из файла.

        Если файла ещё нет, возвращает пустой словарь.

        Returns:
            Словарь, в котором ключ — слово, а значение — перевод.
        """
        if not self._file_path.exists():
            return {}
        with self._file_path.open("r", encoding="utf-8") as file_object:
            return self._load_from_file(file_object)

    def save_words(self, words: dict[str, str]) -> None:
        """Перезаписывает файл словарём words.

        Args:
            words: Словарь для сохранения. Ключ — слово, значение — перевод.

        Raises:
            ValueError: Если words не является словарём.
        """
        if not isinstance(words, dict):
            raise ValueError("Значением параметра `words` должен быть словарь")
        with self._file_path.open("w", encoding="utf-8") as file_object:
            self._save_to_file(words, file_object)

    def _load_from_file(self, file_object: TextIO) -> dict[str, str]:
        """Читает словарь из уже открытого файла.

        Args:
            file_object: Открытый файл с данными словаря.

        Returns:
            Словарь загруженных слов.

        Raises:
            NotImplementedError: Если наследник не реализовал свой формат.
        """
        raise NotImplementedError

    def _save_to_file(
        self,
        words: dict[str, str],
        file_object: TextIO,
    ) -> None:
        """Записывает словарь words в уже открытый файл.

        Args:
            words: Словарь слов и переводов.
            file_object: Открытый файл для записи.

        Raises:
            NotImplementedError: Если наследник не реализовал свой формат.
        """
        raise NotImplementedError

    @classmethod
    def from_source(cls, source: str) -> BaseFileLoader:
        """Создаёт файловый загрузчик для пути source.

        Args:
            source: Путь к файлу со словарём.

        Returns:
            Экземпляр того класса, у которого вызван метод.
        """
        return cls(file_path=source)


def is_txt_source(source: str) -> bool:
    """Проверяет, что источник — файл с расширением .txt."""
    return source.endswith(".txt")


@loader_registry.register(is_txt_source)
class TextFileLoader(BaseFileLoader):
    """Загружает и сохраняет словарь в текстовом файле.

    Формат записи: «слово,перевод».
    """

    DEFAULT_FILE_PATH = "./words.txt"

    def _load_from_file(self, file_object: TextIO) -> dict[str, str]:
        words: dict[str, str] = {}
        for line in file_object:
            word, translation = line.split(",")
            words[word.strip()] = translation.strip()
        return words

    def _save_to_file(
        self,
        words: dict[str, str],
        file_object: TextIO,
    ) -> None:
        for word, translation in words.items():
            file_object.write(f"{word},{translation}\n")


def is_tsv_source(source: str) -> bool:
    """Проверяет, что источник — файл с расширением .tsv."""
    return source.endswith(".tsv")


@loader_registry.register(is_tsv_source)
class TSVFileLoader(BaseFileLoader):
    """Загружает и сохраняет словарь в TSV-файле.

    Формат записи: «слово\\tперевод».
    """

    DEFAULT_FILE_PATH = "./words.tsv"

    def _load_from_file(self, file_object: TextIO) -> dict[str, str]:
        words: dict[str, str] = {}
        for line in file_object:
            word, translation = line.split("\t")
            words[word.strip()] = translation.strip()
        return words

    def _save_to_file(
        self,
        words: dict[str, str],
        file_object: TextIO,
    ) -> None:
        for word, translation in words.items():
            file_object.write(f"{word}\t{translation}\n")


def is_json_source(source: str) -> bool:
    """Проверяет, что источник — файл с расширением .json."""
    return source.endswith(".json")


@loader_registry.register(is_json_source)
class JsonFileLoader(BaseFileLoader):
    """Загружает и сохраняет словарь в JSON-файле."""

    DEFAULT_FILE_PATH = "./words.json"

    def _load_from_file(self, file_object: TextIO) -> dict[str, str]:
        words: dict[str, str] = json.load(file_object)
        for key, value in words.items():
            if not isinstance(key, str) or not isinstance(value, str):
                raise ValueError("Некорректные данные в файле")
        return words

    def _save_to_file(
        self,
        words: dict[str, str],
        file_object: TextIO,
    ) -> None:
        json.dump(words, file_object, indent=2, ensure_ascii=False)


def is_http_source(source: str) -> bool:
    """Проверяет, что источник — ссылка http или https."""
    return source.startswith("http")


@loader_registry.register(is_http_source)
class JsonNetworkLoader:
    """Загружает словарь слов по HTTP из JSON-ответа.

    Сохранение по сети не поддерживается: `save_words` оставлен заглушкой,
    чтобы интерфейс совпадал с файловыми загрузчиками.
    """

    url: str

    def __init__(self, url: str) -> None:
        """Сохраняет адрес источника слов.

        Args:
            url: Ссылка, по которой лежит JSON со словарём.
        """
        self.url = url

    @classmethod
    def from_source(cls, source: str) -> JsonNetworkLoader:
        """Создаёт сетевой загрузчик для ссылки source.

        Args:
            source: Адрес JSON со словарём.

        Returns:
            Экземпляр JsonNetworkLoader.
        """
        return cls(url=source)

    def load_words(self) -> dict[str, str]:
        """Загружает словарь слов по ссылке.

        Returns:
            Словарь, в котором ключ — слово, а значение — перевод.
        """
        response = requests.get(self.url)
        words: dict[str, str] = response.json()
        for key, value in words.items():
            if not isinstance(key, str) or not isinstance(value, str):
                raise ValueError("Некорректные данные получены по сети")
        return words

    def save_words(self, words: dict[str, str] | None = None) -> None:
        """Ничего не делает: удалённый источник не перезаписывается.

        Args:
            words: Словарь, который файловые загрузчики сохранили бы на диск.
        """
        return None
