## RIT_QMBOT

This is a toy example of creating a tutor bot using OpenAPI's beta [Assistants API](https://platform.openai.com/docs/assistants/overview).

The bot emulates a professor tutoring undergraduates in Quantum Chemistry.  The imagined use case is that a student has completed a test/exam and after getting their test graded wants to understand more about where they may have gotten the question wrong or misunderstood the concepts that the question was testing.

If this is the first time using this repo it is suggested to create a local environment from the requirements.txt file with python 3.11. 

```
python3.11 -m venv env
source env/bin/activate
pip install -r requirements.txt
```

To use the bot you will need an openai API key.  Create a .env file and place your API key in there e.g.
```
OPENAI_API_KEY=aaabbbcccetc
```

You will also need to add whatever files you want to add to the KnowledgeBase into that folder they will not be copied in by default.
