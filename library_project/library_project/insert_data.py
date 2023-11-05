from models import (
    BookData,
    Book,
    Author,
    CategoryNames,
    BookCategory,
    Patron,
    Checkout,
    Distance,
    Elevator,
)

# TODO: #2 Figure out how to insert data
def main():
    print(BookData.objects.all().values())
    print(Book.objects.all().values())
    print(Author.objects.all().values())
    print(CategoryNames.objects.all().values())
    print(BookCategory.objects.all().values())
    print(Patron.objects.all().values())
    print(Checkout.objects.all().values())
    print(Distance.objects.all().values())
    print(Elevator.objects.all().values())


if __name__ == "__main__":
    main()


