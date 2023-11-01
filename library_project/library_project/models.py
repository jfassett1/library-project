from django.db import models

# TODO: #1 Figure out how to do composite keys for models
class BookData(models.Model):
    ISBN = models.CharField(max_length=13, primary_key=True)
    Title = models.CharField(max_length=65)
    PublishDate = models.PositiveSmallIntegerField(blank=True, null=True)
    Publisher = models.CharField(max_length=20, blank=True, null=True)
    Description = models.TextField(blank=True)

class Book(models.Model):
    DecimalCode = models.CharField(max_length=12, primary_key=True)
    ISBN = models.ForeignKey(BookData, on_delete=models.CASCADE)
    Status = models.SmallIntegerField()

class Author(models.Model):
    ISBN = models.ForeignKey(BookData, on_delete=models.CASCADE)
    DOB = models.DateField()
    Name = models.CharField(max_length=50)
    # primary_key = models.CompositeKey('ISBN', 'DOB')

class CategoryNames(models.Model):
    CategoryID = models.PositiveIntegerField(primary_key=True)
    Name = models.CharField(max_length=35)

class BookCategory(models.Model):
    CategoryID = models.ForeignKey(CategoryNames, on_delete=models.CASCADE)
    ISBN = models.ForeignKey(BookData, on_delete=models.CASCADE)
    # primary_key = models.CompositeKey('CategoryID', 'ISBN')

class Patron(models.Model):
    AccID = models.AutoField(primary_key=True)
    Name = models.CharField(max_length=50)
    Address = models.CharField(max_length=100)
    Email = models.EmailField(max_length=40)

class Checkout(models.Model):
    Patron = models.ForeignKey(Patron, on_delete=models.CASCADE)
    Book = models.ForeignKey(Book, on_delete=models.CASCADE)
    Out = models.DateTimeField()
    Due = models.DateField()
    # primary_key = models.CompositeKey('Patron', 'Book')

class Distance(models.Model):
    Floor = models.PositiveSmallIntegerField()
    Shelf1 = models.PositiveSmallIntegerField()
    Shelf2 = models.PositiveSmallIntegerField()
    Dist = models.FloatField()
    # primary_key = models.CompositeKey('Shelf1', 'Shelf2')

class Elevator(models.Model):
    ID = models.CharField(max_length=8)
    Floor = models.PositiveSmallIntegerField()
    Wait = models.TimeField()
    # primary_key = models.CompositeKey('ID', 'Floor')
