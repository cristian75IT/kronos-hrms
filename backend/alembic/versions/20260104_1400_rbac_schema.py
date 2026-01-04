"""rbac_schema

Revision ID: rbac_v1
Revises: 68fcec04557f
Create Date: 2026-01-04 14:00:00.000000

"""
from typing import Sequence, Union
from uuid import uuid4

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'rbac_v1'
down_revision: Union[str, None] = '68fcec04557f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create Roles Table
    op.create_table('roles',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('name', sa.String(), nullable=False, unique=True), # keycloak role name mapping
        sa.Column('display_name', sa.String(), nullable=True),
        sa.Column('description', sa.String(), nullable=True),
        sa.Column('is_system', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        schema='auth'
    )

    # 2. Create Create Permissions Table
    op.create_table('permissions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('code', sa.String(), nullable=False, unique=True), # resource:action e.g. leaves:read
        sa.Column('resource', sa.String(), nullable=False), # LEAVES
        sa.Column('action', sa.String(), nullable=False), # READ
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('description', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        schema='auth'
    )

    # 3. Join Table
    op.create_table('role_permissions',
        sa.Column('role_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('permission_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(['role_id'], ['auth.roles.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['permission_id'], ['auth.permissions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('role_id', 'permission_id'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        schema='auth'
    )

    # 4. Seed Data
    # Define Resources and Actions
    resources = {
        'LEAVES': ['read', 'create', 'update', 'delete', 'approve', 'manage_all'],
        'TRIPS': ['read', 'create', 'update', 'delete', 'approve', 'manage_all'],
        'EXPENSES': ['read', 'create', 'update', 'delete', 'approve', 'manage_all'],
        'HR': ['read', 'create', 'update', 'delete', 'manage_all'], # Training, Contracts
        'ADMIN': ['read', 'manage_settings', 'manage_users', 'manage_roles'],
        'USERS': ['read', 'create', 'update', 'delete'],
    }

    # Insert Permissions
    perms_data = []
    for res, actions in resources.items():
        for action in actions:
            code = f"{res.lower()}:{action}"
            name = f"{res.title()} {action.title()}"
            perms_data.append({
                'id': str(uuid4()), # We need IDs to link roles later, but using SQL INSERT ... RETURNING is hard in alembic op.execute batch.
                # Just insert code for now. Mappings will be manual or empty initially.
                # Actually user wants to configure them.
                'code': code,
                'resource': res,
                'action': action,
                'name': name
            })
    
    # We use raw execute for bulk insert
    if perms_data:
        values_str = ", ".join(
            f"(gen_random_uuid(), '{p['code']}', '{p['resource']}', '{p['action']}', '{p['name']}')"
            for p in perms_data
        )
        op.execute(f"INSERT INTO auth.permissions (id, code, resource, action, name) VALUES {values_str}")

    # Seed Roles
    roles_data = [
        ('admin', 'Amministratore', 'Accesso completo al sistema', True),
        ('hr', 'HR Manager', 'Gestione Risorse Umane', True),
        ('manager', 'Manager', 'Gestione Team', True),
        ('approver', 'Approvatore', 'Approvazione Richieste', True),
        ('employee', 'Dipendente', 'Accesso base', True)
    ]

    for r_name, r_disp, r_desc, r_sys in roles_data:
         op.execute(f"INSERT INTO auth.roles (id, name, display_name, description, is_system) VALUES (gen_random_uuid(), '{r_name}', '{r_disp}', '{r_desc}', {str(r_sys).lower()})")
    
    # Default Mappings (Admin gets everything)
    op.execute("""
        INSERT INTO auth.role_permissions (role_id, permission_id)
        SELECT r.id, p.id
        FROM auth.roles r, auth.permissions p
        WHERE r.name = 'admin'
    """)

    # HR gets HR stuff + Leaves/Trips manage
    op.execute("""
        INSERT INTO auth.role_permissions (role_id, permission_id)
        SELECT r.id, p.id
        FROM auth.roles r, auth.permissions p
        WHERE r.name = 'hr' 
        AND (
            p.resource IN ('HR', 'USERS') 
            OR (p.resource IN ('LEAVES', 'TRIPS', 'EXPENSES') AND p.action IN ('read', 'approve', 'manage_all'))
        )
    """)
    
    # Employee gets Create/Read own leaves (Logic for 'own' is implicitly handled by backend ownership checks, permissions usually cover 'access to feature')
    # Or strict 'leaves:create'?
    op.execute("""
        INSERT INTO auth.role_permissions (role_id, permission_id)
        SELECT r.id, p.id
        FROM auth.roles r, auth.permissions p
        WHERE r.name = 'employee' 
        AND p.action IN ('read', 'create', 'update', 'delete') -- Own resources usually
        AND p.resource IN ('LEAVES', 'TRIPS', 'EXPENSES')
    """)

def downgrade() -> None:
    op.drop_table('role_permissions', schema='auth')
    op.drop_table('permissions', schema='auth')
    op.drop_table('roles', schema='auth')
