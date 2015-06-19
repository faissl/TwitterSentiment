# This is the working file. Wanted to keep the original tweet_sentiment.py in tact. 

import sys    # Command line input functionality
import re     # Regular expressions functionality
import json   # JSON parsing functionality


def lines(fp):
    print str(len(fp.readlines()))

# Build sentiment dictionary of key pairs: term,score
def build_dict(file_name):
	sent_data = open(file_name)
	scores = {}                          # empty dictionary init
	for line in sent_data:
		term, score = line.split("\t")   # tab delimited file
		scores[term] = int(score)        # convert score to integer
	return scores

# Get unique words from a string. This function converts negative contractions, e.g., 
# "shouldn't" becomes "should not" and "can't" becomes "cannot". 
# RETURN: unique words as list
def get_unique_words(tweet_text):

	# Replace negative contractions with word + not, e.g., shouldn't -> should not
	# Change can't to cannot
	chk_text = tweet_text
	strPattern = re.compile("can't", re.IGNORECASE)
	tweet_text = strPattern.sub("cannot", tweet_text)
	strPattern = re.compile("n't", re.IGNORECASE)
	tweet_text = strPattern.sub(" not", tweet_text)

	# Get rid of carriage returns
	tweet_text = tweet_text.replace("\n", " ")
	tweet_text = tweet_text.replace("\r", " ")

	# Create a list of the words in the tweet. 
	tweet_words = re.sub("[^\w]", " ", tweet_text).split(' ')

	#if __debug__:
	#	print tweet_words

	return tweet_words


# Get individual tweet's score
# RETURN: words_score (totaled sentiment score for given tweet)
def tweet_score(tweet_text, scores):
	encoded_tweet = tweet_text.encode('utf-8')

	#if __debug__:
	#	print encoded_tweet

	# Get unique words from tweet text string
	tweet_words = get_unique_words(encoded_tweet)

	# Check to see if any of the words are in the sentiment dictionary. 
	# Add up positives; add up negatives
	words_score = 0
	for word in tweet_words:
		if word in scores.keys():		
			words_score += scores[word]

	return words_score



# Get sentiment score for each tweet. 
# Pass in twitter stream output file and sentiment dictionary.
def twitter_stream_score(file_name, scores):
	# Parse JSON file one line at a time
	with open(file_name) as f:
		for line in f: 
			tweet_data = json.loads(line)   # Parse JSON file one line at a time
			# Before you count line, see if it has 'text' key. Only score texts in English.
			if tweet_data.has_key('text'):
				if tweet_data['lang'] == 'en': 				
					print tweet_score(tweet_data['text'], scores)  # Send in the tweet's text.
					#print ('\n')


def main():
    sent_file = open(sys.argv[1])
    tweet_file = open(sys.argv[2])

    #print 'Lines in Sentiment File'
    #lines(sent_file)
    #print 'Lines in Twitter File'
    #lines(tweet_file)

    # Build a sentiment dictionary based on the AFINN-111 text file.
    scores = build_dict(sys.argv[1])

    # Get the scores for all streamed tweets that are in English
    twitter_stream_score(sys.argv[2], scores)


if __name__ == '__main__':
    main()
