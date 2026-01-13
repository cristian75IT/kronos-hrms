"""
KRONOS Auth - Keycloak Sync Service

Handles synchronization of users between Keycloak and local database.
"""
from datetime import datetime
from typing import Optional
from uuid import UUID

from keycloak import KeycloakAdmin, KeycloakOpenIDConnection
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import settings
from src.services.auth.repository import UserRepository
from src.services.auth.schemas import KeycloakSyncRequest, KeycloakSyncResponse
from src.shared.audit_client import get_audit_logger


class KeycloakSyncService:
    """Service for Keycloak synchronization operations."""

    def __init__(self, session: AsyncSession, user_repo: UserRepository) -> None:
        self._session = session
        self._user_repo = user_repo
        self._audit = get_audit_logger("auth-service")

    def _get_keycloak_admin(self) -> KeycloakAdmin:
        """Get authenticated Keycloak Admin client."""
        connection = KeycloakOpenIDConnection(
            server_url=settings.keycloak_url,
            realm_name=settings.keycloak_realm,
            client_id=settings.keycloak_client_id,
            client_secret_key=settings.keycloak_client_secret,
            verify=True
        )
        return KeycloakAdmin(connection=connection)

    async def sync_from_keycloak(self, request: KeycloakSyncRequest) -> KeycloakSyncResponse:
        """Sync all users from Keycloak.
        
        This is an admin operation that fetches all users from
        Keycloak and syncs them to the local database.
        """
        try:
            keycloak_connection = KeycloakOpenIDConnection(
                server_url=settings.keycloak_url,
                realm_name=settings.keycloak_realm,
                client_id=settings.keycloak_client_id,
                client_secret_key=settings.keycloak_client_secret,
            )
            keycloak_admin = KeycloakAdmin(connection=keycloak_connection)
            
            kc_users = keycloak_admin.get_users({})
            
            synced = 0
            created = 0
            updated = 0
            deactivated = 0
            errors = []
            
            keycloak_ids_seen = set()
            
            for kc_user in kc_users:
                try:
                    kc_id = kc_user.get("id")
                    if not kc_id:
                        continue
                    
                    keycloak_ids_seen.add(kc_id)
                    
                    kc_roles = keycloak_admin.get_realm_roles_of_user(kc_id)
                    role_names = [r.get("name") for r in kc_roles]
                    
                    has_otp = False
                    try:
                        creds = keycloak_admin.get_user_credentials(kc_id)
                        has_otp = any(c.get("type") == "otp" for c in creds)
                    except Exception:
                        pass
                    
                    local_user = await self._user_repo.get_by_keycloak_id(kc_id)
                    
                    if local_user:
                        await self._user_repo.update(
                            local_user.id,
                            email=kc_user.get("email", local_user.email),
                            username=kc_user.get("username", local_user.username),
                            first_name=kc_user.get("firstName", local_user.first_name),
                            last_name=kc_user.get("lastName", local_user.last_name),
                            is_admin="admin" in role_names,
                            is_manager="manager" in role_names,
                            is_approver="approver" in role_names,
                            is_hr="hr" in role_names,
                            is_employee="employee" in role_names,
                            is_active=kc_user.get("enabled", True),
                            mfa_enabled=has_otp,
                            last_sync_at=datetime.utcnow(),
                        )
                        updated += 1
                    else:
                        new_user = await self._user_repo.create(
                            keycloak_id=kc_id,
                            email=kc_user.get("email", f"{kc_id}@unknown"),
                            username=kc_user.get("username") or kc_user.get("email", f"{kc_id}@unknown"),
                            first_name=kc_user.get("firstName", ""),
                            last_name=kc_user.get("lastName", ""),
                            is_admin="admin" in role_names,
                            is_manager="manager" in role_names,
                            is_approver="approver" in role_names,
                            is_hr="hr" in role_names,
                            is_employee="employee" in role_names,
                            is_active=kc_user.get("enabled", True),
                            mfa_enabled=has_otp,
                            last_sync_at=datetime.utcnow(),
                        )
                        created += 1
                        
                        await self._audit.log_action(
                            action="CREATE",
                            resource_type="USER",
                            resource_id=str(new_user.id),
                            description=f"User synced from Keycloak: {new_user.email}",
                            request_data={"keycloak_id": kc_id, "roles": role_names},
                        )
                    
                    synced += 1
                    
                except Exception as e:
                    errors.append(f"Error syncing user {kc_user.get('email', 'unknown')}: {str(e)}")
            
            if request.force_full_sync:
                all_local = await self._user_repo.get_all(active_only=False, limit=10000, offset=0)
                for local_user in all_local:
                    if local_user.keycloak_id not in keycloak_ids_seen:
                        if local_user.is_active:
                            await self._user_repo.deactivate(local_user.id)
                            deactivated += 1
            
            return KeycloakSyncResponse(
                synced=synced,
                created=created,
                updated=updated,
                deactivated=deactivated,
                errors=errors,
            )
            
        except Exception as e:
            return KeycloakSyncResponse(
                synced=0,
                created=0,
                updated=0,
                deactivated=0,
                errors=[f"Keycloak connection error: {str(e)}"],
            )

    async def get_or_create_from_token(
        self,
        keycloak_id: str,
        email: str,
        username: str,
        first_name: str,
        last_name: str,
        roles: list[str],
    ):
        """Get existing user or create from Keycloak token.
        
        Called on first login to ensure user exists in local DB.
        """
        user = await self._user_repo.get_by_keycloak_id(keycloak_id)
        
        if user:
            await self._user_repo.update(
                user.id,
                is_admin="admin" in roles,
                is_manager="manager" in roles,
                is_approver="approver" in roles,
                is_hr="hr" in roles,
                is_employee="employee" in roles,
                last_sync_at=datetime.utcnow(),
            )
            return user
        
        if email:
            existing_by_email = await self._user_repo.get_by_email(email)
            if existing_by_email:
                await self._user_repo.update(
                    existing_by_email.id,
                    keycloak_id=keycloak_id,
                    username=username or existing_by_email.username,
                    first_name=first_name or existing_by_email.first_name,
                    last_name=last_name or existing_by_email.last_name,
                    is_admin="admin" in roles,
                    is_manager="manager" in roles,
                    is_approver="approver" in roles,
                    is_hr="hr" in roles,
                    is_employee="employee" in roles,
                    last_sync_at=datetime.utcnow(),
                )
                return await self._user_repo.get_by_keycloak_id(keycloak_id)
        
        base_username = username or email
        final_username = base_username
        counter = 1
        
        while True:
            existing_user = await self._user_repo.get_by_username(final_username)
            if not existing_user:
                break
            final_username = f"{base_username}_{counter}"
            counter += 1

        await self._user_repo.create(
            keycloak_id=keycloak_id,
            email=email,
            username=final_username,
            first_name=first_name or email.split("@")[0],
            last_name=last_name or "",
            is_admin="admin" in roles,
            is_manager="manager" in roles,
            is_approver="approver" in roles,
            is_hr="hr" in roles,
            is_employee="employee" in roles,
            last_sync_at=datetime.utcnow(),
        )
        return await self._user_repo.get_by_keycloak_id(keycloak_id)
