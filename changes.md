- [ ] get rid of references to ai augmented anything and TradingAgents 

- [ ] engineering blog post filters [ALL WRITING PROJECT DIAGRAM] does not work 

- [ ] SORT: DATE ▼ does not work or be clicked on 

- [ ] mermaid diagrams you cannot see easily (too small) - having a zoom-in or enlarge feature would help 

- [ ] some mermaid diagrams you can't see anything at all 

- [ ] some blog post tables you cannot read the text in the header in either light/dark modes

- [ ] some blog post tables are horizontally too long, and we cannot see the rest of it as it goes right to left (right aligned) - no scroll is wanted either. we should center the whole table 

- [ ] Intro description of me (9 years -> 10 years, software engineer -> platform / infrastructure engineering). 

- [ ] Including a resume (latest) 

- [ ] a separate projects tab above to point to all my projects. (new ones are needed to take the spotlight) 

- [ ] a separate financials tab above to point to all my financial undertakings 

- [ ] home should have my intro + keep the engineering + research containers, keep the projects but add the most active (versus the projects tab showing all my important contributions)

- [ ] The intro section above should also include the "I publish technical writeups under /engineering/ and AI-augmented equity research under /research/. The split is the message — engineering content is technical; research notes are generated using my TradingAgents framework and are not investment advice."

- [ ] assets/css/custom.css is a vestigial 197-line file from an earlier theme, force-applying font-family: SFMono-Regular ... !important to
  every text element including td, th, body, h1-h6. It overrides the carefully-chosen design system (--font-display: Departure Mono,
  --font-body: Inter, --font-serif: EB Garamond) site-wide. The visual feel is monospace everywhere, not the typographic mix the tokens
  describe.

  Killing or scoping custom.css is a meaningful aesthetic upgrade (three-typeface hierarchy is what makes a research site feel
  institutional), but it's a visible change that I won't ship without you saying so. Want me to:

  1. Delete custom.css entirely — restores style.css's design system as intended (Departure Mono for display, Inter for body, EB Garamond
  for serif)
  2. Keep but de-fang — drop the !important sweeps so design tokens take precedence where defined, but keep the sidebar font-size tweaks if
   those are still wanted
  3. Leave it alone — current monospace-everywhere look is intentional
