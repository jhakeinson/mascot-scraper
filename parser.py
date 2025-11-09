# parser.py
from bs4 import BeautifulSoup
from pydantic import BaseModel, HttpUrl, validator
from typing import List

class Listing(BaseModel):
    title: str
    price: str
    url: HttpUrl
    image: HttpUrl | None = None

    @validator("price", pre=True)
    def clean_price(cls, v):
        return v.replace("$", "").replace(",", "").strip()

def extract_listings(html: str) -> List[Listing]:
    soup = BeautifulSoup(html, "html.parser")
    items = soup.select("article.listing")   # <-- adapt CSS selector
    listings = []
    for it in items:
        try:
            listings.append(
                Listing(
                    title=it.select_one("h2").get_text(strip=True),
                    price=it.select_one(".price").get_text(strip=True),
                    url=it.select_one("a")["href"],
                    image=it.select_one("img")["src"] if it.select_one("img") else None,
                )
            )
        except Exception as e:
            continue
    return listings
