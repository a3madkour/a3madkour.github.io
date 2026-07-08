---
title: "Recipes"
cascade:
  # Emit the RECIPE download output only for single recipe pages (kind "page"),
  # not the section list page — otherwise Hugo warns "no layout file for recipe
  # for kind section" and would try to render a meaningless section JSON.
  - outputs: ["HTML", "RECIPE"]
    target:
      kind: page
---

Things worth cooking twice — with sources, scalable portions, and a clean download.
