"""
KRONOS Auth - MFA Service

Handles Multi-Factor Authentication (MFA/TOTP) operations via Keycloak.
"""
from typing import Optional
from uuid import UUID

import pyotp
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import settings
from src.core.exceptions import ConflictError
from src.services.auth.repository import UserRepository
from src.services.auth.schemas import MfaSetupResponse, MfaVerifyRequest
from src.shared.audit_client import get_audit_logger


class MfaService:
    """Service for MFA/TOTP operations."""
    
    # TOTP Credential Configuration (Keycloak format)
    TOTP_CREDENTIAL_CONFIG = {
        "algorithm": "TOTP",
        "digits": 6,
        "counter": 0,
        "period": 30
    }

    def __init__(self, session: AsyncSession, user_repo: UserRepository) -> None:
        self._session = session
        self._user_repo = user_repo
        self._audit = get_audit_logger("auth-service")

    def _get_keycloak_admin(self):
        """Get authenticated Keycloak Admin client."""
        from keycloak import KeycloakAdmin, KeycloakOpenIDConnection
        connection = KeycloakOpenIDConnection(
            server_url=settings.keycloak_url,
            realm_name=settings.keycloak_realm,
            client_id=settings.keycloak_client_id,
            client_secret_key=settings.keycloak_client_secret,
            verify=True
        )
        return KeycloakAdmin(connection=connection)

    async def verify_user_otp(self, user_id: UUID, code: str) -> bool:
        """
        Verify OTP code for a user by retrieving their secret from Keycloak.
        Used for internal verification (e.g. Digital Signature) without re-login.
        """
        import httpx
        
        user = await self._user_repo.get(user_id)
        if not user:
            raise ConflictError("Utente non trovato")
        if not user.mfa_enabled or not user.keycloak_id:
            raise ConflictError("MFA non è attivo per questo utente")

        try:
            kc_admin = self._get_keycloak_admin()
            token = kc_admin.token.get("access_token")
            headers = {"Authorization": f"Bearer {token}"}
            
            base_url = settings.keycloak_url.rstrip('/')
            realm = settings.keycloak_realm
            uid = user.keycloak_id
            
            api_url = f"{base_url}/admin/realms/{realm}/users/{uid}/credentials"
            
            async with httpx.AsyncClient(timeout=5.0) as client:
                res = await client.get(api_url, headers=headers)
                if not res.is_success:
                    api_url = f"{base_url}/auth/admin/realms/{realm}/users/{uid}/credentials"
                    res = await client.get(api_url, headers=headers)
                    
                if not res.is_success:
                    raise Exception(f"Failed to fetch credentials: {res.status_code}")
                
                credentials = res.json()
                
                otp_cred = next((c for c in credentials if c.get("type") == "otp"), None)
                if not otp_cred or "secretData" not in otp_cred:
                    raise ConflictError("Segreto MFA non trovato su Keycloak")
                
                secret = otp_cred["secretData"]
                totp = pyotp.TOTP(secret)
                return totp.verify(code)
                
        except ConflictError:
            raise
        except Exception as e:
            await self._audit.log_action(
                user_id=user_id, action="ERROR", resource_type="MFA_VERIFY", 
                description=f"Verification Error: {e}"
            )
            raise ConflictError(f"Errore tecnico verifica MFA: {str(e)}")

    async def setup_mfa(self, user_id: UUID, email: str, actor_id: Optional[UUID] = None) -> MfaSetupResponse:
        """Initialize MFA setup by generating a secret."""
        secret = pyotp.random_base32()
        otp_url = pyotp.totp.TOTP(secret).provisioning_uri(name=email, issuer_name="KRONOS")
        
        await self._audit.log_action(
            user_id=actor_id or user_id,
            action="SETUP_MFA",
            resource_type="USER",
            resource_id=str(user_id),
            description="Initiated 2FA setup"
        )
        
        return MfaSetupResponse(secret=secret, otp_url=otp_url)

    async def enable_mfa(self, user_id: UUID, request: MfaVerifyRequest, actor_id: Optional[UUID] = None) -> bool:
        """Verify code and enable MFA in Keycloak."""
        import json
        import httpx
        
        user = await self._user_repo.get(user_id)
        if not user:
            raise ConflictError("Utente non trovato")
        
        # 1. Verify Code with pyotp
        totp = pyotp.TOTP(request.secret)
        if not totp.verify(request.code):
            raise ConflictError("Codice OTP non valido o scaduto")
             
        # 2. Add Credential to Keycloak
        if user.keycloak_id:
            try:
                payload = {
                    "type": "otp",
                    "userLabel": request.label,
                    "secretData": request.secret,
                    "credentialData": json.dumps(self.TOTP_CREDENTIAL_CONFIG)
                }
                
                kc_admin = self._get_keycloak_admin()
                token = kc_admin.token.get("access_token")
                headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
                
                base_url = settings.keycloak_url.rstrip('/')
                realm = settings.keycloak_realm
                uid = user.keycloak_id
                api_url = f"{base_url}/admin/realms/{realm}/users/{uid}/credentials"
                
                async with httpx.AsyncClient(timeout=10.0) as client:
                    res = await client.post(api_url, json=payload, headers=headers)
                    
                    if res.status_code == 404:
                        api_url = f"{base_url}/auth/admin/realms/{realm}/users/{uid}/credentials"
                        res = await client.post(api_url, json=payload, headers=headers)
                    
                    if not res.is_success:
                        raise Exception(f"Keycloak returned {res.status_code}: {res.text}")
                
            except Exception as e:
                await self._audit.log_action(
                    user_id=actor_id, action="ERROR", resource_type="MFA", 
                    description=f"Keycloak MFA Error: {e}"
                )
                raise ConflictError(f"Errore attivazione 2FA su Keycloak: {str(e)}")
                 
        # 3. Audit
        await self._audit.log_action(
            user_id=actor_id,
            action="ENABLE_MFA",
            resource_type="USER",
            resource_id=str(user_id),
            description="Enabled 2FA (TOTP)"
        )
        
        # 4. Update local user status
        await self._user_repo.update(user_id, mfa_enabled=True)
        
        return True

    async def disable_mfa(self, user_id: UUID, code: str, actor_id: Optional[UUID] = None) -> bool:
        """Disable MFA for user by removing TOTP credential from Keycloak."""
        import httpx
        
        user = await self._user_repo.get(user_id)
        if not user:
            raise ConflictError("Utente non trovato")
        
        if not user.mfa_enabled:
            raise ConflictError("MFA non è attivo per questo utente")
        
        if not user.keycloak_id:
            raise ConflictError("Utente non sincronizzato con Keycloak")
        
        try:
            kc_admin = self._get_keycloak_admin()
            token = kc_admin.token.get("access_token")
            headers = {"Authorization": f"Bearer {token}"}
            
            base_url = settings.keycloak_url.rstrip('/')
            realm = settings.keycloak_realm
            uid = user.keycloak_id
            
            api_url = f"{base_url}/admin/realms/{realm}/users/{uid}/credentials"
            
            async with httpx.AsyncClient(timeout=10.0) as client:
                res = await client.get(api_url, headers=headers)
                if res.status_code == 404:
                    api_url = f"{base_url}/auth/admin/realms/{realm}/users/{uid}/credentials"
                    res = await client.get(api_url, headers=headers)
                
                if not res.is_success:
                    raise Exception(f"Keycloak returned {res.status_code}")
                
                credentials = res.json()
                
                otp_cred = next((c for c in credentials if c.get("type") == "otp"), None)
                if not otp_cred:
                    await self._user_repo.update(user_id, mfa_enabled=False)
                    return True
                
                cred_id = otp_cred.get("id")
                del_url = f"{api_url}/{cred_id}"
                del_res = await client.delete(del_url, headers=headers)
                
                if not del_res.is_success:
                    raise Exception(f"Failed to delete credential: {del_res.status_code}")
            
        except Exception as e:
            await self._audit.log_action(
                user_id=actor_id, action="ERROR", resource_type="MFA", 
                description=f"MFA Disable Error: {e}"
            )
            raise ConflictError(f"Errore disattivazione 2FA: {str(e)}")
        
        await self._audit.log_action(
            user_id=actor_id,
            action="DISABLE_MFA",
            resource_type="USER",
            resource_id=str(user_id),
            description="Disabled 2FA (TOTP)"
        )
        
        await self._user_repo.update(user_id, mfa_enabled=False)
        
        return True

    async def change_password(self, user_id: UUID, current_password: str, new_password: str, actor_id: Optional[UUID] = None) -> bool:
        """Change user's password via Keycloak."""
        import httpx
        
        user = await self._user_repo.get(user_id)
        if not user:
            raise ConflictError("Utente non trovato")
        
        if not user.keycloak_id:
            raise ConflictError("Utente non sincronizzato con Keycloak")
        
        try:
            token_url = f"{settings.keycloak_url}/realms/{settings.keycloak_realm}/protocol/openid-connect/token"
            
            async with httpx.AsyncClient(timeout=10.0) as client:
                # Verify current password
                verify_res = await client.post(token_url, data={
                    "client_id": settings.keycloak_client_id,
                    "grant_type": "password",
                    "username": user.username,
                    "password": current_password,
                })
                
                if verify_res.status_code != 200:
                    raise ConflictError("Password attuale non corretta")
                
                kc_admin = self._get_keycloak_admin()
                admin_token = kc_admin.token.get("access_token")
                headers = {"Authorization": f"Bearer {admin_token}", "Content-Type": "application/json"}
                
                base_url = settings.keycloak_url.rstrip('/')
                realm = settings.keycloak_realm
                uid = user.keycloak_id
                
                reset_url = f"{base_url}/admin/realms/{realm}/users/{uid}/reset-password"
                
                pwd_res = await client.put(reset_url, json={
                    "type": "password",
                    "value": new_password,
                    "temporary": False
                }, headers=headers)
                
                if pwd_res.status_code == 404:
                    reset_url = f"{base_url}/auth/admin/realms/{realm}/users/{uid}/reset-password"
                    pwd_res = await client.put(reset_url, json={
                        "type": "password",
                        "value": new_password,
                        "temporary": False
                    }, headers=headers)
                
                if not pwd_res.is_success:
                    raise Exception(f"Password update failed: {pwd_res.status_code}")
                    
        except ConflictError:
            raise
        except Exception as e:
            await self._audit.log_action(
                user_id=actor_id, action="ERROR", resource_type="PASSWORD", 
                description=f"Password Change Error: {e}"
            )
            raise ConflictError(f"Errore cambio password: {str(e)}")
        
        await self._audit.log_action(
            user_id=actor_id,
            action="CHANGE_PASSWORD",
            resource_type="USER",
            resource_id=str(user_id),
            description="User changed their password"
        )
        
        return True
