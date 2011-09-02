mongodbsearch
=============

mongodbsearch is a simple Full-Text Indexer and Search engine for MongoDB built using python.

Requirements
------------

MongoDB (Tested on v 1.8.2)
Python 2.6+ (I haven't tested on Python 3.x but is should work)
pymongo

Examples
--------

###Adding a couple of documents to our Index

    #Connect to the database
    db = Connection()['mongosearch_test']

    #Instantiate the MongoSearch class
    mdb_search = mongodb_search(db)

    #Create a Document
    facets = {'category': 'books', 'type': 'hard cover' }
    text = "Creepella Von Cacklefur #1: The Thirteen Ghosts"
    fields = {'Author': 'Geronimo Stilton', 'Price': 7.99 }
    
    #Index Document
    mdb_search.index_document('id_1', text, facets=facets, ensure_index=['Author'], **fields)

    #Create another Document
    facets = {'category': 'books', 'type': 'soft cover' }
    text = "The Believing Brain: From Ghosts and Gods to Politics and Conspiracies---How We Construct Beliefs"
    fields = {'Author': 'Michael Shermer', 'Price': 21.12 }

    #Index another Document
    mdb_search.index_document('id_2', text, facets=facets, ensure_index=['Author'], **fields)
    
###Searching for a document
    documents, facets, document_count = mdb_search.search('Ghost', fields=['Author', 'Price'])
    
    print 'Document Count: %s' % document_count
    print ''

    for document in documents:
        print '%s: $%s' % (document['Author'], document['Price'])

    print ''
    for facet, values in facets.iteritems():
        print '---%s' % facet
        for name, value in values.iteritems():
            print '   %s: %s' % (name, value)

###Search for a document, with a condition
    documents, facets, document_count = mdb_search.search('Ghost', fields=['Author', 'Price'], 
                                                          conditions={'Author': 'Geronimo Stilton'})

    print 'Document Count: %s' % document_count
    print ''

    for document in documents:
        print '%s: $%s' % (document['Author'], document['Price'])
            
###Search with custom scoring/sorting
    documents, facets, document_count = mdb_search.search('Ghost', fields=['Author', 'Price'], scoring=('Author', -1))

    print 'Document Count: %s' % document_count
    print ''

    for document in documents:
        print '%s: $%s' % (document['Author'], document['Price'])      
    
#Known Issues and Needed Enhancments
- Need to add Boolean Logic to search query
- Some performance enhancements (reversing and re-increasing token counts)
- Delete a document
    
    
