
import sys
import os
import asyncio
from keycloak import KeycloakAdmin, KeycloakOpenIDConnection

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.core.config import settings

def setup_keycloak_mfa():
    print("Connecting to Keycloak...")
    
    kc_admin = None
    
    # 1. Try Master Admin (Common for dev environments)
    try:
        print("Attempting connection as 'admin' to 'master' realm...")
        connection = KeycloakOpenIDConnection(
            server_url=settings.keycloak_url,
            realm_name="master",
            user_realm_name="master",
            client_id="admin-cli",
            username="admin",
            password="admin", # Common dev default
            verify=True
        )
        kc_admin = KeycloakAdmin(connection=connection)
        print("✅ Connected as Master Admin")
    except Exception as e:
        print(f"⚠️ Could not connect as Master Admin: {e}")
        
    # 2. Try Client Credentials (if Master failed)
    if not kc_admin:
        try:
            print(f"Attempting connection as client '{settings.keycloak_client_id}' to '{settings.keycloak_realm}'...")
            connection = KeycloakOpenIDConnection(
                server_url=settings.keycloak_url,
                realm_name=settings.keycloak_realm,
                client_id=settings.keycloak_client_id,
                client_secret_key=settings.keycloak_client_secret,
                verify=True
            )
            kc_admin = KeycloakAdmin(connection=connection)
            print("✅ Connected as Client")
        except Exception as e:
            print(f"❌ Failed to connect with client credentials: {e}")
            sys.exit(1)

    realm_name = settings.keycloak_realm
    print(f"Updating Realm: {realm_name}")
    
    try:
        # Re-instantiate KeycloakAdmin to target the specific realm
        # reusing the authenticated connection
        kc_admin = KeycloakAdmin(connection=connection, realm_name=realm_name)
             
        # 3. Update OTP Policy
        otp_policy = {
            "otpPolicyType": "totp",
            "otpPolicyAlgorithm": "HmacSHA1",
            "otpPolicyInitialCounter": 0,
            "otpPolicyDigits": 6,
            "otpPolicyLookAheadWindow": 1,
            "otpPolicyPeriod": 30
        }
        
        kc_admin.update_realm(realm_name, otp_policy)
        print("✅ Realm OTP Policy Updated: TOTP, 6 Digits, 30s, HMAC-SHA1")
        
        # 4. Check Flows (Direct Grant)
        try:
            executions = kc_admin.get_authentication_flow_executions("direct-grant")
            otp_exec = next((e for e in executions if e['providerId'] == 'direct-grant-validate-otp'), None)
            
            if otp_exec:
                print(f"✅ Found Direct Grant OTP Execution: {otp_exec['id']} (Requirement: {otp_exec['requirement']})")
            else:
                print("⚠️ Warning: Could not find 'direct-grant-validate-otp' execution in 'direct-grant' flow.")
        except Exception as flow_error:
            print(f"⚠️ Could not inspect 'direct-grant' flow: {flow_error}")
            print("Listing available flows...")
            try:
                flows = kc_admin.get_authentication_flows()
                for f in flows:
                    if f.get('alias') in ['direct-grant', 'Direct Grant', 'browser']:
                        print(f" - Found flow: {f.get('alias')} (ID: {f.get('id')})")
            except:
                pass
    
    except Exception as e:
        print(f"❌ Error configuring Realm: {str(e)}")
        sys.exit(1)

    print("\nSUCCESS: Keycloak Realm MFA configuration Verified/Updated.")

if __name__ == "__main__":
    setup_keycloak_mfa()
