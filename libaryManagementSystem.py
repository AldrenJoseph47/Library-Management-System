import mysql.connector
import re
from _decimal import Decimal
from tabulate import tabulate
import datetime

# Connect to MySQL Database
databaseobj = mysql.connector.connect(
    host='localhost',
    user='root',
    password='faith',
    database='librarydb'
)
cursor = databaseobj.cursor()

# Create tables in the database

# create author table
cursor.execute("""
    CREATE TABLE IF NOT EXISTS Author (
        AuthorID INT AUTO_INCREMENT PRIMARY KEY,
        Name VARCHAR(100)
    )
""")

# create genre table
cursor.execute("""
    CREATE TABLE IF NOT EXISTS Genre (
        GenreID INT AUTO_INCREMENT PRIMARY KEY,
        Name VARCHAR(50)
    )
""")

# create book table
cursor.execute("""
    CREATE TABLE IF NOT EXISTS Book (
        BookID INT AUTO_INCREMENT PRIMARY KEY,
        Title VARCHAR(256),
        AuthorID INT,
        GenreID INT,
        RentPrice DECIMAL(10,2),
        FOREIGN KEY (AuthorID) REFERENCES Author(AuthorID),
        FOREIGN KEY (GenreID) REFERENCES Genre(GenreID)
    )
""")

# create login table
cursor.execute("""
    CREATE TABLE IF NOT EXISTS Login (
        Username VARCHAR(50) PRIMARY KEY,
        Password VARCHAR(50),
        FirstName VARCHAR(50),
        LastName VARCHAR(50),
        Email VARCHAR(50),
        Role ENUM('admin', 'customer') NOT NULL
    )
""")

# create plan table
cursor.execute("""
    CREATE TABLE IF NOT EXISTS Plan (
        PlanID INT AUTO_INCREMENT PRIMARY KEY,
        Duration VARCHAR(255),
        Cost DECIMAL(10,2),
        Details VARCHAR(500)
    )
""")

# create payment table
cursor.execute("""
    CREATE TABLE IF NOT EXISTS Payment (
        PaymentID INT AUTO_INCREMENT PRIMARY KEY,
        UserID VARCHAR(50),
        Amount DECIMAL(10,2),
        PaymentDate DATE,
        PaymentMethod VARCHAR(255),
        FOREIGN KEY (UserID) REFERENCES Login(Username)
    )
""")

# create checkout table
cursor.execute("""
    CREATE TABLE IF NOT EXISTS Checkout (
        CheckoutID INT AUTO_INCREMENT PRIMARY KEY,
        UserID VARCHAR(50),
        BookID INT,
        PlanID INT,
        Rating VARCHAR(255),
        ReviewDate DATE,
        FOREIGN KEY (UserID) REFERENCES Login(Username),
        FOREIGN KEY (BookID) REFERENCES Book(BookID),
        FOREIGN KEY (PlanID) REFERENCES Plan(PlanID)
    )
""")


# Function to validate password
def validate_password(password):
    if len(password) < 8 or len(password) > 24:
        print("Password must be between 8 and 24 characters long.")
        return False
    if not re.search(r'[A-Z]', password):
        print("Password must contain at least one uppercase letter.")
        return False
    if not re.search(r'[0-9]', password):
        print("Password must contain at least one digit.")
        return False
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        print("Password must contain at least one special character.")
        return False
    return True


# Function to validate username
def validate_username(username):
    if not username.isalnum():
        print("Username must be alphanumeric (letters and numbers only).")
        return False
    return True


# Function to validate name (alphabets only, min 3 characters)
def validate_name(name):
    if len(name) < 3 or not name.isalpha():
        print("Name must be at least 3 characters long and contain only alphabets.")
        return False
    return True


# Function to validate email
def validate_email(email):
    if not re.fullmatch(r"[^@]+@[^@]+\.[^@]+", email):
        print("Email must contain '@' and '.'")
        return False
    return True


