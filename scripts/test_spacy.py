from twi.nlp import clean_for_embedding, clean_for_keywords

raw = "I'm **so burnt out**. Check https://example.com - /u/someuser said it's fine"
print(clean_for_embedding(raw))
print(clean_for_keywords(raw))