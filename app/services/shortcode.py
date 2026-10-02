import random


def url_to_shortcode(alias:str|None = None): #Alias will be username or custom alias
    a = list("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789")
    random.shuffle(a)
    b = random.choices(a,k=6)

    if alias:
        return alias + "/" + "".join(b)
    else:
        return "".join(b)




print(url_to_shortcode("Akshit"))