# Function to register new customer
def register():
    while True:
        try:
            print("\n-----CUSTOMER REGISTRATION-----\t")
            print("\tRegister your details here.")

            # Validate first name
            while True:
                first_name = input("-> Enter the first name: ")
                if validate_name(first_name):
                    break

            # Validate last name
            while True:
                last_name = input("-> Enter the last name: ")
                if validate_name(last_name):
                    break

            # Validate username
            while True:
                username = input("-> Create a username (alphanumeric): ")
                if validate_username(username):
                    break

            # Validate email
            while True:
                email = input("-> Enter the email: ")
                if validate_email(email):
                    break

            # Validate password
            while True:
                password = input("-> Enter the password: ")
                if validate_password(password):
                    break

            # Automatically set role as 'customer'
            role = "customer"

            # Insert validated data into the database
            insert_query = """
            INSERT INTO Login (Username, Password, FirstName, LastName, Email, Role) 
            VALUES (%s, %s, %s, %s, %s, %s)
            """
            cursor.execute(insert_query, (username, password, first_name, last_name, email, role))
            databaseobj.commit()
            print("\t\t\t------You have successfully registered as a customer!------\n")

            # Ask user if they want to subscribe to a plan
            subscribe = input("Would you like to subscribe to a plan? (yes): ").strip().lower()

            if subscribe == "yes":
                view_plans()  # Show available plans
                while True:
                    plan_id = input("Enter the PlanID you want to subscribe to: ")
                    cursor.execute("SELECT * FROM Plan WHERE PlanID = %s", (plan_id,))
                    if cursor.fetchone():
                        # Proceed to checkout with selected plan
                        checkout_plan(plan_id, username)
                        break
                    else:
                        print("Invalid PlanID. Please enter a valid PlanID.")
            else:
                print("No plan subscription selected.")

            customer_menu()
            break
        except Exception as e:
            print("Error:", e)


# Function to check out with selected plan
def checkout_plan(plan_id, user_id):
    # Retrieve the selected plan details for pricing
    cursor.execute("SELECT Cost FROM Plan WHERE PlanID = %s", (plan_id,))
    plan_cost = cursor.fetchone()[0]

    # Convert plan_cost to Decimal for accurate monetary calculations
    plan_cost = Decimal(plan_cost)

    tax = Decimal('3.50')  # Fixed tax amount
    service_fee = Decimal('5.00')  # Fixed service fee
    total_amount = plan_cost + tax + service_fee

    # Display checkout details
    print(f"\n\nService fee:                                  Rs. {service_fee:.2f}")
    print(f"Tax:                                          Rs. {tax:.2f}")
    print("--------------------------------------------------------------------------")
    print(f"Total Amount (including tax and service fee): Rs. {total_amount:.2f}")

    proceed = input("\n\tProceed to payment? (yes/no): ")

    if proceed.lower() == "yes":
        # Insert payment and checkout details
        payment_method = input("Enter payment method (gpay/phonepay/credit/debit) : ")
        payment_date = datetime.date.today()  # Correctly calling datetime.date.today()

        # Insert payment record
        insert_payment_query = """
        INSERT INTO Payment (UserID, Amount, PaymentDate, PaymentMethod) 
        VALUES (%s, %s, %s, %s)
        """
        cursor.execute(insert_payment_query, (user_id, total_amount, payment_date, payment_method))

        # Insert checkout record
        insert_checkout_query = """
        INSERT INTO Checkout (UserID, PlanID, ReviewDate)
        VALUES (%s, %s, %s)
        """
        cursor.execute(insert_checkout_query, (user_id, plan_id, payment_date))

        databaseobj.commit()
        print("---->Payment successful! You are now subscribed to the plan.<----")
    else:
        print("---->Payment cancelled. Returning to menu.<----")


