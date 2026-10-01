import random


def url_to_shortcode(username:str|None = None):
    a = list("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789")
    random.shuffle(a)
    b = random.choices(a,k=6)

    if username:
        return username + "/" + "".join(b)
    else:
        return "".join(b)




print(url_to_shortcode("Akshit"))