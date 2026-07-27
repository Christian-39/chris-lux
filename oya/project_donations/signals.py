"""
Cross-app signals for OYA Project Donations.
"""
import logging
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

from .models import Donation

logger = logging.getLogger("oya")


@receiver(post_save, sender=Donation)
def sync_donation_to_finance(sender, instance, created, **kwargs):
    """
    Auto-maintain a linked Income record for confirmed donations.
    Removes the Income if the donation is cancelled or zeroed out.
    """
    if instance.status == "CONFIRMED" and instance.amount and instance.amount > 0:
        _ensure_donation_income(instance)
    else:
        _remove_donation_income(instance)


@receiver(post_delete, sender=Donation)
def cleanup_donation_finance(sender, instance, **kwargs):
    """Delete the linked Income record when a donation is permanently deleted."""
    if instance.income_id:
        try:
            instance.income.delete()
        except Exception:
            pass


def _ensure_donation_income(donation):
    """Create or update the finance Income record for a donation."""
    from finance.models import Income

    # Resolve payer text and (if possible) the linked User for finance.member
    payer_name = "Anonymous"
    member_user = None

    if donation.donor_type == "MEMBER" and donation.member:
        payer_name = donation.member.full_name
        # Adjust this if your Member model links to User differently
        member_user = getattr(donation.member, "user", None)
    elif donation.donor_type == "OUTSIDE" and donation.outside_donor:
        payer_name = donation.outside_donor.full_name

    if donation.income:
        # Update existing income
        donation.income.amount = donation.amount
        donation.income.reason = f"Project Donation — {donation.project.title}"
        donation.income.paid_by = payer_name
        donation.income.income_type = "PROJECT_DONATION"
        if member_user:
            donation.income.member = member_user
        donation.income.save()
    else:
        # Create new income and link back without re-firing signals
        income = Income.objects.create(
            income_type="PROJECT_DONATION",
            amount=donation.amount,
            reason=f"Project Donation — {donation.project.title}",
            paid_by=payer_name,
            member=member_user,
            created_by=donation.recorded_by,
        )
        Donation.objects.filter(pk=donation.pk).update(income=income)


def _remove_donation_income(donation):
    """Unlink and delete the finance Income record."""
    if donation.income_id:
        income = donation.income
        Donation.objects.filter(pk=donation.pk).update(income=None)
        try:
            income.delete()
        except Exception:
            pass