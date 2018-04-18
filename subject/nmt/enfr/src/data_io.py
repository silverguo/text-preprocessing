# created by yuhan


# load text from file
def load_text(file_path, encoding='UTF-8'):
    
    docs = []
    with open(file_path, 'r', encoding=encoding) as f:
        for line in f:
            docs.append(line.strip())
    
    return docs


# save text to file
def save_text(text, file_path, encoding='UTF-8'):
    
    # write to output
    with open(file_path, 'w', encoding=encoding) as f:
        f.write('\n'.join(text))
        f.write('\n')
    
    return
