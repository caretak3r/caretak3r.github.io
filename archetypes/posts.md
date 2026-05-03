---
title: "{{ replace .Name "-" " " | title }}"
date: {{ .Date }}
draft: true
categories: []
tags: []
description: ""
---

Lede paragraph here — one or two sentences that set up the why.

## First section

Body content. Markdown all the way down. Code fences, tables, blockquotes
all render via the article shell defined in `layouts/posts/single.html`.

```python
# code blocks render via Chroma syntax highlighting in the tan palette
print("hello world")
```
