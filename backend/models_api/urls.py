from django.urls import path
from .views import get_features_view, train_model_view, training_status_view, models_registry_view

urlpatterns = [
    path("get/", get_features_view),
    path("train/", train_model_view),
    path("train/status/<str:task_id>/", training_status_view),
    path("registry/", models_registry_view),
]
