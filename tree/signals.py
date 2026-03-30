"""
Signals für die FamilyTree-App.
Wird in apps.py via ready() geladen.
"""
from django.db.models.signals import post_save
from django.contrib.auth.models import User
from django.dispatch import receiver


@receiver(post_save, sender=User)
def ensure_family_profile(sender, instance, created, **kwargs):
    """
    Stellt sicher, dass jeder User ein FamilyProfile hat.
    Neue User ohne explizite Rollenzuweisung erhalten 'member'.
    Admin-Profil wird separat via setup_admin Command oder Admin-Panel gesetzt.
    """
    from tree.models import FamilyProfile
    if created:
        FamilyProfile.objects.get_or_create(user=instance, defaults={'role': 'member'})
