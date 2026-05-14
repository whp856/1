from django.db import models
from apps.medical.prescription_models import Prescription, PrescriptionItem

__all__ = ['MedicalRecord', 'NursingRecord', 'Prescription', 'PrescriptionItem']


class MedicalRecord(models.Model):
    appointment = models.OneToOneField(
        'appointments.Appointment',
        on_delete=models.PROTECT,
        related_name='medical_record',
        verbose_name='关联挂号',
    )
    patient = models.ForeignKey(
        'patients.Patient',
        on_delete=models.PROTECT,
        related_name='medical_records',
        verbose_name='患者',
    )
    doctor = models.ForeignKey(
        'accounts.User',
        on_delete=models.PROTECT,
        limit_choices_to={'role': 'doctor'},
        related_name='medical_records',
        verbose_name='医生',
    )
    chief_complaint = models.TextField(verbose_name='主诉')
    present_illness = models.TextField(blank=True, default='', verbose_name='现病史')
    past_history = models.TextField(blank=True, default='', verbose_name='既往史')
    physical_examination = models.TextField(blank=True, default='', verbose_name='体格检查')
    diagnosis = models.TextField(verbose_name='诊断结果')
    treatment_plan = models.TextField(blank=True, default='', verbose_name='治疗方案')
    advice = models.TextField(blank=True, default='', verbose_name='医嘱建议')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        db_table = 'medical_records'
        verbose_name = '电子病历'
        verbose_name_plural = verbose_name
        ordering = ['-created_at']

    def __str__(self) -> str:
        return f'{self.patient.name} - {self.created_at:%Y-%m-%d %H:%M}'


class NursingRecord(models.Model):
    class ExecutionStatus(models.TextChoices):
        PENDING = 'pending', '待执行'
        EXECUTED = 'executed', '已执行'
        CANCELLED = 'cancelled', '已取消'

    appointment = models.ForeignKey(
        'appointments.Appointment',
        on_delete=models.PROTECT,
        related_name='nursing_records',
        verbose_name='关联挂号',
    )
    patient = models.ForeignKey(
        'patients.Patient',
        on_delete=models.PROTECT,
        related_name='nursing_records',
        verbose_name='患者',
    )
    nurse = models.ForeignKey(
        'accounts.User',
        on_delete=models.PROTECT,
        limit_choices_to={'role': 'nurse'},
        related_name='nursing_records',
        verbose_name='执行护士',
    )
    temperature = models.DecimalField(
        max_digits=4, decimal_places=1, null=True, blank=True, verbose_name='体温(℃)',
    )
    blood_pressure = models.CharField(max_length=20, blank=True, default='', verbose_name='血压(mmHg)')
    heart_rate = models.PositiveIntegerField(null=True, blank=True, verbose_name='心率(次/分)')
    medical_order = models.TextField(verbose_name='医嘱内容')
    execution_status = models.CharField(
        max_length=20,
        choices=ExecutionStatus.choices,
        default=ExecutionStatus.PENDING,
        verbose_name='执行状态',
    )
    note = models.TextField(blank=True, default='', verbose_name='护理备注')
    executed_at = models.DateTimeField(null=True, blank=True, verbose_name='执行时间')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')

    class Meta:
        db_table = 'nursing_records'
        verbose_name = '护理记录'
        verbose_name_plural = verbose_name
        ordering = ['-created_at']

    def __str__(self) -> str:
        return f'{self.patient.name} 护理记录 ({self.get_execution_status_display()})'
