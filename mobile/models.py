from django.db import models
from colorfield.fields import ColorField
from PIL import ImageColor


def lighten_color(hex_color, factor=0.7):
        """Lightens the given hex color by the specified factor (0 to 1)."""
        r, g, b = ImageColor.getrgb(hex_color)
        r = int(r + (255 - r) * factor)
        g = int(g + (255 - g) * factor)
        b = int(b + (255 - b) * factor)
        return f'#{r:02x}{g:02x}{b:02x}'


def is_dark_color(hex_color):
    """Returns True if the color is dark (i.e., needs lightening)."""
    r, g, b = ImageColor.getrgb(hex_color)
    brightness = (0.299 * r + 0.587 * g + 0.114 * b)
    return brightness < 180  # threshold between 0 (black) and 255 (white)


class Event(models.Model):
    title = models.CharField(max_length=100)
    banner = models.ImageField(upload_to='event_banners_mobile/')
    home_color = ColorField(default='#ffffff', help_text="Choose any color — it will be automatically converted to a lighter shade when saved.")
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    active = models.BooleanField(default=False)
    default = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title
    
    def save(self, *args, **kwargs):
        original_color = self.home_color
        if self.pk:
            old = Event.objects.get(pk=self.pk)
            if old.home_color != original_color and is_dark_color(original_color):
                self.home_color = lighten_color(original_color)
        else:
            if is_dark_color(original_color):
                self.home_color = lighten_color(original_color)

        if self.default:
            Event.objects.filter(default=True).update(default=False)
        super().save(*args, **kwargs)

    class Meta:
        ordering = ['-start_date']
        

class EventAds(models.Model):
    event = models.ForeignKey(Event, related_name='ads', on_delete=models.CASCADE)
    image = models.ImageField(upload_to='event_ads_mobile/')
    link = models.URLField(max_length=200, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Ad for {self.event.title}"

    class Meta:
        verbose_name = 'Event Ad'
        verbose_name_plural = 'Event Ads'
        ordering = ['-created_at']