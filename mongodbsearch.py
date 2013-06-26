from pymongo import Connection
import pymongo
import datetime
import stemmer
import re

class mongodb_search():

    def __init__(
            self,
            db,
            documents_collection_name='documents',
            tokens_collection_name='tokens'
    ):
        self.db = db
        self.servers = ','.join([x[0] for x in self.db.connection.nodes])
        self.collection_name = documents_collection_name
        self.tokens_collection_name = tokens_collection_name
        self.db[self.collection_name].ensure_index('text.token')
        self.db[self.collection_name].ensure_index('last_save_date')

    def index_document(self, id, text, facets=None, ensureindex=[], **kwargs):
        """This method indexes a document.
        param id: A unique identifier for the document being indexed.
        type id: str.
        param text: The text which you want indexed.
        type text: str.
        param facets: The facets associated with the indexed document ({'facet_name': value, 'another_facet': value }).
        type facets: dictionary.
        param ensureindex: A list of the mongodb fields you need a "Mongo" indexed created on.
        type ensureindex: list.
        param **kwargs: Any other fields you want associated with the document.
        returns: None.
        """

        #try the find the document in the database
        old_document = self.db[self.collection_name].find_one({'_id': id })

        #If the document exists, reverse the token counts (used for document ranking)
        #We reverse the token count and we re-insert them later on.
        #Doing this ensures that we don't count the tokens each time
        #You're updating a record.
        #TODO improve this to increment only once
        if old_document: self.__reverse_token_count(old_document)

        #get all the tokens
        tokens = re.findall('[0-9a-z]+', text, re.IGNORECASE)
        
        #compute all the counts for the keywords and stem them
        stemmed_tokens = {}
        for token in tokens:
            token = stemmer.Stem(token)
            if token in stemmed_tokens:
                stemmed_tokens[token]['qty'] += 1
            else:
                stemmed_tokens[token] = {'token': token, 'qty': 1 }

        #create the document to insert in the database
        doc = {'_id': id,
            'text': stemmed_tokens.values(),
            'last_save_date': datetime.datetime.utcnow(),
            'facets': facets
            }

        doc.update(kwargs)

        #save the document
        self.db[self.collection_name].save(doc)
        self.db[self.collection_name].ensure_index('text.token')

        for idx in ensureindex:
            self.db[self.collection_name].ensure_index(idx)

        #increment token counts (used for document ranking)
        self.__increment_token_count(stemmed_tokens)

    def __reverse_token_count(self, document):
        """Used to reverse the token frequencies and document count.
        param document: The document dictionary which is in MongoDb.
        type document: dictionary.
        returns: None. """

        #Loop through the document tokens and decrement the token and document counts
        for token in document['text']:
            self.db[self.tokens_collection_name].update({'_id': token['token'] }, {'$inc': {'qty': -token['qty'], 'doc': -1 }})

    def __increment_token_count(self, tokens):
        """Used to increment the token frequencies and document count.
           param document: The document dictionary which is in MongoDb.
           type document: dictionary.
           returns: None. """

        #Loop through the document tokens and increment the token and document count
        for token_qty in tokens.iteritems():
            token = token_qty[1]['token']
            qty = token_qty[1]['qty']

            self.db[self.tokens_collection_name].insert({'_id': token, 'qty': 0, 'doc': 0 })
            self.db[self.tokens_collection_name].update({'_id': token }, {'$inc': {'qty': qty, 'doc': 1 }})

    def __tfidf_scoring(self, documents, stemmed_tokens, *agrs, **kwargs):
        """This method will sort the documents retrieved by a search query using a TF/IDF algorithm.
           param documents: The documents which were retrieved by a search query.
           type documents: list of documents from Mongo.
           param stemmed_tokens: List of pre-stemmed tokens taken from your search query.
           type: list.
           returns: Ordered List of documents.
        """

        #get the total amount of documents
        document_count = self.db[self.collection_name].count()

        document_tokens_counts = {}
        token_counts = {}

        documents_with_score = []
        #loop through the documents
        for document in documents:
            #initialaize dictionary which will contain the document and the tokens/counts
            document_tokens_counts[document['_id']] = {'document': document}
            
            #loop through the tokens in the document
            for doc_token in document['text']:
                #loop through all the tokens which were created by stemming the keywords
                for text_token in stemmed_tokens:

                    #if the document contains one of the token which is in the keywords
                    if doc_token['token'] == text_token:
                        #Get the overall token count from the database, if we haven't done so already
                        if doc_token['token'] not in token_counts:
                            token_counts[doc_token['token']] = self.db[self.tokens_collection_name].find_one({'_id': doc_token['token']})

                        #calculate the term frequency
                        tf = float(doc_token['qty']) / float(len(document['text'])) 
                        #calculate the inverse document frequency
                        idf = float(document_count) / float(token_counts[doc_token['token']]['doc'])

            #set the document score
            document['score'] = (tf * idf)
            documents_with_score.append(document)

        #sort the documents by their score
        documents_with_score.sort(key=lambda x: x['score'])
        #reverse so the biggest value is the first record
        documents_with_score.reverse()

        return documents_with_score

    def search(self, text, max_recs=10, start=0, conditions=None, fields=[], scoring=None, hard_limit=False):
        """Searches a list of documents from Mongo.
        param text: The query you wish to search on.
        type text: str.
        param max_recs: The maximum number of records you wish to return.
        type max_recs: int.
        param start: The index which you'd like your search to start on.  Useful for paging.
        type start: int.
        param conditions: A Mongo query which you wish to used to fileter your results.
        type conditions: MongoDB Query.
        param fields: A list of fields you want to return.  By default MongoSearch only returns text, facets and the _id field from the document.
        type fields: list.
        param scoring: An optional MongoDB sort order.  If no sort order if provided, the relavency TF/IDF method will be used to sort documents.
        type scoring: MongoDB sort paramter.
        param hard_limit: If a hard limit is passed, the limit parameter will be passed to the Mongo query.  If this parameter is set to True the relevancy
                          algorithm and facets will stop working.  Much better for performance though.
        type hard_limit: bool.
        returns: list of documents, list of facets, total document count"""

        sort_condition = None

        #if the user has not passed a scoring function set it to the internal ranking function
        #we do not set it as the default in the method definition because 'self' is not yet defined
        if not scoring: scoring = self.__tfidf_scoring
        else: sort_condition = scoring

        #Get the tokens from the text field and stem them
        tokens = re.findall('[0-9a-z]+', text, re.IGNORECASE)
        stemmed_tokens = [] 
        for token in tokens:
            token = stemmer.Stem(token)
            stemmed_tokens.append(token)

        #create the query, the document can contain 'any' of the tokens
        query = {'text.token': {'$all': stemmed_tokens } }

        #if a seperate condition was passed update the query
        if conditions: query.update(conditions)

        #choose the fields to be returned
        select_fields = ['text', 'facets', '_id']
        select_fields.extend(fields)

        query_limit = 0
        if hard_limit: query_limit = max_recs

        document_count = 0
        #perform the query on mongo
        if sort_condition:
            
            documents = self.db[self.collection_name].find(query, fields=select_fields).sort(sort_condition[0], sort_condition[1]).limit(query_limit)

            document_count = documents.count()
        else:
            documents = self.db[self.collection_name].find(query, fields=select_fields).limit(query_limit)
            document_count = documents.count()
            
            #score the results
            documents = scoring(documents, stemmed_tokens)

        document_list = []
        #compute the facets
        facets = {}
        for document in documents:
            document_list.append(document)
            if document['facets']:
                for kvp in document['facets'].iteritems():
                    facet = kvp[0]
                    value = kvp[1]
                    if facet not in facets: facets[facet] = {}
                    if value not in facets[facet]: facets[facet][value] = 1
                    else: facets[facet][value] += 1
                document.pop('facets')
            document.pop('text')

        #return the results
        return document_list[start:start+max_recs], facets, document_count


