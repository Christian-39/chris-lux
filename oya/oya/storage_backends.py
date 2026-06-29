"""
Custom storage backends for OYA.
Supports local storage (development) and Backblaze B2 (production).
"""

from django.conf import settings
from django.core.files.storage import FileSystemStorage
from storages.backends.s3 import S3Storage


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
    """
    
    # Class-level defaults - these MUST be set as class attributes
    # for django-storages to pick them up properly
    bucket_name = getattr(settings, "B2_BUCKET_NAME", "")
    endpoint_url = getattr(settings, "B2_ENDPOINT_URL", "")
    region_name = getattr(settings, "B2_BUCKET_REGION", "us-west-004")
    signature_version = "s3v4"
    file_overwrite = False
    default_acl = None
    querystring_auth = False
    addressing_style = "virtual"
    
    # B2-specific: disable ACL completely
    # This prevents boto3 from sending x-amz-acl headers
    object_parameters = {}
    
    # Custom domain for public URLs
    custom_domain = getattr(settings, "B2_CUSTOM_DOMAIN", None)
    if custom_domain:
        custom_domain = custom_domain.replace("https://", "").replace("http://", "")
    
    def get_default_settings(self):
        """Override to inject B2-specific settings."""
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
            "custom_domain": self.custom_domain,
            "object_parameters": self.object_parameters,
        }
    
    def get_object_parameters(self, name):
        """
        Override to NEVER send ACL parameters.
        B2 does not support per-object ACLs.
        """
        # Return empty dict - no ACL headers ever
        return {}
    
    def _get_write_parameters(self, name, content=None):
        """
        Override to ensure no ACL is sent with PUT/POST requests.
        """
        params = super()._get_write_parameters(name, content)
        # Strip ACL from write operations
        params.pop("ACL", None)
        params.pop("acl", None)
        return params
    
    def exists(self, name):
        """
        Override exists() to handle B2's quirks with head_object.
        B2 returns 403 instead of 404 for non-existent objects in some cases.
        """
        if not name:
            return False
        try:
            return super().exists(name)
        except Exception as e:
            error_msg = str(e).lower()
            # B2 returns 403 for non-existent objects sometimes
            # Also handle 404 properly
            if "404" in error_msg or "not found" in error_msg:
                return False
            if "403" in error_msg or "forbidden" in error_msg:
                # Object likely doesn't exist, B2 is just being weird
                return False
            # Re-raise if it's a real error
            raise
