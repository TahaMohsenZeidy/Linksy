from keycloak import KeycloakOpenID
from keycloak.exceptions import KeycloakAuthenticationError
import os
import logging
import requests
import time

# Keycloak configuration from environment variables
KEYCLOAK_URL = os.getenv("KEYCLOAK_URL", "http://localhost:8080")
KEYCLOAK_REALM = os.getenv("KEYCLOAK_REALM", "linksy")
KEYCLOAK_CLIENT_ID = os.getenv("KEYCLOAK_CLIENT_ID", "linksy-backend")
KEYCLOAK_CLIENT_SECRET = os.getenv("KEYCLOAK_CLIENT_SECRET", "")

# Initialize Keycloak OpenID client (lazy initialization)
keycloak_openid = None

def get_keycloak_openid() -> KeycloakOpenID:
    """Get or create Keycloak OpenID client instance."""
    global keycloak_openid
    if keycloak_openid is None:
        keycloak_openid = KeycloakOpenID(
            server_url=KEYCLOAK_URL,
            client_id=KEYCLOAK_CLIENT_ID,
            realm_name=KEYCLOAK_REALM,
            client_secret_key=KEYCLOAK_CLIENT_SECRET,
            verify=True
        )
    return keycloak_openid


def authenticate_with_keycloak(username: str, password: str) -> dict:
    """
    Authenticate user with Keycloak and get access token.
    
    Returns:
        dict: Token information with 'access_token' and 'token_type'
    
    Raises:
        KeycloakAuthenticationError: If authentication fails
    """
    try:
        client = get_keycloak_openid()
        token = client.token(username, password)
        return {
            "access_token": token["access_token"],
            "token_type": "bearer",
            "refresh_token": token.get("refresh_token"),
            "expires_in": token.get("expires_in")
        }
    except KeycloakAuthenticationError as e:
        logging.warning(f"Keycloak authentication failed for user {username}: {str(e)}")
        raise


def verify_keycloak_token(token: str) -> dict:
    """
    Verify and decode Keycloak token.
    
    Returns:
        dict: Token payload with user information including:
            - keycloak_user_id: UUID from Keycloak (sub claim)
            - preferred_username: Username from Keycloak
            - email: Email from Keycloak
            - active: Whether token is active
    
    Raises:
        Exception: If token is invalid
    """
    try:
        # Verify token and get user info
        client = get_keycloak_openid()
        userinfo = client.userinfo(token)
        introspect = client.introspect(token)
        
        return {
            "keycloak_user_id": userinfo.get("sub"),  # UUID from Keycloak (sub claim)
            "preferred_username": userinfo.get("preferred_username"),
            "email": userinfo.get("email"),
            "active": introspect.get("active", False)
        }
    except Exception as e:
        logging.warning(f"Keycloak token verification failed: {str(e)}")
        raise


