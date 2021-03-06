import json



def save_cookies(cookies):
    saved = json.dumps(cookies.get_dict())  # 保存
    with open('cookies.json', 'w') as f:
        f.write(saved)


def load_cookies(session):
    with open('cookies.json', 'r') as f:
        session.cookies.update(json.loads(f.read()))  # 读取
    return session


def save_html(index_content):
    with open('foo.html', 'w', encoding='utf-8') as f:
        f.write(index_content)