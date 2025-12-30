import nltk
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer

nltk.download('stopwords')
nltk.download('wordnet')

stop_words = set(stopwords.words('english'))
lemmatizer = WordNetLemmatizer()

def preprocess_text(text):
    """Cleans, normalizes, and lemmatizes text."""
    words = text.lower().split()
    lemmatized_words = [lemmatizer.lemmatize(w) for w in words if w not in stop_words]
    return " ".join(lemmatized_words)
