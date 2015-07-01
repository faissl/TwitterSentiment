import sys    # Command line input functionality
import re     # Regular expressions functionality
import json   # JSON parsing functionality


#DBG = True
DBG = False


class TweetInfo:

	def __init__(self, tweet_score, tweet_word_list):
		self.score = tweet_score
		self.words = tweet_word_list

	def __repr__(self):
			return '\n<Tweet Info: Score - %r \n WORDS: %r>' % (self.score, self.words)


class NewTerm:

	def __init__(self):
		self.pos_count = 0
		self.neg_count = 0
		self.score = float(0)

	def __repr__(self):
		return '<New Sentiment Term %r %r %r>\n' % (self.pos_count, self.neg_count, self.score)


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
# RETURN: tweet words as list
def get_tweet_words(tweet_text):

	if (DBG):
		print ("Tweet Text prior to substitution: %s \n") % tweet_text

	# Replace negative contractions with word + not, e.g., shouldn't -> should not
	# Change can't to cannot

	#chk_text = tweet_text

	tweet_text = tweet_text.lower()

	# Check for RT - embedded manual retweet in text
	if tweet_text.find("rt") >= 0:
		tweet_text = ""
	else:
		# Not a retweet...get tweet's words. 
		strPattern = re.compile("can't", re.IGNORECASE)
		tweet_text = strPattern.sub("cannot", tweet_text)
		strPattern = re.compile("n't", re.IGNORECASE)
		tweet_text = strPattern.sub(" not", tweet_text)

		# Delete links and hashtags. Delete single characters. Delete digits. Delete underscores.
		strPattern = re.compile("http\S*|\s.\s|\W|\d|\s[a-z]\s|(_)", re.IGNORECASE)
		tweet_text = strPattern.sub(" ", tweet_text)

		# Get rid of carriage returns and new lines
		tweet_text = tweet_text.replace("\n", " ")
		tweet_text = tweet_text.replace("\r", " ")

		# Delete extra white spaces
		tweet_text = re.sub("\s+",' ', tweet_text)

	if DBG: 
		print ("Tweet Text after substitution: %s") % tweet_text

	# Create a list of the words in the tweet. 
	tweet_words = re.sub("[^\w]", " ", tweet_text).split(' ')

	# Remove empty strings
	tweet_words = filter(lambda flt: flt != "", tweet_words)

	if DBG:
		print tweet_words

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
	tweet_words = get_tweet_words(encoded_tweet)

	# Check to see if any of the words are in the sentiment dictionary. 
	# Add up positives; add up negatives

	non_sent_words = []
	words_score = 0
	for word in tweet_words:
		if word in scores:		
			words_score += scores[word]
		else:
			non_sent_words.append(word)

	if DBG: 
		print ("Found sentiment words: %s\t") % non_sent_words
		print("\n")

	return words_score, non_sent_words


# Get sentiment score for each tweet. 
# Pass in twitter stream output file and sentiment dictionary.
def twitter_stream_score(file_name, scores):

	# Get a list of the scores and a list of the words not in sentiment dictionary.
	# Treat as list of TweetInfo objects
	tweet_info = []

	# Parse JSON file one line at a time
	with open(file_name) as f:
		for line in f: 
			tweet_data = json.loads(line)   # Parse JSON file one line at a time
			# Before you count line, see if it has 'text' key. Only score texts in English.
			if tweet_data.has_key('text'):
				if tweet_data['lang'] == 'en' and not tweet_data['retweeted']: 	
					# Send tweet text. Returns tweet score and list of non-sentiment words. 			
					words_score, tweet_words = tweet_score(tweet_data['text'], scores) 
					if words_score != 0: 
						tweet_info_obj = TweetInfo(words_score, tweet_words)
						tweet_info.append(tweet_info_obj)

	return tweet_info

# Build new sentiment terms dictionary from the list of TweetInfo object's, which capture
# the tweet's overall score and the non-sentiment words.
def build_new_terms(tweet_info, scores):

	#Initialize new sentiment words dictionary. 
	new_terms = {}

	# Go through the list of tweets that registered positive or negative sentiment. Check 
	# the words in each tweet. If the word doesn't exist in the new_terms dict, add it and
	# initialize the positive, negative counts depending on score, to 1. If the word exists,
	# increment either its positive, negative counts depending on score. 
	for info in tweet_info:
		for word in info.words:
			if word not in new_terms:
				new_terms[word] = NewTerm()
			if info.score > 0:
				new_terms[word].pos_count += 1
			else:
				new_terms[word].neg_count += 1

	# Now grade the new terms. If they only have one instance in all the tweets (either negative
	# or positive), toss them. If the ratio is less than 2, toss them. Ensure there is no divide by zero. 
	filter_keys = []
	for term in new_terms: 
		if new_terms[term].pos_count > 1 or new_terms[term].neg_count > 1:
			if new_terms[term].pos_count < new_terms[term].neg_count:
				numerator = new_terms[term].pos_count
				denominator = new_terms[term].neg_count * -1
			else:
				numerator = new_terms[term].neg_count
				denominator = new_terms[term].pos_count
			if numerator == 0:
				numerator = 1
			new_terms[term].score = float(denominator)/float(numerator)

			# If the ratio of good to bad is less than 2, delete it
			if abs(new_terms[term].score) < 2:
				filter_keys.append(term)
		# Item doesn't meet criteria. Save it's key so item can be deleted after iteration.
		else: 
			filter_keys.append(term)
		
	# Delete the items that didn't meet the criteria. 
	for term in filter_keys:
		del new_terms[term]

	return new_terms


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
	tweet_info = twitter_stream_score(sys.argv[2], scores)

	if DBG: 
		for info in tweet_info:
			print info

	# Build a new sentiment term dictionary
	new_terms = build_new_terms(tweet_info, scores)

	# Sort the new terms for printing, largest to smallest absolute value
	for k, v in sorted(new_terms.items(),
		               key = lambda (k,v) : abs(new_terms[k].score), reverse = True):
		if abs(v.score) >= 2:
			print("%s %0.2f\n") %  (k, v.score)

if __name__ == '__main__':
    main()
