from twi.db.base import SessionLocal
from twi.db.models import Post
from twi.nlp import clean_for_embedding
from twi.embeddings import encode_texts, save_embeddings

session = SessionLocal()
posts = session.query(Post).all()
session.close()

texts = [clean_for_embedding(f"{p.title}. {p.body}") for p in posts]
ids = [p.id for p in posts]

embeddings = encode_texts(texts)
save_embeddings(ids, embeddings)
print(f"Encoded and saved {len(ids)} posts")