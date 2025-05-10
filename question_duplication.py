from sentence_transformers import SentenceTransformer, util

embedder = SentenceTransformer('all-MiniLM-L6-v2')

#Store previous questions
previous_questions = []

def is_semantic_duplicate(question, threshold = 0.8):
    if not previous_questions:
        previous_questions.append(question)
        return False
    
    current_embedding = embedder.encode(question, convert_to_tensor = True)
    previous_embeddings = embedder.encode(previous_questions, convert_to_tensor = True)

    #Compute cosine similarity
    cosine_scores = util.cos_sim(current_embedding, previous_embeddings)
    max_similarity = cosine_scores.max().item()

    if max_similarity >= threshold:
        return True
    
    previous_questions.append(question)
    return False

