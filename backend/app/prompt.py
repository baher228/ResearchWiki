DESCRIPTION_PROMPT = """
Explain the following For people who know “AI” but basically nothing about RL / math. Shortest, simplest. Only output the description, write 2 lines.
"""



BEGINNER_PROMPT = """

For people who know “AI” but basically nothing about RL / math. Shortest, simplest.

```text
You are writing the “Level 1 - Absolute beginner” view of a Wikipedia-style article about this research paper.

Audience:
- Curious person or student who knows what "AI" is, but has NO background in machine learning, statistics, or programming.

Goals:
- Explain only the big picture: what the paper is about, why it matters, and a rough idea of how it works.
- Avoid all math and almost all jargon.

Hard constraints:
- NO equations, NO symbols, NO Greek letters.
- Avoid technical terms like “policy”, “gradient”, “entropy”, “mutual information”, “MDP”, etc.
- If you must name something technical (e.g., “reinforcement learning”), immediately give a one-sentence plain-language explanation.
- Length: 300-500 words (short and skimmable).

Output format (plain markdown headings):
1) Summary
2) Why this paper matters
3) High-level idea in everyday language
4) Simple example to illustrate it
5) What this research could be used for
6) One important limitation or caveat
7) References

Writing style:
- Very simple sentences, minimal jargon.
- Prefer analogies and concrete examples over any detail of the algorithm.
- Assume the reader will only spend 1-2 minutes reading this.
- Do include figures or image placeholders at this level.
```

***
"""

