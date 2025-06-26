from django.contrib import admin

# Register your models here.
# Ini biar model Aperd bisa masuk ke admin dan CRUD
from .models import Aperd, Product, AumData

admin.site.register(Aperd)

admin.site.register(Product)

admin.site.register(AumData)