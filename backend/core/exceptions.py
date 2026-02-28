class SkillHubException(Exception):
    """Base exception for all custom errors"""
    pass

class AuthException(SkillHubException):
    """Authentication/authorization errors"""
    pass

class NotFoundException(SkillHubException):
    """Resource not found"""
    pass

class ValidationException(SkillHubException):
    """Input validation errors"""
    pass

class BusinessException(SkillHubException):
    """Business logic errors"""
    pass
