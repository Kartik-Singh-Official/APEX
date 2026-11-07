"""Paper Research Journal for APEX.
Paper-research-only performance ledger tracking hypothetical signals,
enforcing explicit fee and slippage assumptions without brokerage execution.
"""
import uuid
import time
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from backend.database.db import get_sync_db


class PaperSignalRecord(BaseModel):
    id: str
    forecast_id: Optional[str]
    symbol: str
    timeframe: str
    stance: str
    entry_time: int
    entry_price: float
    target_price: float
    stop_loss: float
    horizon_hours: int
    expiry_time: int
    exit_time: Optional[int] = None
    exit_price: Optional[float] = None
    fee_pct: float = 0.05       # 5 bps each way
    slippage_pct: float = 0.05  # 5 bps estimated slippage
    gross_pnl_pct: Optional[float] = None
    net_pnl_pct: Optional[float] = None
    status: str = "OPEN"        # 'OPEN', 'WIN', 'LOSS', 'EXPIRED'
    notes: Optional[str] = None
    created_at: int


class PaperJournalManager:
    def __init__(self):
        pass

    def record_signal(
        self,
        symbol: str,
        timeframe: str,
        stance: str,
        entry_price: float,
        target_price: float,
        stop_loss: float,
        horizon_hours: int,
        forecast_id: Optional[str] = None,
        notes: Optional[str] = None
    ) -> PaperSignalRecord:
        """Create a new hypothetical paper research position."""
        now_ms = int(time.time() * 1000)
        expiry_ms = now_ms + (horizon_hours * 3600 * 1000)
        rec_id = str(uuid.uuid4())[:12]

        record = PaperSignalRecord(
            id=rec_id,
            forecast_id=forecast_id,
            symbol=symbol.upper(),
            timeframe=timeframe,
            stance=stance,
            entry_time=now_ms,
            entry_price=entry_price,
            target_price=target_price,
            stop_loss=stop_loss,
            horizon_hours=horizon_hours,
            expiry_time=expiry_ms,
            fee_pct=0.05,
            slippage_pct=0.05,
            status="OPEN",
            notes=notes,
            created_at=now_ms,
        )

        conn = get_sync_db()
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO paper_journal (
                    id, forecast_id, symbol, timeframe, stance, entry_time, entry_price,
                    target_price, stop_loss, horizon_hours, expiry_time, fee_pct,
                    slippage_pct, status, notes, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record.id,
                    record.forecast_id,
                    record.symbol,
                    record.timeframe,
                    record.stance,
                    record.entry_time,
                    record.entry_price,
                    record.target_price,
                    record.stop_loss,
                    record.horizon_hours,
                    record.expiry_time,
                    record.fee_pct,
                    record.slippage_pct,
                    record.status,
                    record.notes,
                    record.created_at,
                ),
            )
            conn.commit()
        finally:
            conn.close()

        return record

    def list_records(self, limit: int = 50) -> List[PaperSignalRecord]:
        """Fetch chronological paper research signals."""
        conn = get_sync_db()
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT id, forecast_id, symbol, timeframe, stance, entry_time, entry_price,
                       target_price, stop_loss, horizon_hours, expiry_time, exit_time,
                       exit_price, fee_pct, slippage_pct, gross_pnl_pct, net_pnl_pct,
                       status, notes, created_at
                FROM paper_journal
                ORDER BY entry_time DESC
                LIMIT ?
                """,
                (limit,),
            )
            rows = cursor.fetchall()
            return [
                PaperSignalRecord(
                    id=r["id"],
                    forecast_id=r["forecast_id"],
                    symbol=r["symbol"],
                    timeframe=r["timeframe"],
                    stance=r["stance"],
                    entry_time=r["entry_time"],
                    entry_price=r["entry_price"],
                    target_price=r["target_price"],
                    stop_loss=r["stop_loss"],
                    horizon_hours=r["horizon_hours"],
                    expiry_time=r["expiry_time"],
                    exit_time=r["exit_time"],
                    exit_price=r["exit_price"],
                    fee_pct=r["fee_pct"],
                    slippage_pct=r["slippage_pct"],
                    gross_pnl_pct=r["gross_pnl_pct"],
                    net_pnl_pct=r["net_pnl_pct"],
                    status=r["status"],
                    notes=r["notes"],
                    created_at=r["created_at"],
                )
                for r in rows
            ]
        finally:
            conn.close()

    def update_settlements(self, current_price: float, symbol: str):
        """Check open paper signals and evaluate take-profit, stop-loss or horizon expiry."""
        now_ms = int(time.time() * 1000)
        conn = get_sync_db()
        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM paper_journal WHERE symbol = ? AND status = 'OPEN'",
                (symbol.upper(),),
            )
            open_records = cursor.fetchall()

            for r in open_records:
                stance = r["stance"]
                entry_p = r["entry_price"]
                target_p = r["target_price"]
                stop_p = r["stop_loss"]
                expiry_t = r["expiry_time"]
                rec_id = r["id"]

                settle = False
                status = "OPEN"
                exit_price = current_price

                if stance in ["BULLISH", "STRONG_BULLISH"]:
                    if current_price >= target_p:
                        settle = True
                        status = "WIN"
                        exit_price = target_p
                    elif current_price <= stop_p:
                        settle = True
                        status = "LOSS"
                        exit_price = stop_p
                    elif now_ms >= expiry_t:
                        settle = True
                        status = "EXPIRED"
                elif stance in ["BEARISH", "STRONG_BEARISH"]:
                    if current_price <= target_p:
                        settle = True
                        status = "WIN"
                        exit_price = target_p
                    elif current_price >= stop_p:
                        settle = True
                        status = "LOSS"
                        exit_price = stop_p
                    elif now_ms >= expiry_t:
                        settle = True
                        status = "EXPIRED"

                if settle:
                    gross_ret = (exit_price - entry_p) / entry_p if stance in ["BULLISH", "STRONG_BULLISH"] else (entry_p - exit_price) / entry_p
                    total_costs_pct = (r["fee_pct"] * 2.0) + (r["slippage_pct"] * 2.0)
                    net_ret = gross_ret - (total_costs_pct / 100.0)

                    cursor.execute(
                        """
                        UPDATE paper_journal
                        SET status = ?, exit_time = ?, exit_price = ?, gross_pnl_pct = ?, net_pnl_pct = ?
                        WHERE id = ?
                        """,
                        (
                            status,
                            now_ms,
                            exit_price,
                            round(gross_ret * 100.0, 2),
                            round(net_ret * 100.0, 2),
                            rec_id,
                        ),
                    )
            conn.commit()
        finally:
            conn.close()


paper_journal_manager = PaperJournalManager()
