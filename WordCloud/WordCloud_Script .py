from wordcloud import WordCloud, STOPWORDS
import matplotlib.pyplot as plt
import pandas as pd

df = pd.read_csv(r"summary_read.csv", encoding="latin-1", names=["titles"])  # summary_cloud06022022

stopwords = list(STOPWORDS)+['study', 'review', 'analysis', 'low',
                             'slurries', 'finned',  'change material', 'flash', 'using', 'heat pump', 'heat', 'pump']  # Common english words
comment_words = ''
for i in range(len(df)):
    val = df.iat[i, 0]
    # typecaste each val to string
    val = str(val)
    # split the value
    tokens = val.split()
    # Converts each token into lowercase
    for j in range(len(tokens)):
        tokens[j] = tokens[j].lower()

    comment_words += " ".join(tokens)+" "

wordcloud = WordCloud(width=1400, height=900,
                      background_color='white',
                      stopwords=stopwords,
                      min_font_size=8).generate(comment_words)

# plot the WordCloud image
plt.figure(figsize=(8, 8), facecolor=None)
plt.imshow(wordcloud)
plt.axis("off")
plt.tight_layout(pad=0)

plt.show()
