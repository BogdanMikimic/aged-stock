from django.urls import path, include
from . import views

urlpatterns = [
            path('', views.homepage, name='home'),
	        path('accounts/', include('django.contrib.auth.urls')),
            path('superuserreports/', views.superuserreports, name='superuserreports'),
            path('userseallstock/', views.userseallstock, name='userseallstock'),
            path('usersmakeoffer/<str:itm_id>', views.usersmakeoffer, name='usersmakeoffer'),
            path('notenoughstock/<str:stockId>', views.notenoughstock, name='notenoughstock'),
            path('userawesomeoffer/<str:offerId>', views.userawesomeoffer, name='userawesomeoffer'),
            path('userpendingoffers/', views.userpendingoffers, name='userpendingoffers'),
            path('fileupload/', views.fileupload, name='fileupload'),
            path('salespeopleupload/', views.salespeopleupload, name='salespeopleupload'),
            path('agedstockupload/', views.agedstockupload, name='agedstockupload'),
            path('task1/', views.task1),
            path('changeofferedstatus/<str:offer_id>', views.changeofferedstatus, name='changeofferedstatus'),
            path('changeoffer/<str:offer_id>/<str:mess>', views.changeoffer, name='changeoffer'),
            path('help/', views.help, name='help'),

]
