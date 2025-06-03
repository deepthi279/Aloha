
from django.urls import path  # type: ignore
from .views import (
    clientsView, 
    ProviderView,
    ScheduleView,
    LoginView,
    SignUpView,
    ForgotPasswordView,
    ResetPasswordView,
    AuthorizationView,
    AuthorizationExpiryView,
    ContactViewByClientsID

   
    
    
    
)

urlpatterns = [
    path('clients/', clientsView.as_view(), name='clients'),
    path('clients/<str:Alias>/', clientsView.as_view(), name='client_by_name'),
    path('Provider/', ProviderView.as_view(), name='Provider_by_list'),  # GET all, POST new provider
    path('Provider/<str:alias>/', ProviderView.as_view(), name='Provider_by_name'),  # GET, PUT, DELETE by alias
    path('Schedule/', ScheduleView.as_view(), name='Schedule_list'),
    path('login/', LoginView.as_view(), name='login'),
    path('SignUp/', SignUpView.as_view(), name='SignUp'),
    path('forgot-password/', ForgotPasswordView.as_view(), name='forgot-password'),
    path('reset-password/', ResetPasswordView.as_view(), name='reset_password'),
    path('authorization/', AuthorizationView.as_view(), name='authorization'),
    path('authorization/expiring-soon/', AuthorizationExpiryView.as_view(), name='authorization-expiring-soon'),
    path('contacts/<int:clients_id>/', ContactViewByClientsID.as_view(),name='contacts'),


]
