from sqlalchemy.ext.asyncio import AsyncSession

from src.models.audit_log import AuditLog


class AuditService:
    @staticmethod
    async def record(
        db: AsyncSession,
        action: str,
        *,
        actor_user_id: int | None = None,
        entity_type: str | None = None,
        entity_id: str | int | None = None,
        request_id: str | None = None,
        ip_address: str | None = None,
        metadata: dict | None = None,
    ) -> None:
        db.add(
            AuditLog(
                actor_user_id=actor_user_id,
                action=action,
                entity_type=entity_type,
                entity_id=str(entity_id) if entity_id is not None else None,
                request_id=request_id,
                ip_address=ip_address,
                metadata_json=metadata or {},
            )
        )
        await db.commit()
