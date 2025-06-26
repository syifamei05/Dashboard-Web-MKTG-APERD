from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.loginPage, name='login'),
    path('logout/', views.logoutUser, name='logout'),  

    path('', views.home, name='home'),

    path('aperd/<str:pk>/', views.aperd, name='aperd'),

    path('addAperd/', views.addAperd, name='add-aperd'),
    path('editAperd/<str:pk>/', views.editAperd, name='edit-aperd'),
    path('deleteAperd/<str:pk>/', views.deleteAperd, name='delete-aperd'),

    path('product/<str:pk>/', views.product, name='product'),
    
    path('addProduct/', views.addProduct, name='add-product'),
    path('editProduct/<str:pk>/', views.editProduct, name='edit-product'),
    path('deleteProduct/<str:pk>/', views.deleteProduct, name='delete-product'),

    path('product/<str:pk>/data/add/', views.add_product_data, name='add-product-data'),
    path('product/<str:pk>/data/<str:data_pk>/edit/', views.edit_product_data, name='edit-product-data'),
    path('product/<str:pk>/data/<str:data_pk>/delete/', views.delete_product_data, name='delete-product-data'),
]