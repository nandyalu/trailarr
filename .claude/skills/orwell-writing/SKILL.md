---
name: orwell-writing
description: Use when an agent is asked to draft, rewrite, edit, review, polish, copyedit, simplify, humanize, or create written prose, including creative writing, essays, posts, scripts, speeches, emails, documentation pages, READMEs, docstrings, release notes, log messages, code comments, and product copy — and when the user mentions STE100, Simplified Technical English, or orwell-writing. Apply George Orwell's six rules and ASD-STE100 Simplified Technical English as a plain-English discipline while preserving the user's intended meaning, audience, tone, and explicit constraints. Prefer short sentences and short paragraphs, and break sets of items into bullets or tables, because readers skip dense prose.
---

# Orwell writing (Orwell's rules and ASD-STE100 Simplified Technical English)

## Overview

Use Orwell's rules and [ASD-STE100](https://www.asd-ste100.org/) Simplified Technical English (STE) as practical filters for clear, direct, and honest prose. The goal is to remove ambiguity about intent, and to make text easy to understand, follow, and translate — many readers are not native English speakers.

Use STE by default for technical, instructional, business, and product prose. Apply the rules to drafting and to revision. Do not erase deliberate voice, character, rhythm, humor, or genre when the user clearly wants them.

STE has writing rules and a controlled dictionary. Use an approved word with its approved meaning when the dictionary is available. Do not claim strict STE conformance without a check against the current ASD-STE100 issue and dictionary.

## Where it applies

- Documentation pages and READMEs
- Docstrings
- Release notes — **new entries only; never rewrite the notes of an already-released version**
- Log messages and code comments (recommended)
- General prose the user asks for: emails, posts, product copy, essays, scripts

Apply to NEW or CHANGED content. Do not rewrite untouched text only to comply, unless the project has scheduled an explicit retroactive pass (for example, quiv Phase 6).

## Orwell's six rules

Remember these rules from "Politics and the English Language":

1. Never use a metaphor, simile, or other figure of speech which you are used to seeing in print.
2. Never use a long word where a short one will do.
3. If it is possible to cut a word out, always cut it out.
4. Never use the passive where you can use the active.
5. Never use a foreign phrase, a scientific word, or a jargon word if you can think of an everyday English equivalent.
6. Break any of these rules sooner than say anything outright barbarous.

## Rules

1. **One instruction per sentence.** One idea per sentence for descriptive text.
2. **Active voice, present tense.** Use the imperative for procedures: "Call `shutdown()` before exit", not "`shutdown()` should be called". Name the actor when the actor matters.
3. **Keep sentences short.** At most 20 words in procedures, 25 in descriptions. Split long sentences instead of chaining clauses with dashes or semicolons.
4. **One topic per paragraph.**
5. **No idioms or figurative language.** Use familiar words with one precise meaning. Write "many tasks start at the same time", not "thundering herd". Write "fails immediately", not "fails loudly".
6. **One name per concept.** Pick one term and keep it: do not alternate "handler" / "callable" / "function" for the same thing within a document. Do not change a term only to avoid repetition.
7. **Use a specific technical term when accuracy needs it.** Define it, or link to its definition.
8. **No long noun clusters.** At most 3 nouns in a row; break longer clusters with prepositions ("the deadline of the timeout for the job" is clearer than "job timeout deadline enforcement logic").
9. **Do not drop articles.** Write "the scheduler starts the loop", not "scheduler starts loop".
10. **Make warnings and conditions explicit.** State the condition first: "If the handler ignores the stop event, the thread continues to run." Write a procedure as the condition, the action, and the expected result.
11. **Prefer a positive instruction.** State what the reader must do.
12. **Use consistent American English spelling**, unless the user's style guide requires another variety.

When strict STE is not possible, keep the text clear. Mark the terms or passages that need a domain-specific exception.

## Layout

People skip long paragraphs. They read short bullet points. Layout is therefore part of clarity, not decoration: a correct sentence nobody reads has failed.