# Function to register new admin (accessible from the admin menu only)
def register_new_admin():
    while True:
        try:
            print("\n-----ADMIN REGISTRATION-----")
            print("------------------------------\n\t ENTER DETAILS BELOW\n")
            # Validate first name
            while True:
                first_name = input("[] Enter the first name: ")
                if validate_name(first_name):
                    break

            # Validate last name
            while True:
                last_name = input("[] Enter the last name: ")
                if validate_name(last_name):
                    break

            # Validate username
            while True:
                username = input("[] Create a username (alphanumeric): ")
                if validate_username(username):
                    break

            # Validate email
            while True:
                email = input("[] Enter the email: ")
                if validate_email(email):
                    break

            # Validate password
            while True:
                password = input("[] Enter the password: ")
                if validate_password(password):
                    break

            # Automatically set role as 'admin'
            role = "admin"

            # Insert validated data into the database
            insert_query = """
            INSERT INTO Login (Username, Password, FirstName, LastName, Email, Role) 
            VALUES (%s, %s, %s, %s, %s, %s)
            """
            cursor.execute(insert_query, (username, password, first_name, last_name, email, role))
            databaseobj.commit()
            print("-->New admin registered successfully!<--")
            break
        except Exception as e:
            print("Error:", e)


# Function to view all books with BookID, Title, Author Name, Genre Name, and Rent Price
def view_books():
    query = """
    SELECT Book.BookID, Book.Title, Author.Name AS AuthorName, Genre.Name AS GenreName, Book.RentPrice
    FROM Book
    JOIN Author ON Book.AuthorID = Author.AuthorID
    JOIN Genre ON Book.GenreID = Genre.GenreID
    """
    try:
        cursor.execute(query)
        result = cursor.fetchall()

        if result:
            headers = ["BookID", "Title", "Author Name", "Genre", "Rent Price"]
            print("\nBooks:")
            print(tabulate(result, headers=headers, tablefmt="grid"))
        else:
            print("No books found.")
    except Exception as e:
        print("Error:", e)


# Function to view all authors
def view_authors():
    query = "SELECT AuthorID, Name FROM Author"
    try:
        cursor.execute(query)
        result = cursor.fetchall()

        if result:
            headers = ["AuthorID", "Name"]
            print("\nAuthors:")
            print(tabulate(result, headers=headers, tablefmt="grid"))
        else:
            print("No authors found.")
    except Exception as e:
        print("Error:", e)


# Function to view all genres
def view_genres():
    query = "SELECT * FROM Genre"
    try:
        cursor.execute(query)
        result = cursor.fetchall()

        if result:
            headers = ["GenreID", "Name"]
            print("\nGenres:")
            print(tabulate(result, headers=headers, tablefmt="grid"))
        else:
            print("No genres found.")
    except Exception as e:
        print("Error:", e)


# Function to add a new book with author and genre names instead of IDs
def add_book():
    try:
        title = input("Enter book title: ")

        # Handle Author if not present in the database new author will be added
        while True:
            author_name = input("Enter author name: ")
            cursor.execute("SELECT AuthorID FROM Author WHERE Name = %s", (author_name,))
            result = cursor.fetchone()

            if result:
                author_id = result[0]
                break
            else:
                print("Author not found. Adding new author.")
                cursor.execute("INSERT INTO Author (Name) VALUES (%s)", (author_name,))
                databaseobj.commit()
                cursor.execute("SELECT AuthorID FROM Author WHERE Name = %s", (author_name,))
                author_id = cursor.fetchone()[0]
                print(f"New author added with AuthorID: {author_id}")
                break

        # Handle Genre if not present in the database new genre will be added
        while True:
            genre_name = input("Enter genre name: ")
            cursor.execute("SELECT GenreID FROM Genre WHERE Name = %s", (genre_name,))
            result = cursor.fetchone()

            if result:
                genre_id = result[0]
                break
            else:
                print("Genre not found. Adding new genre.")
                cursor.execute("INSERT INTO Genre (Name) VALUES (%s)", (genre_name,))
                databaseobj.commit()
                cursor.execute("SELECT GenreID FROM Genre WHERE Name = %s", (genre_name,))
                genre_id = cursor.fetchone()[0]
                print(f"New genre added with GenreID: {genre_id}")
                break
        # Handle rent price in decimal
        rent_price = Decimal(input("Enter rent price: "))

        insert_query = """
        INSERT INTO Book (Title, AuthorID, GenreID, RentPrice) 
        VALUES (%s, %s, %s, %s)
        """
        cursor.execute(insert_query, (title, author_id, genre_id, rent_price))
        databaseobj.commit()
        print("---->Book added successfully!<----")
    except Exception as e:
        print("Error:", e)