def create_user_in_keycloak(username: str, email: str, password: str, first_name: str = None, last_name: str = None, date_of_birth: str = None, phone_number: str = None) -> str:
    """
    Create a new user in Keycloak.
    
    Returns:
        str: Keycloak user ID
    
    Raises:
        Exception: If user creation fails
    """
    try:
        # Admin user exists in 'master' realm, get token using KeycloakOpenID
        keycloak_openid_master = KeycloakOpenID(
            server_url=KEYCLOAK_URL,
            client_id="admin-cli",  # Admin CLI client in master realm
            realm_name="master",
            verify=True
        )
        
        # Get admin token by authenticating with admin credentials
        admin_username = os.getenv("KEYCLOAK_ADMIN", "admin")
        admin_password = os.getenv("KEYCLOAK_ADMIN_PASSWORD", "admin")
        token_response = keycloak_openid_master.token(admin_username, admin_password)
        admin_token = token_response.get("access_token")
        
        # Create user via REST API in target realm (without password first)
        create_user_url = f"{KEYCLOAK_URL}/admin/realms/{KEYCLOAK_REALM}/users"
        headers = {
            "Authorization": f"Bearer {admin_token}",
            "Content-Type": "application/json"
        }
        
        # Create user without password first
        # Note: Don't set emailVerified=True initially - let Keycloak handle it naturally
        # Setting it to True can trigger required actions in some Keycloak configurations
        # Set default values for firstName and lastName - Keycloak may require these to be non-empty
        # Use username capitalized as default for firstName, "User" as default for lastName
        default_first_name = first_name or username.capitalize()
        default_last_name = last_name or "User"
        
        # Build user attributes for Keycloak (custom attributes)
        attributes = {}
        if date_of_birth:
            attributes["dateOfBirth"] = [date_of_birth]
        if phone_number:
            attributes["phoneNumber"] = [phone_number]
        
        user_data_no_password = {
            "username": username,
            "email": email,
            "firstName": default_first_name,
            "lastName": default_last_name,
            "enabled": True,
            "emailVerified": False,  # Set to False initially, will update later if needed
            "attributes": attributes if attributes else {}
        }
        
        response = requests.post(create_user_url, json=user_data_no_password, headers=headers, verify=True)
        response.raise_for_status()
        
        # Get the user ID from the Location header
        location = response.headers.get("Location")
        if location:
            user_id = location.split("/")[-1]
            logging.info(f"User {username} created in Keycloak with ID: {user_id}")
        else:
            # Fallback: search for the user to get ID
            search_url = f"{KEYCLOAK_URL}/admin/realms/{KEYCLOAK_REALM}/users"
            search_params = {"username": username}
            search_response = requests.get(search_url, headers=headers, params=search_params, verify=True)
            search_response.raise_for_status()
            users = search_response.json()
            if users:
                user_id = users[0]["id"]
                logging.info(f"User {username} found in Keycloak with ID: {user_id}")
            else:
                raise Exception("User created but ID not found")
        
        # Set password via separate API call (required for Keycloak)
        # Keycloak password reset endpoint expects credentials array format
        password_url = f"{KEYCLOAK_URL}/admin/realms/{KEYCLOAK_REALM}/users/{user_id}/reset-password"
        password_data = {
            "type": "password",
            "value": password,
            "temporary": False
        }
        
        logging.info(f"Setting password for user {username} (ID: {user_id})")
        password_response = requests.put(password_url, json=password_data, headers=headers, verify=True)
        
        if password_response.status_code not in [200, 204]:
            error_msg = f"Failed to set password for user {username}: {password_response.status_code} - {password_response.text}"
            logging.error(error_msg)
            raise Exception(error_msg)
        
        logging.info(f"Password set successfully for user {username} (ID: {user_id})")
        
        # Get current user data and update to ensure account is fully set up
        get_user_url = f"{KEYCLOAK_URL}/admin/realms/{KEYCLOAK_REALM}/users/{user_id}"
        get_user_response = requests.get(get_user_url, headers=headers, verify=True)
        if get_user_response.status_code == 200:
            user_data_current = get_user_response.json()
            
            # Update user to ensure enabled=True, requiredActions=[], and firstName/lastName are set
            # Keycloak requires the full user object, so merge our changes into the current data
            update_data = user_data_current.copy()
            
            # Set default values for firstName and lastName if they're empty
            if not update_data.get("firstName") or update_data.get("firstName") == "":
                update_data["firstName"] = username.capitalize()
            if not update_data.get("lastName") or update_data.get("lastName") == "":
                update_data["lastName"] = "User"
            
            # Preserve existing attributes if they exist, otherwise initialize empty dict
            if "attributes" not in update_data or update_data["attributes"] is None:
                update_data["attributes"] = {}
            
            # Ensure enabled=True and requiredActions=[] (critical for account to be fully set up)
            update_data.update({
                "enabled": True,
                "requiredActions": []
            })
            
            # Update user
            update_user_url = f"{KEYCLOAK_URL}/admin/realms/{KEYCLOAK_REALM}/users/{user_id}"
            update_response = requests.put(update_user_url, json=update_data, headers=headers, verify=True)
            
            if update_response.status_code not in [200, 204]:
                error_text = update_response.text if hasattr(update_response, 'text') else str(update_response.content)
                logging.warning(f"Failed to update user {username}: {update_response.status_code} - {error_text}")
            else:
                logging.info(f"Updated user {username} to ensure account is fully set up")
        else:
            logging.warning(f"Failed to get user data for {username}: {get_user_response.status_code}")
        
        # Add a small delay to ensure Keycloak processes the changes
        time.sleep(1)
        
        logging.info(f"User {username} created in Keycloak realm '{KEYCLOAK_REALM}' with ID: {user_id} and password set")
        return user_id
                
    except Exception as e:
        logging.error(f"Failed to create user in Keycloak: {str(e)}")
        raise

