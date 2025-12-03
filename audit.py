from extensions import db
from models import AuditLog


def log_action(user, action, entity_type, entity_id):
    """Create an audit log entry"""
    audit_log = AuditLog(
        tenant_id=user.tenant_id,
        user_id=user.id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id
    )
    db.session.add(audit_log)
    db.session.commit()