# Function to delete a book using its BookID
def delete_book():
    view_books()  # Show the list of books to help the admin choose which one to delete
    book_id = input("Enter the BookID of the book you want to delete: ")

    try:
        cursor.execute("DELETE FROM Book WHERE BookID = %s", (book_id,))
        databaseobj.commit()
        print("Book deleted successfully!")
    except Exception as e:
        print("Error:", e)


# Function to update a book's details
def update_book():
    view_books()  # Show the list of books to help the admin choose which one to update
    book_id = input("Enter the BookID of the book you want to update: ")

    title = input("Enter the new title of the book: ")
    rent_price = input("Enter the new rent price of the book: ")

    try:
        rent_price = Decimal(rent_price)
        update_query = """
        UPDATE Book 
        SET Title = %s, RentPrice = %s 
        WHERE BookID = %s
        """
        cursor.execute(update_query, (title, rent_price, book_id))
        databaseobj.commit()
        print("Book updated successfully!")
    except Exception as e:
        print("Error:", e)


# Function to view all plans
def view_plans():
    query = "SELECT * FROM Plan"
    try:
        cursor.execute(query)
        result = cursor.fetchall()

        if result:
            headers = ["PlanID", "Duration", "Cost", "Details"]
            print("\nPlans:")
            print(tabulate(result, headers=headers, tablefmt="grid"))
        else:
            print("No plans found.")
    except Exception as e:
        print("Error:", e)


# Function to display customer menu
def customer_menu():
    while True:
        print("\n\t\t-------------------------------------------"
              "\n\t\t\t\t ----CUSTOMER MENU----\n\t\t-------------------------------------------\n")
        print("\t[1]. View Books")
        print("\t[2]. View Authors")
        print("\t[3]. View Genre")
        print("\t[4]. Rent Book")
        print("\t[5]. Logout")

        choice = input("\n\t\tEnter your choice: ")

        if choice == "1":
            view_books()
        elif choice == "2":
            view_authors()
        elif choice == "3":
            view_genres()
        elif choice == "4":
            rent_book()
        elif choice == "5":
            print("Logging out...")
            break
        else:
            print("Invalid choice. Please select a valid option.")


# Function to handle book rental
def rent_book():
    view_books()  # Show the list of books to help the customer choose which one to rent
    book_id = input("Enter the BookID of the book you want to rent: ")
    username = input("Enter your username: ")  # Assuming the user is logged in

    try:
        cursor.execute("SELECT RentPrice FROM Book WHERE BookID = %s", (book_id,))
        rent_price = cursor.fetchone()[0]

        # Convert rent_price to Decimal for accurate monetary calculations
        rent_price = Decimal(rent_price)

        tax = Decimal('3.50')  # Fixed tax amount
        service_fee = Decimal('5.00')  # Fixed service fee
        total_amount = rent_price + tax + service_fee

        print(f"Total Amount (including tax and service fee): Rs. {total_amount:.2f}")
        proceed = input("Proceed to payment? (yes/no): ")

        if proceed.lower() == "yes":
            payment_method = input("Enter payment method: ")
            payment_date = datetime.date.today()

            # Insert payment record
            insert_payment_query = """
            INSERT INTO Payment (UserID, Amount, PaymentDate, PaymentMethod) 
            VALUES (%s, %s, %s, %s)
            """
            cursor.execute(insert_payment_query, (username, total_amount, payment_date, payment_method))

            # Insert checkout record
            insert_checkout_query = """
            INSERT INTO Checkout (UserID, BookID, Rating, ReviewDate)
            VALUES (%s, %s, %s, %s)
            """
            rating = input("Enter your rating (optional): ")
            cursor.execute(insert_checkout_query, (username, book_id, rating, payment_date))

            databaseobj.commit()
            print("Payment successful! Enjoy your book.")
        else:
            print("Payment cancelled. Returning to menu.")
    except Exception as e:
        print("Error:", e)


