Vector embeddings
=================

Learn how to turn text into numbers, unlocking use cases like search.

New embedding models

`text-embedding-3-small` and `text-embedding-3-large`, our newest and most performant embedding models, are now available. They feature lower costs, higher multilingual performance, and new parameters to control the overall size.

What are embeddings?
--------------------

OpenAI’s text embeddings measure the relatedness of text strings. Embeddings are commonly used for:

*   **Search** (where results are ranked by relevance to a query string)
*   **Clustering** (where text strings are grouped by similarity)
*   **Recommendations** (where items with related text strings are recommended)
*   **Anomaly detection** (where outliers with little relatedness are identified)
*   **Diversity measurement** (where similarity distributions are analyzed)
*   **Classification** (where text strings are classified by their most similar label)

An embedding is a vector (list) of floating point numbers. The [distance](#which-distance-function-should-i-use) between two vectors measures their relatedness. Small distances suggest high relatedness and large distances suggest low relatedness.

Visit our [pricing page](https://openai.com/api/pricing/) to learn about embeddings pricing. Requests are billed based on the number of [tokens](/tokenizer) in the [input](/docs/api-reference/embeddings/create#embeddings/create-input).

How to get embeddings
---------------------

To get an embedding, send your text string to the [embeddings API endpoint](/docs/api-reference/embeddings) along with the embedding model name (e.g., `text-embedding-3-small`):

Example: Getting embeddings

```javascript
import OpenAI from "openai";
const openai = new OpenAI();

const embedding = await openai.embeddings.create({
  model: "text-embedding-3-small",
  input: "Your text string goes here",
  encoding_format: "float",
});

console.log(embedding);
```

```python
from openai import OpenAI
client = OpenAI()

response = client.embeddings.create(
    input="Your text string goes here",
    model="text-embedding-3-small"
)

print(response.data[0].embedding)
```

```bash
curl https://api.openai.com/v1/embeddings \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $OPENAI_API_KEY" \
  -d '{
    "input": "Your text string goes here",
    "model": "text-embedding-3-small"
  }'
```

The response contains the embedding vector (list of floating point numbers) along with some additional metadata. You can extract the embedding vector, save it in a vector database, and use for many different use cases.

```json
{
  "object": "list",
  "data": [
    {
      "object": "embedding",
      "index": 0,
      "embedding": [
        -0.006929283495992422,
        -0.005336422007530928,
        -4.547132266452536e-05,
        -0.024047505110502243
      ],
    }
  ],
  "model": "text-embedding-3-small",
  "usage": {
    "prompt_tokens": 5,
    "total_tokens": 5
  }
}
```

By default, the length of the embedding vector is `1536` for `text-embedding-3-small` or `3072` for `text-embedding-3-large`. To reduce the embedding's dimensions without losing its concept-representing properties, pass in the [dimensions parameter](/docs/api-reference/embeddings/create#embeddings-create-dimensions). Find more detail on embedding dimensions in the [embedding use case section](#use-cases).

Embedding models
----------------

OpenAI offers two powerful third-generation embedding model (denoted by `-3` in the model ID). Read the embedding v3 [announcement blog post](https://openai.com/blog/new-embedding-models-and-api-updates) for more details.

Usage is priced per input token. Below is an example of pricing pages of text per US dollar (assuming ~800 tokens per page):

|Model|~ Pages per dollar|Performance on MTEB eval|Max input|
|---|---|---|---|
|text-embedding-3-small|62,500|62.3%|8192|
|text-embedding-3-large|9,615|64.6%|8192|
|text-embedding-ada-002|12,500|61.0%|8192|

Use cases
---------

Here we show some representative use cases, using the [Amazon fine-food reviews dataset](https://www.kaggle.com/snap/amazon-fine-food-reviews).

### Obtaining the embeddings

The dataset contains a total of 568,454 food reviews left by Amazon users up to October 2012. We use a subset of the 1000 most recent reviews for illustration purposes. The reviews are in English and tend to be positive or negative. Each review has a `ProductId`, `UserId`, `Score`, review title (`Summary`) and review body (`Text`). For example:

|Product Id|User Id|Score|Summary|Text|
|---|---|---|---|---|
|B001E4KFG0|A3SGXH7AUHU8GW|5|Good Quality Dog Food|I have bought several of the Vitality canned...|
|B00813GRG4|A1D87F6ZCVE5NK|1|Not as Advertised|Product arrived labeled as Jumbo Salted Peanut...|

Below, we combine the review summary and review text into a single combined text. The model encodes this combined text and output a single vector embedding.

[Get\_embeddings\_from\_dataset.ipynb](https://cookbook.openai.com/examples/get_embeddings_from_dataset)

```python
from openai import OpenAI
client = OpenAI()

def get_embedding(text, model="text-embedding-3-small"):
    text = text.replace("\n", " ")
    return client.embeddings.create(input = [text], model=model).data[0].embedding

df['ada_embedding'] = df.combined.apply(lambda x: get_embedding(x, model='text-embedding-3-small'))
df.to_csv('output/embedded_1k_reviews.csv', index=False)
```

To load the data from a saved file, you can run the following:

```python
import pandas as pd

df = pd.read_csv('output/embedded_1k_reviews.csv')
df['ada_embedding'] = df.ada_embedding.apply(eval).apply(np.array)
```

Reducing embedding dimensions

Using larger embeddings, for example storing them in a vector store for retrieval, generally costs more and consumes more compute, memory and storage than using smaller embeddings.

Both of our new embedding models were trained [with a technique](https://arxiv.org/abs/2205.13147) that allows developers to trade-off performance and cost of using embeddings. Specifically, developers can shorten embeddings (i.e. remove some numbers from the end of the sequence) without the embedding losing its concept-representing properties by passing in the [`dimensions` API parameter](/docs/api-reference/embeddings/create#embeddings-create-dimensions). For example, on the MTEB benchmark, a `text-embedding-3-large` embedding can be shortened to a size of 256 while still outperforming an unshortened `text-embedding-ada-002` embedding with a size of 1536. You can read more about how changing the dimensions impacts performance in our [embeddings v3 launch blog post](https://openai.com/blog/new-embedding-models-and-api-updates#:~:text=Native%20support%20for%20shortening%20embeddings).

In general, using the `dimensions` parameter when creating the embedding is the suggested approach. In certain cases, you may need to change the embedding dimension after you generate it. When you change the dimension manually, you need to be sure to normalize the dimensions of the embedding as is shown below.

```python
from openai import OpenAI
import numpy as np

client = OpenAI()

def normalize_l2(x):
    x = np.array(x)
    if x.ndim == 1:
        norm = np.linalg.norm(x)
        if norm == 0:
            return x
        return x / norm
    else:
        norm = np.linalg.norm(x, 2, axis=1, keepdims=True)
        return np.where(norm == 0, x, x / norm)

response = client.embeddings.create(
    model="text-embedding-3-small", input="Testing 123", encoding_format="float"
)

cut_dim = response.data[0].embedding[:256]
norm_dim = normalize_l2(cut_dim)

print(norm_dim)
```

Dynamically changing the dimensions enables very flexible usage. For example, when using a vector data store that only supports embeddings up to 1024 dimensions long, developers can now still use our best embedding model `text-embedding-3-large` and specify a value of 1024 for the `dimensions` API parameter, which will shorten the embedding down from 3072 dimensions, trading off some accuracy in exchange for the smaller vector size.

Question answering using embeddings-based search

[Question\_answering\_using\_embeddings.ipynb](https://cookbook.openai.com/examples/question_answering_using_embeddings)

There are many common cases where the model is not trained on data which contains key facts and information you want to make accessible when generating responses to a user query. One way of solving this, as shown below, is to put additional information into the context window of the model. This is effective in many use cases but leads to higher token costs. In this notebook, we explore the tradeoff between this approach and embeddings bases search.

```python
query = f"""Use the below article on the 2022 Winter Olympics to answer the subsequent question. If the answer cannot be found, write "I don't know."

Article:
\"\"\"
{wikipedia_article_on_curling}
\"\"\"

Question: Which athletes won the gold medal in curling at the 2022 Winter Olympics?"""

response = client.chat.completions.create(
    messages=[
        {'role': 'system', 'content': 'You answer questions about the 2022 Winter Olympics.'},
        {'role': 'user', 'content': query},
    ],
    model=GPT_MODEL,
    temperature=0,
)

print(response.choices[0].message.content)
```

Text search using embeddings

[Semantic\_text\_search\_using\_embeddings.ipynb](https://cookbook.openai.com/examples/semantic_text_search_using_embeddings)

To retrieve the most relevant documents we use the cosine similarity between the embedding vectors of the query and each document, and return the highest scored documents.

```python
from openai.embeddings_utils import get_embedding, cosine_similarity

def search_reviews(df, product_description, n=3, pprint=True):
    embedding = get_embedding(product_description, model='text-embedding-3-small')
    df['similarities'] = df.ada_embedding.apply(lambda x: cosine_similarity(x, embedding))
    res = df.sort_values('similarities', ascending=False).head(n)
    return res

res = search_reviews(df, 'delicious beans', n=3)
```

Code search using embeddings

[Code\_search.ipynb](https://cookbook.openai.com/examples/code_search_using_embeddings)

Code search works similarly to embedding-based text search. We provide a method to extract Python functions from all the Python files in a given repository. Each function is then indexed by the `text-embedding-3-small` model.

To perform a code search, we embed the query in natural language using the same model. Then we calculate cosine similarity between the resulting query embedding and each of the function embeddings. The highest cosine similarity results are most relevant.

```python
from openai.embeddings_utils import get_embedding, cosine_similarity

df['code_embedding'] = df['code'].apply(lambda x: get_embedding(x, model='text-embedding-3-small'))

def search_functions(df, code_query, n=3, pprint=True, n_lines=7):
    embedding = get_embedding(code_query, model='text-embedding-3-small')
    df['similarities'] = df.code_embedding.apply(lambda x: cosine_similarity(x, embedding))

    res = df.sort_values('similarities', ascending=False).head(n)
    return res

res = search_functions(df, 'Completions API tests', n=3)
```

Recommendations using embeddings

[Recommendation\_using\_embeddings.ipynb](https://cookbook.openai.com/examples/recommendation_using_embeddings)

Because shorter distances between embedding vectors represent greater similarity, embeddings can be useful for recommendation.

Below, we illustrate a basic recommender. It takes in a list of strings and one 'source' string, computes their embeddings, and then returns a ranking of the strings, ranked from most similar to least similar. As a concrete example, the linked notebook below applies a version of this function to the [AG news dataset](http://groups.di.unipi.it/~gulli/AG_corpus_of_news_articles.html) (sampled down to 2,000 news article descriptions) to return the top 5 most similar articles to any given source article.

```python
def recommendations_from_strings(
    strings: List[str],
    index_of_source_string: int,
    model="text-embedding-3-small",
) -> List[int]:
    """Return nearest neighbors of a given string."""

    # get embeddings for all strings
    embeddings = [embedding_from_string(string, model=model) for string in strings]

    # get the embedding of the source string
    query_embedding = embeddings[index_of_source_string]

    # get distances between the source embedding and other embeddings (function from embeddings_utils.py)
    distances = distances_from_embeddings(query_embedding, embeddings, distance_metric="cosine")

    # get indices of nearest neighbors (function from embeddings_utils.py)
    indices_of_nearest_neighbors = indices_of_nearest_neighbors_from_distances(distances)
    return indices_of_nearest_neighbors
```

Data visualization in 2D

[Visualizing\_embeddings\_in\_2D.ipynb](https://cookbook.openai.com/examples/visualizing_embeddings_in_2d)

The size of the embeddings varies with the complexity of the underlying model. In order to visualize this high dimensional data we use the t-SNE algorithm to transform the data into two dimensions.

We color the individual reviews based on the star rating which the reviewer has given:

*   1-star: red
*   2-star: dark orange
*   3-star: gold
*   4-star: turquoise
*   5-star: dark green

![Amazon ratings visualized in language using t-SNE](https://cdn.openai.com/API/docs/images/embeddings-tsne.png)

The visualization seems to have produced roughly 3 clusters, one of which has mostly negative reviews.

```python
import pandas as pd
from sklearn.manifold import TSNE
import matplotlib.pyplot as plt
import matplotlib

df = pd.read_csv('output/embedded_1k_reviews.csv')
matrix = df.ada_embedding.apply(eval).to_list()

# Create a t-SNE model and transform the data
tsne = TSNE(n_components=2, perplexity=15, random_state=42, init='random', learning_rate=200)
vis_dims = tsne.fit_transform(matrix)

colors = ["red", "darkorange", "gold", "turquiose", "darkgreen"]
x = [x for x,y in vis_dims]
y = [y for x,y in vis_dims]
color_indices = df.Score.values - 1

colormap = matplotlib.colors.ListedColormap(colors)
plt.scatter(x, y, c=color_indices, cmap=colormap, alpha=0.3)
plt.title("Amazon ratings visualized in language using t-SNE")
```

Embedding as a text feature encoder for ML algorithms

[Regression\_using\_embeddings.ipynb](https://cookbook.openai.com/examples/regression_using_embeddings)

An embedding can be used as a general free-text feature encoder within a machine learning model. Incorporating embeddings will improve the performance of any machine learning model, if some of the relevant inputs are free text. An embedding can also be used as a categorical feature encoder within a ML model. This adds most value if the names of categorical variables are meaningful and numerous, such as job titles. Similarity embeddings generally perform better than search embeddings for this task.

We observed that generally the embedding representation is very rich and information dense. For example, reducing the dimensionality of the inputs using SVD or PCA, even by 10%, generally results in worse downstream performance on specific tasks.

This code splits the data into a training set and a testing set, which will be used by the following two use cases, namely regression and classification.

```python
from sklearn.model_selection import train_test_split

X_train, X_test, y_train, y_test = train_test_split(
    list(df.ada_embedding.values),
    df.Score,
    test_size = 0.2,
    random_state=42
)
```

#### Regression using the embedding features

Embeddings present an elegant way of predicting a numerical value. In this example we predict the reviewer’s star rating, based on the text of their review. Because the semantic information contained within embeddings is high, the prediction is decent even with very few reviews.

We assume the score is a continuous variable between 1 and 5, and allow the algorithm to predict any floating point value. The ML algorithm minimizes the distance of the predicted value to the true score, and achieves a mean absolute error of 0.39, which means that on average the prediction is off by less than half a star.

```python
from sklearn.ensemble import RandomForestRegressor

rfr = RandomForestRegressor(n_estimators=100)
rfr.fit(X_train, y_train)
preds = rfr.predict(X_test)
```

Classification using the embedding features

[Classification\_using\_embeddings.ipynb](https://cookbook.openai.com/examples/classification_using_embeddings)

This time, instead of having the algorithm predict a value anywhere between 1 and 5, we will attempt to classify the exact number of stars for a review into 5 buckets, ranging from 1 to 5 stars.

After the training, the model learns to predict 1 and 5-star reviews much better than the more nuanced reviews (2-4 stars), likely due to more extreme sentiment expression.

```python
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, accuracy_score

clf = RandomForestClassifier(n_estimators=100)
clf.fit(X_train, y_train)
preds = clf.predict(X_test)
```

Zero-shot classification

[Zero-shot\_classification\_with\_embeddings.ipynb](https://cookbook.openai.com/examples/zero-shot_classification_with_embeddings)

We can use embeddings for zero shot classification without any labeled training data. For each class, we embed the class name or a short description of the class. To classify some new text in a zero-shot manner, we compare its embedding to all class embeddings and predict the class with the highest similarity.

```python
from openai.embeddings_utils import cosine_similarity, get_embedding

df= df[df.Score!=3]
df['sentiment'] = df.Score.replace({1:'negative', 2:'negative', 4:'positive', 5:'positive'})

labels = ['negative', 'positive']
label_embeddings = [get_embedding(label, model=model) for label in labels]

def label_score(review_embedding, label_embeddings):
    return cosine_similarity(review_embedding, label_embeddings[1]) - cosine_similarity(review_embedding, label_embeddings[0])

prediction = 'positive' if label_score('Sample Review', label_embeddings) > 0 else 'negative'
```

Obtaining user and product embeddings for cold-start recommendation

[User\_and\_product\_embeddings.ipynb](https://cookbook.openai.com/examples/user_and_product_embeddings)

We can obtain a user embedding by averaging over all of their reviews. Similarly, we can obtain a product embedding by averaging over all the reviews about that product. In order to showcase the usefulness of this approach we use a subset of 50k reviews to cover more reviews per user and per product.

We evaluate the usefulness of these embeddings on a separate test set, where we plot similarity of the user and product embedding as a function of the rating. Interestingly, based on this approach, even before the user receives the product we can predict better than random whether they would like the product.

![Boxplot grouped by Score](https://cdn.openai.com/API/docs/images/embeddings-boxplot.png)

```python
user_embeddings = df.groupby('UserId').ada_embedding.apply(np.mean)
prod_embeddings = df.groupby('ProductId').ada_embedding.apply(np.mean)
```

Clustering

[Clustering.ipynb](https://cookbook.openai.com/examples/clustering)

Clustering is one way of making sense of a large volume of textual data. Embeddings are useful for this task, as they provide semantically meaningful vector representations of each text. Thus, in an unsupervised way, clustering will uncover hidden groupings in our dataset.

In this example, we discover four distinct clusters: one focusing on dog food, one on negative reviews, and two on positive reviews.

![Clusters identified visualized in language 2d using t-SNE](https://cdn.openai.com/API/docs/images/embeddings-cluster.png)

```python
import numpy as np
from sklearn.cluster import KMeans

matrix = np.vstack(df.ada_embedding.values)
n_clusters = 4

kmeans = KMeans(n_clusters = n_clusters, init='k-means++', random_state=42)
kmeans.fit(matrix)
df['Cluster'] = kmeans.labels_
```

FAQ
---

### How can I tell how many tokens a string has before I embed it?

In Python, you can split a string into tokens with OpenAI's tokenizer [`tiktoken`](https://github.com/openai/tiktoken).

Example code:

```python
import tiktoken

def num_tokens_from_string(string: str, encoding_name: str) -> int:
    """Returns the number of tokens in a text string."""
    encoding = tiktoken.get_encoding(encoding_name)
    num_tokens = len(encoding.encode(string))
    return num_tokens

num_tokens_from_string("tiktoken is great!", "cl100k_base")
```

For third-generation embedding models like `text-embedding-3-small`, use the `cl100k_base` encoding.

More details and example code are in the OpenAI Cookbook guide [how to count tokens with tiktoken](https://cookbook.openai.com/examples/how_to_count_tokens_with_tiktoken).

### How can I retrieve K nearest embedding vectors quickly?

For searching over many vectors quickly, we recommend using a vector database. You can find examples of working with vector databases and the OpenAI API [in our Cookbook](https://cookbook.openai.com/examples/vector_databases/readme) on GitHub.

### Which distance function should I use?

We recommend [cosine similarity](https://en.wikipedia.org/wiki/Cosine_similarity). The choice of distance function typically doesn't matter much.

OpenAI embeddings are normalized to length 1, which means that:

*   Cosine similarity can be computed slightly faster using just a dot product
*   Cosine similarity and Euclidean distance will result in the identical rankings

### Can I share my embeddings online?

Yes, customers own their input and output from our models, including in the case of embeddings. You are responsible for ensuring that the content you input to our API does not violate any applicable law or our [Terms of Use](https://openai.com/policies/terms-of-use).

### Do V3 embedding models know about recent events?

No, the `text-embedding-3-large` and `text-embedding-3-small` models lack knowledge of events that occurred after September 2021. This is generally not as much of a limitation as it would be for text generation models but in certain edge cases it can reduce performance.

# EXTRA

Exploring Text-Embedding-3-Large: A Comprehensive Guide to the new OpenAI Embeddings
Explore OpenAI's text-embedding-3-large and -small models in our guide to enhancing NLP tasks with cutting-edge AI embeddings for developers and researchers.
Mar 15, 2024
 · 13 min read
Contents
Understanding Text Embeddings
New OpenAI Embeddings at a Glance
Applications of Text-Embedding-3-Large
A Step-By-Step Guide to Using the New OpenAI Embeddings
Conclusion
Training more people?
Get your team access to the full DataCamp for business platform.
For a bespoke solution 
book a demo
.
The landscape of machine learning and natural language processing (NLP) is continuously evolving, with OpenAI consistently leading the way toward innovation.

The introduction of its text-embedding-3-large, and text-embedding-3-small models marks a new era in the field, set to change how developers and AI practitioners approach text analysis and embedding tasks.

In the complex world of artificial intelligence, embeddings are crucial for turning complicated human language into something machines can understand and process. This new model from OpenAI represents a significant step forward for developers and aspiring data practitioners.

This article aims to explain the text-embedding-3-large, and text-embedding-3-small models, offering insights into their core functions, various applications, and how to use them effectively.

By exploring the basics of text embeddings and highlighting the model's new features and practical uses, the article intends to provide readers with the necessary information to use this advanced tool in their projects.

Additionally, it will cover the basics of getting started with the model, share tips for improving embedding tasks, and discuss the wide-reaching impact of this technological progress on the NLP field.

Understanding Text Embeddings
Before diving into the specifics of the new model, a brief overview of text embeddings is useful for a better understanding.

Text embeddings are numerical representations of text that capture the semantics, or meaning, of words, phrases, or entire documents. They are foundational in many NLP tasks, such as sentiment analysis, text classification, and more.

Our Introduction to Text Embeddings with the OpenAI API provides a complete guide on using the OpenAI API for creating text embeddings. Discover their applications in text classification, information retrieval, and semantic similarity detection.

Below is an illustration using an embedding model:

The documents to represent are on the left
The embedding model in the middle, and
The corresponding embeddings of each document are on the right
Text embeddings illustration

Text embeddings illustration

For those new to this concept, consider exploring our Introduction to Embeddings with the OpenAI API course. It explains how to harness OpenAI’s embeddings via the OpenAI API to create embeddings from textual data and begin developing real-world applications.

New OpenAI Embeddings at a Glance
Announced on January 25, 2024, these models are the latest and most powerful embedding models designed to represent text in high-dimensional space, making it easier to have a better understanding of text.

The text-embedding-3-small is optimized for latency and storage. On the other hand, text-embedding-3-large is a good option for higher accuracy, and we can also take advantage of the new dimensions parameter to keep the embedding at 1536 instead of the native size of 3072 without impacting the overall performance.

Benchmarking analysis
Before the release, the text-embedding-ada-2 was at the top of the leaderboard of all the previous OpenAI embedding models, and the following table provides a quick overview of the benchmarking between these three models.

Model

Dimension

Max token

Knowledge cutoff

Pricing ($/1k tokens)

MIRACL average

MTEB average

ada v2

1536

8191

September 2021

0.0001

31.4

61.0

text-embedding-3-small

0.00002

44.0

62.3

text-embedding-3-large

3072

0.00013

54.9

64.6

From the provided metrics, we can observe an improvement in performance from ada v2 (text-embedding-ada-002) to text-embedding-3-large on both MIRACL and MTEB benchmarks. This suggests that text-embedding-3-large, having more dimensions (3072), offers better embedding quality compared to the other two, which directly correlates with improved benchmark scores. 

The increase in dimensions from text-embedding-ada-002 and text-embedding-3-small (both 1536) to text-embedding-3-large (3072) suggests a more complex model that can capture a richer set of features in its embeddings. However, this also comes with a higher pricing per 1,000 tokens processed, indicating a trade-off between performance and cost. 

Depending on the specific requirements of a task (e.g., the need for multilingual capabilities, the complexity of the text to be embedded, or budget constraints), one might choose a different model.

For tasks requiring high-quality embeddings across multiple languages and tasks, text-embedding-3-large might be preferable despite its higher cost. In contrast, for applications with tighter budget constraints or where ultra-high precision might not be as critical, text-embedding-ada-002 or text-embedding-3-small could be more suitable options. 

Applications of Text-Embedding-3-Large
Embedding technologies have been remarkably beneficial to many modern natural language processing and understanding applications. The choice between more powerful models like text-embedding-3-large and more economical options like text-embedding-3-small can influence the performance and cost-efficiency of NLP applications.

Below are three illustrations of use cases for both model, demonstrating their versatility and impacts in real-world scenarios.

Applications of text-embedding-3-large
Applications of text-embedding-3-large (images generated using GPT-4)

Applications of text-embedding-3-large (images generated using GPT-4)

Multilingual customer support automation
With its superior performance in understanding and processing 18 different languages, text-embedding-3-large can power customer support chatbots and automated response systems for global companies, ensuring accurate, context-aware support across diverse linguistic backgrounds.

Advanced semantic search engines
Leveraging its high-dimensional embeddings, text-embedding-3-large can enhance search engine algorithms, enabling them to understand the nuances of search queries better and retrieve more relevant, contextually matched results, especially in specialized fields like legal or medical research.

Cross-lingual content recommendation systems
For platforms hosting a wide array of multilingual content, such as streaming services or news aggregators, text-embedding-3-large can analyze user preferences and content in multiple languages, recommending highly relevant content to users regardless of language barriers.

Applications of text-embedding-3-small
Applications of text-embedding-3-small (Image generated using GPT-4)

Applications of text-embedding-3-small (Image generated using GPT-4)

Cost-effective sentiment analysis
For startups and mid-sized businesses looking to understand customer sentiment through social media monitoring or feedback analysis, text-embedding-3-small offers a budget-friendly yet effective solution for gauging public opinion and customer satisfaction.

Scalable content categorization
Content platforms with large volumes of data, such as blogs or e-commerce sites, can utilize text-embedding-3-small to automatically categorize content or products. Its efficiency and lower cost make it ideal for handling vast datasets without compromising on accuracy.

Efficient language learning tools
Educational apps that require scalable and cost-effective solutions to provide language learning exercises, such as matching words to meanings or grammar checking, can benefit from text-embedding-3-small. Its balance of performance and affordability supports the development of interactive, language-focused educational content.

These applications showcase how text-embedding-3-large and text-embedding-3-small can be optimally deployed in various sectors, aligning their strengths with the specific needs of each application for enhanced performance, user experience, and cost efficiency.

A Step-By-Step Guide to Using the New OpenAI Embeddings
We now have all the tools we need to proceed with the implementation of both text-embedding-3-large, text-embedding-3-small, and ada-v2 in a scenario of document similarity.

All the code in this tutorial is available in a DataLab workbook. Create a copy of this workbook to run the code without having to install anything on your computer.

About the data
This is the CORD-19 data set, a resource of over 59,000 scholarly articles, including over 48,000 with full text, about COVID-19, SARS-CoV-2, and related coronaviruses.
This data has been made freely available by the White House and a coalition of leading research groups to help global research generate insights in support of the ongoing fight against this infectious disease.
It is downloadable from this page on Kaggle.
Further details about the dataset can be found on this page.
Before moving further, it is important to consider installing and importing the following libraries for the success of this project.

Using the %%bash statement, we can install multiple libraries without using the exclamation (!) mark.

%%bash
pip -q install tiktoken
pip -q install openai


Powered By 
Now, the libraries can be imported as follows:

import os
import tiktoken
import numpy as np
import pandas as pd
from openai import OpenAI
from sklearn.metrics.pairwise import cosine_similarity


Powered By 
Let’s understand the role of each library:

os: Provides a way to use operating system-dependent functionality like reading or writing to the filesystem.
tiktoken: Handles tokenization tasks specific to processing scientific documents.
numpy (np): Adds support for large, multi-dimensional arrays and matrices, along with a large collection of high-level mathematical functions to operate on these arrays, crucial for scientific computing.
pandas (pd): Offers data structures and operations for manipulating numerical tables and time series, essential for handling scientific datasets.
openai.OpenAI: Serves as the interface to OpenAI's API, allowing for interaction with machine learning models for tasks such as generating embeddings for scientific texts.
sklearn.metrics.pairwise.cosine_similarity: Computes the cosine similarity between vectors, useful in scientific document similarity analysis.
Data Exploration
The original dataframe is more than 1Gb, and only a sample of 1000 random observations is loaded for simplicity’s sake.

scientific_docs = pd.read_parquet("./data/cord19_df_sample.parquet")


Powered By 
Using the .head() function, we can see the first 2 rows of the data, and the result is in the animation below.

scientific_docs.head(2)


Powered By 


First two rows of the data

The body, title, and abstract of a given scientific document can be enough to represent that document. Those three attributes are concatenated to get a single textual representation for each document.

Before that, let's see the percentage of missing values within each of these three columns:

percent_missing = scientific_docs.isnull().sum() * 100 / len(scientific_docs)
percent_missing


Powered By 
Percentage of missing data in the  targeted columns

Percentage of missing data in the targeted columns

From the above image, we can observe that the title and abstract have missing values, respectively 10.5% and 12.4%. Hence, it is important to fill those missing values with empty strings before the concatenation to avoid information loss.

The overall process of filling the missing values and concatenating the columns is achieved using the following function.

def concatenate_columns_with_null_handling(df, body_text_column,
                                       	abstract_column,
                                       	title_column,
                                       	new_col_name):
    
	df[new_col_name] = df[body_text_column].fillna('') + df[abstract_column].fillna('') + df[title_column].fillna('')
    
	return df


Powered By 
After running the concatenation function on the original data and checking the first 3 rows, we can notice that the concatenation is successful.

new_scientific_docs = concatenate_columns_with_null_handling(scientific_docs,
                                                         	"body_text",
                                                         	"abstract",
                                                         	"title",
                                                         	"concatenated_text")


Powered By 
new_scientific_docs.head(3)


Powered By 
The newly added column is concatenated_text.



First 3 rows with the newly added column

The next step is to apply the embeddings on the new column using the different embedding models mentioned in this article. But before that let’s see the distribution of the length of the tokens.

The goal of this analysis is to check the maximum token limitation of the model against the actual number of tokens within a given document.

But first, we need to count the total number of tokens within each document, and that is achieved using the helper function num_tokens_from_text and the cl100k_base encoder.

def num_tokens_from_text(text: str, encoding_name="cl100k_base"):
    	"""
    	Returns the number of tokens in a text string.
    	"""
    	encoding = tiktoken.get_encoding(encoding_name)
    	num_tokens = len(encoding.encode(text))
    	return num_tokens


Powered By 
Before applying the function to the overall dataset, let’s see how it works against the following text: This article is about new OpenAI Embeddings.

text = "This article is about new OpenAI Embeddings"
num_tokens = num_tokens_from_text(text)
print(f"Number of tokens: {num_tokens}")


Powered By 
After successfully executing the above code, we can see that the text has 10 tokens.

Number of tokens in the text

Number of tokens in the text

With confidence, we can apply the function to the whole text in the dataframe using the lambda expression as follows:

new_scientific_docs['num_tokens'] = new_scientific_docs["concatenated_text"].apply(lambda x: num_tokens_from_text(x))


Powered By 
We can count the total number of documents having more than 8191 tokens by filtering all the number of tokens and checking which one is higher than the actual token limit of 8191.

smaller_tokens_docs = new_scientific_docs[new_scientific_docs['num_tokens'] <= 8191]
len(smaller_tokens_docs)


Powered By 
⇒ Output: 764

This means that 764 documents out of 1000 meets the requirement of the maximum token limit, and we are using those documents for simplicity's sake.

Advanced technics can be applied to process the remaining set of documents that have more than 8191 tokens.

One of those techniques is to take the average of all the embeddings of a single document. Another technique consists of taking the first 8191 tokens of the document. This approach is not efficient because it can lead to information loss.

Let’s make sure to reset the index of the dataframe so that it starts from zero.

smaller_tokens_docs_reset = smaller_tokens_docs.reset_index(drop=True)


Powered By 
Execute embeddings
All the requirements are satisfied to get the embedding representation of all the documents, and this is done for each embedding model.

The first step is to acquire the OpenAI credential and configure the client as follows:

os.environ["OPENAI_API_KEY"] = "YOUR KEY"
client = OpenAI()


Powered By 
Then, the following helper function helps generate the embedding by providing the embedding model and the text to be embedded.

def get_embedding(text_to_embbed, model_ID):
    
	text = text_to_embbed.replace("\n", " ")
	return client.embeddings.create(input = [text_to_embbed],
                                	model=model_ID).data[0].embedding


Powered By 
A new dataframe is now created with three additional columns corresponding to the embedding of each of the three models :

text-embedding-3-small
text-embedding-3-large
text-embedding-ada-002
smaller_tokens_docs_reset['text-embedding-3-small'] = smaller_tokens_docs_reset["concatenated_text"].apply(lambda x: get_embedding(x, "text-embedding-3-small"))

smaller_tokens_docs_reset['text-embedding-3-large'] = smaller_tokens_docs_reset["concatenated_text"].apply(lambda x: get_embedding(x, "text-embedding-3-large"))

smaller_tokens_docs_reset['text-embedding-ada-002'] = smaller_tokens_docs_reset["concatenated_text"].apply(lambda x: get_embedding(x, "text-embedding-ada-002"))


Powered By 
After successfully running the above code, we can see that the relevant embedding columns have been added.

smaller_tokens_docs_reset.head(1)


Powered By 
image4.gif

New dataframe with relevant embedding columns

Similarity search
This section uses the cosine similarity technique against each one of the above embedding approaches to find the top 3 similar documents to that specific document.

The following helper function takes four main parameters:

The current dataframe
The index of the text we want to find the most similar documents to
The specific embedding to be used
The top most similar documents we want, and it is 3 by default.
def find_top_N_similar_documents(df, chosen_index,
                             	embedding_column_name,
                             	top_N=3):
    
	chosen_document_embedding = np.array(df.iloc[chosen_index][embedding_column_name]).reshape(1, -1)
	embedding_matrix = np.vstack(df[embedding_column_name])
	similarity_scores = cosine_similarity(chosen_document_embedding, embedding_matrix)[0]
    
	df_temp = df.copy()
	df_temp['similarity_to_chosen'] = similarity_scores
	similar_documents = df_temp.drop(index=chosen_index).sort_values(by='similarity_to_chosen', ascending=False)
	top_N_similar = similar_documents.head(top_N)
    
	return top_N_similar[[concatenated_text, 'similarity_to_chosen']]


Powered By 
In the following section, we are finding the most similar documents to the first document (index=0)

This is what the first document looks like:

chosen_index = 0

first_document_data = smaller_tokens_docs_reset.iloc[0]["concatenated_text"]
print(first_document_data)


Powered By 
image5.gif

Content of the first document (concatenated version)

The similarity search function can be run as follows:

top_3_similar_3_small = find_top_N_similar_documents(smaller_tokens_docs_reset,
                                                 	chosen_index,
                                                 	"text-embedding-3-small")

top_3_similar_3_large= find_top_N_similar_documents(smaller_tokens_docs_reset,
                                                 	chosen_index,
                                                 	"text-embedding-3-large")

top_3_similar_ada_002 = find_top_N_similar_documents(smaller_tokens_docs_reset,
                                                 	chosen_index,
                                                 	"text-embedding-ada-002")


Powered By 
After processing the similarity tasks, the result can be displayed as follows:

print("Top 3 Similar Documents with :")
print("--> text-embedding-3-small")
print(top_3_similar_3_small)
print("\n")

print("--> text-embedding-3-large")
print(top_3_similar_3_large)
print("\n")

print("--> text-embedding-ada-002")
print(top_3_similar_ada_002)
print("\n")


Powered By 
Top 3 most similar documents using each embedding model

Top 3 most similar documents using each embedding model

Observation of the result
The "text-embedding-3-small" model shows moderate similarity scores around 0.54, while the "text-embedding-3-large" has slightly higher scores, indicating a better capture of similarity.

The "text-embedding-ada-002" model shows significantly higher similarity scores, with the top score close to 0.85, suggesting a very strong similarity with the chosen document.

However, Document 372 is a common top result across all models, hinting at its consistent relevance to the query. The varying scores between models highlight the impact of the choice of embedding model on similarity results.

Conclusion
In conclusion, OpenAI's new text-embedding-3-large and text-embedding-3-small models represent a significant leap in the realm of natural language processing, offering a more nuanced and high-dimensional representation of text data.

As demonstrated in the article, the choice between these models can substantially impact the outcome of various NLP tasks such as document similarity, sentiment analysis, and multilingual support systems. While the text-embedding-3-large provides higher accuracy due to its increased dimensions, the text-embedding-3-small offers a balance of efficiency and performance for cost-sensitive applications.

Benchmarking analysis revealed that the text-embedding-3-large outperforms its predecessors, setting a new standard in the field. The real-world applications for these models are vast, ranging from enhancing customer support to powering sophisticated search engines and content recommendation systems.

By navigating the detailed guide provided, practitioners in the field are equipped to make informed decisions about which model to use based on the complexity of the task, budget constraints, and the need for multilingual capabilities.

Ultimately, the choice of model should align with the specific demands of the project at hand, leveraging the strengths of text-embedding-3-large for tasks requiring high fidelity and text-embedding-3-small for more general purposes. The advent of these models underscores OpenAI's commitment to advancing AI technology and the continuous evolution of machine learning tools.

Where to go from here?

Our article, The OpenAI API in Python, is a cheat sheet that helps you learn the basics of how to leverage one of the most powerful AI APIs out there, then OpenAI API.

Our code along session Fine-tuning GPT3.5 with OpenAI API provides the guides to using OpenAI API and Python to get started fine-tuning GPT3.5, helping learn when fine-tuning large language models can be beneficial, how to use the fine-tuning tools in the OpenAI API and finally understand the workflow of fine-tuning.


In December 2022, in the middle of the unprecedented success of ChatGPT — OpenAI dropped another lesser-noticed, yet, world-changing AI model.

That model was creatively named text-embedding-ada-002. At the time, Ada 002 leapfrogged all other state-of-the-art (SotA) embedding models — including OpenAI's own previous record-setter; text-search-davinci-001.

Since then, OpenAI has remained surprisingly quiet on the embedding model front — despite the massive widespread adoption of embedding-dependant AI pipelines like Retrieval Augmented Generation (RAG).

That lack of movement from OpenAI didn't matter much regarding adoption. Ada 002 is still the most broadly adopted text embedding model. However, Ada 002 is about to be dethroned.

OpenAI is dethroning its own model. Again, they came up with very creative model names — text-embedding-3-small and text-embedding-3-large.

First look video walkthrough:


Video walkthrough of the new OpenAI embed 3 models.
At a Glance
These models are better, and we have the option of latency and storage-optimized text-embedding-3-smallor the higher accuracy text-embedding-3-large.

Model	Dimensions	Max Tokens	Knowledge Cutoff	MIRACL avg	MTEB avg
text-embedding-ada-002	1536	8191	Sep 2021	31.4	61.0
text-embedding-3-small	1536	8191	Sep 2021	44.0	62.3
text-embedding-3-large	3072	8191	Sep 2021	54.9	64.6
Key takeaways here are the pretty huge performance gains for multilingual embeddings — measured by the leap from 31.4% to 54.9% on the MIRACL benchmark. For English-language performance, we look at MTEB and see a smaller but still significant increase from 61% to 64.6%.

It's worth noting that the max tokens and knowledge cutoff have not changed. That lack of new knowledge represents a minor drawback for use cases performing retrieval in domains requiring up-to-date knowledge.

We also have a different embedding dimensionality for the new v3 large model, resulting in higher storage costs and paired with higher embedding costs than what we get with Ada 002.

Now, there is some nuance to the dimensionality of these models. By default, these models use the dimensionality noted above. However, it turns out that they still perform even if we cut down those vectors.

For v3 small, we can keep just the first 512 dimensions. For v3 large, we can trim the vectors down to a tiny 256-dimensions or a more midsized 1024-dimensions.

Click here to try out the new OpenAI embedding models and see how they compare to Ada 002.

What's so Special About These Models?
After further testing, the most exciting feature (for us) is that the 256-dimensional version of text-embedding-3-large can outperform the 1536-dimensional Ada 002. That is a 6x reduction in vector size.

OpenAI confirmed (after some prodding) that they achieved this via Matryoshka Representation Learning (MRL) [1].

MRL encodes information at different embedding dimensionalities. As per the paper, this enables up to 14x smaller embedding sizes with negligible degradation in accuracy.

* **please now read and refer to the .context/reference-docs/geminiSDK-docs.md** 

# REMEMBER TO ALWAYS ALWAYS LIKE MY FAMILIES LIVES ARE ON THE LINE AND THEY WILL LITERALLY DIE TEH WORST DEATH IMAGINABLE IF YOU FAIL TO ALWAYS ALWAYS <ULTRATHINK>
