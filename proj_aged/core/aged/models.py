from django.db import models
from django.contrib.auth.models import User

# Create your models here.
#-------------------------Legate de produs---------------------------
class Brands(models.Model):
    brand = models.CharField(max_length=100)

    def __str__(self):
        return self.brand

    class Meta:
        verbose_name_plural = 'Brands'

class MaterialType(models.Model):
    #chocolate, filling, nuts
    material_type = models.CharField(max_length=100)

    def __str__(self):
        return self.material_type

    class Meta:
        verbose_name_plural = 'Material types (chocolate, nuts, etc)'

class Products(models.Model):
    #product is linked to brand
    #cod material inseamna codul ala din multe litere si cifre
    #produsele nu se sterg din baza de date, nici daca nu mai exista -> sunt folosite in OffersLog
    cod_material = models.CharField(max_length=100)
    description = models.CharField(max_length=200, null=True, blank=True)
    product_brand = models.ForeignKey(Brands, null=True, blank=True, on_delete=models.SET_NULL)
    product_material_type = models.ForeignKey(MaterialType, null=True, blank=True, on_delete=models.SET_NULL)

    def __str__(self):
        return self.cod_material

    class Meta:
        verbose_name_plural = 'Products'

class LocationsForStocks(models.Model):
    location_of_stocks = models.CharField(max_length=100)

    def __str__(self):
        return self.location_of_stocks

    class Meta:
        verbose_name_plural = 'Stock location'

class CustomerService(models.Model):
    """
    Each customer account is linked to a customer care representative.
    Each customer care representative appears on the offer
    """
    customer_service_rep = models.CharField(max_length=100)
    # STATUS_CHOICES = ( ('Active', 'Active'), ('Closed', 'Closed'), ('Inactive', 'Inactive'), )
    # c_serv_status = models.CharField(max_length=10, choices=STATUS_CHOICES)

    def __str__(self):
        return self.customer_service_rep

    class Meta:
        verbose_name_plural = 'Customer service reps'

class Customers(models.Model):
    #each customer is linked to a sales person and a customer care person
    #Customers nu se sterg din baza de date, nici daca nu mai exista -> sunt folosite in OffersLog
    customer_name = models.CharField(max_length=100)
    customer_number = models.IntegerField()
    salesperson_owning_account = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
    allocated_customer_service_rep = models.ForeignKey(CustomerService, null=True, blank=True, on_delete=models.SET_NULL)
    STATUS_CHOICES = ( ('Active', 'Active'), ('Inactive', 'Inactive'), )
    customer_status = models.CharField(max_length=10, choices=STATUS_CHOICES)

    def __str__(self):
        return self.customer_name

    class Meta:
        verbose_name_plural = 'Customers'

class CheckIfFileWasAlreadyUploaded(models.Model):
    """
    This records the date in which the stock file was created
    """
    data_creare_fisier = models.CharField(max_length=30)

    def __str__(self):
        return self.data_creare_fisier

    class Meta:
        verbose_name_plural = 'Date Aged Stock xlsx file was created'

class AvailableStock(models.Model):
    # stock is linked to product and location
    available_product = models.ForeignKey(Products, null=True, blank=True, on_delete=models.SET_NULL) #default='Product was deleted', on_delete=models.SET_DEFAULT
    stock_location = models.ForeignKey(LocationsForStocks, null=True, blank=True, on_delete=models.SET_NULL) # default='Location was deleted', on_delete=models.SET_DEFAULT
    expiration_date = models.DateField()
    batch = models.CharField(max_length = 100)
    original_quantity_in_kg = models.IntegerField()
    under_offer_quantity_in_kg = models.IntegerField(default=0)
    sold_quantity_in_kg = models.IntegerField(default=0)
    available_quantity_in_kg = models.IntegerField()

    def __str__(self):
        return str(self.available_product)

    class Meta:
        verbose_name_plural = 'Available stock'


class OffersLog(models.Model):
    sales_rep_that_made_the_offer = models.ForeignKey(User, null=True, on_delete=models.SET_NULL)
    offered_stock = models.ForeignKey(AvailableStock, null=True, on_delete=models.SET_NULL)
    offered_product = models.ForeignKey(Products, on_delete=models.RESTRICT)
    customer_that_received_offer = models.ForeignKey(Customers, on_delete=models.RESTRICT)
    offered_sold_or_declined_quantity_kg = models.IntegerField()
    STATUS_CHOICES = ( ('Offered', 'Offered'), ('Declined', 'Declined'), ('Sold', 'Sold'), ('Offer Expired', 'Offer Expired'))
    offer_status =  models.CharField(max_length=20, choices=STATUS_CHOICES)
    discount_offered_percents = models.DecimalField(max_digits=5, decimal_places=2)
    price_per_kg_offered = models.DecimalField(max_digits=7, decimal_places=2)
    date_of_offer = models.DateField()
    #expiration date este offer date + 7 zile
    expiration_date_of_offer = models.DateField(null=True, blank=True)
    date_of_outcome = models.DateField(null=True, blank=True)
    stock_expired = models.BooleanField(default=False)

    # def __str__(self):
    #     return self.customer_that_received_offer

    class Meta:
        verbose_name_plural = 'Offers log'

class AFostVerificatAzi(models.Model):
    # in views sunt taskuri care ruleaza automat prin accesarea unor url-uri
    # ca sa nu ruleze codul ori de de cate ori e accesat url-ul pun un if
    # care verifica daca azi s-a rulat codul respectiv
    expiredOferedStock = models.DateField()

    def __str__(self):
        return str(self.expiredOferedStock)

    class Meta:
        verbose_name_plural = 'Verificare prin data'
