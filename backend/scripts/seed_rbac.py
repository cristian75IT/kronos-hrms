"""
KRONOS - Seed RBAC Permissions and Roles
Populates the auth.permissions and auth.roles tables with enterprise RBAC structure.
"""
import asyncio
from uuid import uuid4

# Setup path for imports
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text
from src.core.database import async_session_factory

# ═══════════════════════════════════════════════════════════
# Permission Definitions
# Format: (code, resource, action, name, description)
# ═══════════════════════════════════════════════════════════

PERMISSIONS = [
    # Users Management
    ("users:view", "USERS", "VIEW", "Visualizza Utenti", "Permette di visualizzare la lista utenti"),
    ("users:create", "USERS", "CREATE", "Crea Utenti", "Permette di creare nuovi utenti"),
    ("users:edit", "USERS", "EDIT", "Modifica Utenti", "Permette di modificare i dati utente"),
    ("users:delete", "USERS", "DELETE", "Elimina Utenti", "Permette di disattivare/eliminare utenti"),
    ("users:roles", "USERS", "ROLES", "Gestione Ruoli Utente", "Permette di assegnare ruoli agli utenti"),
    
    # Leaves
    ("leaves:view", "LEAVES", "VIEW", "Visualizza Ferie", "Permette di visualizzare richieste ferie"),
    ("leaves:create", "LEAVES", "CREATE", "Richiedi Ferie", "Permette di creare richieste ferie"),
    ("leaves:edit", "LEAVES", "EDIT", "Modifica Ferie", "Permette di modificare richieste ferie"),
    ("leaves:delete", "LEAVES", "DELETE", "Annulla Ferie", "Permette di annullare richieste ferie"),
    ("leaves:approve", "LEAVES", "APPROVE", "Approva Ferie", "Permette di approvare/rifiutare ferie"),
    ("leaves:manage", "LEAVES", "MANAGE", "Gestione Completa Ferie", "Accesso completo alla gestione ferie HR"),
    
    # Trips
    ("trips:view", "TRIPS", "VIEW", "Visualizza Trasferte", "Permette di visualizzare trasferte"),
    ("trips:create", "TRIPS", "CREATE", "Richiedi Trasferta", "Permette di creare richieste trasferta"),
    ("trips:edit", "TRIPS", "EDIT", "Modifica Trasferte", "Permette di modificare trasferte"),
    ("trips:delete", "TRIPS", "DELETE", "Annulla Trasferte", "Permette di annullare trasferte"),
    ("trips:approve", "TRIPS", "APPROVE", "Approva Trasferte", "Permette di approvare/rifiutare trasferte"),
    ("trips:manage", "TRIPS", "MANAGE", "Gestione Completa Trasferte", "Accesso completo alla gestione trasferte HR"),
    
    # Expenses
    ("expenses:view", "EXPENSES", "VIEW", "Visualizza Note Spese", "Permette di visualizzare note spese"),
    ("expenses:create", "EXPENSES", "CREATE", "Crea Nota Spese", "Permette di creare note spese"),
    ("expenses:edit", "EXPENSES", "EDIT", "Modifica Note Spese", "Permette di modificare note spese"),
    ("expenses:delete", "EXPENSES", "DELETE", "Elimina Note Spese", "Permette di eliminare note spese"),
    ("expenses:approve", "EXPENSES", "APPROVE", "Approva Note Spese", "Permette di approvare/rifiutare spese"),
    ("expenses:manage", "EXPENSES", "MANAGE", "Gestione Completa Spese", "Accesso completo alla gestione spese HR"),
    
    # Approvals
    ("approvals:view", "APPROVALS", "VIEW", "Visualizza Approvazioni", "Permette di vedere richieste in attesa"),
    ("approvals:process", "APPROVALS", "PROCESS", "Processa Approvazioni", "Permette di approvare/rifiutare richieste"),
    ("approvals:config", "APPROVALS", "CONFIG", "Configura Workflow", "Permette di configurare workflow approvazione"),
    
    # Calendar
    ("calendar:view", "CALENDAR", "VIEW", "Visualizza Calendario", "Permette di visualizzare calendari"),
    ("calendar:edit", "CALENDAR", "EDIT", "Modifica Calendario", "Permette di modificare eventi"),
    ("calendar:manage", "CALENDAR", "MANAGE", "Gestione Calendari Sistema", "Gestione calendari di sistema"),
    
    # Notifications
    ("notifications:view", "NOTIFICATIONS", "VIEW", "Visualizza Notifiche", "Visualizza le proprie notifiche"),
    ("notifications:send", "NOTIFICATIONS", "SEND", "Invia Notifiche", "Permette di inviare notifiche bulk"),
    ("notifications:templates", "NOTIFICATIONS", "TEMPLATES", "Gestione Template", "Gestione template email"),
    ("notifications:settings", "NOTIFICATIONS", "SETTINGS", "Impostazioni Email", "Configura provider email"),
    
    # Reports
    ("reports:view", "REPORTS", "VIEW", "Visualizza Report", "Accesso ai report HR"),
    ("reports:export", "REPORTS", "EXPORT", "Esporta Report", "Esportazione report"),
    ("reports:advanced", "REPORTS", "ADVANCED", "Report Avanzati", "Accesso a report avanzati e analytics"),
    
    # Audit
    ("audit:view", "AUDIT", "VIEW", "Visualizza Audit Log", "Accesso ai log di audit"),
    ("audit:export", "AUDIT", "EXPORT", "Esporta Audit", "Esportazione log audit"),
    
    # Admin Settings
    ("settings:view", "SETTINGS", "VIEW", "Visualizza Impostazioni", "Visualizza configurazioni sistema"),
    ("settings:edit", "SETTINGS", "EDIT", "Modifica Impostazioni", "Modifica configurazioni sistema"),
    
    # RBAC Management
    ("roles:view", "ROLES", "VIEW", "Visualizza Ruoli", "Visualizza ruoli e permessi"),
    ("roles:edit", "ROLES", "EDIT", "Modifica Ruoli", "Modifica assegnazione permessi ai ruoli"),
    
    # Training
    ("training:view", "TRAINING", "VIEW", "Visualizza Formazione", "Visualizza record formazione"),
    ("training:manage", "TRAINING", "MANAGE", "Gestione Formazione", "Gestione completa formazione"),
    
    # Contracts
    ("contracts:view", "CONTRACTS", "VIEW", "Visualizza Contratti", "Visualizza contratti nazionali"),
    ("contracts:manage", "CONTRACTS", "MANAGE", "Gestione Contratti", "Gestione contratti CCNL"),
    
    # Wiki/Documents
    ("wiki:view", "WIKI", "VIEW", "Visualizza Documenti", "Accesso alla wiki/documenti"),
    ("wiki:edit", "WIKI", "EDIT", "Modifica Documenti", "Modifica wiki/documenti"),
]

