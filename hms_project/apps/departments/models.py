from django.db import models


class Department(models.Model):
    name = models.CharField(max_length=50, unique=True, verbose_name='科室名称')
    description = models.TextField(blank=True, default='', verbose_name='科室描述')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')

    class Meta:
        db_table = 'departments'
        verbose_name = '科室'
        verbose_name_plural = verbose_name
        ordering = ['name']

    def __str__(self) -> str:
        return self.name
