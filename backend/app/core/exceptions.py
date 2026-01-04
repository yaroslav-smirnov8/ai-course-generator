# app/core/exceptions.py
from typing import Optional


class BaseAppException(Exception):
    """Base exception class for all application exceptions"""
    def __init__(self, message: str = None):
        self.message = message
        super().__init__(self.message)

class NotFoundException(BaseAppException):
    """Raised when a requested resource is not found"""
    pass

class ValidationError(BaseAppException):
    """Raised when input data validation fails"""
    pass

class AccessDeniedError(BaseAppException):
    """Raised when user doesn't have permission to access a resource"""
    pass

class ResourceExistsError(BaseAppException):
    """Raised when attempting to create a resource that already exists"""
    pass

class GenerationError(BaseAppException):
    """Raised when content generation fails"""
    pass

class ExportError(BaseAppException):
    """Raised when course export fails"""
    pass

class PointsBaseException(Exception):
    """Базовое исключение для системы баллов"""
    def __init__(self, message: str, user_id: Optional[int] = None):
        self.message = message
        self.user_id = user_id
        super().__init__(self.message)

class InsufficientBalanceError(PointsBaseException):
    """Исключение при недостаточном балансе"""
    def __init__(self, message: str, user_id: Optional[int] = None, required_amount: int = 0):
        super().__init__(message, user_id)
        self.required_amount = required_amount

class DailyLimitExceededError(PointsBaseException):
    """Исключение при превышении дневного лимита"""
    def __init__(self, message: str, user_id: Optional[int] = None, limit_type: str = None):
        super().__init__(message, user_id)
        self.limit_type = limit_type

class InvalidTransactionError(PointsBaseException):
    """Исключение при некорректной транзакции"""
    def __init__(self, message: str, user_id: Optional[int] = None, transaction_type: str = None):
        super().__init__(message, user_id)
        self.transaction_type = transaction_type

class TransactionTimeoutError(PointsBaseException):
    """Исключение при превышении времени ожидания транзакции"""
    def __init__(self, message: str, user_id: Optional[int] = None, timeout: int = None):
        super().__init__(message, user_id)
        self.timeout = timeout

class TransactionConflictError(PointsBaseException):
    """Исключение при конфликте транзакций"""
    def __init__(self, message: str, user_id: Optional[int] = None, conflicting_transaction_id: Optional[int] = None):
        super().__init__(message, user_id)
        self.conflicting_transaction_id = conflicting_transaction_id

class InvalidAmountError(PointsBaseException):
    """Исключение при некорректной сумме транзакции"""
    def __init__(self, message: str, user_id: Optional[int] = None, amount: Optional[int] = None):
        super().__init__(message, user_id)
        self.amount = amount

class RefundError(PointsBaseException):
    """Исключение при ошибке возврата баллов"""
    def __init__(
        self,
        message: str,
        user_id: Optional[int] = None,
        original_transaction_id: Optional[int] = None,
        refund_amount: Optional[int] = None
    ):
        super().__init__(message, user_id)
        self.original_transaction_id = original_transaction_id
        self.refund_amount = refund_amount

class TariffLimitError(PointsBaseException):
    """Исключение при нарушении лимитов тарифа"""
    def __init__(
        self,
        message: str,
        user_id: Optional[int] = None,
        tariff_type: Optional[str] = None,
        limit_name: Optional[str] = None,
        current_value: Optional[int] = None,
        max_value: Optional[int] = None
    ):
        super().__init__(message, user_id)
        self.tariff_type = tariff_type
        self.limit_name = limit_name
        self.current_value = current_value
        self.max_value = max_value

class PointsPurchaseError(PointsBaseException):
    """Исключение при ошибке покупки баллов"""
    def __init__(
        self,
        message: str,
        user_id: Optional[int] = None,
        amount: Optional[int] = None,
        payment_id: Optional[str] = None,
        payment_status: Optional[str] = None
    ):
        super().__init__(message, user_id)
        self.amount = amount
        self.payment_id = payment_id
        self.payment_status = payment_status