from __future__ import annotations

import argparse
from types import TracebackType
from typing import Literal

from anki.anki import Anki
from anki.loader import LoaderProtocol, loader_registry
from anki.ui import TextUI


def get_loader(source: str) -> LoaderProtocol:
    """Выбирает загрузчик по стратегии применимости и создаёт его из source.

    Args:
        source: Путь к файлу или ссылка.

    Returns:
        Экземпляр загрузчика с методами load_words и save_words.

    Raises:
        ValueError: Если ни один загрузчик не подходит.
    """
    loader_cls = loader_registry.get_loader(source)
    return loader_cls.from_source(source)


class GameContext:
    """Загружает слова перед игрой и сохраняет их после выхода из блока.

    Сохранение выполняется и тогда, когда тело `with` завершилось с ошибкой.
    """

    _loader: LoaderProtocol
    _anki: Anki

    def __init__(self, loader: LoaderProtocol, anki: Anki) -> None:
        """Запоминает загрузчик и игру, которыми управляет контекст.

        Args:
            loader: Объект с методами load_words и save_words.
            anki: Экземпляр Anki, в который попадут загруженные слова.
        """
        self._loader = loader
        self._anki = anki

    def __enter__(self) -> Anki:
        """Загружает словарь и записывает его в игру."""
        self._anki.words = self._loader.load_words()
        return self._anki

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> Literal[False]:
        """Сохраняет текущий словарь и пропускает исключение дальше.

        Args:
            exc_type: Тип исключения из тела `with` или None.
            exc_val: Само исключение или None.
            exc_tb: Трассировка исключения или None.

        Returns:
            False, чтобы ошибка из игры не была скрыта.
        """
        self._loader.save_words(self._anki.words)
        return False


def main() -> None:
    """Запускает игру с источником слов из аргумента --source."""
    parser = argparse.ArgumentParser(prog="anki")
    parser.add_argument(
        "--source",
        default="./words.txt",
        help="Путь до источника со словами или URL",
        metavar="SOURCE_PATH",
    )
    args = parser.parse_args()
    loader = get_loader(args.source)
    anki = Anki()
    with GameContext(loader, anki):
        ui = TextUI(anki)
        ui.main_loop()


if __name__ == "__main__":
    main()
