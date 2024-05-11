from django.contrib import admin
from .models import *

# Register your models here.
@admin.register(Brands)
class BrandsAdmin(admin.ModelAdmin):
    list_display = ('brand',)

@admin.register(MaterialType)
class MaterialTypeAdmin(admin.ModelAdmin):
    list_display = ('material_type',)

@admin.register(Products)
class ProductsAdmin(admin.ModelAdmin):
    list_display = ('cod_material', 'description', 'id')
    search_fields = ('cod_material','description')

@admin.register(LocationsForStocks)
class LocationsForStocksAdmin(admin.ModelAdmin):
    list_display = ('location_of_stocks',)


@admin.register(CustomerService)
class CustomerServiceAdmin(admin.ModelAdmin):
    list_display = ('customer_service_rep',)

@admin.register(Customers)
class CustomersAdmin(admin.ModelAdmin):
    list_display = ('customer_name','id','salesperson_owning_account')

@admin.register(AvailableStock)
class AvailableStockAdmin(admin.ModelAdmin):
    list_display = ('id','available_product', 'available_quantity_in_kg', 'expiration_date', 'original_quantity_in_kg', 'under_offer_quantity_in_kg', 'sold_quantity_in_kg', 'available_quantity_in_kg' )
    search_fields = ('available_product__cod_material', )

@admin.register(OffersLog)
class OffersLogAdmin(admin.ModelAdmin):
    readonly_fields = ('date_of_offer', )
    list_display = ('id', 'offered_product', 'sales_rep_that_made_the_offer', 'offer_status', 'expiration_date_of_offer' )
    search_fields = ('offered_stock',)

@admin.register(CheckIfFileWasAlreadyUploaded)
class CheckIfFileWasAlreadyUploadedAdmin(admin.ModelAdmin):
    list_display = ('data_creare_fisier',)

@admin.register(AFostVerificatAzi)
class AFostVerificatAziAdmin(admin.ModelAdmin):
    list_display = ('expiredOferedStock',)
