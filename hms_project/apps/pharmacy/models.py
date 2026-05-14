from django.db import models
from django.core.exceptions import ValidationError
from datetime import date


class Medicine(models.Model):
    class Category(models.TextChoices):
        WESTERN = 'western', '西药'
        CHINESE_PATENT = 'chinese_patent', '中成药'
        EXTERNAL = 'external', '外用药'
        INJECTION = 'injection', '注射剂'
        OTHER = 'other', '其他'

    name = models.CharField(max_length=100, verbose_name='药品名称')
    pinyin_code = models.CharField(max_length=50, db_index=True, verbose_name='拼音首字母')
    specification = models.CharField(max_length=100, verbose_name='规格')
    manufacturer = models.CharField(max_length=100, verbose_name='生产厂家')
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='单价')
    stock_quantity = models.PositiveIntegerField(default=0, verbose_name='库存数量')
    warning_stock = models.PositiveIntegerField(default=10, verbose_name='预警库存')
    expiry_date = models.DateField(verbose_name='有效期至')
    category = models.CharField(max_length=50, choices=Category.choices, verbose_name='药品分类')
    is_active = models.BooleanField(default=True, verbose_name='是否启用')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        db_table = 'medicines'
        verbose_name = '药品'
        verbose_name_plural = verbose_name
        ordering = ['name']

    def __str__(self) -> str:
        return f'{self.name} ({self.specification})'

    @property
    def is_low_stock(self) -> bool:
        return self.stock_quantity <= self.warning_stock

    @property
    def is_expiring_soon(self) -> bool:
        return (self.expiry_date - date.today()).days <= 30

    @property
    def is_expired(self) -> bool:
        return self.expiry_date < date.today()

    def clean(self) -> None:
        if self.unit_price < 0:
            raise ValidationError({'unit_price': '单价不能为负数'})
        if self.stock_quantity < 0:
            raise ValidationError({'stock_quantity': '库存数量不能为负数'})


class StockIn(models.Model):
    medicine = models.ForeignKey(
        Medicine,
        on_delete=models.PROTECT,
        related_name='stock_ins',
        verbose_name='药品',
    )
    quantity = models.PositiveIntegerField(verbose_name='入库数量')
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='入库单价')
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, verbose_name='总金额')
    batch_number = models.CharField(max_length=50, verbose_name='批号')
    supplier = models.CharField(max_length=100, blank=True, default='', verbose_name='供应商')
    operator = models.ForeignKey(
        'accounts.User',
        on_delete=models.PROTECT,
        limit_choices_to={'role__in': ['admin', 'pharmacist']},
        related_name='stock_ins',
        verbose_name='操作人',
    )
    note = models.TextField(blank=True, default='', verbose_name='备注')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='入库时间')

    class Meta:
        db_table = 'stock_ins'
        verbose_name = '药品入库'
        verbose_name_plural = verbose_name
        ordering = ['-created_at']

    def __str__(self) -> str:
        return f'{self.medicine.name} 入库 x{self.quantity}'

    def save(self, *args, **kwargs) -> None:
        self.total_amount = self.quantity * self.unit_price
        is_new = self.pk is None
        if is_new:
            self.medicine.stock_quantity += self.quantity
            self.medicine.save(update_fields=['stock_quantity'])
        super().save(*args, **kwargs)


class StockOut(models.Model):
    medicine = models.ForeignKey(
        Medicine,
        on_delete=models.PROTECT,
        related_name='stock_outs',
        verbose_name='药品',
    )
    quantity = models.PositiveIntegerField(verbose_name='出库数量')
    prescription = models.ForeignKey(
        'medical.Prescription',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='stock_outs',
        verbose_name='关联处方',
    )
    operator = models.ForeignKey(
        'accounts.User',
        on_delete=models.PROTECT,
        limit_choices_to={'role__in': ['admin', 'pharmacist']},
        related_name='stock_outs',
        verbose_name='操作人',
    )
    note = models.TextField(blank=True, default='', verbose_name='备注')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='出库时间')

    class Meta:
        db_table = 'stock_outs'
        verbose_name = '药品出库'
        verbose_name_plural = verbose_name
        ordering = ['-created_at']

    def __str__(self) -> str:
        return f'{self.medicine.name} 出库 x{self.quantity}'

    def save(self, *args, **kwargs) -> None:
        is_new = self.pk is None
        if is_new:
            if self.quantity > self.medicine.stock_quantity:
                raise ValidationError(f'{self.medicine.name} 库存不足，当前库存: {self.medicine.stock_quantity}')
            self.medicine.stock_quantity -= self.quantity
            self.medicine.save(update_fields=['stock_quantity'])
        super().save(*args, **kwargs)


class StockCheck(models.Model):
    medicine = models.ForeignKey(
        Medicine,
        on_delete=models.PROTECT,
        related_name='stock_checks',
        verbose_name='药品',
    )
    system_quantity = models.PositiveIntegerField(verbose_name='系统库存')
    actual_quantity = models.PositiveIntegerField(verbose_name='实际库存')
    difference = models.IntegerField(verbose_name='差异数量')
    operator = models.ForeignKey(
        'accounts.User',
        on_delete=models.PROTECT,
        limit_choices_to={'role__in': ['admin', 'pharmacist']},
        related_name='stock_checks',
        verbose_name='盘点人',
    )
    note = models.TextField(blank=True, default='', verbose_name='备注')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='盘点时间')

    class Meta:
        db_table = 'stock_checks'
        verbose_name = '库存盘点'
        verbose_name_plural = verbose_name
        ordering = ['-created_at']

    def __str__(self) -> str:
        return f'{self.medicine.name} 盘点 ({self.created_at:%Y-%m-%d})'

    def save(self, *args, **kwargs) -> None:
        self.difference = self.actual_quantity - self.system_quantity
        super().save(*args, **kwargs)
