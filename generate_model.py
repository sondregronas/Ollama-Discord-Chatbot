import ollama
import os
from dotenv import load_dotenv

load_dotenv()
MODEL_NAME = os.getenv('MODEL_NAME')

with open('model.txt', 'r') as f:
    modelfile = f.read()

ollama.create(model=MODEL_NAME, modelfile=modelfile)

print("Model created successfully!")