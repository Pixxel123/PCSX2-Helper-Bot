# cpu_rating = [('message': 'Overkill', 'score': 2800),
#               ('message': 'Great for most games', 'score': 2400),
#               ('message': 'Good for most games', 'score': 2000),
#               ('message': 'Okay for 3D games', 'score': 1600),
#               ('message': 'Okay for 2D games', 'score': 1200),
#               ('message': 'Very slow', 'score': 800),
#               ('message': 'Awful', 'score': 0)]

myscore = 2900


# for i in range(len(cpu_rating)):
#     if myscore >= cpu_rating[i]['score']:
#         print(cpu_rating[i]['message'])
#         break
#     elif cpu_rating[i + 1]['score'] <= myscore <= cpu_rating[i]['score']:
#         print(cpu_rating[i + 1]['message'])
#         break

myscore = 900
cpu_rating = [(2800, 'Overkill'),
              (2400, 'Great for most'),
              (2000, 'Good for most games'),
              (1600, 'Okay for 3D games'),
              (1200, 'Okay for 2D games'),
              (800, 'Very Slow'),
              (0, 'Awful')]

cpu_rating = [(0, 'Awful'),
              (800, 'Very slow'),
              (1200, 'OK for 2D games'),
              (1600, 'OK for 3D games'),
              (2000, 'Good for most games'),
              (2400, 'Great for most'),
              (2800, 'Overkill')]
result = ""
for threshold, cpu_message in cpu_rating:
    if myscore >= threshold:
        result = cpu_message
    else:
        break
