from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator

# Create your models here.

class Aperd(models.Model):
    name = models.CharField(max_length=200)
    pic = models.CharField(max_length=500)

    progress_choice = [
        ('On Board', 'On Board'),
        ('OPS Memo', 'OPS Memo'),
        ('MPD', 'MPD'),
        ('Next Action', 'Next Action'),
        ('PKS', 'PKS'),
        ('PKS 2', 'PKS 2'),
        ('Resiprokal Transaksi', 'Resiprokal Transaksi')
    ]

    progress = models.CharField(max_length=200, choices=progress_choice, default=None)
    desc = models.TextField(null=True, blank=True)

    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name
    
class Product(models.Model):
    name = models.CharField(max_length=200)

    status_choice = [
        ('New', 'New'),
        ('In Progress', 'In Progress'),
        ('Under Review', 'Under Review'),
        ('Published', 'Published'),
        ('Freeze', 'Freeze'),
        ('Paused', 'Paused'),
    ]

    status = models.CharField(max_length=200, choices=status_choice, default=None)
    desc = models.TextField(null=True, blank=True, verbose_name="Description")

    aperd = models.ManyToManyField(Aperd)

    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

class AumData(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    date = models.DateField()
    aum = models.DecimalField(
        max_digits=20, 
        decimal_places=2,
        validators=[MinValueValidator(0)],
        verbose_name="Asset Under Management (IDR)"
    )
    aperd = models.ForeignKey(Aperd, on_delete=models.CASCADE, verbose_name="APERD SA")
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['date']

        # can't have the same data based on its date
        # (not used)
        # unique_together = ['product', 'date']

    def __str__(self):
        return f"{self.product.name} - {self.date.strftime('%Y-%m-%d')} (APERD: {self.aperd.name})"
