from django.db import connection # type: ignore
from rest_framework.response import Response # type: ignore
from rest_framework.views import APIView # type: ignore
from rest_framework import status # type: ignore
from django.shortcuts import get_object_or_404
from django.http import JsonResponse
import base64
import uuid
from datetime import datetime, timedelta
from django.utils.timezone import make_aware
from django.core.mail import send_mail
from django.conf import settings


class clientsView(APIView):

    def get(self, request, *args, **kwargs):
        """Retrieve all clients, or retrieve a client by FirstName, LastName, or Alias"""

        # Retrieve parameters from the URL
        alias = kwargs.get('Alias', None)
        first_name = kwargs.get('FirstName', None)
        last_name = kwargs.get('LastName', None)

        query = ""
        params = []

        if alias:
            # If Alias is provided, search by Alias
            query = """
                SELECT ID, FirstName, MiddleName, LastName, Alias, Office, DOB, Gender, Status, 
                       Street, City, State, ZipCode, AddressNotes, 
                       Email, Primary_Phone_number, Alternate_Phone_number, PayerName
                FROM clients
                WHERE Alias = %s;
            """
            params = [alias]
        elif first_name and last_name:
            # If FirstName and LastName are provided, search by Name
            query = """
                SELECT FirstName, MiddleName, LastName, Alias, Office, DOB, Gender, Status, 
                       Street, City, State, ZipCode, AddressNotes, 
                       Email, Primary_Phone_number, Alternate_Phone_number, PayerName
                FROM clients
                WHERE FirstName = %s AND LastName = %s;
            """
            params = [first_name, last_name]
        else:
            # If no parameters are provided, return all clients
            query = """
                SELECT ID, FirstName, MiddleName, LastName, Alias, Office, DOB, Gender, Status, 
                       Street, City, State, ZipCode, AddressNotes, 
                       Email, Primary_Phone_number, Alternate_Phone_number, PayerName
                FROM clients;
            """

        try:
            with connection.cursor() as cursor:
                cursor.execute(query, params)
                rows = cursor.fetchall()

                columns = [col[0] for col in cursor.description]
                results = [dict(zip(columns, row)) for row in rows]

                if not results:
                    return Response({"message": "Client not found."}, status=status.HTTP_404_NOT_FOUND)

                return Response(results, status=status.HTTP_200_OK)

        except Exception as e:
            print(f"Error: {str(e)}")
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


            
    def post(self, request, *args, **kwargs):
        print('post called')
        """Add a new client with a unique Alias (GUID formed by FirstName + LastName)"""

        # Retrieve FirstName and LastName from the request body
        first_name = request.data.get('FirstName')
        last_name = request.data.get('LastName')

        # Check if both FirstName and LastName are provided
        if not first_name or not last_name:
            return Response({"error": "FirstName and LastName are required to generate Alias."}, status=status.HTTP_400_BAD_REQUEST)

        # Generate Alias by concatenating FirstName and LastName
        alias = first_name + last_name  # Combining FirstName and LastName as Alias
        print('Generated Alias:', alias)

        # Check if Alias already exists in the database
        check_alias_query = "SELECT COUNT(*) FROM clients WHERE Alias = %s;"

        try:
            #data = request.data
            # Check if the Alias exists
            with connection.cursor() as cursor:
                cursor.execute(check_alias_query, [alias])
                alias_count = cursor.fetchall()

            if alias_count[0][0] > 0:
                return Response({"error": "Alias must be unique."}, status=status.HTTP_400_BAD_REQUEST)   

            # # If Alias already exists, return error message
            # print('alias', alias_count)
            # if alias_count > 0:
            #     return Response({"error": "Alias must be unique."}, status=status.HTTP_400_BAD_REQUEST)

            # Insert the new client data into the database
            insert_query = """
                INSERT INTO clients (FirstName, MiddleName, LastName, Alias, Office, DOB, Gender, Status, Street, City, State, ZipCode, 
                                     AddressNotes, Email, Primary_Phone_number, Alternate_Phone_number, PayerName)  
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
            """
            with connection.cursor() as cursor:
                cursor.execute(insert_query, (
                request.data.get('FirstName'), request.data.get('MiddleName'), request.data.get('LastName'), request.data.get('Alias'),
                request.data.get('Office'), request.data.get('DOB'), request.data.get('Gender'), request.data.get('Status'),
                request.data.get('Street'), request.data.get('City'), request.data.get('State'), request.data.get('ZipCode'),
                request.data.get('AddressNotes'), request.data.get('Email'), request.data.get('Primary_Phone_number'),
                request.data.get('Alternate_Phone_number'), request.data.get('PayerName')
                ))
                connection.commit()  # Ensure the data is committed to the database

            # Return a success response with the Alias
            return Response({"message": "Client added successfully.", "Alias": alias}, status=status.HTTP_201_CREATED)

        
        except Exception as e:
            print(f"Error: {str(e)}")  # Log the error for debugging
            return Response({"error": "An error occurred while processing the request."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            # Return error response in case of an exception
            # return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def put(self, request, *args, **kwargs):
        """Update an existing client by Alias (GUID)"""
        alias = request.data.get('Alias')
        if not alias:
            return Response({"error": "Alias is required."}, status=status.HTTP_400_BAD_REQUEST)

        # Update the client details
        update_query = """
            UPDATE clients
            SET FirstName=%s, MiddleName=%s, LastName=%s, Alias=%s, Office=%s, DOB=%s, Gender=%s, Status=%s, 
                Street=%s, City=%s, State=%s, ZipCode=%s, AddressNotes=%s, Email=%s, Primary_Phone_number=%s, Alternate_Phone_number=%s,
                PayerName=%s
            WHERE Alias=%s;
        """
        try:
            data = request.data
            with connection.cursor() as cursor:
                cursor.execute(update_query, (
                    data.get('FirstName'), data.get('MiddleName'), data.get('LastName'), data.get('Alias'), 
                    data.get('Office'), data.get('DOB'), data.get('Gender'), data.get('Status'),
                    data.get('Street'), data.get('City'), data.get('State'), data.get('ZipCode'),
                    data.get('AddressNotes'), data.get('Email'), data.get('Primary_Phone_number'), data.get('Alternate_Phone_number'),
                    data.get('PayerName'),
                    
                ))
                connection.commit()
            return Response({"message": "Client updated successfully."}, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
   
    def delete(self, request, *args, **kwargs):
        """Delete a client by Alias (GUID)"""
        
        # Retrieve the Alias from the URL parameter (kwargs)
        alias = kwargs.get('Alias')  # Correctly get Alias from URL parameters

        if not alias:
            return Response({"error": "Alias is required."}, status=status.HTTP_400_BAD_REQUEST)

        # SQL query to delete the client by Alias
        delete_query = "DELETE FROM clients WHERE Alias = %s;"

        try:
            with connection.cursor() as cursor:
                cursor.execute(delete_query, [alias])  # Execute the delete query with the Alias

                if cursor.rowcount == 0:
                    return Response({"message": "Client not found."}, status=status.HTTP_404_NOT_FOUND)

            return Response({"message": "Client deleted successfully."}, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        


class ProviderView(APIView):

    def get(self, request, *args, **kwargs):
        """Retrieve all providers or filter by alias."""
        alias = kwargs.get('alias', None)
        query = "Select * from Provider;"
        params = []

        if alias:
            query = """
            SELECT Provider_id, firstname, middlename, lastname, alias, jobtitle, office, department, type,
                                  hiredate, dob, gender, service_provider, status, email, phone_type, phone_number, phone_extension,
                                  profile_picture, street, city, state, zip_code, address_notes
            FROM Provider
            WHERE Alias = %s;
        """
            params = [alias]
            # query += " WHERE alias = %s"
            # params.append(alias)
        
        try:
            with connection.cursor() as cursor:
                cursor.execute(query, params)
                rows = cursor.fetchall()

                if not rows:
                    return Response({"message": "No Provider found."}, status=status.HTTP_404_NOT_FOUND)
                
                columns = [col[0] for col in cursor.description]

                # Process data and convert profile_picture to Base64 if it's binary
                data = []
                for row in rows:
                    row_data = dict(zip(columns, row))
                  
                    if row_data.get('profile_picture'):
                        row_data['profile_picture'] = base64.b64encode(row_data['profile_picture']).decode('utf-8')

                    data.append(row_data)

            return Response(data, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


    def post(self, request, *args, **kwargs):
        """Add a new provider."""
        query = """
            INSERT INTO Provider (firstname, middlename, lastname, alias, jobtitle, office, department, type,
                                  hiredate, dob, gender, service_provider, status, email, phone_type, phone_number, phone_extension,
                                  profile_picture, street, city, state, zip_code, address_notes)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
        """
        try:
            data = request.data
            profile_picture = data.get('profile_picture')  # This should be in base64 encoded string if it's provided

            # If profile picture is provided, convert it to bytes (if it's an actual file or base64 string)
            if profile_picture:
                # Check if it's base64 encoded
                try:
                    profile_picture = base64.b64decode(profile_picture)
                except Exception as e:
                    return JsonResponse({"error": "Invalid base64 encoding for profile_picture."}, status=400)

            # Insert the provider data
            with connection.cursor() as cursor:
                cursor.execute(query, (
                    data.get('firstname'), data.get('middlename'), data.get('lastname'), data.get('alias'),
                    data.get('jobtitle'), data.get('office'), data.get('department'), data.get('type'), data.get('hiredate'),
                    data.get('dob'), data.get('gender'), data.get('service_provider'),
                    data.get('status'), data.get('email'), data.get('phone_type'), data.get('phone_number'), data.get('phone_extension'),
                    profile_picture, data.get('street'), data.get('city'), data.get('state'), data.get('zip_code'), data.get('address_notes')
                ))
            return JsonResponse({"message": "Provider added successfully."}, status=200)
        
        except Exception as e:
            print(f"Error: {str(e)}")
            return JsonResponse({"error": str(e)}, status=500)
        

    def put(self, request, *args, **kwargs):
        """Update an existing provider"""
        provider_id = kwargs.get('provider_id')
        query = """
            UPDATE Provider
            SET firstname=%s, middlename=%s, lastname=%s, alias=%s, jobtitle=%s, office=%s, department=%s, type=%s,
                hiredate=%s, dob=%s, gender=%s, service_provider=%s, status=%s, email=%s, phone_type=%s, phone_number=%s, phone_extension=%s,
                profile_picture=%s, street=%s, city=%s, state=%s, zip_code=%s, address_notes=%s
            WHERE Provider_id=%s;
        """
        try:
            data = request.data
            profile_picture = data.get('profile_picture')  # This should be in binary format, not a string

            # If profile picture is provided, convert it to bytes (if it's an actual file)
            if profile_picture:
                # For simplicity, assume profile_picture is base64 encoded
                import base64
                profile_picture = base64.b64decode(profile_picture)

            with connection.cursor() as cursor:
                cursor.execute(query, (
                    data.get('firstname'), data.get('middlename'), data.get('lastname'), data.get('alias'),
                    data.get('jobtitle'), data.get('office'), data.get('department'),data.get('type'), data.get('hiredate'),
                    data.get('dob'), data.get('gender'), data.get('service_provider'),
                    data.get('status'), data.get('email'), data.get('phone_type'), data.get('phone_number'), data.get('phone_extension'), profile_picture, data.get('street'),
                    data.get('city'), data.get('state'), data.get('zip_code'), data.get('address_notes'),
                    provider_id  # ID for the record we want to update
                ))
                if cursor.rowcount == 0:
                    return JsonResponse({"message": "Provider not found."}, status=404)

            return JsonResponse({"message": "Provider updated successfully."}, status=200)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
        

# views.py
    
class ScheduleView(APIView):

    def get(self, request, *args, **kwargs):
        """Retrieve schedules for a particular client or provider within a specified date range."""
        
        # Get parameters from request
        # schedule_id = kwargs.get('schedule_id', None)
        id = request.query_params.get('id', None)  # client ID
        type = request.query_params.get('type', None)  # provider ID
        start_date = request.query_params.get('start_date', None)  # Start date of the range
        end_date = request.query_params.get('end_date', None)  # End date of the range

        
        query = ""
        params = []

        if type == 'client':
            query = "SELECT * FROM Schedule WHERE clients_ID = %s AND start_date BETWEEN %s AND %s"
            params = [id, start_date, end_date]
        else:
            query = "SELECT * FROM Schedule WHERE Provider_id = %s AND start_date BETWEEN %s AND %s"
            params = [id, start_date, end_date]

        
        try:
            with connection.cursor() as cursor:
                cursor.execute(query, params)
                rows = cursor.fetchall()

                if not rows:
                    return Response({"message": "No schedules found."}, status=status.HTTP_404_NOT_FOUND)
                
                columns = [col[0] for col in cursor.description]

                # Process data and convert any binary data if necessary
                data = []
                for row in rows:
                    row_data = dict(zip(columns, row))
                    data.append(row_data)

            return Response(data, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



    def post(self, request, *args, **kwargs):
        query = """
            INSERT INTO Schedule (sched_status, start_date, end_date, start_time, end_time, duration, service, 
                                clients_ID, Provider_id, title, location, notes, color)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
        """
        try:
            data = request.data

            client_id = data.get('clients_ID')
            provider_id = data.get('Provider_id')
            sched_status = data.get('sched_status')  # renamed variable here

            # Check if client exists
            with connection.cursor() as cursor:
                cursor.execute("SELECT * FROM clients WHERE ID = %s", [client_id])
                client_exists = cursor.fetchone()

            if not client_exists:
                return Response({"error": f"Client ID {client_id} does not exist."}, status=status.HTTP_400_BAD_REQUEST)

            # Check if provider exists
            with connection.cursor() as cursor:
                cursor.execute("SELECT * FROM Provider WHERE Provider_id = %s", [provider_id])
                provider_exists = cursor.fetchone()

            if not provider_exists:
                return Response({"error": f"Provider ID {provider_id} does not exist."}, status=status.HTTP_400_BAD_REQUEST)

            # Validate sched_status
            if sched_status not in ['Active', 'Inactive']:
                return Response({"error": "Invalid sched_status. Only 'Active' or 'Inactive' are allowed."}, status=status.HTTP_400_BAD_REQUEST)

            # Insert data
            with connection.cursor() as cursor:
                cursor.execute(query, (
                    sched_status, data.get('start_date'), data.get('end_date'), data.get('start_time'),
                    data.get('end_time'), data.get('duration'), data.get('service'), client_id, provider_id,
                    data.get('title'), data.get('location'), data.get('notes'), data.get('color')
                ))

            return Response({"message": "Schedule added successfully."}, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



class SignUpView(APIView):

    def post(self, request):
        data = request.data
        username = data.get('username')
        password = data.get('password')
        email = data.get('email')
        full_name = data.get('full_name')
        phone_number = data.get('phone_number')

        if not username or not password:
            return Response({"error": "username and password are required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            with connection.cursor() as cursor:
                # Check if username already exists in Login table
                cursor.execute("SELECT username FROM Login WHERE username = %s", [username])
                if cursor.fetchone():
                    return Response({"error": "username already exists."}, status=status.HTTP_409_CONFLICT)

                # Insert username and password into Login table
                cursor.execute(
                    "INSERT INTO Login (username, password) VALUES (%s, %s)",
                    [username, password]
                )

                # Insert full details into SignUp table
                cursor.execute("""
                    INSERT INTO SignUp (username, password, email, full_name, phone_number)
                    VALUES (%s, %s, %s, %s, %s)
                """, [username, password, email, full_name, phone_number])

                return Response({"message": "Registration successful."}, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response({"error": f"Server error: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class LoginView(APIView):

    def post(self, request):
        data = request.data
        username = data.get('username')
        password = data.get('password')

        if not username or not password:
            return Response({"error": "username and password are required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT password FROM Login WHERE username = %s", [username])
                row = cursor.fetchone()

                # if row:
                #     hashed_password = row[0]
                #     if check_password(raw_password, hashed_password):  # ✅ use this to compare
                if row:
                    stored_password = row[0]
                    if password == stored_password:  # plain text comparison
                        return Response({"message": "Login successful."}, status=status.HTTP_200_OK)
                    else:
                        return Response({"error": "Invalid username or password."}, status=status.HTTP_401_UNAUTHORIZED)
                else:
                    return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)

        except Exception as e:
            return Response({"error": f"Server error: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        

class ForgotPasswordView(APIView):

    def post(self, request):
        email = request.data.get('email')
        if not email:
            return Response({'error': 'Email is required'}, status=status.HTTP_400_BAD_REQUEST)
 
        # Get username from SignUp table
        with connection.cursor() as cursor:
            cursor.execute("SELECT username FROM SignUp WHERE email = %s", [email])
            row = cursor.fetchone()
 
        if not row:
            return Response({'error': 'Email not registered'}, status=status.HTTP_404_NOT_FOUND)
 
        username = row[0]
        token = str(uuid.uuid4())
        expiry = datetime.now() + timedelta(hours=1)
 
        # Save token to PasswordResetTokens table (deleting old tokens first)
        with connection.cursor() as cursor:
            cursor.execute("DELETE FROM PasswordResetTokens WHERE username = %s", [username])
            cursor.execute(
                "INSERT INTO PasswordResetTokens (username, token, expiry) VALUES (%s, %s, %s)",
                [username, token, expiry]
            )
 
        reset_link = f"http://your-frontend-url/reset-password?email={email}&token={token}"
 
        # Send email using Django's send_mail
        try:
            send_mail(
                subject="Password Reset Request",
                message=(
                    f"Hello {username},\n\n"
                    f"Use the following link to reset your password:\n{reset_link}\n\n"
                    f"This link expires in 1 hour."
                ),
                from_email=settings.EMAIL_HOST_USER,
                recipient_list=[email],
                fail_silently=False,
            )
        except Exception as e:
            return Response({'error': f'Failed to send email: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
 
        return Response({'message': 'Password reset link sent', 'reset_link': reset_link}, status=status.HTTP_200_OK)


class ResetPasswordView(APIView):

    def post(self, request):
        email = request.data.get('email')
        token = request.data.get('token')
        new_password = request.data.get('new_password')

        if not all([email, token, new_password]):
            return Response({'error': 'Email, token, and new_password are required'}, status=status.HTTP_400_BAD_REQUEST)

        with connection.cursor() as cursor:
            cursor.execute("SELECT username FROM SignUp WHERE email = %s", [email])
            row = cursor.fetchone()

        if not row:
            return Response({'error': 'Email not registered'}, status=status.HTTP_404_NOT_FOUND)

        username = row[0]

        with connection.cursor() as cursor:
            cursor.execute("SELECT token, expiry FROM PasswordResetTokens WHERE username = %s", [username])
            token_row = cursor.fetchone()

        if not token_row:
            return Response({'error': 'No password reset request found'}, status=status.HTTP_400_BAD_REQUEST)

        saved_token, expiry = token_row
        expiry = make_aware(expiry) if expiry.tzinfo is None else expiry
        now = make_aware(datetime.now())

        if saved_token != token:
            return Response({'error': 'Invalid token'}, status=status.HTTP_400_BAD_REQUEST)
        if now > expiry:
            return Response({'error': 'Token expired'}, status=status.HTTP_400_BAD_REQUEST)

        # Update password in SignUp table
        with connection.cursor() as cursor:
            cursor.execute("UPDATE SignUp SET password = %s WHERE username = %s", [new_password, username])
            # Delete token after successful reset
            cursor.execute("DELETE FROM PasswordResetTokens WHERE username = %s", [username])

        return Response({'message': 'Password updated successfully'}, status=status.HTTP_200_OK)
    

class AuthorizationView(APIView):
    
    def get(self, request, *args, **kwargs):
        """Retrieve all authorization records or filter by client ID"""
        client_id = request.query_params.get('client_id', None)

        query = "SELECT * FROM Authorization"
        params = []

        if client_id:
            query += " WHERE clients_ID = %s"
            params.append(client_id)

        try:
            with connection.cursor() as cursor:
                cursor.execute(query, params)
                rows = cursor.fetchall()

                if not rows:
                    return Response({"message": "No Authorization records found."}, status=status.HTTP_404_NOT_FOUND)

                columns = [col[0] for col in cursor.description]
                result = [dict(zip(columns, row)) for row in rows]

            return Response(result, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def post(self, request, *args, **kwargs):
        """Add a new authorization record for a client"""
        data = request.data

        required_fields = ['Authorization_name', 'Service', 'start_date', 'end_date',
                           'allowed_limit', 'unit_type', 'per_unit', 'clients_ID']

        for field in required_fields:
            if not data.get(field):
                return Response({"error": f"{field} is required."}, status=status.HTTP_400_BAD_REQUEST)

        insert_query = """
            INSERT INTO Authorization (
                Authorization_name, Service, start_date, end_date,
                allowed_limit, unit_type, per_unit, clients_ID
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """

        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT ID FROM clients WHERE ID = %s", [data.get('clients_ID')]
                )
                client_exists = cursor.fetchone()

                if not client_exists:
                    return Response({"error": "Client ID does not exist."}, status=status.HTTP_400_BAD_REQUEST)

                cursor.execute(insert_query, (
                    data.get('Authorization_name'), data.get('Service'), data.get('start_date'), data.get('end_date'),
                    data.get('allowed_limit'), data.get('unit_type'), data.get('per_unit'), data.get('clients_ID')
                ))

            return Response({"message": "Authorization record added successfully."}, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


from datetime import datetime, timedelta

class AuthorizationExpiryView(APIView):
    def get(self, request, *args, **kwargs):
        """
        Get all clients whose authorization expires within next 30 days.
        """
        today = datetime.now().date()
        expiry_limit = today + timedelta(days=30)

        query = """
            SELECT c.ID as client_id, c.FirstName, c.LastName, a.Auth_id, a.Authorization_name, a.start_date, a.end_date
            FROM clients c
            JOIN Authorization a ON c.ID = a.clients_ID
            WHERE a.end_date BETWEEN %s AND %s
            ORDER BY a.end_date ASC;
        """
        params = [today, expiry_limit]

        try:
            with connection.cursor() as cursor:
                cursor.execute(query, params)
                rows = cursor.fetchall()

                if not rows:
                    return Response({"message": "No authorizations expiring within 30 days."}, status=status.HTTP_404_NOT_FOUND)

                columns = [col[0] for col in cursor.description]
                results = [dict(zip(columns, row)) for row in rows]

            return Response(results, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
import traceback
        
class ContactViewByClientsID(APIView):
    def get(self, request, clients_id, *args, **kwargs):
        """
        Retrieve all contact records associated with a specific client ID.
        """
        query = """
            SELECT id, clients_ID, firstname, middlename, lastname, relationship,
                   street, city, state, zipcode, addressnotes, mobilephone,
                   otherphone, email
            FROM contacts
            WHERE clients_ID = %s
        """
 
        try:
            with connection.cursor() as cursor:
                cursor.execute(query, [clients_id])
                rows = cursor.fetchall()
 
                if not rows:
                    return Response(
                        {"message": "No contacts found for this client."},
                        status=status.HTTP_404_NOT_FOUND
                    )
 
                columns = [col[0] for col in cursor.description]
                result = [dict(zip(columns, row)) for row in rows]
 
            return Response(result, status=status.HTTP_200_OK)
 
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
 
    def post(self, request, clients_id, *args, **kwargs):
        """
        Create a new contact record for a specific client.
        """
        data = request.data
        required_fields = [
            'firstname', 'lastname', 'relationship',
            'street', 'city', 'state', 'zipcode',
            'addressnotes', 'mobilephone', 'email'
        ]
 
        missing_fields = [field for field in required_fields if not data.get(field)]
        if missing_fields:
            return Response(
                {"error": f"Missing required fields: {', '.join(missing_fields)}"},
                status=status.HTTP_400_BAD_REQUEST
            )
 
        insert_query = """
            INSERT INTO contacts (
                clients_ID, firstname, middlename, lastname, relationship,
                street, city, state, zipcode, addressnotes, mobilephone,
                otherphone, email
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
 
        try:
            with connection.cursor() as cursor:
                # Validate client existence
                cursor.execute("SELECT ID FROM clients WHERE ID = %s", [clients_id])
                if not cursor.fetchone():
                    return Response({"error": "Client ID does not exist."}, status=status.HTTP_400_BAD_REQUEST)
 
                # Insert contact
                cursor.execute(insert_query, (
                    clients_id,
                    data.get('firstname'),
                    data.get('middlename'),
                    data.get('lastname'),
                    data.get('relationship'),
                    data.get('street'),
                    data.get('city'),
                    data.get('state'),
                    data.get('zipcode'),
                    data.get('addressnotes'),
                    data.get('mobilephone'),
                    data.get('otherphone'),
                    data.get('email')
                ))
 
            return Response({"message": "Contact record added successfully."}, status=status.HTTP_201_CREATED)
 
        except Exception as e:
            traceback.print_exc()
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
 