# ═══════════════════════════════════════════════════════════
# Role Definitions with Default Permissions
# ═══════════════════════════════════════════════════════════

ROLES = [
    {
        "name": "admin",
        "display_name": "Amministratore",
        "description": "Accesso completo al sistema (bypass automatico)",
        "is_system": True,
        "permissions": [],  # Admin bypasses permission checks
    },
    {
        "name": "hr",
        "display_name": "Risorse Umane",
        "description": "Gestione completa HR",
        "is_system": True,
        "permissions": [
            "users:view", "users:create", "users:edit",
            "leaves:view", "leaves:manage", "leaves:approve",
            "trips:view", "trips:manage", "trips:approve",
            "expenses:view", "expenses:manage", "expenses:approve",
            "approvals:view", "approvals:process",
            "calendar:view", "calendar:manage",
            "notifications:view", "notifications:send", "notifications:templates",
            "reports:view", "reports:export", "reports:advanced",
            "training:view", "training:manage",
            "contracts:view", "contracts:manage",
            "wiki:view", "wiki:edit",
        ],
    },
    {
        "name": "manager",
        "display_name": "Manager",
        "description": "Responsabile di team",
        "is_system": True,
        "permissions": [
            "users:view",
            "leaves:view", "leaves:approve",
            "trips:view", "trips:approve",
            "expenses:view", "expenses:approve",
            "approvals:view", "approvals:process",
            "calendar:view",
            "notifications:view",
            "reports:view",
            "training:view",
            "wiki:view",
        ],
    },
    {
        "name": "approver",
        "display_name": "Approvatore",
        "description": "Può approvare richieste",
        "is_system": True,
        "permissions": [
            "leaves:view", "leaves:approve",
            "trips:view", "trips:approve",
            "expenses:view", "expenses:approve",
            "approvals:view", "approvals:process",
            "calendar:view",
            "notifications:view",
        ],
    },
    {
        "name": "employee",
        "display_name": "Dipendente",
        "description": "Utente base dipendente",
        "is_system": True,
        "permissions": [
            "leaves:view", "leaves:create", "leaves:edit", "leaves:delete",
            "trips:view", "trips:create", "trips:edit", "trips:delete",
            "expenses:view", "expenses:create", "expenses:edit", "expenses:delete",
            "calendar:view",
            "notifications:view",
            "wiki:view",
        ],
    },
    {
        "name": "dipendente",
        "display_name": "Dipendente (IT)",
        "description": "Alias italiano per employee",
        "is_system": True,
        "parent": "employee",  # Inherits from employee
        "permissions": [],
    },
]


