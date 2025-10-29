
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, cast, Date
from datetime import datetime, timedelta
from typing import List, Optional
from app.database.database import get_db
from app.schemas.dashboard import (
    SummaryMetrics,
    DailyTransaction,
    DailyUserCount,
    UsersOverTimeResponse,
    LatestTransaction
)
from app.models.transactions import Transaction
from app.models.users import User, Role
from app.models.manual_deposits import ManualDeposit
from app.models.kyc_documents import KYCDocument
from app.security import get_current_user
from sqlalchemy.orm import joinedload
from app.schemas.kyc_documents import KYCDocumentUser
from app.schemas.dashboard import MetricWithChange


router = APIRouter()


def require_admin(user: User = Depends(get_current_user)) -> User:
    if user.role not in [Role.admin, Role.finance_officer, Role.support]:
        raise HTTPException(status_code=403, detail="Not authorized to view dashboard")
    return user

@router.get("/summary", response_model=SummaryMetrics)
def get_summary_metrics(
    db: Session = Depends(get_db),
    _: User = Depends(require_admin)
):
    today = datetime.utcnow().date()
    week_ago = today - timedelta(days=7)
    previous_week = week_ago - timedelta(days=7)

    # Current totals
    total_etb = db.query(func.sum(Transaction.amount)).filter(
        Transaction.status == 'completed',
        Transaction.currency == 'ETB'
    ).scalar() or 0

    total_tx = db.query(func.sum(Transaction.amount)).filter(
        Transaction.status == 'completed'
    ).scalar() or 0

    today_tx = db.query(func.sum(Transaction.amount)).filter(
        func.date(Transaction.created_at) == today,
        Transaction.status == 'completed'
    ).scalar() or 0

    pending_deposits = db.query(ManualDeposit).filter(ManualDeposit.completed == False).count()

    total_users = db.query(func.count(User.user_id)).scalar() or 0

    # Previous week values for change %
    previous_total_etb = db.query(func.sum(Transaction.amount)).filter(
        Transaction.status == 'completed',
        Transaction.currency == 'ETB',
        Transaction.created_at >= previous_week,
        Transaction.created_at < week_ago
    ).scalar() or 0

    previous_total_tx = db.query(func.sum(Transaction.amount)).filter(
        Transaction.status == 'completed',
        Transaction.created_at >= previous_week,
        Transaction.created_at < week_ago
    ).scalar() or 0

    previous_today_tx = db.query(func.sum(Transaction.amount)).filter(
        func.date(Transaction.created_at) == today - timedelta(days=1),
        Transaction.status == 'completed'
    ).scalar() or 0

    previous_pending_deposits = db.query(ManualDeposit).filter(
        ManualDeposit.completed == False,
        ManualDeposit.created_at < week_ago
    ).count()

    previous_total_users = db.query(func.count(User.user_id)).filter(
        User.created_at < week_ago
    ).scalar() or 0

    # Helper to calculate % change
    def calc_change(current, previous):
        if previous == 0:
            return 0.0
        return ((current - previous) / previous) * 100

    return SummaryMetrics(
        total_etb_disbursed=MetricWithChange(
            value=total_etb,
            percentage_change=calc_change(total_etb, previous_total_etb)
        ),
        total_transactions=MetricWithChange(
            value=total_tx,
            percentage_change=calc_change(total_tx, previous_total_tx)
        ),
        today_transactions=MetricWithChange(
            value=today_tx,
            percentage_change=calc_change(today_tx, previous_today_tx)
        ),
        pending_deposits=MetricWithChange(
            value=pending_deposits,
            percentage_change=calc_change(pending_deposits, previous_pending_deposits)
        ),
        total_users=MetricWithChange(
            value=total_users,
            percentage_change=calc_change(total_users, previous_total_users)
        )
    )


@router.get("/daily-transactions", response_model=List[DailyTransaction])
def get_daily_transactions(
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
    days: int = 10
):
    start_date = datetime.utcnow().date() - timedelta(days=days)

    result = db.query(
        cast(Transaction.created_at, Date).label("date"),
        func.sum(Transaction.amount).label("amount")
    ).filter(
        Transaction.created_at >= start_date,
        Transaction.status == 'completed'
    ).group_by(
        cast(Transaction.created_at, Date)
    ).order_by(
        cast(Transaction.created_at, Date)
    ).all()

    return [DailyTransaction(date=row.date, amount=row.amount or 0) for row in result]


@router.get("/users-over-time", response_model=UsersOverTimeResponse)
def get_users_over_time(
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
    days: int = 14
):
    today = datetime.utcnow().date()
    start_date = today - timedelta(days=days)
    week_start = today - timedelta(days=7)

    daily_data = db.query(
        cast(User.created_at, Date).label("date"),
        func.count(User.user_id).label("count")
    ).filter(
        User.created_at >= start_date
    ).group_by(
        cast(User.created_at, Date)
    ).order_by(
        cast(User.created_at, Date)
    ).all()

    daily_counts = [DailyUserCount(date=row.date, count=row.count) for row in daily_data]

    today_total = db.query(func.count(User.user_id))\
        .filter(func.date(User.created_at) == today)\
        .scalar() or 0

    week_total = db.query(func.count(User.user_id))\
        .filter(User.created_at >= week_start)\
        .scalar() or 0

    previous_week_total = db.query(func.count(User.user_id))\
        .filter(User.created_at >= week_start - timedelta(days=7),
                User.created_at < week_start)\
        .scalar() or 0

    percentage_change = (
        ((week_total - previous_week_total) / previous_week_total) * 100
        if previous_week_total > 0 else 0.0
    )

    return UsersOverTimeResponse(
        today_total=today_total,
        week_total=week_total,
        percentage_change=percentage_change,
        daily_counts=daily_counts
    )
from sqlalchemy.orm import joinedload

@router.get("/latest-transactions", response_model=List[LatestTransaction])
def get_latest_transactions(
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),    
    limit: int = 10
):
    query = db.query(Transaction).options(
        joinedload(Transaction.user).joinedload(User.kyc_document)
    ).join(
        User, User.user_id == Transaction.user_id
    ).order_by(
        Transaction.created_at.desc()
    ).limit(limit)

    transactions = query.all()

    # Return serialized results including KYC document
    results = []
    for tx in transactions:
        user = tx.user
        kyc_doc = user.kyc_document if user and user.kyc_document else None
        results.append(LatestTransaction(
            transaction_id=tx.transaction_id,
            reference=tx.transaction_reference,
            status=tx.status,
            amount=tx.amount,
            created_at=tx.created_at,            
            currency=tx.currency,
            kyc_document=KYCDocumentUser.from_orm(kyc_doc) if kyc_doc else None        ))

    return results

