"""Enterprise Audit Enhancements

Revision ID: 028_enterprise_audit
Revises: seed_generic_tmpl
Create Date: 2026-01-03
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


# revision identifiers, used by Alembic.
revision: str = '028_enterprise_audit'
down_revision: str = 'seed_generic_tmpl'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add enterprise audit enhancements."""
    
    # ═══════════════════════════════════════════════════════════════════
    # Performance Indexes for audit_logs
    # ═══════════════════════════════════════════════════════════════════
    
    # Index for filtering by user
    op.create_index(
        'ix_audit_logs_user_id',
        'audit_logs',
        ['user_id'],
        schema='audit'
    )
    
    # Index for filtering by resource
    op.create_index(
        'ix_audit_logs_resource',
        'audit_logs',
        ['resource_type', 'resource_id'],
        schema='audit'
    )
    
    # Index for filtering by date (most common query pattern)
    op.create_index(
        'ix_audit_logs_created_at',
        'audit_logs',
        ['created_at'],
        schema='audit',
        postgresql_using='btree'
    )
    
    # Composite index for common admin queries
    op.create_index(
        'ix_audit_logs_admin_query',
        'audit_logs',
        ['service_name', 'action', 'status', 'created_at'],
        schema='audit'
    )
    
    # ═══════════════════════════════════════════════════════════════════
    # Performance Indexes for audit_trail
    # ═══════════════════════════════════════════════════════════════════
    
    # Index for entity lookup
    op.create_index(
        'ix_audit_trail_entity',
        'audit_trail',
        ['entity_type', 'entity_id'],
        schema='audit'
    )
    
    # Index for user lookup
    op.create_index(
        'ix_audit_trail_changed_by',
        'audit_trail',
        ['changed_by'],
        schema='audit'
    )
    
    # Index for date filtering
    op.create_index(
        'ix_audit_trail_changed_at',
        'audit_trail',
        ['changed_at'],
        schema='audit',
        postgresql_using='btree'
    )
    
    # ═══════════════════════════════════════════════════════════════════
    # Audit Archive Table (for data retention)
    # ═══════════════════════════════════════════════════════════════════
    
    op.create_table(
        'audit_logs_archive',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', UUID(as_uuid=True), nullable=True),
        sa.Column('user_email', sa.String(255), nullable=True),
        sa.Column('action', sa.String(50), nullable=False),
        sa.Column('resource_type', sa.String(50), nullable=False),
        sa.Column('resource_id', sa.String(100), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('request_data', sa.dialects.postgresql.JSONB(), nullable=True),
        sa.Column('response_data', sa.dialects.postgresql.JSONB(), nullable=True),
        sa.Column('ip_address', sa.dialects.postgresql.INET(), nullable=True),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('endpoint', sa.String(255), nullable=True),
        sa.Column('http_method', sa.String(10), nullable=True),
        sa.Column('status', sa.String(20), nullable=False),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('service_name', sa.String(50), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('archived_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        schema='audit'
    )
    
    # Index for archived logs
    op.create_index(
        'ix_audit_logs_archive_created',
        'audit_logs_archive',
        ['created_at'],
        schema='audit'
    )
    
    # ═══════════════════════════════════════════════════════════════════
    # Audit Trail Archive Table
    # ═══════════════════════════════════════════════════════════════════
    
    op.create_table(
        'audit_trail_archive',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('entity_type', sa.String(50), nullable=False),
        sa.Column('entity_id', sa.String(100), nullable=False),
        sa.Column('version', sa.Integer(), nullable=False),
        sa.Column('operation', sa.String(10), nullable=False),
        sa.Column('before_data', sa.dialects.postgresql.JSONB(), nullable=True),
        sa.Column('after_data', sa.dialects.postgresql.JSONB(), nullable=True),
        sa.Column('changed_fields', sa.dialects.postgresql.JSONB(), nullable=True),
        sa.Column('changed_by', UUID(as_uuid=True), nullable=True),
        sa.Column('changed_by_email', sa.String(255), nullable=True),
        sa.Column('changed_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('change_reason', sa.Text(), nullable=True),
        sa.Column('service_name', sa.String(50), nullable=False),
        sa.Column('request_id', sa.String(100), nullable=True),
        sa.Column('archived_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        schema='audit'
    )
    
    # Index for archived trail
    op.create_index(
        'ix_audit_trail_archive_changed',
        'audit_trail_archive',
        ['changed_at'],
        schema='audit'
    )
    
    # ═══════════════════════════════════════════════════════════════════
    # Audit Statistics Materialized View
    # ═══════════════════════════════════════════════════════════════════
    
    op.execute("""
        CREATE MATERIALIZED VIEW IF NOT EXISTS audit.audit_daily_stats AS
        SELECT 
            DATE(created_at) as date,
            service_name,
            action,
            resource_type,
            status,
            COUNT(*) as count,
            COUNT(DISTINCT user_id) as unique_users
        FROM audit.audit_logs
        GROUP BY DATE(created_at), service_name, action, resource_type, status
        ORDER BY date DESC, count DESC;
    """)
    
    # Index on materialized view
    op.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS ix_audit_daily_stats_unique
        ON audit.audit_daily_stats (date, service_name, action, resource_type, status);
    """)
    
    # ═══════════════════════════════════════════════════════════════════
    # Archive Function
    # ═══════════════════════════════════════════════════════════════════
    
    op.execute("""
        CREATE OR REPLACE FUNCTION audit.archive_old_logs(retention_days INTEGER DEFAULT 90)
        RETURNS INTEGER AS $$
        DECLARE
            archived_count INTEGER;
            cutoff_date TIMESTAMP WITH TIME ZONE;
        BEGIN
            cutoff_date := NOW() - (retention_days || ' days')::INTERVAL;
            
            -- Archive audit_logs
            INSERT INTO audit.audit_logs_archive
            SELECT 
                id, user_id, user_email, action, resource_type, resource_id,
                description, request_data, response_data, ip_address, user_agent,
                endpoint, http_method, status, error_message, service_name,
                created_at, NOW()
            FROM audit.audit_logs
            WHERE created_at < cutoff_date;
            
            GET DIAGNOSTICS archived_count = ROW_COUNT;
            
            -- Delete archived records
            DELETE FROM audit.audit_logs
            WHERE created_at < cutoff_date;
            
            -- Archive audit_trail
            INSERT INTO audit.audit_trail_archive
            SELECT 
                id, entity_type, entity_id, version, operation,
                before_data, after_data, changed_fields,
                changed_by, changed_by_email, changed_at,
                change_reason, service_name, request_id, NOW()
            FROM audit.audit_trail
            WHERE changed_at < cutoff_date;
            
            DELETE FROM audit.audit_trail
            WHERE changed_at < cutoff_date;
            
            -- Refresh stats
            REFRESH MATERIALIZED VIEW audit.audit_daily_stats;
            
            RETURN archived_count;
        END;
        $$ LANGUAGE plpgsql;
    """)
    
    # ═══════════════════════════════════════════════════════════════════
    # Purge Archive Function (for GDPR compliance)
    # ═══════════════════════════════════════════════════════════════════
    
    op.execute("""
        CREATE OR REPLACE FUNCTION audit.purge_archives(archive_retention_days INTEGER DEFAULT 365)
        RETURNS INTEGER AS $$
        DECLARE
            purged_count INTEGER;
            cutoff_date TIMESTAMP WITH TIME ZONE;
        BEGIN
            cutoff_date := NOW() - (archive_retention_days || ' days')::INTERVAL;
            
            DELETE FROM audit.audit_logs_archive
            WHERE archived_at < cutoff_date;
            
            GET DIAGNOSTICS purged_count = ROW_COUNT;
            
            DELETE FROM audit.audit_trail_archive
            WHERE archived_at < cutoff_date;
            
            RETURN purged_count;
        END;
        $$ LANGUAGE plpgsql;
    """)


def downgrade() -> None:
    """Remove enterprise audit enhancements."""
    
    # Drop functions
    op.execute("DROP FUNCTION IF EXISTS audit.purge_archives(INTEGER)")
    op.execute("DROP FUNCTION IF EXISTS audit.archive_old_logs(INTEGER)")
    
    # Drop materialized view
    op.execute("DROP MATERIALIZED VIEW IF EXISTS audit.audit_daily_stats")
    
    # Drop archive tables
    op.drop_index('ix_audit_trail_archive_changed', table_name='audit_trail_archive', schema='audit')
    op.drop_table('audit_trail_archive', schema='audit')
    
    op.drop_index('ix_audit_logs_archive_created', table_name='audit_logs_archive', schema='audit')
    op.drop_table('audit_logs_archive', schema='audit')
    
    # Drop indexes from audit_trail
    op.drop_index('ix_audit_trail_changed_at', table_name='audit_trail', schema='audit')
    op.drop_index('ix_audit_trail_changed_by', table_name='audit_trail', schema='audit')
    op.drop_index('ix_audit_trail_entity', table_name='audit_trail', schema='audit')
    
    # Drop indexes from audit_logs
    op.drop_index('ix_audit_logs_admin_query', table_name='audit_logs', schema='audit')
    op.drop_index('ix_audit_logs_created_at', table_name='audit_logs', schema='audit')
    op.drop_index('ix_audit_logs_resource', table_name='audit_logs', schema='audit')
    op.drop_index('ix_audit_logs_user_id', table_name='audit_logs', schema='audit')
