# Use Cases

## Use Case 1: User Registration
**Description:** This use case describes how a new user registers for the system.

**Actors:** New User

**Preconditions:** The user must have access to the registration page.

**Postconditions:** The user is registered and can log in.

**Main Flow:**
1. The user navigates to the registration page.
2. The user fills in the required fields (name, email, password).
3. The user submits the registration form.
4. The system validates the input and creates a new user account.
5. The user receives a confirmation email.

## Use Case 2: User Login
**Description:** This use case describes how a registered user logs into the system.

**Actors:** Registered User

**Preconditions:** The user must have a registered account.

**Postconditions:** The user is logged into the system.

**Main Flow:**
1. The user navigates to the login page.
2. The user enters their email and password.
3. The user submits the login form.
4. The system validates the credentials.
5. The user is redirected to the dashboard.

## Use Case 3: Data Retrieval
**Description:** This use case describes how users retrieve data from the system.

**Actors:** Logged-in User

**Preconditions:** The user must be logged into the system.

**Postconditions:** The user views the requested data.

**Main Flow:**
1. The user navigates to the data retrieval section.
2. The user selects the type of data to retrieve.
3. The user submits the request.
4. The system processes the request and displays the data.

## Use Case 4: User Logout
**Description:** This use case describes how a user logs out of the system.

**Actors:** Logged-in User

**Preconditions:** The user must be logged into the system.

**Postconditions:** The user is logged out and redirected to the homepage.

**Main Flow:**
1. The user clicks on the logout button.
2. The system logs the user out.
3. The user is redirected to the homepage.