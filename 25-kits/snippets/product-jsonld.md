# Product markup with a time-limited sale price

Describe only the product the page is about (not the carousel of related products) and only what the page shows. For a sale, `price` is the sale price, the regular price is a `StrikethroughPrice`, and `validFrom` with `priceValidUntil` (or `validThrough`) bound the sale in ISO 8601 with a time zone, so a sale price that lingers in cached markup is not treated as current. The template must still switch to the regular price (and drop the `StrikethroughPrice`) when the sale ends: Google warns that a listing may not display if `priceValidUntil` is in the past. Keep the dates aligned with the Merchant Center feed. Shipping and returns point by `@id` alone to the policies defined once in the organisation block.

```html
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "Product",
  "@id": "https://www.example.com/chairs/oak-dining-chair#product",
  "name": "Oak dining chair with woven seat",
  "description": "Solid oak dining chair with a hand-woven paper-cord seat.",
  "image": [
    "https://www.example.com/img/oak-chair-1200.webp",
    "https://www.example.com/img/oak-chair-side-1200.webp"
  ],
  "sku": "CH-OAK-01",
  "brand": {
    "@type": "Brand",
    "name": "Example Shop"
  },
  "offers": {
    "@type": "Offer",
    "url": "https://www.example.com/chairs/oak-dining-chair",
    "price": 149.00,
    "priceCurrency": "EUR",
    "availability": "https://schema.org/InStock",
    "itemCondition": "https://schema.org/NewCondition",
    "validFrom": "2026-11-27T00:00:00+01:00",
    "priceValidUntil": "2026-11-30T23:59:59+01:00",
    "priceSpecification": {
      "@type": "UnitPriceSpecification",
      "priceType": "https://schema.org/StrikethroughPrice",
      "price": 199.00,
      "priceCurrency": "EUR"
    },
    "shippingDetails": {
      "@type": "OfferShippingDetails",
      "hasShippingService": {
        "@id": "https://www.example.com/#standard-shipping"
      }
    },
    "hasMerchantReturnPolicy": {
      "@id": "https://www.example.com/#returns"
    }
  }
}
</script>
```
