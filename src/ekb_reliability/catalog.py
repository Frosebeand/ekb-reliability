from __future__ import annotations

from dataclasses import dataclass

from ekb_reliability.rules import classify_by_rules
from ekb_reliability.taxonomy import default_subfamily


@dataclass
class CatalogItem:
    mpn: str
    family: str
    subfamily: str
    manufacturer: str | None = None
    source: str = "catalog"


class InMemoryCatalog:
    def __init__(self):
        self._by_mpn: dict[str, CatalogItem] = {}

    def add(self, mpn: str, family: str, subfamily: str | None = None, manufacturer: str | None = None, source: str = "catalog"):
        self._by_mpn[mpn] = CatalogItem(
            mpn=mpn,
            family=family,
            subfamily=subfamily or default_subfamily(family),
            manufacturer=manufacturer,
            source=source,
        )

    def match(self, mpn: str | None):
        if not mpn:
            return None
        return self._by_mpn.get(mpn)

    @classmethod
    def from_rows(cls, rows):
        catalog = cls()
        for row in rows:
            if not row.mpn:
                continue
            ident = classify_by_rules(row.normalized_description)
            if ident.family != "unknown" and ident.confidence >= 0.85:
                catalog.add(row.mpn, ident.family, ident.subfamily, manufacturer=row.manufacturer, source="bom_bootstrap")
        return catalog
