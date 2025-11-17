from collections import UserDict
from datetime import datetime, timedelta
import pickle


class Field:
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return str(self.value)


class Name(Field):
    pass


class Phone(Field):
    def __init__(self, value):
        if not self.validate(value):
            raise ValueError("Phone number must be 10 digits.")
        super().__init__(value)
    
    @staticmethod
    def validate(value):
        return len(value) == 10 and value.isdigit()


class Birthday(Field):
    def __init__(self, value):
        try:
            self.value = datetime.strptime(value, "%d.%m.%Y")
        except ValueError:
            raise ValueError("Invalid date format. Use DD.MM.YYYY")
    
    def __str__(self):
        return self.value.strftime("%d.%m.%Y")


class Record:
    def __init__(self, name):
        self.name = Name(name)
        self.phones = []
        self.birthday = None

    def add_phone(self, phone):
        self.phones.append(Phone(phone))

    def remove_phone(self, phone):
        self.phones = [p for p in self.phones if p.value != phone]

    def edit_phone(self, old_phone, new_phone):
        for p in self.phones:
            if p.value == old_phone:
                if not Phone.validate(new_phone):
                    raise ValueError("Phone number must be 10 digits.")
                p.value = new_phone
                return
        raise ValueError(f"Phone {old_phone} not found.")

    def find_phone(self, phone):
        for p in self.phones:
            if p.value == phone:
                return p
        return None

    def add_birthday(self, birthday):
        self.birthday = Birthday(birthday)

    def __str__(self):
        phones_str = '; '.join(p.value for p in self.phones)
        birthday_str = f", birthday: {self.birthday}" if self.birthday else ""
        return f"Contact name: {self.name.value}, phones: {phones_str}{birthday_str}"


class AddressBook(UserDict):
    def add_record(self, record):
        self.data[record.name.value] = record

    def find(self, name):
        return self.data.get(name)

    def delete(self, name):
        if name in self.data:
            del self.data[name]

    def get_upcoming_birthdays(self):
        today = datetime.today().date()
        upcoming_birthdays = []

        for record in self.data.values():
            if record.birthday is None:
                continue

            birthday_date = record.birthday.value.date()
            birthday_this_year = birthday_date.replace(year=today.year)

            if birthday_this_year < today:
                birthday_this_year = birthday_date.replace(year=today.year + 1)

            days_until_birthday = (birthday_this_year - today).days

            if 0 <= days_until_birthday <= 7:
                if birthday_this_year.weekday() >= 5:
                    days_to_monday = 7 - birthday_this_year.weekday()
                    birthday_this_year += timedelta(days=days_to_monday)

                upcoming_birthdays.append({
                    "name": record.name.value,
                    "congratulation_date": birthday_this_year.strftime("%d.%m.%Y")
                })

        return upcoming_birthdays


def save_data(book, filename="addressbook.pkl"):
    with open(filename, "wb") as f:
        pickle.dump(book, f)


def load_data(filename="addressbook.pkl"):
    try:
        with open(filename, "rb") as f:
            return pickle.load(f)
    except FileNotFoundError:
        return AddressBook()


def input_error(func):
    def inner(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ValueError as e:
            return f"Error: {str(e)}"
        except KeyError:
            return "Error: Contact not found."
        except IndexError:
            return "Error: Not enough arguments provided."
        except AttributeError:
            return "Error: Contact not found."
    return inner


def parse_input(user_input):
    user_input = user_input.strip()
    if not user_input:
        return "", []
    
    parts = user_input.split()
    cmd = parts[0].lower()
    args = parts[1:]
    return cmd, args


@input_error
def add_contact(args, book: AddressBook):
    if len(args) < 2:
        raise ValueError("Please provide name and phone number. Usage: add [name] [phone]")
    
    name, phone, *_ = args
    record = book.find(name)
    message = "Contact updated."
    if record is None:
        record = Record(name)
        book.add_record(record)
        message = "Contact added."
    record.add_phone(phone)
    return message


@input_error
def change_contact(args, book: AddressBook):
    if len(args) < 3:
        raise ValueError("Please provide name, old phone and new phone. Usage: change [name] [old_phone] [new_phone]")
    
    name, old_phone, new_phone, *_ = args
    record = book.find(name)
    record.edit_phone(old_phone, new_phone)
    return "Contact updated."


@input_error
def show_phone(args, book: AddressBook):
    if len(args) < 1:
        raise ValueError("Please provide contact name. Usage: phone [name]")
    
    name = args[0]
    record = book.find(name)
    
    if not record.phones:
        return f"No phones saved for {name}."
    return '; '.join(p.value for p in record.phones)


@input_error
def show_all(book: AddressBook):
    if not book.data:
        return "No contacts saved."
    return '\n'.join(str(record) for record in book.data.values())


@input_error
def add_birthday(args, book: AddressBook):
    if len(args) < 2:
        raise ValueError("Please provide name and birthday. Usage: add-birthday [name] [DD.MM.YYYY]")
    
    name, birthday, *_ = args
    record = book.find(name)
    record.add_birthday(birthday)
    return "Birthday added."


@input_error
def show_birthday(args, book: AddressBook):
    if len(args) < 1:
        raise ValueError("Please provide contact name. Usage: show-birthday [name]")
    
    name = args[0]
    record = book.find(name)
    if record.birthday is None:
        return "Birthday not set for this contact."
    return str(record.birthday)


@input_error
def birthdays(book: AddressBook):
    upcoming = book.get_upcoming_birthdays()
    if not upcoming:
        return "No upcoming birthdays in the next week."
    
    result = "Upcoming birthdays:\n"
    for entry in upcoming:
        result += f"{entry['name']}: {entry['congratulation_date']}\n"
    return result.strip()


def main():
    book = load_data()
    print("Welcome to the assistant bot!")
    
    try:
        while True:
            try:
                user_input = input("Enter a command: ")
            except KeyboardInterrupt:
                print("\nGood bye!")
                break
            
            command, args = parse_input(user_input)

            if not command:
                continue

            if command in ["close", "exit"]:
                print("Good bye!")
                break

            elif command == "hello":
                print("How can I help you?")

            elif command == "add":
                print(add_contact(args, book))

            elif command == "change":
                print(change_contact(args, book))

            elif command == "phone":
                print(show_phone(args, book))

            elif command == "all":
                print(show_all(book))

            elif command == "add-birthday":
                print(add_birthday(args, book))

            elif command == "show-birthday":
                print(show_birthday(args, book))

            elif command == "birthdays":
                print(birthdays(book))

            else:
                print("Invalid command.")
    
    except KeyboardInterrupt:
        print("\nGood bye!")
    except EOFError:
        print("\nGood bye!")
    finally:
        save_data(book)


if __name__ == "__main__":
    main()