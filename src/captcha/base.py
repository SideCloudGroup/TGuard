"""Abstract base class for captcha providers."""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class CaptchaVerificationResult:
    """Result of captcha verification."""
    success: bool
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    score: Optional[float] = None  # For services that provide confidence scores
    challenge_ts: Optional[str] = None  # Timestamp of challenge
    hostname: Optional[str] = None
    extra_data: Optional[Dict[str, Any]] = None


class CaptchaProvider(ABC):
    """Abstract base class for captcha providers."""
    
    def __init__(self, site_key: str, secret_key: str, timeout: int = 30):
        """Initialize captcha provider.
        
        Args:
            site_key: Public site key for frontend
            secret_key: Secret key for backend verification
            timeout: HTTP timeout in seconds
        """
        self.site_key = site_key
        self.secret_key = secret_key
        self.timeout = timeout
    
    @abstractmethod
    async def verify(
        self,
        response: str,
        remote_ip: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> CaptchaVerificationResult:
        """Verify captcha response.
        
        Args:
            response: The captcha response token from frontend
            remote_ip: User's IP address (optional)
            user_agent: User's user agent (optional)
            
        Returns:
            CaptchaVerificationResult with verification status and details
        """
        pass
    
    @abstractmethod
    def get_frontend_config(self) -> Dict[str, Any]:
        """Get configuration for frontend integration.
        
        Returns:
            Dictionary containing frontend configuration
        """
        pass
    
    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Get provider name."""
        pass
