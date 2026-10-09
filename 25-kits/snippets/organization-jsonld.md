# Organization-level identity, returns, shipping and loyalty markup

One block, usually on the homepage, identifies the business by its homepage `url` and a stable `@id`, and states the policies that apply to most products: a return policy, a shipping service and a loyalty program. Product pages only override what differs.

```html
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "OnlineStore",
  "@id": "https://www.example.com/#organization",
  "name": "Example Shop",
  "url": "https://www.example.com/",
  "logo": "https://www.example.com/img/logo-512.png",
  "sameAs": [
    "https://video.example.net/@exampleshop",
    "https://social.example.org/exampleshop"
  ],
  "hasMerchantReturnPolicy": {
    "@type": "MerchantReturnPolicy",
    "@id": "https://www.example.com/#returns",
    "applicableCountry": ["ES", "FR"],
    "returnPolicyCountry": "ES",
    "returnPolicyCategory": "https://schema.org/MerchantReturnFiniteReturnWindow",
    "merchantReturnDays": 30,
    "returnMethod": "https://schema.org/ReturnByMail",
    "returnFees": "https://schema.org/FreeReturn",
    "refundType": "https://schema.org/FullRefund"
  },
  "hasShippingService": {
    "@type": "ShippingService",
    "@id": "https://www.example.com/#standard-shipping",
    "name": "Standard shipping to Spain and France",
    "fulfillmentType": "FulfillmentTypeDelivery",
    "handlingTime": {
      "@type": "ServicePeriod",
      "cutoffTime": "14:00:00+01:00",
      "duration": {
        "@type": "QuantitativeValue",
        "minValue": 0,
        "maxValue": 1,
        "unitCode": "DAY"
      },
      "businessDays": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
    },
    "shippingConditions": [
      {
        "@type": "ShippingConditions",
        "shippingDestination": [
          { "@type": "DefinedRegion", "addressCountry": "ES" },
          { "@type": "DefinedRegion", "addressCountry": "FR" }
        ],
        "orderValue": {
          "@type": "MonetaryAmount",
          "minValue": 0,
          "maxValue": 99.99,
          "currency": "EUR"
        },
        "shippingRate": {
          "@type": "MonetaryAmount",
          "value": 4.95,
          "currency": "EUR"
        },
        "transitTime": {
          "@type": "ServicePeriod",
          "duration": {
            "@type": "QuantitativeValue",
            "minValue": 2,
            "maxValue": 4,
            "unitCode": "DAY"
          }
        }
      },
      {
        "@type": "ShippingConditions",
        "shippingDestination": [
          { "@type": "DefinedRegion", "addressCountry": "ES" },
          { "@type": "DefinedRegion", "addressCountry": "FR" }
        ],
        "orderValue": {
          "@type": "MonetaryAmount",
          "minValue": 100,
          "currency": "EUR"
        },
        "shippingRate": {
          "@type": "MonetaryAmount",
          "value": 0,
          "currency": "EUR"
        },
        "transitTime": {
          "@type": "ServicePeriod",
          "duration": {
            "@type": "QuantitativeValue",
            "minValue": 2,
            "maxValue": 4,
            "unitCode": "DAY"
          }
        }
      }
    ]
  },
  "hasMemberProgram": {
    "@type": "MemberProgram",
    "name": "Example Club",
    "description": "Free membership: earn points on every order.",
    "url": "https://www.example.com/club/",
    "hasTiers": [
      {
        "@type": "MemberProgramTier",
        "@id": "https://www.example.com/club/#member",
        "name": "Member",
        "hasTierBenefit": ["https://schema.org/TierBenefitLoyaltyPoints"],
        "membershipPointsEarned": 5
      }
    ]
  }
}
</script>
```
