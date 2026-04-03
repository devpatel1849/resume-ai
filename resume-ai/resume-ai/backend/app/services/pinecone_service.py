from pinecone import Pinecone, ServerlessSpec
from app.config import settings
from app.utils.embedding import generate_embedding

class PineconeService:
    def __init__(self):
        self.pc = Pinecone(api_key=settings.PINECONE_API_KEY)
        self.index_name = settings.PINECONE_INDEX

        if self.index_name not in self.pc.list_indexes().names():
            self.pc.create_index(
                name=self.index_name,
                dimension=100,
                metric="cosine",
                spec=ServerlessSpec(cloud="aws", region=settings.PINECONE_ENV)
            )

        self.index = self.pc.Index(self.index_name)

    def store(self, id: str, text: str):
        vector = generate_embedding(text)

        self.index.upsert([
            {
                "id": id,
                "values": vector,
                "metadata": {"text": text}
            }
        ])

    def query(self, query: str):
        vector = generate_embedding(query)

        results = self.index.query(
            vector=vector,
            top_k=3,
            include_metadata=True
        )

        return [match["metadata"]["text"] for match in results["matches"]]


pinecone_service = PineconeService()