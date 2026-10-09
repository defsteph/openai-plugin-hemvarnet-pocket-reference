# Renderer input

UTF-8 JSON object:

```json
{
  "title": "PEDARS",
  "subtitle": "MINNESKORT • HEMVÄRNET",
  "source": "Handbook name and page, if verified",
  "entries": [
    {"label": "P", "title": "Personal", "lines": ["Ange antal, namn och befattning.", "Lediga, sjuka, skadade, döda och saknade."]},
    {"section": "KLARGÖRING"},
    {"label": "1", "lines": ["Armarna utfällda (klick)."]}
  ]
}
```

`title` and nonempty `entries` are required. Each entry is either a section bar or a content row. Content rows require at least one `lines` item; `label` and `title` are optional. An explicit line may wrap automatically at word boundaries. Prefer two short lines per reporting row. Omit `label` for full-width checklists. Use short labels (letters or step numbers), not sentences. At least one content row is required. `source` is stored as PDF metadata and never printed.

The title scales to fit beside the emblem. Section bars keep uppercase text. The renderer uses numbered/acronym rows and sectioned checklists, not the specialized two-column L<C>ABCDE table; for that requested layout adapt the existing reference with ReportLab while retaining the same dimensions, fonts, emblem and paired-output contract.

Assets were retained from this user's approved cards. The FM Sans regular and bold fonts originated from the official Försvarsmakten website's FM Sans variable font, instantiated at weights 400 and 700 with distinct font names. The emblem originated from the official white Hemvärnet SVG and was recolored black on white. Use these assets for this user's cards; no need to download them again.
