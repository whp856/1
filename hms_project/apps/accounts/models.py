from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    class Role(models.TextChoices):
        ADMIN = 'admin', '系统管理员'
        DOCTOR = 'doctor', '医生'
        NURSE = 'nurse', '护士'
        PHARMACIST = 'pharmacist', '药剂师'

    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.DOCTOR,
        verbose_name='角色',
    )
    full_name = models.CharField(max_length=50, default='', verbose_name='真实姓名')
    department = models.ForeignKey(
        'departments.Department',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='users',
        verbose_name='所属科室',
    )
    phone = models.CharField(max_length=20, blank=True, default='', verbose_name='联系电话')
    is_active = models.BooleanField(default=True, verbose_name='是否启用')

    class Meta:
        db_table = 'users'
        verbose_name = '用户'
        verbose_name_plural = verbose_name
        ordering = ['-date_joined']

    def __str__(self) -> str:
        return f'{self.full_name} ({self.get_role_display()})'

    def get_full_name(self) -> str:
        return self.full_name or self.username

    @property
    def is_admin(self) -> bool:
        return self.role == self.Role.ADMIN

    @property
    def is_doctor(self) -> bool:
        return self.role == self.Role.DOCTOR

    @property
    def is_nurse(self) -> bool:
        return self.role == self.Role.NURSE

    @property
    def is_pharmacist(self) -> bool:
        return self.role == self.Role.PHARMACIST
