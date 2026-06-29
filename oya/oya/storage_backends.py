"""
Custom storage backends for OYA.
Supports local storage (development) and Backblaze B2 (production).
"""

from django.conf import settings
from django.core.files.storage import FileSystemStorage
from storages.backends.s3 import S3Storage
from botocore.exceptions import ClientError


class LocalMediaStorage(FileSystemStorage):
    """Local filesystem storage for development."""
    
    def __init__(self, location=None, base_url=None):
        location = location or settings.MEDIA_ROOT
        base_url = base_url or settings.MEDIA_URL
        super().__init__(location, base_url)


class BackblazeB2Storage(S3Storage):
    """
    Backblaze B2 cloud media storage using the S3-compatible API.
    Fixed for django-storages >= 1.14 with proper B2 addressing.
    
    Fixes:
    - 403 Forbidden on head_object (exists check) by catching permission errors
    - Proper custom_domain handling in get_default_settings()
    - Ensures no ACL parameters are sent to B2
    """
    
    # Class-level defaults
    bucket_name = getattr(settings, "B2_BUCKET_NAME", "")
    endpoint_url = getattr(settings, "B2_ENDPOINT_URL", "")
    region_name = getattr(settings, "B2_BUCKET_REGION", "us-west-004")
    signature_version = "s3v4"
    file_overwrite = False
    default_acl = None
    querystring_auth = False
    addressing_style = "virtual"
    
    def get_default_settings(self):
        """Override to inject B2-specific settings."""
        # Handle custom_domain properly - strip protocol if present
        custom_domain = getattr(settings, "B2_CUSTOM_DOMAIN", None)
        if custom_domain:
            custom_domain = custom_domain.replace("https://", "").replace("http://", "")
        
        return {
            **super().get_default_settings(),
            "bucket_name": self.bucket_name,
            "endpoint_url": self.endpoint_url,
            "region_name": self.region_name,
            "signature_version": self.signature_version,
            "file_overwrite": self.file_overwrite,
            "default_acl": self.default_acl,
            "querystring_auth": self.querystring_auth,
            "addressing_style": self.addressing_style,
            "custom_domain": custom_domain,
        }
    
    def exists(self, name):
        """
        Override to handle B2 403 Forbidden on head_object.
        
        Backblaze B2 may return 403 if the application key lacks 'readFiles'
        permission. We catch this and treat it as "file does not exist",
        allowing the upload to proceed.
        
        Also handles 404 (Not Found) which is the normal "doesn't exist" case.
        """
        try:
            return super().exists(name)
        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "Unknown")
            error_message = e.response.get("Error", {}).get("Message", "").lower()
            
            # Treat 403 Forbidden as "does not exist" so save can proceed
            # This happens when the B2 key lacks readFiles permission
            if error_code in ("403", "Forbidden", "AccessDenied"):
                return False
            
            # 404 NotFound is normal - file doesn't exist
            if error_code in ("404", "NotFound", "NoSuchKey"):
                return False
            
            # Re-raise any other unexpected errors
            raise
    
    def get_object_parameters(self, name):
        """
        Override to NEVER send ACL parameters.
        B2 does not support per-object ACLs.
        """
        return {}
    
    def _get_write_parameters(self, name, content=None):
        """
        Override to ensure no ACL is sent with PUT/POST requests.
        """
        params = super()._get_write_parameters(name, content)
        params.pop("ACL", None)
        params.pop("acl", None)
        return params
