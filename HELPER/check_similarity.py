import numpy as np
import faiss
import ast
def cosine_similarity(current_news_vec, result_vector) -> float:

    current_news_vec = current_news_vec.astype("float32")

    result_vector_list = ast.literal_eval(result_vector)
    result_vector_float = np.array(result_vector_list, dtype=np.float32)

    # Normalize both vectors
    current_news_vec_norm = current_news_vec / np.linalg.norm(current_news_vec)
    results_vector_norm = result_vector_float / np.linalg.norm(result_vector_float)

    index = faiss.IndexFlatIP(768)  
    index.add(results_vector_norm.reshape(1, -1))  

    # Search with vec1
    D, I = index.search(current_news_vec_norm.reshape(1, -1), k=1)

    # Print cosine similarity score
    similarity_score = float(D[0][0])
    print(f"Cosine Similarity via FAISS: {similarity_score}")
    return similarity_score



def check_cosine_similarity(news_embedding, all_filtered_news):
    similarity_threshold = 0.9
    
    similar_news_id = None
    somewhat_similar_news_id = None
    max_similar_news_score = -1
    max_somewhat_similar_news_score = -1
    if not all_filtered_news:
        print("Empty Database")
        return similar_news_id, somewhat_similar_news_id
    for single_filterd_news in all_filtered_news:
        single_news_embedding = single_filterd_news[1]
        cosine_score = cosine_similarity(news_embedding,single_news_embedding)
        if cosine_score >= similarity_threshold:
            print("Very Similar")
            if cosine_score >= max_similar_news_score:
                max_similar_news_score = cosine_score
                similar_news_id = single_filterd_news[0]
        elif 0.6 < cosine_score < similarity_threshold:
            print("Somewhat Similar")
            if cosine_score >= max_somewhat_similar_news_score:
                max_similar_news_score = cosine_score
                somewhat_similar_news_id = single_filterd_news[0]
        else:
            print("NO MATCH")


    return similar_news_id,somewhat_similar_news_id