import vk
import requests
from bs4 import BeautifulSoup
import datetime

group_id = xxxxxxxx # Id group

bots_DB = {}
count = 0

def get_user(short_name): # Получает user_ID из short_name
    data = vk_api.users.get(user_ids=short_name, )
    user_id = data[0]['id']
    return user_id

def get_create_account(user_id): #Получает дату создания аккаунта
    URL = 'https://vk.com/foaf.php?id='
    responce = requests.get(URL + str(user_id))
    soup = BeautifulSoup(responce.content,"html.parser")
    #if soup.find("ya:profilestate") == 'banned':
        #return 'Профиль забанен.'
    try:
        create_date = soup.find("ya:created")['dc:date']
    except:
        return 'Профиль недоступен.'
    create_date = datetime.datetime.strptime(create_date, "%Y-%m-%dT%H:%M:%S%z")
    return create_date

def get_comment_post(group_id, count=1, offset=0):
    post_id = {}
    postidlist = vk_api.wall.get(owner_id=group_id, count=count, offset=offset, extended=1)
    for postid in postidlist['items']:
        post_id[postid['id']] = {'count_com' : postid['comments']['count']}
        post_id[postid['id']]['text'] = postid['text']
    return post_id

def check_comments(group_id, post_id, comment_id, offset):
    res = {}
    comments = vk_api.wall.getComments(owner_id=group_id,
                                       post_id=post_id,
                                       offset=offset,
                                       comment_id=comment_id,
                                       count=100,
                                       sort='desc',
                                       extended=1)
    if comments['items'] == []:
        return res
    for comment in comments['items']:
        global count
        #count += 1
        if comment['from_id'] == 100:
            continue
        if comment['from_id'] not in res.keys():
            res[comment['from_id']] = {'date_create' : get_create_account(comment['from_id']), 'comment_id' : comment['id'], 'comment_text' : [comment['text']]}
            if res[comment['from_id']]['date_create'] == 'Профиль недоступен.':
                del res[comment['from_id']]
                continue
            if check_date(res[comment['from_id']]['date_create']):
                print(f"{str(comment['from_id'])} {res[comment['from_id']]['date_create']} {comment['text']}")
            else:
                del res[comment['from_id']]
            if 'thread' in comment.keys():
                if comment['thread']['count'] > 0:
                    comment_id = comment['id']
                    recur_res = check_comments(group_id=group_id,
                                          post_id=post_id,
                                          comment_id=comment_id,
                                          offset=0)

                    for key in recur_res.keys():
                        if key in res:
                            res[key]['comment_text'].append(recur_res[key]['comment_text'][0])
                        else:
                            res.update({key : recur_res[key]})
                    recur_res.clear()

    if comments['count'] < 100:
        #print(f'{count} необработанных коментариев')
        return res

    if offset >= comments['count']:
        #print(f'{count} необработанных коментариев')
        return res
    else:
        offset += 100
        recur_res = check_comments(group_id, post_id, offset=offset, comment_id=0)
        res.update(recur_res)
        recur_res.clear()
        return res




def check_date(date):
    date_war = datetime.datetime.strptime('2022-02-23T00:00:00+03:00', "%Y-%m-%dT%H:%M:%S%z")
    if date_war <= date:
        return True
    else:
        return False

def percent_bot_comment(bot_list, count_com):
    coms = 0
    for id in bot_list['items'].keys():
        coms += len(bot_list['items'][id]['comment_text'])
    if coms == 0:
        return 0
    return (coms / count_com) * 100

def main():
    count = 0
    bots_DB[group_id] = []
    post_list = get_comment_post(group_id=group_id, count=10)
    for post in post_list:
        print(f"Текст поста: {post_list[post]['text']}")
        print()
        bots_DB[group_id].append({post : {'items' : check_comments(group_id=group_id, post_id=post, comment_id=0, offset=0)}})
        bots_DB[group_id][count][post].update({'percent_bots' : percent_bot_comment(bots_DB[group_id][count][post], post_list[post]['count_com'])})
        bots_DB[group_id][count][post].update({'post_text' : post_list[post]['text'] })
        print(bots_DB[group_id][count][post]['percent_bots'],'%')
        count += 1
        print('=' * 100)
        print()
    print()

if __name__ == "__main__":
    token = "" #Ваш токен
    vk_api = vk.API(token, v='5.91')

    main()