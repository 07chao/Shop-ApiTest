"""
自定义异常类
============

定义应用级别的异常类，提供统一的错误处理和响应格式。
包含业务逻辑异常、验证异常、认证异常等。

设计思路:
1. 继承 FastAPI 的 HTTPException 或自定义基础异常
2. 提供详细的错误信息和错误代码
3. 支持国际化错误消息
4. 集成日志记录
5. 提供异常处理器
"""

from typing import Any, Dict, Optional
from fastapi import HTTPException, status
import structlog

# 配置日志
logger = structlog.get_logger(__name__)


class FastAPIShopException(Exception):
    """应用基础异常类"""
    
    def __init__(
        self,
        message: str,
        error_code: str = "GENERAL_ERROR",
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        super().__init__(self.message)


class ValidationError(FastAPIShopException):
    """数据验证异常"""
    
    def __init__(
        self,
        message: str = "Validation failed",
        field: Optional[str] = None,
        value: Optional[Any] = None
    ):
        details = {}
        if field:
            details["field"] = field
        if value is not None:
            details["value"] = str(value)
            
        super().__init__(
            message=message,
            error_code="VALIDATION_ERROR",
            details=details
        )


class AuthenticationError(FastAPIShopException):
    """认证异常"""
    
    def __init__(self, message: str = "Authentication failed"):
        super().__init__(
            message=message,
            error_code="AUTHENTICATION_ERROR"
        )


class AuthorizationError(FastAPIShopException):
    """授权异常"""
    
    def __init__(self, message: str = "Insufficient permissions"):
        super().__init__(
            message=message,
            error_code="AUTHORIZATION_ERROR"
        )


class NotFoundError(FastAPIShopException):
    """资源未找到异常"""
    
    def __init__(
        self,
        resource: str = "Resource",
        resource_id: Optional[str] = None
    ):
        message = f"{resource} not found"
        if resource_id:
            message += f" (ID: {resource_id})"
            
        super().__init__(
            message=message,
            error_code="NOT_FOUND",
            details={"resource": resource, "resource_id": resource_id}
        )


class ConflictError(FastAPIShopException):
    """资源冲突异常"""
    
    def __init__(
        self,
        message: str = "Resource conflict",
        conflicting_field: Optional[str] = None
    ):
        details = {}
        if conflicting_field:
            details["conflicting_field"] = conflicting_field
            
        super().__init__(
            message=message,
            error_code="CONFLICT",
            details=details
        )


class RateLimitError(FastAPIShopException):
    """限流异常"""
    
    def __init__(
        self,
        message: str = "Rate limit exceeded",
        retry_after: Optional[int] = None
    ):
        details = {}
        if retry_after:
            details["retry_after"] = retry_after
            
        super().__init__(
            message=message,
            error_code="RATE_LIMIT",
            details=details
        )


class BusinessLogicError(FastAPIShopException):
    """业务逻辑异常"""
    
    def __init__(
        self,
        message: str,
        business_code: str = "BUSINESS_ERROR"
    ):
        super().__init__(
            message=message,
            error_code=business_code
        )


class ExternalServiceError(FastAPIShopException):
    """外部服务异常"""
    
    def __init__(
        self,
        service_name: str,
        message: str = "External service error"
    ):
        super().__init__(
            message=message,
            error_code="EXTERNAL_SERVICE_ERROR",
            details={"service": service_name}
        )


class DatabaseError(FastAPIShopException):
    """数据库异常"""
    
    def __init__(
        self,
        message: str = "Database operation failed",
        operation: Optional[str] = None
    ):
        details = {}
        if operation:
            details["operation"] = operation
            
        super().__init__(
            message=message,
            error_code="DATABASE_ERROR",
            details=details
        )


class FileUploadError(FastAPIShopException):
    """文件上传异常"""
    
    def __init__(
        self,
        message: str = "File upload failed",
        filename: Optional[str] = None,
        reason: Optional[str] = None
    ):
        details = {}
        if filename:
            details["filename"] = filename
        if reason:
            details["reason"] = reason
            
        super().__init__(
            message=message,
            error_code="FILE_UPLOAD_ERROR",
            details=details
        )


class PaymentError(FastAPIShopException):
    """支付异常"""
    
    def __init__(
        self,
        message: str = "Payment processing failed",
        payment_id: Optional[str] = None,
        gateway_response: Optional[Dict[str, Any]] = None
    ):
        details = {}
        if payment_id:
            details["payment_id"] = payment_id
        if gateway_response:
            details["gateway_response"] = gateway_response
            
        super().__init__(
            message=message,
            error_code="PAYMENT_ERROR",
            details=details
        )


class InventoryError(FastAPIShopException):
    """库存异常"""
    
    def __init__(
        self,
        message: str = "Inventory operation failed",
        product_id: Optional[int] = None,
        requested_quantity: Optional[int] = None,
        available_quantity: Optional[int] = None
    ):
        details = {}
        if product_id:
            details["product_id"] = product_id
        if requested_quantity:
            details["requested_quantity"] = requested_quantity
        if available_quantity:
            details["available_quantity"] = available_quantity
            
        super().__init__(
            message=message,
            error_code="INVENTORY_ERROR",
            details=details
        )


class AIError(FastAPIShopException):
    """AI 服务异常"""
    
    def __init__(
        self,
        message: str = "AI service error",
        service: Optional[str] = None,
        model: Optional[str] = None
    ):
        details = {}
        if service:
            details["service"] = service
        if model:
            details["model"] = model
            
        super().__init__(
            message=message,
            error_code="AI_ERROR",
            details=details
        )


def log_exception(exception: Exception, context: Optional[Dict[str, Any]] = None) -> None:
    """
    记录异常日志
    
    Args:
        exception: 异常对象
        context: 上下文信息
    """
    context = context or {}
    
    if isinstance(exception, FastAPIShopException):
        logger.error(
            "Application exception occurred",
            error_code=exception.error_code,
            message=exception.message,
            details=exception.details,
            **context
        )
    else:
        logger.error(
            "Unexpected exception occurred",
            exception_type=type(exception).__name__,
            message=str(exception),
            **context
        )


def create_http_exception(
    exception: FastAPIShopException,
    status_code: int = status.HTTP_400_BAD_REQUEST
) -> HTTPException:
    """
    将应用异常转换为 HTTP 异常
    
    Args:
        exception: 应用异常
        status_code: HTTP 状态码
        
    Returns:
        HTTPException: HTTP 异常对象
    """
    return HTTPException(
        status_code=status_code,
        detail={
            "error_code": exception.error_code,
            "message": exception.message,
            "details": exception.details
        }
    )