def view_payments():
    query = "SELECT PaymentID, UserID, Amount, PaymentDate, PaymentMethod FROM Payment"
    try:
        cursor.execute(query)
        payments = cursor.fetchall()

        if payments:
            headers = ["Payment ID", "Customer ID", "Amount", "Date", "Payment Method"]
            table = []
            for payment in payments:
                payment_id = payment[0]
                customer_id = payment[1]
                amount = payment[2]
                date = payment[3]
                payment_method = payment[4]
                table.append([payment_id, customer_id, amount, date, payment_method])

            print("\nPayments:")
            print(tabulate(table, headers=headers, tablefmt="grid"))
        else:
            print("No payments available.")
    except Exception as e:
        print("Error:", e)


def view_customer_details():
    query = """
    SELECT username, email, firstname, lastname
    FROM login
    WHERE role = 'customer'
    """
    try:
        cursor.execute(query)
        customers = cursor.fetchall()

        if customers:
            headers = ["Username", "Email", "First Name", "Last Name"]
            table = []
            for customer in customers:
                username = customer[0]
                email = customer[1]
                first_name = customer[2]
                last_name = customer[3]
                table.append([username, email, first_name, last_name])

            print("\nCustomer Details:")
            print(tabulate(table, headers=headers, tablefmt="grid"))
        else:
            print("No customer details available.")
    except Exception as e:
        print("Error:", e)


# Function to handle admin menu
def admin_menu():
    while True:
        print("\n\t\t-------------------------------------------"
              "\n\t\t\t       ----ADMIN MENU----\n\t\t-------------------------------------------\n")
        print("\t[1]. Add Book")
        print("\t[2]. View Books")
        print("\t[3]. Delete Book")
        print("\t[4]. View Customer Details")
        print("\t[5]. View Authors")
        print("\t[6]. View Genres")
        print("\t[7]. View Plans")
        print("\t[8]. Register New Admin")
        print("\t[9]. View Payments")
        print("\t[10]. Logout")

        choice = input("\n\t\tEnter your choice: ")

        if choice == '1':
            add_book()
        elif choice == '2':
            view_books()
        elif choice == '3':
            delete_book()
        elif choice == '4':
            view_customer_details()
        elif choice == '5':
            view_authors()
        elif choice == '6':
            view_genres()
        elif choice == '7':
            view_plans()
        elif choice == '8':
            register_new_admin()
        elif choice == '9':
            view_payments()
        elif choice == '10':
            print("Logging out...")
            break
        else:
            print("Invalid choice. Please try again.")


# Main function to start the application
def main():
    while True:
        print("\n\t\t-------------------------------------------"
              "\n\t\t\t----Library Management System----\n\t\t-------------------------------------------\n")
        print("\t[1]. Register")
        print("\t[2]. Login")
        print("\t[3]. Exit")

        choice = input("\n\t\tEnter your choice : ")

        if choice == "1":
            register()
        elif choice == "2":
            username = input("\n\t[] Enter username : ")
            password = input("\t[] Enter password : ")

            cursor.execute("SELECT Role FROM Login WHERE Username = %s AND Password = %s", (username, password))
            result = cursor.fetchone()

            if result:
                role = result[0]
                if role == "admin":
                    admin_menu()
                elif role == "customer":
                    customer_menu()
            else:
                print("Invalid username or password.")
        elif choice == "3":
            print("Exiting...")
            break
        else:
            print("Invalid choice. Please select a valid option.")


if __name__ == "__main__":
    main()