1. Keep a paragraph to three or four sentences. Break a longer one.
2. Turn a paragraph into a list when it holds a set of items — steps, options, conditions, causes, findings, or things to check. A paragraph that contains "first", "also", "and then", or a run of semicolons is usually a list already. Use a list whenever it makes the content easier to scan.
3. Put one idea in each bullet. Start the bullet with the word that carries the meaning, not with filler.
4. Front-load the point. Put the conclusion in the first sentence of the paragraph, or in the bolded lead of the bullet, so a reader who stops there still gets it.
5. Use a table when the items share fields, such as a name and a number each. A table beats both a paragraph and a list for that.
6. Add headings so a reader can find one section without reading the others.
7. Split a list longer than about seven items into groups under headings. A long list is a long paragraph with dashes in front.
8. **In Markdown files, write each paragraph as one continuous line.** Do not insert line breaks at a character limit; let the editor soft-wrap. Hard-wrapped paragraphs break rendering in some site generators (for example, zensical) and make diffs noisy. A new source line starts only for a new paragraph, list item, or heading.

**When to keep the paragraph.** Bullets show items. They do not show reasoning. An argument that depends on "because", "so", or "which meant" loses those links when it is cut into a list, and what remains reads as assertions nobody has connected. Keep prose for narrative, for cause and effect, and for anything the reader must be persuaded of rather than merely told. Three tight sentences beat five weak bullets.

## Workflow

When writing from scratch:

1. Identify the audience, purpose, and promised tone from the user's request.
2. Draft in concrete, direct English.
3. Remove stock phrases, dead metaphors, filler, pompous diction, needless abstraction, and avoidable jargon.
4. Prefer active verbs and clear subjects, unless passive voice better serves emphasis, tact, suspense, or technical accuracy.
5. Keep necessary nuance; do not make prose crude, false, or flat only to make it short.
6. Choose the layout with the content. Use bullets for sets of items, a table for items with shared fields, and short paragraphs for reasoning.
7. Apply the rules above. Check terms, sentence structure, instructions, and technical exceptions.

When revising existing text:

1. Preserve the user's meaning and any explicit tone or format constraints.
2. Cut words, clauses, and sentences that do no work.
3. Replace stale figures of speech with plain phrasing, or with a fresh and specific image.
4. Replace long, foreign, scientific, or jargon terms with everyday English when accuracy permits.
5. Convert a passive construction to an active one when the actor matters and is known.
6. Flag jargon, passive voice, or ornate phrasing that is necessary. Do not remove important precision without a note.
7. Break long paragraphs. Convert a paragraph that lists items into bullets or a table, and keep as prose the parts that carry an argument.
8. Run a final STE pass. Check that each technical term is consistent, each instruction states the required action, and each exception is intentional.

## Creative writing

For fiction, poetry, memoir, scripts, and lyrical prose, treat STE as a clarity aid, not a requirement that overrides the user's form. Keep intentional ambiguity, cadence, dialogue style, imagery, and character voice when they create a real effect. Remove only language that feels inherited, inflated, evasive, or lazy. Use strict STE when the user asks for it, and say when that request conflicts with a creative effect.

## Exemptions

- Code identifiers, API names, and established technical terms (`fixed_interval`, "WAL", "thread pool") are exempt from the approved-word restriction. Keep their exact spelling.
- Text quoted verbatim (error messages, command output) stays unchanged.
- Commands, product names, legal text, and required quotations stay unchanged. Do not simplify them silently.
- Release notes of already-released versions are immutable — they are historical record.

## Quality check before finishing

Read each new sentence and ask: can a non-native reader parse it in one pass, and is there exactly one way to understand it? If not, split it or replace the ambiguous words.

Also check for:
- Consistency in terminology and style.
- Correct use of punctuation and grammar.
- Logical flow and coherence between sentences and paragraphs.
- Redundancy or repetition that can be removed without loss of meaning.
