from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from .models import User, UserProfile


@receiver(post_save, sender=User)
def post_save_create_profile_receiver(sender, instance, created, **kwargs):
    print(created)
    if created:
        print("instance====> ",instance)
        print("instance role====> ",instance.role)
        UserProfile.objects.create(
            user=instance,
            profile_picture='vendor/profile_and_cover_default/default-profile-new.png',
            cover_photo='vendor/profile_and_cover_default/vendor-header-bg.png'
        )
    else:
        try:
            profile = UserProfile.objects.get(user=instance)
            profile.save()
        except:
            # Create the userprofile if not exist
            UserProfile.objects.create(
            user=instance,
            profile_picture='vendor/profile_and_cover_default/default-profile-new.png',
            cover_photo='vendor/profile_and_cover_default/vendor-header-bg.png'
        )


@receiver(pre_save, sender=User)
def pre_save_profile_receiver(sender, instance, **kwargs):
    pass
# post_save.connect(post_save_create_profile_receiver, sender=User)