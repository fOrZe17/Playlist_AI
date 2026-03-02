class DomainException(Exception):
    """Базовое доменное исключение."""


class UserNotFound(DomainException):
    """Пользователь не найден."""


class UserAlreadyExists(DomainException):
    """Пользователь с таким email уже существует."""


class InvalidCredentials(DomainException):
    """Неверные учётные данные."""


class PlaylistNotFound(DomainException):
    """Плейлист не найден."""
