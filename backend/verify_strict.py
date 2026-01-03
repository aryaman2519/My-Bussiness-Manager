from app.services.scraper import get_market_prices

def test(query):
    print(f"\n--- Testing '{query}' ---")
    results = get_market_prices(query)
    print(f"Found {len(results)} items.")
    for item in results[:5]:
        print(f"  [{item['platform']}] {item['title']} - {item['price']}")

if __name__ == "__main__":
    test("iphone 15")
    test("iphone 15 case")
