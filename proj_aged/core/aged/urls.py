from django.urls import path, include
from . import views

urlpatterns = [
            path('', views.homepage, name='home'),
	        path('accounts/', include('django.contrib.auth.urls')),
            path('superuser_reports/', views.superuser_reports, name='superuser_reports'),
            path('all_available_stock/', views.all_available_stock, name='all_available_stock'),
            path('make_offer/<str:itm_id>', views.make_offer, name='make_offer'),
            path('not_enough_stock/<str:stock_id>', views.not_enough_stock, name='not_enough_stock'),
            path('offer_completed/<str:offer_id>', views.offer_completed, name='offer_completed'),
            path('existing_offers/', views.existing_offers, name='existing_offers'),
            path('upload_files/', views.upload_files, name='upload_files'),
            path('upload_file_with_sales_people/', views.upload_file_with_sales_people, name='upload_file_with_sales_people'),
            path('upload_file_with_aged_stock/', views.upload_file_with_aged_stock, name='upload_file_with_aged_stock'),
            path('task1/', views.task1),
            path('change_offer_status/<str:offer_id>', views.change_offer_status, name='change_offer_status'),
            path('modify_existing_offer/<str:offer_id>/<str:mess>', views.modify_existing_offer, name='modify_existing_offer'),
            path('stock_help/', views.stock_help, name='help'),

]
