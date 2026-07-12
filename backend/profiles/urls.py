from django.urls import path

from .views import AvatarUploadView, ProfileView, AdminProfileListView

urlpatterns = [
    path('avatar/', AvatarUploadView.as_view(), name='profile_avatar'),
    path('admin/users/', AdminProfileListView.as_view(), name='admin_profile_list'),
    path('<str:section>/', ProfileView.as_view(), name='profile_section_update'),
    path('', ProfileView.as_view(), name='profile_detail'),
]
