from django.db import models


class Prescription(models.Model):
    class Status(models.TextChoices):
        PENDING = 'pending', '待缴费'
        PAID = 'paid', '已缴费'
        DISPENSED = 'dispensed', '已发药'
        CANCELLED = 'cancelled', '已取消'
        EXPIRED = 'expired', '已过期'

    appointment = models.OneToOneField(
        'appointments.Appointment',
        on_delete=models.PROTECT,
        related_name='prescription',
        verbose_name='关联挂号',
    )
    patient = models.ForeignKey(
        'patients.Patient',
        on_delete=models.PROTECT,
        related_name='prescriptions',
        verbose_name='患者',
    )
    doctor = models.ForeignKey(
        'accounts.User',
        on_delete=models.PROTECT,
        limit_choices_to={'role': 'doctor'},
        related_name='prescriptions',
        verbose_name='开方医生',
    )
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name='总金额')
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        verbose_name='处方状态',
    )
    payment_time = models.DateTimeField(null=True, blank=True, verbose_name='支付时间')
    dispense_time = models.DateTimeField(null=True, blank=True, verbose_name='发药时间')
    pharmacist = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        limit_choices_to={'role': 'pharmacist'},
        related_name='dispensed_prescriptions',
        verbose_name='发药药剂师',
    )
    note = models.TextField(blank=True, default='', verbose_name='备注')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='开方时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        db_table = 'prescriptions'
        verbose_name = '处方'
        verbose_name_plural = verbose_name
        ordering = ['-created_at']

    def __str__(self) -> str:
        return f'{self.patient.name} 处方 #{self.id}'

    def calculate_total(self) -> None:
        total = self.items.aggregate(total=models.Sum('subtotal'))['total'] or 0
        self.total_amount = total
        self.save(update_fields=['total_amount'])


class PrescriptionItem(models.Model):
    prescription = models.ForeignKey(
        Prescription,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name='处方',
    )
    medicine = models.ForeignKey(
        'pharmacy.Medicine',
        on_delete=models.PROTECT,
        related_name='prescription_items',
        verbose_name='药品',
    )
    quantity = models.PositiveIntegerField(verbose_name='数量')
    dosage = models.CharField(max_length=100, verbose_name='用法用量')
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='单价')
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='小计')

    class Meta:
        db_table = 'prescription_items'
        verbose_name = '处方明细'
        verbose_name_plural = verbose_name

    def __str__(self) -> str:
        return f'{self.medicine.name} x{self.quantity}'

    def save(self, *args, **kwargs) -> None:
        self.subtotal = self.quantity * self.unit_price
        super().save(*args, **kwargs)
