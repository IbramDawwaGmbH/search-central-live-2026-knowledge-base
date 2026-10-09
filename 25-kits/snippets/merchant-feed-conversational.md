# Merchant Center feed item with Q&A, product details and highlights

An XML (RSS 2.0) feed item that adds the attributes Google stresses for AI shopping experiences to the core data: `product_highlight` lines, `product_detail` specifications as section, name and value, and `question_and_answer` pairs (no prices, shipping, dates or company name in them). Keep price, availability, brand and GTIN identical to the product page's markup.

```xml
<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:g="http://base.google.com/ns/1.0">
  <channel>
    <title>Example Shop</title>
    <link>https://www.example.com/</link>
    <description>Example Shop product feed</description>
    <item>
      <g:id>KT-17-STEEL</g:id>
      <g:title>Steel kettle 1.7 l with temperature control</g:title>
      <g:description>Stainless steel kettle with five temperature settings and a keep-warm mode.</g:description>
      <g:link>https://www.example.com/kettles/steel-kettle-17</g:link>
      <g:image_link>https://www.example.com/img/steel-kettle-17-1200.jpg</g:image_link>
      <g:price>59.00 EUR</g:price>
      <g:availability>in_stock</g:availability>
      <g:condition>new</g:condition>
      <g:brand>Example Home</g:brand>
      <g:gtin>4006381333931</g:gtin>
      <g:product_highlight>Five temperature settings from 70 to 100 degrees Celsius</g:product_highlight>
      <g:product_highlight>Keeps water warm for up to 30 minutes</g:product_highlight>
      <g:product_detail>
        <g:section_name>General</g:section_name>
        <g:attribute_name>Capacity</g:attribute_name>
        <g:attribute_value>1.7 l</g:attribute_value>
      </g:product_detail>
      <g:product_detail>
        <g:section_name>Power</g:section_name>
        <g:attribute_name>Wattage</g:attribute_name>
        <g:attribute_value>2200 W</g:attribute_value>
      </g:product_detail>
      <g:question_and_answer>
        <g:question>Does the kettle switch off when it boils dry?</g:question>
        <g:answer>Yes. Boil-dry protection switches it off when there is no water in it.</g:answer>
      </g:question_and_answer>
      <g:question_and_answer>
        <g:question>Can I set it to 80 degrees for green tea?</g:question>
        <g:answer>Yes. The 80 degree setting is one of the five presets.</g:answer>
      </g:question_and_answer>
    </item>
  </channel>
</rss>
```
