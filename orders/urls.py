from django.urls import path
from . import views

urlpatterns = [
    path('place_order/', views.place_order, name='place_order'),
    path('payments/', views.payments, name='payments'),
    path('order_complete/', views.order_complete, name='order_complete'),
    path('new_order/', views.create_order, name='create_order'),
    path('new_order/<str:order_id>/capture/', views.capture_order, name='capture_order'),
]