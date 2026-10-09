# Video watch page: video element plus VideoObject with key moments

Put the video in a `<video>` (or `<iframe>`/`<embed>`/`<object>`) element that loads without a click, on a page where it is the main content, and describe it with VideoObject markup. `Clip` parts enable key moments; their `url` points to the same watch page at that second.

```html
<video controls preload="metadata" width="1280" height="720"
       poster="https://www.example.com/video/chair-assembly-1280.jpg">
  <source src="https://www.example.com/video/chair-assembly.mp4" type="video/mp4">
</video>

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "VideoObject",
  "name": "How to assemble the oak dining chair",
  "description": "Step-by-step assembly of the oak dining chair in four minutes, with the tools you need.",
  "thumbnailUrl": ["https://www.example.com/video/chair-assembly-1280.jpg"],
  "uploadDate": "2026-09-15T09:00:00+02:00",
  "duration": "PT4M12S",
  "contentUrl": "https://www.example.com/video/chair-assembly.mp4",
  "embedUrl": "https://www.example.com/embed/chair-assembly",
  "hasPart": [
    {
      "@type": "Clip",
      "name": "Unpacking the parts",
      "startOffset": 0,
      "endOffset": 35,
      "url": "https://www.example.com/videos/chair-assembly?t=0"
    },
    {
      "@type": "Clip",
      "name": "Attaching the legs",
      "startOffset": 35,
      "endOffset": 140,
      "url": "https://www.example.com/videos/chair-assembly?t=35"
    },
    {
      "@type": "Clip",
      "name": "Fitting the seat",
      "startOffset": 140,
      "endOffset": 252,
      "url": "https://www.example.com/videos/chair-assembly?t=140"
    }
  ]
}
</script>
```
