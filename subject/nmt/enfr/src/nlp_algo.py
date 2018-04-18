# created by yuhan
import fastText


# get language code by fasttext
def get_lang(docs, model_path, kmost=1):

    lang_classifier = fastText.load_model(model_path)

    return lang_classifier.predict(docs, kmost)
