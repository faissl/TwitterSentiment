import sys    # Command line input functionality
import re     # Regular expressions functionality
import json   # JSON parsing functionality



class NewWord:

	def __init__(self):
		self.freq = 0
		self.score = float(0)

	def __repr__(self):
		return '<New Word %r %r>\n' % (self.freq, self.score)


# Get unique words from a string. This function converts negative contractions, e.g., 
# "shouldn't" becomes "should not" and "can't" becomes "cannot". 
# RETURN: tweet words as list
def get_tweet_words(tweet_text):

	encoded_tweet = tweet_text.encode('utf-8')

	if __debug__:
		print ("Tweet Text prior to substitution: %s \n") % tweet_text

	tweet_text = tweet_text.lower()

	# Check for RT - embedded manual retweet in text
	if tweet_text.find("rt") >= 0:
		tweet_text = ""
	else:
		# Not a retweet...get tweet's words. 
		# Replace can't with cannot. Replace n't with space and not.
		strPattern = re.compile("can't", re.IGNORECASE)
		tweet_text = strPattern.sub("cannot", tweet_text)
		strPattern = re.compile("n't", re.IGNORECASE)
		tweet_text = strPattern.sub(" not", tweet_text)

		# Delete links and hashtags. Delete single characters. Delete digits. Delete underscores.
		strPattern = re.compile("http\S*|#\S*|\s.\s|\W|\d|\s[a-z]\s|(_)", re.IGNORECASE)
		tweet_text = strPattern.sub(" ", tweet_text)

		# Get rid of carriage returns and new lines
		tweet_text = tweet_text.replace("\n", " ")
		tweet_text = tweet_text.replace("\r", " ")

		# Delete extra white spaces
		tweet_text = re.sub("\s+",' ', tweet_text)

	if __debug__: 
		print ("Tweet Text after substitution: %s") % tweet_text

	# Create a list of the words in the tweet. 
	tweet_words = re.sub("[^\w]", " ", tweet_text).split(' ')

	# Remove empty strings
	tweet_words = filter(lambda flt: flt != "", tweet_words)

	if __debug__:
		print tweet_words

	return tweet_words



# Get tweet words and compute frequency for each unique word in tweet streams.  
def main():

	# Keep a list of the unique words in the Twitter stream and keep a tally of their frequency.
	stream_words = {}
	agg_words = 0

	file_name = sys.argv[1]

	# Parse JSON file one line at a time
	with open(file_name) as f:
		for line in f: 
			tweet_data = json.loads(line)   # Parse JSON file one line at a time
			# Before you count line, see if it has 'text' key. Only score texts in English.
			if tweet_data.has_key('text'):
				# Don't double-count retweets.
				if tweet_data['lang'] == 'en' and not tweet_data['retweeted']: 	
					# Parse the tweet words from the tweet. Then add it to the dictionary containing
					# the unique words and their frequency. Create a new key if it hasn't already
					# been placed in dictionary. Increment frequency as necessary. 			
					tweet_words = get_tweet_words(tweet_data['text']) 

					# Check each word returned to see if its already in the dictionary containing
					# all the unique words found and their frequency. 
					for word in tweet_words:
						if word not in stream_words:
							stream_words[word] = NewWord()
						#Increment frequency of word
						stream_words[word].freq += 1
						agg_words += 1

	print agg_words

	# Build a dictionary of unique NewWord objects, which capture the word's frequency
	# and use it to create a histogram of the overall score of its occurrence in all tweets. 
	# Also return the total count of all words and their overall frequency.
	for word in stream_words:
		stream_words[word].score = float(stream_words[word].freq)/agg_words

	# Sort the twitter stream words for printing, largest to smallest absolute value
	for k, v in sorted(stream_words.items(),
		               key = lambda (k,v) : abs(stream_words[k].score), reverse = True):
		if v.score > .001:
			print("%s %0.5f") %  (k, v.score)

if __name__ == '__main__':
    main()
