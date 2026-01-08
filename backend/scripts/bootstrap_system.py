#!/usr/bin/env python3
"""
KRONOS - System Bootstrap Script
Consolidates all essential setup tasks for a clean system initialization:
1. Database Schema Creation
2. RBAC Seeding (Permissions & Roles)
3. Superadmin User Creation
4. Superadmin Role Assignment
5. Email Templates Seeding
"""
import asyncio
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from uuid import UUID, uuid4

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text
from sqlalchemy.orm import sessionmaker
from src.core.database import engine as async_engine, async_session_factory
from src.services.auth.models import User
from src.services.notifications.models import EmailTemplate, NotificationType

# ═══════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════

SCHEMAS = ["auth", "leaves", "expenses", "config", "notifications", "audit", "calendar", "hr_reporting", "approvals", "time_wallet", "wallet"]

# Updated Permissions with Org/Exec Management
PERMISSIONS = [
    # Users & Org Management
    ("users:view", "USERS", "VIEW", "Visualizza Utenti", "Permette di visualizzare la lista utenti"),
    ("users:create", "USERS", "CREATE", "Crea Utenti", "Permette di creare nuovi utenti"),
    ("users:edit", "USERS", "EDIT", "Modifica Utenti", "Permette di modificare i dati utente"),
    ("users:delete", "USERS", "DELETE", "Elimina Utenti", "Permette di disattivare/eliminare utenti"),
    ("users:roles", "USERS", "ROLES", "Gestione Ruoli Utente", "Permette di assegnare ruoli agli utenti"),
    ("org:manage", "ORGANIZATION", "MANAGE", "Gestione Organigramma", "Gestione Dipartimenti e Servizi"),
    ("exec_levels:manage", "EXECUTIVE_LEVELS", "MANAGE", "Gestione Livelli Esecutivi", "Gestione gerarchia C-Suite"),
    
    # Assenze (Ferire/Permessi)
    ("leaves:view", "LEAVES", "VIEW", "Visualizza Ferie", "Permette di visualizzare richieste ferie"),
    ("leaves:create", "LEAVES", "CREATE", "Richiedi Ferie", "Permette di creare richieste ferie"),
    ("leaves:manage", "LEAVES", "MANAGE", "Gestione Completa Assenze", "Accesso completo alla gestione HR"),
    ("leaves:approve", "LEAVES", "APPROVE", "Approva Assenze", "Permette di approvare/rifiutare assenze"),
    
    # Trasferte e Spese
    ("trips:manage", "TRIPS", "MANAGE", "Gestione Trasferte", "Accesso completo gestione trasferte"),
    ("expenses:manage", "EXPENSES", "MANAGE", "Gestione Spese", "Accesso completo gestione spese"),
    
    # Configurazioni & Approvazioni
    ("approvals:config", "APPROVALS", "CONFIG", "Configura Workflow", "Configura i flussi di approvazione"),
    ("approvals:process", "APPROVALS", "PROCESS", "Processa Approvazioni", "Approva/rifiuta richieste"),
    ("settings:edit", "SETTINGS", "EDIT", "Impostazioni Sistema", "Modifica configurazioni globali"),
    
    # Altro
    ("calendar:manage", "CALENDAR", "MANAGE", "Gestione Calendari", "Configura festività e calendari"),
    ("notifications:send", "NOTIFICATIONS", "SEND", "Invia Notifiche", "Invia comunicazioni bulk"),
    ("reports:view", "REPORTS", "VIEW", "Visualizza Report", "Accesso alla sezione analytics"),
    ("audit:view", "AUDIT", "VIEW", "Visualizza Audit", "Monitoraggio log di sistema"),
    ("wiki:edit", "WIKI", "EDIT", "Gestione Documenti", "Modifica wiki e documenti"),
]

# Roles Mapping
ROLES = [
    {
        "name": "admin",
        "display_name": "Amministratore",
        "description": "Accesso completo al sistema (System Admin)",
        "permissions": [p[0] for p in PERMISSIONS] # All permissions
    },
    {
        "name": "hr",
        "display_name": "Risorse Umane",
        "description": "Responsabile Personale",
        "permissions": [
            "users:view", "users:create", "users:edit", "org:manage", "exec_levels:manage",
            "leaves:view", "leaves:manage", "leaves:approve", "trips:manage", "expenses:manage",
            "approvals:view", "calendar:manage", "notifications:send", "reports:view", "wiki:edit"
        ]
    },
    {
        "name": "manager",
        "display_name": "Manager",
        "description": "Responsabile di Team",
        "permissions": ["users:view", "leaves:view", "leaves:approve", "approvals:process", "reports:view"]
    },
    {
        "name": "employee",
        "display_name": "Dipendente",
        "description": "Utente Base",
        "permissions": ["leaves:create", "leaves:view"]
    }
]

# Superadmin Info
ADMIN_ID = UUID("3a5b855c-e426-42e0-a51a-210fc1ac3f61")

# Default Templates (Mini version from seed_templates.py)
DEFAULT_TEMPLATES = [
    {
        "code": "generic_notification",
        "name": "Notifica Generica",
        "subject": "{{title}}",
        "type": "INFO"
    },
    {
        "code": "leave_request_submitted",
        "name": "Richiesta Ferie Inviata",
        "subject": "Richiesta Ferie Inviata - {{leave_type}}",
        "type": "LEAVE_REQUEST_SUBMITTED"
    }
]

# ═══════════════════════════════════════════════════════════
# EXECUTION STEPS
# ═══════════════════════════════════════════════════════════

