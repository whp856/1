from django.db import models


class Appointment(models.Model):
    class Status(models.TextChoices):
        PENDING = 'pending', '待就诊'
        COMPLETED = 'completed', '已就诊'
        CANCELLED = 'cancelled', '已取消'
        EXPIRED = 'expired', '已过期'

    class PaymentMethod(models.TextChoices):
        CASH = 'cash', '现金'
        WECHAT = 'wechat', '微信'
        ALIPAY = 'alipay', '支付宝'

    patient = models.ForeignKey(
        'patients.Patient',
        on_delete=models.PROTECT,
        related_name='appointments',
        verbose_name='患者',
    )
    doctor = models.ForeignKey(
        'accounts.User',
        on_delete=models.PROTECT,
        limit_choices_to={'role': 'doctor', 'is_active': True},
        related_name='doctor_appointments',
        verbose_name='医生',
    )
    department = models.ForeignKey(
        'departments.Department',
        on_delete=models.PROTECT,
        related_name='appointments',
        verbose_name='科室',
    )
    appointment_date = models.DateField(verbose_name='就诊日期')
    appointment_time = models.TimeField(verbose_name='就诊时段')
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        verbose_name='挂号状态',
    )
    fee = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='挂号费')
    payment_status = models.BooleanField(default=False, verbose_name='支付状态')
    payment_method = models.CharField(
        max_length=20,
        choices=PaymentMethod.choices,
        blank=True,
        default='',
        verbose_name='支付方式',
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='挂号时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        db_table = 'appointments'
        verbose_name = '挂号'
        verbose_name_plural = verbose_name
        ordering = ['-appointment_date', '-appointment_time']
        indexes = [
            models.Index(fields=['appointment_date', 'status']),
            models.Index(fields=['doctor', 'appointment_date']),
        ]

    def __str__(self) -> str:
        return f'{self.patient.name} - {self.doctor.get_full_name()} ({self.appointment_date})'

    def can_cancel(self) -> bool:
        if self.status != self.Status.PENDING:
            return False
        from datetime import datetime, timedelta
        from django.utils import timezone
        appt_dt = datetime.combine(self.appointment_date, self.appointment_time)
        appt_dt = timezone.make_aware(appt_dt)
        return timezone.now() + timedelta(minutes=30) < appt_dt


class DoctorSchedule(models.Model):
    doctor = models.ForeignKey(
        'accounts.User',
        on_delete=models.CASCADE,
        limit_choices_to={'role': 'doctor', 'is_active': True},
        related_name='schedules',
        verbose_name='医生',
    )
    date = models.DateField(verbose_name='排班日期')
    max_patients = models.PositiveIntegerField(default=30, verbose_name='最大号源数')
    current_patients = models.PositiveIntegerField(default=0, verbose_name='已挂号数')
    is_available = models.BooleanField(default=True, verbose_name='是否可挂号')

    class Meta:
        db_table = 'doctor_schedules'
        verbose_name = '医生排班'
        verbose_name_plural = verbose_name
        unique_together = ['doctor', 'date']
        ordering = ['date']

    def __str__(self) -> str:
        return f'{self.doctor.get_full_name()} - {self.date} ({self.current_patients}/{self.max_patients})'

    @property
    def remaining(self) -> int:
        return max(0, self.max_patients - self.current_patients)

    @property
    def is_full(self) -> bool:
        return self.current_patients >= self.max_patients