async def seed_permissions_and_roles():
    """Seed permissions and roles into database."""
    async with async_session_factory() as session:
        # Set schema
        await session.execute(text("SET search_path TO auth, public"))
        
        print("🔐 Seeding RBAC Permissions and Roles...")
        
        # 1. Insert Permissions
        print("  📋 Inserting permissions...")
        permission_ids = {}
        
        for code, resource, action, name, description in PERMISSIONS:
            # Check if exists
            result = await session.execute(
                text("SELECT id FROM auth.permissions WHERE code = :code"),
                {"code": code}
            )
            existing = result.scalar_one_or_none()
            
            if existing:
                permission_ids[code] = existing
                print(f"    ✓ {code} (exists)")
            else:
                perm_id = uuid4()
                await session.execute(
                    text("""
                        INSERT INTO auth.permissions (id, code, resource, action, name, description)
                        VALUES (:id, :code, :resource, :action, :name, :description)
                    """),
                    {
                        "id": perm_id,
                        "code": code,
                        "resource": resource,
                        "action": action,
                        "name": name,
                        "description": description,
                    }
                )
                permission_ids[code] = perm_id
                print(f"    + {code}")
        
        # 2. Insert Roles
        print("\n  👥 Inserting roles...")
        role_ids = {}
        
        for role_data in ROLES:
            result = await session.execute(
                text("SELECT id FROM auth.roles WHERE name = :name"),
                {"name": role_data["name"]}
            )
            existing = result.scalar_one_or_none()
            
            if existing:
                role_ids[role_data["name"]] = existing
                print(f"    ✓ {role_data['name']} (exists)")
            else:
                role_id = uuid4()
                
                # Get parent_id if specified
                parent_id = None
                if "parent" in role_data and role_data["parent"] in role_ids:
                    parent_id = role_ids[role_data["parent"]]
                
                await session.execute(
                    text("""
                        INSERT INTO auth.roles (id, name, display_name, description, is_system, parent_id)
                        VALUES (:id, :name, :display_name, :description, :is_system, :parent_id)
                    """),
                    {
                        "id": role_id,
                        "name": role_data["name"],
                        "display_name": role_data["display_name"],
                        "description": role_data["description"],
                        "is_system": role_data.get("is_system", False),
                        "parent_id": parent_id,
                    }
                )
                role_ids[role_data["name"]] = role_id
                print(f"    + {role_data['name']}")
        
        # 3. Link Roles to Permissions
        print("\n  🔗 Linking roles to permissions...")
        for role_data in ROLES:
            role_id = role_ids[role_data["name"]]
            
            # Clear existing permissions for this role (to update)
            await session.execute(
                text("DELETE FROM auth.role_permissions WHERE role_id = :role_id"),
                {"role_id": role_id}
            )
            
            for perm_code in role_data.get("permissions", []):
                if perm_code in permission_ids:
                    await session.execute(
                        text("""
                            INSERT INTO auth.role_permissions (role_id, permission_id, scope)
                            VALUES (:role_id, :permission_id, 'GLOBAL')
                            ON CONFLICT DO NOTHING
                        """),
                        {
                            "role_id": role_id,
                            "permission_id": permission_ids[perm_code],
                        }
                    )
            
            perm_count = len(role_data.get("permissions", []))
            print(f"    ✓ {role_data['name']}: {perm_count} permissions")
        
        await session.commit()
        
        print("\n✅ RBAC seeding complete!")
        print(f"   - {len(PERMISSIONS)} permissions")
        print(f"   - {len(ROLES)} roles")


if __name__ == "__main__":
    asyncio.run(seed_permissions_and_roles())
