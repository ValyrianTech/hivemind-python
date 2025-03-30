from src.hivemind.state import HivemindState
from pprint import pprint

state = HivemindState(cid='Qme7adkj35wAHJqDns8WDYoZVMD5TWWnKBkN4w7aDV11MM')


# print(state.hivemind_id)
# print(state.option_cids)
# print(state.opinion_cids)
# pprint(state._rankings)
# print('--------')
# print(state._options)
#
# for question_index in range(len(state._opinions)):
#     print('Question:', question_index)
#     print(state._opinions[question_index])
#
#
# for question_index in range(len(state._opinions)):
#     print('Question:', question_index)
#     pprint(state._rankings[question_index])
#     print('----results----')
#     results = state.calculate_results(question_index=question_index)
#     pprint(results)
#
#     print('----contributions----')
#     pprint(state.contributions(results=results, question_index=question_index))

print('--------------------------')
print(state.cid())
print(state.option_cids)
print(state.final)

print('--------------------------')
while state.previous_cid is not None:
    state = HivemindState(cid=state.previous_cid)
    print(state.cid())
    print(state.option_cids)
    print(state.final)
    print('--------------------------')

print('a'*5000)