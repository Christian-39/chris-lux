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
    
    # Class-level defaults
    bucket_name = getattr(settings, "B2_BUCKET_NAME", "")
    endpoint_url = getattr(settings, "B2_ENDPOINT_URL", "")
    region_name = getattr(settings, "B2_BUCKET_REGION", "us-west-004")
    signature_version = "s3v4"
    file_overwrite = False
    default_acl = None
    querystring_auth = False
    addressing_style = "virtual"
    
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
        }
    
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
