from django.contrib import admin
from apps.pharmacy.models import Medicine, StockIn, StockOut, StockCheck

@admin.register(Medicine)
class MedicineAdmin(admin.ModelAdmin):
    list_display = ['name', 'specification', 'category', 'unit_price', 'stock_quantity', 'expiry_date']
    list_filter = ['category', 'is_active']
    search_fields = ['name', 'pinyin_code']

@admin.register(StockIn)
class StockInAdmin(admin.ModelAdmin):
    list_display = ['medicine', 'quantity', 'batch_number', 'operator', 'created_at']

@admin.register(StockOut)
class StockOutAdmin(admin.ModelAdmin):
    list_display = ['medicine', 'quantity', 'prescription', 'operator', 'created_at']

@admin.register(StockCheck)
class StockCheckAdmin(admin.ModelAdmin):
    list_display = ['medicine', 'system_quantity', 'actual_quantity', 'difference', 'operator', 'created_at']
