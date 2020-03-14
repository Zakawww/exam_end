from django.contrib.auth.models import User
from django.db import models
from django.urls import reverse


class File(models.Model):
    name = models.CharField(max_length=100, verbose_name='Название')
    created_at = models.DateField(auto_now_add=True, verbose_name='Дата создания')
    author = models.ForeignKey(User, null=True, blank=True, related_name='files', on_delete=models.CASCADE, verbose_name='Автор')
    file = models.FileField(upload_to='files', verbose_name='Файл')

    def get_absolute_url(self):
        return reverse('file_detail', args=[str(self.id)])

    def __str__(self):
        return self.name
