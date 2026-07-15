class DuplicateRequestError(RuntimeError):
    pass


class IdentityScopeMismatchError(RuntimeError):
    pass


class DeviceRoleNotAllowedError(RuntimeError):
    pass


class AIServiceUnavailableError(RuntimeError):
    pass


class AIServiceTimeoutError(RuntimeError):
    pass


class AIServiceInvalidOutputError(RuntimeError):
    pass
