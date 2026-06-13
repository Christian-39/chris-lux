"""
Custom storage backends for OYA.
Supports local storage (development) and Backblaze B2 (production).
"""

from django.conf import settings
from django.core.files.storage import FileSystemStorage
from storages.backends.s3boto3 import S3Boto3Storage


class LocalMediaStorage(FileSystemStorage):
    """Local filesystem storage for development."""
    
    def __init__(self, location=None, base_url=None):
        location = location or settings.MEDIA_ROOT
        base_url = base_url or settings.MEDIA_URL
        super().__init__(location, base_url)


class BackblazeB2Storage(S3Boto3Storage):
    """
    Backblaze B2 cloud media storage using the S3-compatible API wrapper.
    """
    def __init__(self, *args, **kwargs):
        # Enforce target Backblaze B2 operational behaviors
        kwargs["bucket_name"] = getattr(settings, "B2_BUCKET_NAME", "")
        kwargs["endpoint_url"] = getattr(settings, "B2_ENDPOINT_URL", "")
        kwargs["region_name"] = getattr(settings, "B2_BUCKET_REGION", "us-west-004")
        kwargs["signature_version"] = "s3v4"
        kwargs["file_overwrite"] = False
        
        # B2 uses bucket-level visibility; setting object ACLs can throw 400 Bad Request errors.
        kwargs["default_acl"] = None
        kwargs["querystring_auth"] = False
        
        # Target custom domain if present (stripping schemas safely)
        custom_domain = getattr(settings, "B2_CUSTOM_DOMAIN", None)
        if custom_domain:
            kwargs["custom_domain"] = custom_domain.replace("https://", "").replace("http://", "")
            
        super().__init__(*args, **kwargs)