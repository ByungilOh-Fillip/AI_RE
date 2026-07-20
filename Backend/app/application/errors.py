class DuplicateRequestError(RuntimeError):
    pass


class IdentityScopeMismatchError(RuntimeError):
    pass


class DeviceRoleNotAllowedError(RuntimeError):
    pass


class DeviceAlreadyRegisteredError(RuntimeError):
    pass


class DeviceNotFoundError(RuntimeError):
    pass


class InvalidPairingCodeError(RuntimeError):
    pass


class ExpiredPairingCodeError(RuntimeError):
    pass


class UsedPairingCodeError(RuntimeError):
    pass


class AIServiceUnavailableError(RuntimeError):
    pass


class AIServiceTimeoutError(RuntimeError):
    pass


class AIServiceInvalidOutputError(RuntimeError):
    pass
