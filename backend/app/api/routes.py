from fastapi import APIRouter

router = APIRouter()


@router.get("/inventory/low-stock", tags=["inventory"])
async def list_low_stock() -> dict[str, list[dict[str, str | float]]]:
    """
    Placeholder endpoint returning static velocity-based low-stock insights.
    """

    sample = [
        {
            "sku": "IPHN-15-TYPEC",
            "name": "Type-C Cable (Anker 60W)",
            "days_remaining": 1.8,
            "status": "critical",
        },
        {
            "sku": "PIX-8-CASE-CLEAR",
            "name": "Pixel 8 Clear Case",
            "days_remaining": 4.2,
            "status": "warning",
        },
    ]
    return {"items": sample}


@router.get("/market-pulse/{sku}", tags=["pricing"])
async def market_pulse(sku: str) -> dict[str, object]:
    """
    Returns mocked competitor pricing and margin suggestion for demo purposes.
    """

    competitor_prices = [
        {"channel": "Amazon", "price": 14999},
        {"channel": "Flipkart", "price": 14500},
        {"channel": "Croma", "price": 15250},
    ]
    landing_cost = 13800
    suggested_price = 14400

    return {
        "sku": sku,
        "competitors": competitor_prices,
        "landing_cost": landing_cost,
        "suggested_price": suggested_price,
        "profit": suggested_price - landing_cost,
    }







