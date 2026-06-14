# Science Agent 

A LangGraph-powered AI agent that searches high quality academic and reference sources to answer research questions with cited, verifiable answers.

Its aim is to help source citation from high quality online information, like scientific papers, from established reputable outlets.

## Architecture

```
[User Query]
    |
[Classifier Node] <- LLM classifies query domain (medical, historical, scientific...)
    |
[Source Router Node] <- Maps domain to its best source APIs
    |
[Parallel Fetch] <- Hits multiple APIs concurrently 
    |
[Ranker Node] <- Scores results by relevance + credibility
    |
[Synthetizer Node] <- LLM summarizez with citations
    |
[Final Answer] <- Response with the sources the user can verify
```

## Supported Sources
| Source | Domain | API Type |
| --- | --- | --- |