# created by yuhan


# remove duplicate pair
def pair_deduplicate(doc_left, doc_right):
    
    doc_left_clean = []
    doc_right_clean = []
    
    # already exist
    doc_contain = set()
    
    for dl, dr in zip(doc_left, doc_right):
        if (dl not in doc_contain) and (dr not in doc_contain):
            doc_left_clean.append(dl)
            doc_right_clean.append(dr)
        
        doc_contain.add(dl)
        doc_contain.add(dr)
        
    print('remove duplicate from langauge pair')
    print('from {0} to {1}'.format(len(doc_left), len(doc_left_clean)))
    
    return doc_left_clean, doc_right_clean


# remove duplicate pair
def pair_oversize(doc_left, doc_right, th_num=80):
    
    doc_left_clean = []
    doc_right_clean = []
    
    for dl, dr in zip(doc_left, doc_right):
        
        ll = len(dl.split())
        lr = len(dr.split())
        
        if (ll < th_num) and (lr < th_num):
            doc_left_clean.append(dl)
            doc_right_clean.append(dr)
        
    print('remove oversize pair from langauge pair')
    print('from {0} to {1}'.format(len(doc_left), len(doc_left_clean)))
    
    return doc_left_clean, doc_right_clean


# remove mislang pair
def pair_mislang(doc_left, doc_right, lang_left, lang_right, model_path, kmost=2, verbose=False):
    
    res_left = get_lang(doc_left, model_path, kmost)
    res_right = get_lang(doc_right, model_path, kmost)
    
    doc_left_clean = []
    doc_right_clean = []
    
    doc_verbose = []
    
    for idx in range(len(doc_left)):
        
        rl = [l.split('__')[-1] for l in res_left[0][idx]]
        rr = [l.split('__')[-1] for l in res_right[0][idx]]
        
        if (lang_left in rl) and (lang_right in rr):
            doc_left_clean.append(doc_left[idx])
            doc_right_clean.append(doc_right[idx])
        elif verbose:
            doc_verbose.append(doc_left[idx]+' || '+doc_right[idx])
    
    print('remove mislength from langauge pair')
    print('from {0} to {1}'.format(len(doc_left), len(doc_left_clean)))
    
    if verbose:
        print('removed mislength sentences')
        for idx in random.sample(range(0,len(doc_verbose)), 25):
            print(doc_verbose[idx])
    
    return doc_left_clean, doc_right_clean
