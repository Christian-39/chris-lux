"""
Account Tokens - Email Verification and Password Reset Tokens
"""
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils import timezone
import six


class AccountActivationTokenGenerator(PasswordResetTokenGenerator):
    """Token generator for account activation"""
    
    def _make_hash_value(self, user, timestamp):
        return (
            six.text_type(user.pk) +
            six.text_type(timestamp) +
            six.text_type(user.email_verified)
        )


account_activation_token = AccountActivationTokenGenerator()
