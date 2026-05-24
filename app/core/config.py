from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql://postgres:Satya199$$@localhost/pinterest"
    REDIS_URL: str = "redis://localhost:6379/0"
    ELASTICSEARCH_URL: str = "http://localhost:9200"
    ELASTICSEARCH_INDEX: str = "pins"
    SECRET_KEY: str = "b1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4"
    ALGORITHM: str = "HS256"
    CLOUDINARY_CLOUD_NAME: str = "dgsyfonz8"
    CLOUDINARY_API_KEY: str = "226568586269397"
    CLOUDINARY_API_SECRET: str = "8I7jR_F2RAzWde1yeTENfZ9-anM"


settings = Settings()
