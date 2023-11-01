from django.db import models


class BookData(models.Model):
    ISBN = models.CharField(max_length=12, primary_key=True)

class Book(models.Model):
    DecimalCode = models.CharField(max_length=12, primary_key=True)
    ISBN = models.CharField(max_length=13, foreign_key=True)
    Status = models.IntegerField()
