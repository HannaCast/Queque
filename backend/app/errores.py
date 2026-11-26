"""Errores de negocio. Cada uno sabe con qué código HTTP se responde."""


class ErrorNegocio(Exception):
    status = 400


class NoAutorizado(ErrorNegocio):
    """Falta iniciar sesión, la sesión venció o las credenciales no coinciden."""
    status = 401


class Prohibido(ErrorNegocio):
    """Hay sesión, pero el rol no permite esta acción."""
    status = 403


class Bloqueado(ErrorNegocio):
    """Demasiados intentos fallidos de inicio de sesión."""
    status = 429


class NoEncontrado(ErrorNegocio):
    status = 404


class Conflicto(ErrorNegocio):
    status = 409


class FormatoNoSoportado(ErrorNegocio):
    status = 415


class Invalido(ErrorNegocio):
    status = 422


class ErrorProcesamiento(Exception):
    """Falla al analizar un trabajo. El trabajo queda en estado 'error'; no se cae el servicio."""
