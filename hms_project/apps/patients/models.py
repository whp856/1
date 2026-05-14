from django.db import models


class Patient(models.Model):
    class Gender(models.TextChoices):
        MALE = 'male', '男'
        FEMALE = 'female', '女'

    id_card = models.CharField(max_length=18, unique=True, verbose_name='身份证号')
    name = models.CharField(max_length=50, verbose_name='姓名')
    gender = models.CharField(max_length=10, choices=Gender.choices, verbose_name='性别')
    age = models.PositiveIntegerField(verbose_name='年龄')
    phone = models.CharField(max_length=20, verbose_name='联系电话')
    allergy_history = models.TextField(blank=True, default='', verbose_name='过敏史')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='建档时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        db_table = 'patients'
        verbose_name = '患者'
        verbose_name_plural = verbose_name
        ordering = ['-created_at']

    def __str__(self) -> str:
        return f'{self.name} ({self.id_card})'
