from uuid import UUID
from decimal import Decimal
from datetime import date, datetime
from typing import List, Optional
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload


class InventoryService:
    """Service layer for inventory module (BR-INV-001 through BR-INV-005)."""

    def __init__(self, db: AsyncSession):
        self.db = db

    # ── BR-INV-001: Item Master ─────────────────────────────────
    async def get_item_catalogue(self, school_id: UUID) -> list:
        """Returns all inventory items with current stock levels and reorder status."""
        from src.modules.inventory.models.inventory import InventoryItem, StockBalance, ItemCategory
        result = await self.db.execute(
            select(InventoryItem, StockBalance)
            .join(StockBalance, StockBalance.item_id == InventoryItem.id, isouter=True)
            .where(InventoryItem.school_id == school_id)
        )
        items = []
        for item, balance in result.all():
            qty = float(balance.quantity_on_hand) if balance else 0.0
            reorder = float(item.reorder_level)
            status = "ok" if qty > reorder * 1.5 else ("warn" if qty > reorder else "bad")
            items.append({
                "id": str(item.id),
                "item_name": item.name,
                "code": item.code,
                "unit_of_measure": item.unit_of_measure.value if hasattr(item.unit_of_measure, 'value') else str(item.unit_of_measure),
                "quantity_in_stock": qty,
                "reorder_level": reorder,
                "unit_cost": float(item.unit_cost),
                "stock_status": status,
            })
        return items

    # ── BR-INV-002: Reorder Alert Check ────────────────────────
    async def check_and_raise_reorder_alerts(self, school_id: UUID) -> list:
        """
        Scans all stock balances. If qty_on_hand < reorder_level, creates
        a ReorderAlert and notifies Procurement (BR-INV-002).
        """
        from src.modules.inventory.models.inventory import InventoryItem, StockBalance, ReorderAlert
        result = await self.db.execute(
            select(InventoryItem, StockBalance)
            .join(StockBalance, StockBalance.item_id == InventoryItem.id)
            .where(InventoryItem.school_id == school_id)
        )
        triggered = []
        for item, balance in result.all():
            if float(balance.quantity_on_hand) < float(item.reorder_level):
                # Check for existing unresolved alert
                existing = await self.db.scalar(
                    select(ReorderAlert).where(
                        ReorderAlert.item_id == item.id,
                        ReorderAlert.school_id == school_id,
                        ReorderAlert.is_resolved == False
                    )
                )
                if not existing:
                    alert = ReorderAlert(
                        school_id=school_id,
                        item_id=item.id,
                        triggered_at=datetime.utcnow(),
                        qty_on_hand=balance.quantity_on_hand,
                        reorder_level=item.reorder_level,
                    )
                    self.db.add(alert)
                    triggered.append({"item": item.name, "qty": float(balance.quantity_on_hand), "reorder": float(item.reorder_level)})
        if triggered:
            await self.db.commit()
        return triggered

    # ── BR-INV-003: Create GIN ─────────────────────────────────
    async def create_gin(self, school_id: UUID, warehouse_id: UUID, department: str,
                         requested_by: UUID, items: list) -> object:
        """
        Creates a Goods Issue Note. MANDATORY before stock deduction (BR-INV-003).
        items: [{"item_id": UUID, "qty_requested": Decimal}]
        """
        from src.modules.inventory.models.inventory import GoodsIssueNote, GINItem, GINStatus
        import uuid as uuidlib
        gin = GoodsIssueNote(
            school_id=school_id,
            gin_number=f"GIN-{uuidlib.uuid4().hex[:8].upper()}",
            warehouse_id=warehouse_id,
            issued_to_department=department,
            requested_by_staff_id=requested_by,
            status=GINStatus.PENDING.value,
        )
        self.db.add(gin)
        await self.db.flush()
        for line in items:
            self.db.add(GINItem(
                school_id=school_id,
                gin_id=gin.id,
                item_id=line["item_id"],
                qty_requested=Decimal(str(line["qty_requested"])),
            ))
        await self.db.commit()
        return gin

    async def approve_and_issue_gin(self, gin_id: UUID, issued_by: UUID) -> object:
        """
        Approves a GIN and deducts stock from StockBalance. (BR-INV-003)
        Raises ValueError if stock is insufficient.
        """
        from src.modules.inventory.models.inventory import GoodsIssueNote, StockBalance, GINStatus
        gin = await self.db.scalar(
            select(GoodsIssueNote).options(selectinload(GoodsIssueNote.items)).where(GoodsIssueNote.id == gin_id)
        )
        if not gin or gin.status != GINStatus.PENDING.value:
            raise ValueError("GIN not found or not in PENDING state.")
        for line in gin.items:
            balance = await self.db.scalar(
                select(StockBalance).where(
                    StockBalance.item_id == line.item_id,
                    StockBalance.warehouse_id == gin.warehouse_id
                )
            )
            if not balance or float(balance.quantity_on_hand) < float(line.qty_requested):
                raise ValueError(f"Insufficient stock for item {line.item_id}.")
            balance.quantity_on_hand -= line.qty_requested
            line.qty_issued = line.qty_requested
        gin.status = GINStatus.ISSUED.value
        gin.issued_by_staff_id = issued_by
        gin.issued_at = datetime.utcnow()
        await self.db.commit()
        return gin

    # ── BR-INV-004: Kitchen Requisition ────────────────────────
    async def submit_kitchen_requisition(self, school_id: UUID, req_date: date,
                                          student_count: int, submitted_by: UUID,
                                          items: list) -> object:
        """
        Kitchen submits daily food requisition (BR-INV-004).
        Must be approved before storekeeper can issue.
        """
        from src.modules.inventory.models.inventory import KitchenRequisition, KitchenRequisitionItem, KitchenRequisitionStatus
        import uuid as uuidlib
        req = KitchenRequisition(
            school_id=school_id,
            req_number=f"KR-{req_date.strftime('%Y%m%d')}-{uuidlib.uuid4().hex[:4].upper()}",
            requisition_date=req_date,
            student_count=student_count,
            submitted_by_staff_id=submitted_by,
            status=KitchenRequisitionStatus.PENDING.value,
        )
        self.db.add(req)
        await self.db.flush()
        for line in items:
            self.db.add(KitchenRequisitionItem(
                school_id=school_id,
                req_id=req.id,
                item_id=line["item_id"],
                qty_requested=Decimal(str(line["qty_requested"])),
                unit_of_measure=line.get("unit", "KG"),
            ))
        await self.db.commit()
        return req

    async def approve_kitchen_requisition(self, req_id: UUID, approver_id: UUID) -> object:
        """Storekeeper / Boarding Master approves kitchen requisition."""
        from src.modules.inventory.models.inventory import KitchenRequisition, KitchenRequisitionStatus
        req = await self.db.scalar(select(KitchenRequisition).where(KitchenRequisition.id == req_id))
        if not req or req.status != KitchenRequisitionStatus.PENDING.value:
            raise ValueError("Requisition not found or not pending.")
        req.status = KitchenRequisitionStatus.APPROVED.value
        req.approved_by_staff_id = approver_id
        req.approved_at = datetime.utcnow()
        await self.db.commit()
        return req

    # ── BR-INV-005: Stocktake / Physical Count ─────────────────
    async def open_stocktake(self, school_id: UUID, name: str, count_date: date,
                              conducted_by: UUID, warehouse_id: UUID) -> object:
        """
        Opens a new stocktake session with system counts pre-filled (BR-INV-005).
        """
        from src.modules.inventory.models.inventory import StocktakeSession, StocktakeLine, StockBalance, InventoryItem, StocktakeStatus
        import uuid as uuidlib
        session = StocktakeSession(
            school_id=school_id,
            session_ref=f"ST-{uuidlib.uuid4().hex[:8].upper()}",
            session_name=name,
            count_date=count_date,
            status=StocktakeStatus.OPEN.value,
            conducted_by_staff_id=conducted_by,
        )
        self.db.add(session)
        await self.db.flush()
        # Pre-fill system counts from StockBalance
        balances = await self.db.execute(
            select(StockBalance, InventoryItem)
            .join(InventoryItem, InventoryItem.id == StockBalance.item_id)
            .where(StockBalance.school_id == school_id, StockBalance.warehouse_id == warehouse_id)
        )
        for balance, item in balances.all():
            self.db.add(StocktakeLine(
                school_id=school_id,
                session_id=session.id,
                item_id=item.id,
                system_count=balance.quantity_on_hand,
                unit_cost=item.unit_cost,
            ))
        await self.db.commit()
        return session

    async def post_stocktake_variances(self, session_id: UUID, lines: list) -> dict:
        """
        Posts physical counts, calculates variances, adjusts StockBalance (BR-INV-005).
        lines: [{"line_id": UUID, "physical_count": Decimal, "variance_reason": str}]
        Returns summary of total variance value for audit trail.
        """
        from src.modules.inventory.models.inventory import StocktakeSession, StocktakeLine, StockBalance, StocktakeStatus
        session = await self.db.scalar(
            select(StocktakeSession).options(selectinload(StocktakeSession.lines)).where(StocktakeSession.id == session_id)
        )
        if not session or session.status != StocktakeStatus.OPEN.value:
            raise ValueError("Session not found or not open.")
        total_variance_value = Decimal("0.00")
        line_map = {l["line_id"]: l for l in lines}
        for line in session.lines:
            if str(line.id) in line_map:
                entry = line_map[str(line.id)]
                physical = Decimal(str(entry["physical_count"]))
                line.physical_count = physical
                line.variance = physical - line.system_count
                line.variance_value = line.variance * line.unit_cost
                line.variance_reason = entry.get("variance_reason", "")
                total_variance_value += line.variance_value
                # Adjust StockBalance
                balance = await self.db.scalar(
                    select(StockBalance).where(StockBalance.item_id == line.item_id, StockBalance.school_id == session.school_id)
                )
                if balance:
                    balance.quantity_on_hand = physical
                    balance.last_counted_date = datetime.utcnow()
        session.status = StocktakeStatus.POSTED.value
        session.total_variance_value = total_variance_value
        session.posted_at = datetime.utcnow()
        await self.db.commit()
        return {"session_ref": session.session_ref, "total_variance_value": float(total_variance_value)}