async def bootstrap():
    print("🚀🚀 KRONOS SYSTEM BOOTSTRAP 🚀🚀\n")
    
    async with async_session_factory() as session:
        # 1. Schemas
        print("🔧 Step 1: Creating Database Schemas...")
        for schema in SCHEMAS:
            await session.execute(text(f"CREATE SCHEMA IF NOT EXISTS {schema}"))
        print("   ✓ All schemas verified.\n")
        
        # 2. Permissions
        print("🔐 Step 2: Seeding RBAC Permissions...")
        perm_map = {}
        for code, res, act, name, desc in PERMISSIONS:
            result = await session.execute(text("SELECT id FROM auth.permissions WHERE code = :code"), {"code": code})
            p_id = result.scalar()
            if not p_id:
                p_id = uuid4()
                await session.execute(text(
                    "INSERT INTO auth.permissions (id, code, resource, action, name, description) "
                    "VALUES (:id, :code, :res, :act, :name, :desc)"
                ), {"id": p_id, "code": code, "res": res, "act": act, "name": name, "desc": desc})
                print(f"   + Permission: {code}")
            perm_map[code] = p_id
            
        # 3. Roles
        print("\n👥 Step 3: Seeding Roles and Linking Permissions...")
        role_map = {}
        for r in ROLES:
            result = await session.execute(text("SELECT id FROM auth.roles WHERE name = :name"), {"name": r["name"]})
            r_id = result.scalar()
            if not r_id:
                r_id = uuid4()
                await session.execute(text(
                    "INSERT INTO auth.roles (id, name, display_name, description, is_system) "
                    "VALUES (:id, :name, :dname, :desc, true)"
                ), {"id": r_id, "name": r["name"], "dname": r["display_name"], "desc": r["description"]})
                print(f"   + Role: {r['name']}")
            role_map[r["name"]] = r_id
            
            # Link permissions
            await session.execute(text("DELETE FROM auth.role_permissions WHERE role_id = :r_id"), {"r_id": r_id})
            for p_code in r["permissions"]:
                if p_code in perm_map:
                    await session.execute(text(
                        "INSERT INTO auth.role_permissions (role_id, permission_id, scope) VALUES (:r_id, :p_id, 'GLOBAL')"
                    ), {"r_id": r_id, "p_id": perm_map[p_code]})
        
        # 4. Superadmin User
        print("\n👤 Step 4: Creating Superadmin User...")
        admin = await session.get(User, ADMIN_ID)
        if not admin:
            admin = User(
                id=ADMIN_ID,
                keycloak_id="456255c9-3f01-42c1-87b6-1f9240b4087b",
                email="cristian@example.com",
                username="cristian",
                first_name="Cristian",
                last_name="Manager",
                is_admin=True,
                is_manager=True,
                is_employee=True,
                is_active=True
            )
            session.add(admin)
            await session.flush()  # Persist user before FK-dependent inserts
            print("   + User: cristian@example.com")
        
        # 5. Link Admin Role
        print("\n🔗 Step 5: Assigning 'admin' role to Superadmin...")
        result = await session.execute(text(
            "SELECT 1 FROM auth.user_roles WHERE user_id = :uid AND role_name = 'admin'"
        ), {"uid": ADMIN_ID})
        if not result.scalar():
            await session.execute(text(
                "INSERT INTO auth.user_roles (id, user_id, role_name, scope) VALUES (:id, :uid, 'admin', 'GLOBAL')"
            ), {"id": uuid4(), "uid": ADMIN_ID})
            print("   ✓ Role 'admin' linked to user.")
            
        # 6. Templates
        print("\n📧 Step 6: Seeding Essential Email Templates...")
        for t in DEFAULT_TEMPLATES:
            # Check exist
            result = await session.execute(text("SELECT 1 FROM notifications.email_templates WHERE code = :code"), {"code": t["code"]})
            if not result.scalar():
                await session.execute(text(
                    "INSERT INTO notifications.email_templates (id, code, name, subject, notification_type, is_active, html_content, text_content) "
                    "VALUES (:id, :code, :name, :subject, :type, true, '<html><body>Placeholder</body></html>', 'Placeholder')"
                ), {"id": uuid4(), "code": t["code"], "name": t["name"], "subject": t["subject"], "type": t["type"]})
                print(f"   + Template: {t['code']}")

        # 7. Contract Types
        print("\n📝 Step 7: Seeding Base Contract Types...")
        CONTRACT_TYPES = [
            {"code": "FT", "name": "Full Time 100%", "is_pt": False, "pct": 100.0},
            {"code": "PT50", "name": "Part Time 50%", "is_pt": True, "pct": 50.0},
            {"code": "PT75", "name": "Part Time 75%", "is_pt": True, "pct": 75.0},
        ]
        for ct in CONTRACT_TYPES:
            result = await session.execute(text("SELECT 1 FROM config.contract_types WHERE code = :code"), {"code": ct["code"]})
            if not result.scalar():
                await session.execute(text(
                    "INSERT INTO config.contract_types (id, code, name, is_part_time, part_time_percentage) "
                    "VALUES (:id, :code, :name, :is_pt, :pct)"
                ), {"id": uuid4(), "code": ct["code"], "name": ct["name"], "is_pt": ct["is_pt"], "pct": ct["pct"]})
                print(f"   + Contract Type: {ct['code']}")

        await session.commit()
        print("\n🎉🎉 SYSTEM BOOTSTRAP COMPLETE! 🎉🎉")
        print("You can now login as Cristian and use the System Initialization UI.")

if __name__ == "__main__":
    asyncio.run(bootstrap())
